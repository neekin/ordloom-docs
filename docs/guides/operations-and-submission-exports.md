# 运维预检、任务告警与答卷后台导出

::: warning 源码新增能力
本页描述当前源码的 P1 增强，尚未包含在已发布的 Ordloom 1.0.0 中。使用对应源码安装并执行 `python manage.py migrate`，应用 `0027_operations_submission_exports`。现有同步导出、权限和默认关闭的可选功能保持原有行为。
:::

## 运行预检

```bash
python manage.py ordloom_check --json
python manage.py ordloom_check --probe --json
```

默认检查配置，不写入探测记录。显式 `--probe` 使用随机临时缓存键验证 add/get/incr，并在启用事件时通过随机临时组验证 Channels 收发；事件等待最多 3 秒，组清理另有短超时。不会修改业务缓存、发布模型事件或执行维护任务，不输出连接凭据与原始异常。

本机缓存或 InMemory channel layer 会提示跨进程能力未确认。单进程探测成功不证明多实例共享；Web、任务进程须使用相同 Redis/Memcached 连接及 `KEY_PREFIX`，多实例推送需要共享 Redis channel layer。缓存网络超时由宿主客户端配置。

## 任务主动告警

```python
ORDLOOM_TASK_DIAGNOSTICS = {
    'enabled': True,
    'stale_after_seconds': {
        'submission_exports': 900,
        'submission_cleanup': 86400,
    },
}
ORDLOOM_TASK_ALERTS = {
    'enabled': True,
    'cooldown_seconds': 3600,
    'lock_seconds': 30,
    'queue_threshold': 100,
    'max_recipients': 100,
}
```

告警默认关闭，依赖运行诊断及站内通知；告警状态、通知和账号表要求使用 default 数据库。由宿主 cron/任务平台周期执行：

```bash
# 默认只预览，不写告警状态、不发送通知
python manage.py ordloom_check_tasks --json
# 显式发送站内告警与恢复通知
python manage.py ordloom_check_tasks --apply --json
```

监测已启用功能的最近失败、执行超时、长期未观测及等待队列达到阈值。首次无记录有一个相应任务周期的观察宽限，尚在正常执行中的任务不被当作恢复；状态或缓存不可读取时也不发送恢复通知。恢复仅表示已观测状态恢复，不表示进程实时在线。

仅向当前有效超级管理员发送，普通 staff、外部服务身份和公开访问不能获取全局任务信息。通知可跳转至只读任务诊断。短期共享缓存租约协调多进程，数据库状态修订与通知唯一键避免重复；同一状态在冷却期内抑制，期满可提醒，旧评估结果不能覆盖新评估。通知与状态在同一事务中保存；缓存故障或评估失败不阻断原业务任务，命令返回失败供宿主监测。

不自动发送邮件、Webhook 或群机器人消息，不增加网页执行任务入口。收件人数超过预算会明确报错，不静默遗漏部分管理员。

## 答卷检索

```python
ORDLOOM_SUBMISSION_SEARCH_ROWS = 100000
```

原结果界面的表单、时间与关键词筛选继续使用。关键词大小写归一化后逐项匹配表单名、题目与答案，保留 Unicode 和 `%`、`_`、反斜线的字面语义，不跨题目拼接。

SQLite/PostgreSQL 在数据库内匹配规范化 JSON 文本投影并分页，默认最多处理 100000 份经表单/时间限定的源答卷，可配置 5000–1000000。该投影与原答卷一同保存、删除，不进入缓存或公开响应；它不是全文索引，性能取决于数据库、筛选范围和目标负载。

新迁移分批回填现有答卷；普通保存、`bulk_create`、`bulk_update` 自动维护。QuerySet `update()` 修改题目/答案/表单名会标记投影待修复；直接 SQL 修改后须主动重建：

```bash
python manage.py ordloom_reindex_submissions --json
python manage.py ordloom_reindex_submissions --apply --limit 10000 --json
# 外部 SQL 导入或直接修改后，分批重建全部投影
python manage.py ordloom_reindex_submissions --apply --all --limit 100000 --json
# 全量重建超过单批上限时，使用上次输出的 next_after_id 继续
python manage.py ordloom_reindex_submissions --apply --all --after-id 100000 --limit 100000 --json
```

命令支持 `--database`。投影未就绪或其他数据库使用原有 5000 份兼容扫描，超限明确提示修复/缩小范围。汇总仍限 5000 份及 200 个题目快照版本，未取消数值精度和资源预算。

## 启用私有后台导出

```python
ORDLOOM_SUBMISSION_EXPORTS = {
    'enabled': True,
    'retention_days': 7,
    'max_rows': 100000,
    'max_file_bytes': 8388608,
    'max_pending_per_user': 3,
    'max_artifacts_per_user': 10,
    'max_runs_per_user': 50,
    'lease_seconds': 300,
    'max_attempts': 3,
    'create_per_minute': 5,
}
```

默认关闭；启用后在「收集结果 → 后台导出」按当前筛选创建 CSV/Excel 任务，查看排队、生成、失败、可下载和过期状态，也可取消或清除文件。生成中的列表每 5 秒刷新，浏览器隐藏时暂停。原同步 CSV/Excel 入口保留。

任务表与答卷、页面、账号源表目前要求在 `default` 数据库。后台导出不依赖 GraphQL。文件存于私有数据库字段，不生成媒体目录公开 URL；数据按执行时读取，记录创建任务时的提交 ID 上界，之后新增答卷不混入。保存的是筛选配置与边界，不是创建时的业务值快照。

```bash
python manage.py ordloom_export_submissions --json
python manage.py ordloom_export_submissions --apply --limit 20 --json
python manage.py ordloom_export_submissions --apply --prune-only --json
```

由宿主调度命令执行，不内置 worker 调度平台。默认只预览，显式 `--apply` 才生成或清理文件；关闭功能后仍可用 `--prune-only` 清理。启用导出后，运行诊断额外显示答卷导出与清理两类任务。

创建、执行、完成前与下载都复核当前页面管理权限；个人资源遵循所有者/超级管理员，工作区资源复用当前管理员规则。普通 staff 只查看自己创建且当前仍可管理页面的导出，超级管理员可查看其管理范围内全部导出；下载还复核原创建账号及贡献答卷是否仍存在。只读/编辑共享不授予答卷结果管理权限。

创建请求使用 UUID 去重和共享缓存频控；租约、重试次数及条件更新阻止重复领取和迟到结果覆盖取消/新任务。文件到期、超出每账号保留预算或显式清除后不能再下载，后台清理负责回收字节。权限撤销不能收回已经下载的文件或中断已经通过校验的响应。

### API

所有入口使用后台 Session/CSRF，公开分享令牌与服务 Bearer 不授予访问权。路径相对于 Ordloom 挂载点：

| 方法 | 路径 | 用途 |
| --- | --- | --- |
| GET/POST | `/api/pages/<page_id>/submission-exports/` | 分页列出/创建 |
| GET/DELETE | `/api/pages/<page_id>/submission-exports/<run_id>/` | 查看/取消并清除 |
| GET | `/api/pages/<page_id>/submission-exports/<run_id>/download/` | 当前权限复核后下载 |

创建请求：

```json
{
  "request_id": "c2d147cd-94cd-4b7b-a323-d4be48595b74",
  "format": "csv",
  "filters": {"widget_id": "survey", "q": "杭州", "since": "2026-11-01T00:00:00+08:00"}
}
```

相同账号与请求编号只能用于相同页面、格式与筛选；配置不符为 409，频控 429，缓存故障 503，未完成/失效 409，过期下载 410。列表不返回文件内容、贡献源 ID 或原始错误。

## 推送能力声明

`visualDataCatalog.supportsPush` 按当前入口、事件开关和 Channels layer 是否配置返回，并受原模型/字段权限约束；依赖不可用时为 false。后台模型通知与组件推送并未重新开发，现有轮询和签名兜底保持原规则。

外部只读服务目录始终为 false；公开授权页仍使用轮询，不开放匿名模型订阅。true 表示配置具备后台推送能力，不保证网络可达或跨进程广播，连通性使用运行预检及实际部署验证。
