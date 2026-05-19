# AstrBot Daily Score

群聊每日积分插件。管理员在群里发送 `@成员 加一分 理由` 或 `@成员 扣一分 理由`，插件会记录积分流水，并生成日报、周报、月榜、累计榜和积分明细。

## 功能特性

- 按群隔离积分数据
- 通过配置名单控制积分管理员和重置权限
- 支持加分、扣分和操作理由记录
- 拦截操作者给自己扣分
- 支持日报、周报、月榜和累计榜
- 排行榜使用 AstrBot 自带 HTML t2i 渲染为智人排行图片
- 图片渲染失败时自动回退为文本排行
- 支持查看今日、本周、累计积分明细
- 支持清空当前群积分流水
- 使用 JSON 文件持久化保存数据

## 安装

在 AstrBot 插件目录安装：

```bash
cd AstrBot/data/plugins
git clone https://github.com/bread-ovO/daily-score.git astrbot_plugin_daily_score
```

安装后在 AstrBot WebUI 的插件管理页重载插件。

## 配置

在 AstrBot 插件管理页配置。AstrBot 会根据 `_conf_schema.json` 生成可视化配置项。

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

| 配置项 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `admin_user_ids` | list | `[]` | 允许操作积分和查看报告的用户 ID，留空表示全体可用 |
| `reset_user_ids` | list | `[]` | 允许清空当前群积分记录的用户 ID |
| `group_whitelist` | list | `[]` | 允许使用插件的群 ID，留空表示所有群可用 |
| `enable_auto_report` | bool | `true` | 启用日报和周报自动发送 |
| `report_subscribe_groups` | list | `[]` | 订阅自动日报和周报的群 ID |
| `timezone` | string | `Asia/Shanghai` | 统计和定时任务使用的时区 |
| `daily_report_time` | string | `23:55` | 日报发送时间，格式 `HH:MM` |
| `weekly_report_day` | string | `Sunday` | 周报发送星期，支持英文星期和 `周一` 到 `周日` |
| `weekly_report_time` | string | `23:58` | 周报发送时间，格式 `HH:MM` |
| `ranking_limit` | int | `10` | 排行榜展示人数 |
| `detail_limit` | int | `20` | 积分明细展示条数 |

自动报告需要目标群先触发一次有效管理命令或手动报告命令，用于记录 AstrBot 的 `unified_msg_origin`。

## 命令

| 命令 | 说明 |
| --- | --- |
| `@张三 加一分 作业完成质量高` | 为成员加 1 分并记录理由 |
| `@张三 扣一分 迟到` | 为成员扣 1 分并记录理由 |
| `/score daily` | 查看今日日报 |
| `/score weekly` | 查看本周周报 |
| `/score monthly` | 查看智人分数最高月榜 |
| `/score month` | 查看智人分数最高月榜 |
| `/score 月榜` | 查看智人分数最高月榜 |
| `/score total` | 查看累计榜 |
| `/score detail` | 查看今日积分明细 |
| `/score detail weekly` | 查看本周积分明细 |
| `/score detail total` | 查看累计积分明细 |
| `/score detail @张三` | 查看指定成员今日积分明细 |
| `/score 明细` | 查看今日积分明细 |
| `/分数明细` | 查看今日积分明细 |
| `/score reset` | 清空当前群积分流水 |
| `/score 重置` | 清空当前群积分流水 |

## 排行规则

- 日报统计当天积分流水
- 周报统计当前 ISO 周积分流水
- 月榜统计当前自然月积分流水
- 累计榜统计全部历史积分流水
- 排行榜默认按分数从高到低排列
- 同分时按用户 ID 升序排列
- 智人排行图片展示名次、昵称、用户 ID、分数、加分次数、扣分次数和记录数

## 权限规则

- `admin_user_ids` 控制加分、扣分、查看报告和查看明细
- `reset_user_ids` 控制重置积分流水
- `group_whitelist` 控制插件生效群
- 操作者给自己扣分会返回 `自己不能给自己扣分`

## 数据存储

积分数据保存在 AstrBot 数据目录：

```text
data/plugin_data/astrbot_plugin_daily_score/scores.json
```

数据文件损坏时，插件会把原文件备份为：

```text
scores.broken-YYYYMMDDHHMMSS.json
```

随后创建新的空数据文件。

## 常见问题

### 自动报告没有发送

确认以下配置：

- `enable_auto_report` 为 `true`
- 当前群 ID 已加入 `report_subscribe_groups`
- 群里已执行过一次有效管理命令或手动报告命令
- `timezone`、`daily_report_time`、`weekly_report_day`、`weekly_report_time` 符合预期

### 排行榜以文本形式发送

HTML t2i 渲染失败时，插件会发送文本排行榜。查看 AstrBot 日志中的 `daily score render ranking image failed` 可定位渲染服务问题。

## 版本

当前版本：`v1.5.0`

## 许可证

本项目使用 `AGPL-3.0 License`，详见 [LICENSE](LICENSE)。
