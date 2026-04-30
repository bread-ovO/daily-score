# AstrBot Daily Score

群聊每日积分插件。管理员在群里发送 `@某人 加一分 理由` 或 `@某人 扣一分 理由`，插件记录积分流水，并生成日报、周报、累计排名和积分明细。指定用户可清空当前群积分记录。

## 功能

- 按群隔离积分数据
- 按配置名单控制管理员权限
- 支持 `@成员 加一分 理由` / `@成员 扣一分 理由`
- 每天 23:55 自动发送今日日报
- 每周日 23:58 自动发送本周周报
- 支持手动查看日报、周报、累计榜和积分明细
- 支持指定用户清空当前群积分记录

## 配置

在 AstrBot 插件管理页配置：

```json
{
  "admin_user_ids": ["123456"],
  "reset_user_ids": ["123456"],
  "group_whitelist": ["987654321"],
  "enable_auto_report": true,
  "report_subscribe_groups": ["987654321"],
  "timezone": "Asia/Shanghai",
  "daily_report_time": "23:55",
  "weekly_report_day": "Sunday",
  "weekly_report_time": "23:58",
  "ranking_limit": 10,
  "detail_limit": 20
}
```

`admin_user_ids` 填允许操作积分的用户 ID，留空表示全体可用。`reset_user_ids` 填允许清空当前群积分记录的用户 ID。`group_whitelist` 填允许使用插件的群 ID，留空表示所有群可用。`report_subscribe_groups` 填订阅自动日报和周报的群 ID，留空表示不自动发送。`detail_limit` 控制积分明细最多显示的记录数。自动报告依赖群聊里已有一次有效管理命令或手动报告命令，用于记录 AstrBot 的 `unified_msg_origin`。

## 命令

```text
@张三 加一分 作业完成质量高
@张三 扣一分 迟到
/score daily
/score weekly
/score total
/score detail
/score 明细
/分数明细
/score detail weekly
/score detail total
/score detail @张三
/score reset
/score 重置
```

加减分成功后会回复目标成员今日分、本周分和本次操作理由。日报统计当天流水，周报统计本周一到周日流水，累计榜统计全部历史流水。积分明细默认展示今日流水，可通过 `weekly` 查看本周明细，通过 `total` 查看累计明细，在命令中 `@成员` 可只查看该成员明细。`/score reset` 和 `/score 重置` 清空当前群全部积分流水，保留群配置和成员名缓存。

## 数据

积分数据保存在 AstrBot 数据目录：

```text
data/plugin_data/astrbot_plugin_daily_score/scores.json
```

数据文件损坏时，插件会把原文件备份为 `scores.broken-YYYYMMDDHHMMSS.json`，然后创建新的空数据文件。
