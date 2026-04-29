# AstrBot Daily Score

群聊每日积分插件。管理员在群里发送 `@某人 加一分` 或 `@某人 扣一分`，插件记录积分流水，并生成日报、周报和累计排名。

## 功能

- 按群隔离积分数据
- 按配置名单控制管理员权限
- 支持 `@成员 加一分` / `@成员 扣一分`
- 每天 23:55 自动发送今日日报
- 每周日 23:58 自动发送本周周报
- 支持手动查看日报、周报和累计榜

## 配置

在 AstrBot 插件管理页配置：

```json
{
  "admin_user_ids": ["123456"],
  "group_whitelist": ["987654321"],
  "enable_auto_report": true,
  "timezone": "Asia/Shanghai",
  "daily_report_time": "23:55",
  "weekly_report_day": "Sunday",
  "weekly_report_time": "23:58",
  "ranking_limit": 10
}
```

`admin_user_ids` 填允许操作积分的用户 ID。`group_whitelist` 填允许使用插件的群 ID，留空表示所有群可用。自动报告依赖群聊里已有一次有效管理命令或手动报告命令，用于记录 AstrBot 的 `unified_msg_origin`。

## 命令

```text
@张三 加一分
@张三 扣一分
/score daily
/score weekly
/score total
```

加减分成功后会回复目标成员今日分和本周分。日报统计当天流水，周报统计本周一到周日流水，累计榜统计全部历史流水。

## 数据

积分数据保存在 AstrBot 数据目录：

```text
data/plugin_data/astrbot_plugin_daily_score/scores.json
```

数据文件损坏时，插件会把原文件备份为 `scores.broken-YYYYMMDDHHMMSS.json`，然后创建新的空数据文件。
