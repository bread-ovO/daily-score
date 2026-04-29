# Changelog

## v1.1.0

- 新增群聊白名单配置 `group_whitelist`，留空时所有群可用。
- 管理员配置 `admin_user_ids` 留空时允许全体用户操作积分和查看报告。
- 修正插件元数据仓库地址为 `https://github.com/bread-ovO/daily-score`。

## v1.0.0

- 实现群聊积分功能，支持 `@成员 加一分` 和 `@成员 扣一分`。
- 支持日报、周报和累计积分排名。
- 支持自动定时发送日报和周报。
- 支持 JSON 持久化存储积分流水。
