import asyncio
import json
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from zoneinfo import ZoneInfo

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star, register
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


PLUGIN_NAME = "astrbot_plugin_daily_score"
DEFAULT_TIMEZONE = "Asia/Shanghai"
WEEKDAY_NAMES = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
    "周一": 0,
    "周二": 1,
    "周三": 2,
    "周四": 3,
    "周五": 4,
    "周六": 5,
    "周日": 6,
    "星期一": 0,
    "星期二": 1,
    "星期三": 2,
    "星期四": 3,
    "星期五": 4,
    "星期六": 5,
    "星期日": 6,
    "星期天": 6,
}


@register(PLUGIN_NAME, "yinchangyu", "群聊每日积分日报和周报插件", "1.0.0")
class DailyScorePlugin(Star):
    def __init__(self, context: Context, config: Optional[AstrBotConfig] = None):
        super().__init__(context)
        self.config = config or {}
        self._lock = asyncio.Lock()
        self._scheduler_task: Optional[asyncio.Task] = None
        self._data_dir = Path(get_astrbot_data_path()) / "plugin_data" / PLUGIN_NAME
        self._data_path = self._data_dir / "scores.json"
        self._data: Dict[str, Any] = self._empty_data()

    async def initialize(self):
        self._data_dir.mkdir(parents=True, exist_ok=True)
        await self._load_data()
        if self._config_bool("enable_auto_report", True):
            self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    @filter.command_group("score")
    def score(self):
        pass

    @score.command("daily")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def daily_report(self, event: AstrMessageEvent):
        """发送本群今日日报排名"""
        async for result in self._handle_manual_report(event, "daily"):
            yield result

    @score.command("weekly")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def weekly_report(self, event: AstrMessageEvent):
        """发送本群本周周报排名"""
        async for result in self._handle_manual_report(event, "weekly"):
            yield result

    @score.command("total")
    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def total_report(self, event: AstrMessageEvent):
        """发送本群累计总分排名"""
        async for result in self._handle_manual_report(event, "total"):
            yield result

    @filter.event_message_type(filter.EventMessageType.GROUP_MESSAGE)
    async def handle_score_message(self, event: AstrMessageEvent):
        """处理 @成员 加一分 / @成员 扣一分"""
        parsed = self._parse_score_command(event)
        if parsed is None:
            return

        group_id = self._get_group_id(event)
        operator_id = self._get_sender_id(event)
        if not group_id or not operator_id:
            return

        if not self._is_group_allowed(group_id):
            return

        if not self._is_config_admin(operator_id):
            yield event.plain_result("你没有积分管理权限")
            return

        target_id, target_name, delta, error = parsed
        if error:
            yield event.plain_result(error)
            return

        now = self._now()
        async with self._lock:
            group = self._ensure_group(group_id)
            self._remember_origin(group, event)
            self._remember_member(group, target_id, target_name)
            record = {
                "group_id": group_id,
                "operator_id": operator_id,
                "target_id": target_id,
                "target_name": target_name,
                "delta": delta,
                "timestamp": int(now.timestamp()),
                "date": now.date().isoformat(),
                "iso_week": self._iso_week_key(now),
            }
            group["records"].append(record)
            today_score = self._sum_records(group["records"], target_id, date=record["date"])
            week_score = self._sum_records(
                group["records"], target_id, iso_week=record["iso_week"]
            )
            await self._save_data_locked()

        action = "加" if delta > 0 else "扣"
        yield event.plain_result(
            f"已为 {target_name} {action} 1 分，今日：{today_score}，本周：{week_score}"
        )

    async def terminate(self):
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        async with self._lock:
            await self._save_data_locked()

    async def _handle_manual_report(self, event: AstrMessageEvent, period: str):
        group_id = self._get_group_id(event)
        operator_id = self._get_sender_id(event)
        if not group_id or not operator_id:
            return

        if not self._is_group_allowed(group_id):
            yield event.plain_result("当前群未启用积分插件")
            return

        if not self._is_config_admin(operator_id):
            yield event.plain_result("你没有积分管理权限")
            return

        async with self._lock:
            group = self._ensure_group(group_id)
            self._remember_origin(group, event)
            text = self._build_report(group_id, period, self._now())
            await self._save_data_locked()

        yield event.plain_result(text)

    async def _scheduler_loop(self):
        while True:
            try:
                await self._run_due_reports()
                await asyncio.sleep(30)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.error(f"daily score scheduler error: {exc}")
                await asyncio.sleep(60)

    async def _run_due_reports(self):
        now = self._now()
        hour, minute = now.hour, now.minute
        daily_time = self._parse_hhmm(self._config_str("daily_report_time", "23:55"))
        weekly_time = self._parse_hhmm(self._config_str("weekly_report_time", "23:58"))
        weekly_day = self._parse_weekday(self._config_str("weekly_report_day", "Sunday"))

        async with self._lock:
            reports = self._data.setdefault("reports", {})
            should_daily = (hour, minute) == daily_time and reports.get("daily_date") != now.date().isoformat()
            should_weekly = (
                (hour, minute) == weekly_time
                and now.weekday() == weekly_day
                and reports.get("weekly_iso_week") != self._iso_week_key(now)
            )

            tasks: List[Tuple[str, str, str]] = []
            if should_daily:
                reports["daily_date"] = now.date().isoformat()
                tasks.extend(self._collect_report_tasks("daily", now))
            if should_weekly:
                reports["weekly_iso_week"] = self._iso_week_key(now)
                tasks.extend(self._collect_report_tasks("weekly", now))

            if tasks:
                await self._save_data_locked()

        for unified_msg_origin, period, text in tasks:
            try:
                await self.context.send_message(
                    unified_msg_origin, MessageChain().message(text)
                )
            except Exception as exc:
                logger.error(f"daily score send {period} report failed: {exc}")

    def _collect_report_tasks(self, period: str, now: datetime) -> List[Tuple[str, str, str]]:
        tasks: List[Tuple[str, str, str]] = []
        for group_id, group in self._data.get("groups", {}).items():
            if not self._is_group_allowed(group_id):
                continue
            origin = group.get("unified_msg_origin")
            if origin:
                tasks.append((origin, period, self._build_report(group_id, period, now)))
        return tasks

    def _parse_score_command(self, event: AstrMessageEvent):
        text = self._message_text(event)
        has_add = "加一分" in text
        has_sub = "扣一分" in text
        if not has_add and not has_sub:
            return None

        at_users = self._extract_at_users(event)
        if has_add and has_sub:
            return "", "", 0, "一次只能选择加一分或扣一分"
        if len(at_users) != 1:
            return "", "", 0, "请在消息中 @ 一位成员"

        target_id, target_name = at_users[0]
        return target_id, target_name, 1 if has_add else -1, ""

    def _extract_at_users(self, event: AstrMessageEvent) -> List[Tuple[str, str]]:
        users: List[Tuple[str, str]] = []
        for component in self._message_components(event):
            component_name = component.__class__.__name__.lower()
            component_type = str(getattr(component, "type", "")).lower()
            if component_name != "at" and component_type != "at":
                continue

            user_id = self._first_attr(
                component, ("qq", "user_id", "target", "id", "uin")
            )
            if user_id is None:
                continue
            target_id = str(user_id)
            target_name = self._first_attr(
                component, ("name", "nickname", "display", "card")
            )
            users.append((target_id, str(target_name or target_id)))
        return users

    def _build_report(self, group_id: str, period: str, now: datetime) -> str:
        group = self._data.get("groups", {}).get(group_id, {})
        records = group.get("records", [])
        members = group.get("members", {})
        ranking_limit = max(1, int(self._config_int("ranking_limit", 10)))

        if period == "daily":
            title = f"今日积分日报 {now.date().isoformat()}"
            filtered = [record for record in records if record.get("date") == now.date().isoformat()]
            empty_text = "今日暂无积分记录"
        elif period == "weekly":
            title = f"本周积分周报 {self._iso_week_key(now)}"
            filtered = [record for record in records if record.get("iso_week") == self._iso_week_key(now)]
            empty_text = "本周暂无积分记录"
        else:
            title = "累计积分排名"
            filtered = list(records)
            empty_text = "暂无积分记录"

        totals: Dict[str, int] = defaultdict(int)
        latest_names: Dict[str, str] = {}
        for record in filtered:
            target_id = str(record.get("target_id", ""))
            if not target_id:
                continue
            totals[target_id] += int(record.get("delta", 0))
            latest_names[target_id] = str(record.get("target_name") or target_id)

        if not totals:
            return f"{title}\n{empty_text}"

        ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
        lines = [title]
        for index, (target_id, score) in enumerate(ranked[:ranking_limit], start=1):
            name = members.get(target_id, {}).get("name") or latest_names.get(target_id) or target_id
            lines.append(f"{index}. {name} {score}分")
        return "\n".join(lines)

    def _sum_records(
        self,
        records: Iterable[Dict[str, Any]],
        target_id: str,
        date: Optional[str] = None,
        iso_week: Optional[str] = None,
    ) -> int:
        total = 0
        for record in records:
            if str(record.get("target_id")) != target_id:
                continue
            if date and record.get("date") != date:
                continue
            if iso_week and record.get("iso_week") != iso_week:
                continue
            total += int(record.get("delta", 0))
        return total

    async def _load_data(self):
        if not self._data_path.exists():
            self._data = self._empty_data()
            await self._save_data_locked()
            return

        try:
            self._data = json.loads(self._data_path.read_text(encoding="utf-8"))
            self._data.setdefault("version", 1)
            self._data.setdefault("groups", {})
            self._data.setdefault("reports", {})
        except Exception as exc:
            backup_path = self._data_path.with_suffix(
                f".broken-{datetime.now().strftime('%Y%m%d%H%M%S')}.json"
            )
            os.replace(self._data_path, backup_path)
            logger.error(f"daily score data broken, backup created: {backup_path}, {exc}")
            self._data = self._empty_data()
            await self._save_data_locked()

    async def _save_data_locked(self):
        self._data_dir.mkdir(parents=True, exist_ok=True)
        tmp_path = self._data_path.with_suffix(".json.tmp")
        tmp_path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        os.replace(tmp_path, self._data_path)

    def _empty_data(self) -> Dict[str, Any]:
        return {"version": 1, "groups": {}, "reports": {}}

    def _ensure_group(self, group_id: str) -> Dict[str, Any]:
        group = self._data.setdefault("groups", {}).setdefault(
            group_id, {"unified_msg_origin": "", "members": {}, "records": []}
        )
        group.setdefault("unified_msg_origin", "")
        group.setdefault("members", {})
        group.setdefault("records", [])
        return group

    def _remember_origin(self, group: Dict[str, Any], event: AstrMessageEvent):
        origin = getattr(event, "unified_msg_origin", "")
        if origin:
            group["unified_msg_origin"] = origin

    def _remember_member(self, group: Dict[str, Any], user_id: str, name: str):
        group.setdefault("members", {})[user_id] = {"name": name or user_id}

    def _is_config_admin(self, user_id: str) -> bool:
        admin_ids = self._config_list("admin_user_ids")
        return str(user_id) in {str(item) for item in admin_ids}

    def _is_group_allowed(self, group_id: str) -> bool:
        group_ids = self._config_list("group_whitelist")
        return not group_ids or str(group_id) in {str(item) for item in group_ids}

    def _message_text(self, event: AstrMessageEvent) -> str:
        return str(getattr(event, "message_str", "") or getattr(event.message_obj, "message_str", ""))

    def _message_components(self, event: AstrMessageEvent) -> List[Any]:
        if hasattr(event, "get_messages"):
            return list(event.get_messages())
        return list(getattr(event.message_obj, "message", []) or [])

    def _get_group_id(self, event: AstrMessageEvent) -> str:
        if hasattr(event, "get_group_id"):
            group_id = event.get_group_id()
            if group_id:
                return str(group_id)
        return str(getattr(event.message_obj, "group_id", "") or "")

    def _get_sender_id(self, event: AstrMessageEvent) -> str:
        if hasattr(event, "get_sender_id"):
            sender_id = event.get_sender_id()
            if sender_id:
                return str(sender_id)
        sender = getattr(event.message_obj, "sender", None)
        return str(
            self._first_attr(sender, ("user_id", "id", "qq", "uin")) or ""
        )

    def _now(self) -> datetime:
        try:
            tz = ZoneInfo(self._config_str("timezone", DEFAULT_TIMEZONE))
        except Exception:
            tz = ZoneInfo(DEFAULT_TIMEZONE)
        return datetime.now(tz)

    def _iso_week_key(self, value: datetime) -> str:
        iso = value.isocalendar()
        return f"{iso.year}-W{iso.week:02d}"

    def _parse_hhmm(self, value: str) -> Tuple[int, int]:
        try:
            hour_text, minute_text = value.strip().split(":", 1)
            hour = max(0, min(23, int(hour_text)))
            minute = max(0, min(59, int(minute_text)))
            return hour, minute
        except Exception:
            return 23, 55

    def _parse_weekday(self, value: str) -> int:
        return WEEKDAY_NAMES.get(value.strip().lower(), 6)

    def _config_str(self, key: str, default: str) -> str:
        value = self.config.get(key, default)
        return str(value if value not in (None, "") else default)

    def _config_int(self, key: str, default: int) -> int:
        try:
            return int(self.config.get(key, default))
        except Exception:
            return default

    def _config_bool(self, key: str, default: bool) -> bool:
        value = self.config.get(key, default)
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on", "是"}
        return bool(value)

    def _config_list(self, key: str) -> List[str]:
        value = self.config.get(key, [])
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return []

    def _first_attr(self, obj: Any, names: Iterable[str]) -> Any:
        if obj is None:
            return None
        if isinstance(obj, dict):
            for name in names:
                if name in obj and obj[name] not in (None, ""):
                    return obj[name]
            return None
        for name in names:
            value = getattr(obj, name, None)
            if value not in (None, ""):
                return value
        return None
