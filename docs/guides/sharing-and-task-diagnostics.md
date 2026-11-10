# 分享密码与任务诊断

分享密码限速和任务诊断复用现有权限与 Django 默认缓存。部署配置前先按 [安装说明](../getting-started/installation.md) 执行迁移建表。

## 分享密码限速

默认开启，配置默认值如下：

```python
ORDLOOM_SHARE_LIMITS = {
    'enabled': True,
    'window_seconds': 300,
    'max_failures': 10,
    'per_ip_failures': 100,
}
```

固定窗口内，同一来源对同一页面/轮播最多 10 次失败，跨资源最多 100 次失败。
页面、轮播、公开数据读取和表单提交共用密码守卫，原分享状态、令牌、有效期、数据权限和 CSRF 检查继续生效。
校验前预留并发额度，正确密码释放本次预留，不抹掉已有失败；持续正确的轮询不累计失败。
无密码的入口提示不计数；受保护 POST 的缺失密码视为错误尝试。

错误密码仍返回 403。额度耗尽后返回 429、`Retry-After` 秒数及 `context.retry_after`；即使密码正确也需等待，在途校验也占额度。
页面与轮播保留密码重试入口，窗口结束后可以同密码重试。
缓存异常或配置无效时，受密码保护的访问返回通用 503；无密码页面不依赖这项限速缓存。
`enabled=False` 可显式沿用原密码校验行为。

来源只取可信 `REMOTE_ADDR`，不直接信任客户端 `X-Forwarded-For`。可信代理需正确设置连接来源；同一 NAT 出口共享来源预算。
缓存键使用 HMAC，不包含密码、原始 IP 或公开 UUID。

## 后台任务运行诊断

默认关闭。启用后，超级管理员账号菜单显示「后台任务运行诊断」：

```python
ORDLOOM_TASK_DIAGNOSTICS = {
    'enabled': True,
    'history_size': 10,
    'retention_seconds': 604800,
    'running_timeout_seconds': 3600,
    'stale_after_seconds': {
        'webhooks': 300,
        'report_exports': 900,
        'report_cleanup': 86400,
        'audit_retention': 86400,
        'share_visits': 86400,
    },
}
```

上例除 `enabled=True` 外均为默认值。普通 staff、匿名访问和单独 Bearer 凭据不能读取全局记录。
相对挂载点使用 `GET /api/task-diagnostics/?database=default`，响应不缓存；页面支持选择数据库与手动刷新。
切走取消请求，迟到响应不覆盖当前内容，权限失败清除旧记录。

诊断观测五类任务：

| 任务 | 原有管理命令 |
| --- | --- |
| Webhook 投递 | `ordloom_deliver_webhooks` |
| 报表导出 | `ordloom_export_reports` |
| 报表文件清理 | `ordloom_export_reports --prune-only` |
| 审计留存 | `ordloom_prune_audit` |
| 分享访问清理 | `ordloom_prune_share_visits` |

仅显式 `--apply` 写入执行记录，默认预览不写遥测；原参数、输出与退出码保持兼容。
仍由宿主调度原命令，网页不提供执行/重试/删除操作。启用诊断不替代各业务功能自身的开关。

记录按任务/数据库隔离，保存有限开始/结束 UTC 时间、耗时、状态、固定错误码与允许的整数计数；兼容宿主 `USE_TZ=False`。
不保存参数、查询结果、文件路径、目标地址、凭据、响应正文或原始异常。诊断配置或缓存故障不阻断原业务命令。
当前队列仅汇总数量；报表导出/清理仍限 `default` 数据库，其他命令按自身已有数据库参数支持范围观测。

「尚无执行记录」「近期未观测到执行」「执行超时或中断待核对」需结合调度器判断；缓存历史不证明进程死亡或实时在线，也不代替持久审计。
阈值仅用于界面提示，不自动重试或外发告警。

## 共享缓存与部署

多 Web/命令进程需使用同一个 `CACHES['default']`，并具有原子 `add/incr/decr`，例如正确配置的 Redis 或 Memcached。
每进程独立的 LocMemCache 无法提供跨进程额度或完整运行历史；非已识别共享缓存会在诊断页提示共享能力待确认。
缓存记录会因数量限制、TTL 或逐出消失，不作为不可变审计记录。

调整设置后运行 `python manage.py ordloom_check`，再按宿主流程重启 Web 与任务进程；具体部署步骤见 [部署与升级](../development/deployment.md)。
