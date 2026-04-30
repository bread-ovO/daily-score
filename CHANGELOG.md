# Changelog

## v1.4.0

- 新增 `reset_user_ids` 配置，只有配置中的用户可以清空积分记录。
- 新增 `/score reset` 和 `/score 重置` 命令，清空当前群全部积分流水。

## v1.3.0

- 加分和扣分记录支持保存操作理由。
- 新增 `/score detail`、`/score details`、`/score 明细` 和 `/分数明细` 积分明细命令。
- 新增 `detail_limit` 配置控制明细显示条数。

## v1.2.0

- 新增自动报告订阅配置 `report_subscribe_groups`，只有配置中的群会收到日报和周报。
- 自动报告订阅列表留空时不发送日报和周报。

## v1.1.0

- 新增群聊白名单配置 `group_whitelist`，留空时所有群可用。
- 管理员配置 `admin_user_ids` 留空时允许全体用户操作积分和查看报告。
- 修正插件元数据仓库地址为 `https://github.com/bread-ovO/daily-score`。

## v1.0.0

- 实现群聊积分功能，支持 `@成员 加一分` 和 `@成员 扣一分`。
- 支持日报、周报和累计积分排名。
- 支持自动定时发送日报和周报。
- 支持 JSON 持久化存储积分流水。
