# 站内通知、日志与审计留存

站内消息按接收人隔离，操作日志按当前业务范围读取；留存清理由明确配置的维护命令执行。

## 持久通知中心

先执行 `python manage.py migrate` 应用 `0014_notifications_retention`。此能力不依赖 GraphQL、Channels 或外部消息服务。
顶栏「消息中心」显示当前账号的持久收件箱，支持未读计数、每页 20 条、状态筛选、标记已读/未读，以及当前快照的全部已读。
快照之后新到的消息保持未读。超级管理员也只能读取自己的收件箱；原有「最近操作」继续显示操作记录。
超级管理员可搜索有效 staff 接收人，一次向 1–50 人发送纯文本通知；普通 staff 无发送或接收人目录权限。

```python
ORDLOOM_NOTIFICATIONS = {
    'enabled': True,         # 默认开启；False 时管理端点返回 404、界面隐藏入口
    'poll_seconds': 60,      # 未读计数间隔，15–3600 整数秒
    'send_per_minute': 10,   # 每发送人每分钟请求限额，1–1000
}
```

计数请求不重叠，浏览器隐藏时取消并暂停，恢复时立即读取；关闭收件箱会取消未完成的列表请求。
UI 使用普通文本渲染。自助改密、TOTP 开启/关闭及公开数据授权变更会和业务操作同事务写入通知，写入失败时回滚该操作。
这些自动通知不复制密码、动态码、密钥、分享令牌、查询参数值、页面名称或业务结果。
通知链接只记录站内资源引用，每次读取按当前所有权重新判断是否提供跳转；链接不授予数据权限。

宿主可在自己的业务事务中创建通知：

```python
from django.db import transaction
from ordloom.notifications import notify

with transaction.atomic():
    # 宿主业务保存……
    notice = notify(staff_user, '任务处理完成', '请查看当前处理结果。',
                    category='general', level='success', dedupe_key='job:123:finished')
```

`notify` 对停用或非 staff 接收人返回 `None`；去重键按接收人唯一，相同内容重试返回原记录并保留已读状态，改变内容会报错。
可传 `using=<数据库别名>`，应与宿主事务和接收人所属数据库一致；自动授权通知沿用页面数据库。
`target` 可为 `{'kind':'security'}`，或 `{'kind':'page|dataset|report|playlist','id':'非负整数标识'}`（`kind` 取其中一种）；兼容历史导入的零主键资源，不接受任意 URL。

管理 API（均为当前 Session 与 staff 权限；写入要求 CSRF）：

| 路径 | 行为 |
| --- | --- |
| `GET /api/notifications/?state=all|read|unread&page=1` | 自己的收件箱；返回 `snapshot` 和未读数 |
| `GET /api/notifications/summary/` | 未读数和计数刷新间隔 |
| `GET/PUT /api/notifications/<id>/` | 读取或设置自己的 `{"read":true|false}` |
| `POST /api/notifications/read-all/` | `{"before_id":"snapshot 值"}`，仅处理快照内记录 |
| `GET /api/notifications/recipients/?q=账号&page=1` | 超级管理员搜索有效 staff，每页 20 人 |
| `POST /api/notifications/` | 超级管理员发送；`request_id` 为 UUID，`recipients` 为账号标识字符串数组，加 `title`、`message`、可选 `level`、`target` |

发送重试应复用相同请求 UUID 与内容；去重按发送人、接收人及 UUID 隔离，冲突返回 409，批量写入全部回滚。
达到发送请求限额返回 429 与 `Retry-After`；多实例使用共享 cache。此处负责站内投递，外发通知见下文模型 Webhook。

## 审计留存与分批清理

0014 同时提供不可改写的 `AuditRetentionBatch` 摘要表。默认不删除任何历史审计；可以分别配置操作记录与公开授权变更的保留周期：

```python
ORDLOOM_AUDIT_RETENTION = {
    'admin_log_days': None,    # None 永久保留，或 1–36500 整数天
    'grant_audit_days': None,
    'batch_size': 500,         # 每批 1–1000 条
    'max_rows': 10000,         # 每次、每类最多 1–100000 条
}
```

```bash
python manage.py ordloom_prune_audit --json          # 只预览候选数量，不改数据库
python manage.py ordloom_prune_audit --apply --json  # 显式清理
# 多数据库工程：加 --database <alias>
```

命令以开始时固定的截止时间和主键上界选取严格早于保留周期的记录，不追赶本次之后插入的数据。
每个批次在同一事务中删除并追加摘要，仅包含执行编号、记录类型、截止时间、数量与执行时间。
它不存原记录内容，也不清理自己的摘要、业务表、页面、答卷、数据集或不可变发布版本。
遇到关联业务记录时阻止本批次，不执行连带删除或置空；发生错误时该批次回滚、退出码为 1，之前成功批次仍有匹配摘要，可再次运行。
达到数量上限时 `has_more` 表示仍有候选记录；定时运行可由宿主任务调度器或系统 cron 调用，应用不会默认启动清理任务。

超级管理员可在「操作记录 → 审计留存」只读查看当前策略和最近 20 个已提交批次，接口为 `GET /api/audit-retention/`。
普通 staff 不可读取全局策略；网页没有删除入口。`ordloom_check` 会检查留存和通知配置是否合法。
