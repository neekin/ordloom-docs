# 模型 Webhook 与群机器人

通过批准目标订阅模型变更，后台重新验证当前权限后投递。外部 HTTP 与群机器人由宿主配置和调度。

## 模型 Webhook

此扩展默认关闭，使用已有 GraphQL 注册模型与字段可见权限，需要启用数据层（Python ≥ 3.10、Django ≥ 5.2），
先执行迁移 `0015_webhooks`。关闭扩展时核心包仍支持 Django 4.2，也不需要外部队列服务。

```python
ORDLOOM_WEBHOOKS = {
    'enabled': True,
    'allowed_targets': ['https://receiver.example.com/ordloom/events'],
    'allowed_networks': [],        # 默认只连接公网单播地址；内网可显式加入 '10.0.0.0/8' 等 CIDR
    'allow_http': False,           # 默认 HTTPS；内网 HTTP 也需明确允许且地址在完整白名单中
    'timeout_seconds': 5,          # DNS 完成后的连接、TLS 与响应共用网络时间预算，1–15 秒
    'max_attempts': 5,             # 一轮最多 1–10 次尝试
    'retry_seconds': 30,           # 指数退避起始间隔，1–3600 秒，最大间隔 1 小时
    'lease_seconds': 300,          # 认领租约，60–3600 秒；worker 崩溃后可恢复
    'max_endpoints_per_user': 20,  # 每创建者未归档端点上限，1–100
    'manual_per_minute': 30,       # 手动测试/重新投递频控，1–1000；多实例使用共享 cache
    # 'signing_key': '至少32字符的独立服务端主密钥',  # 默认使用 Django SECRET_KEY
    # 'permission_context': 'myapp.webhooks.permission_request',
}
```

`allowed_targets` 是最多 100 个**完整接收 URL**，限制协议、主机、端口和路径；界面只选择已批准地址。
地址不接受账号、查询参数、片段或未编码的非 ASCII 路径。每次投递重新检查 DNS 的全部 A/AAAA 地址，
任一地址不符合公网/显式网络策略即停止，连接固定到已校验的 IP，同时保留原 HTTPS SNI、证书主机名与 Host 校验。
多播与未指定地址始终拒绝；不使用环境代理、不跟随重定向、不持久保存响应体。DNS 解析时限由宿主解析器管理；
网络预算从解析完成后计算。内网 HTTPS 接收器使用受宿主系统信任的证书。

登录后通过账号菜单「模型 Webhook」管理。普通 staff 只管理本人端点与历史，超级管理员可管理全部，
实际投递始终以**端点创建者**当前账号状态和模型/字段可见规则授权，管理员编辑别人的端点不会提升接收权限。
模型目录与现有变更订阅一致，排除 Webhook 自身的控制模型；账号停用、权限撤销、模型撤回或地址不再批准时停止投递。
归档会停用端点并保留历史，恢复后保持停用。修改地址、模型、事件或启用状态、轮换密钥会增加配置代次并取消旧队列；
只修改名称保留队列。记录中保留当时地址和代次。已在网络中的请求无法撤回，迟到 worker 不能覆盖新的投递状态。

### 事件、事务与权限上下文

事件是模型级失效通知，保存（含创建/更新/软删除）为 `model.saved`，物理删除为 `model.deleted`：

```json
{"schema_version":1,"id":"事件 UUID","event":"model.saved","model":"sales.order","occurred_at":"2026-11-10T02:00:00+00:00"}
```

载荷只有模型、事件类型、时间和事件编号，不复制对象主键、字段值或请求凭据。
接收方可用通知触发授权数据重读；读取依然走现有 QuerySet、软删除、对象和字段权限链。
外部只读服务身份可按「外部只读数据服务（0016）」另行配置；Webhook 不会给接收方自动授予数据接口权限。

### 钉钉与飞书机器人

可选 `bot_targets` 配置将模型事件发送为钉钉/飞书文本消息，复用 0015。
完整机器人地址与平台密钥仅由宿主服务端保存；界面选择批准目标，端点和历史保存 `bot:<id>` 引用。
使用各平台签名及业务成功码校验；凭据变化取消旧队列，发送间隔等待不消耗重试次数，当前创建者权限保持生效。
通用 Webhook 的完整地址、Ordloom HMAC 与一次性密钥流程继续兼容。
配置示例、协议来源、状态分类、共享缓存及真实群验收边界见 [机器人接入文档](bot-targets.md)。

常规 `save()` / `delete()` 产生事件，队列保存在源数据库；同一事务内同一端点、模型、事件和配置代次合并。
回滚包含队列回滚，保存点回滚后可正常再次排队；历史迁移模型不触发实时通知。业务 API 已使用事务，
宿主直接保存模型时，应显式使用 `transaction.atomic(using=...)` 才能保证业务与队列联合回滚；
独立 autocommit 写入已先提交业务 SQL，之后的排队错误无法回滚那次业务写入。
`update()` / `bulk_create()` / 原始 SQL 不发模型信号，可信宿主可在同一业务事务内调用：

```python
from django.db import transaction
from ordloom.webhooks.signals import publish

with transaction.atomic(using='default'):
    Order.objects.filter(...).update(...)
    publish('sales.order', event='saved', using='default')
```

后台会重新从同库加载创建者，不持久化浏览器 Session 或请求头。默认权限请求带当前账号和空 Session；
若已有规则依赖租户等请求上下文，可配置受信任的 `permission_context(user, using) -> HttpRequest`，
由宿主根据账号与数据库补齐确定的租户信息。接口保存时校验真实请求和后台请求，投递前再次校验；上下文缺失或规则异常均拒绝投递。
端点、队列与账号应在相同数据库，投递命令使用对应 `--database`，连接路由由宿主管理。

### 投递任务与重试

```bash
python manage.py ordloom_deliver_webhooks --json               # 只预览待处理数量
python manage.py ordloom_deliver_webhooks --apply --limit 100 --json
# 多数据库：加 --database <alias>；--limit 为 1–1000，默认 100
```

由宿主 cron/任务调度器周期调用，应用不默认启动外发。worker 必须在业务事务外执行，认领事务提交后才进行 HTTP。
每次调用数量有上限，使用认领令牌与租约避免并发覆盖；租约过期标记旧尝试并恢复。网络失败、408/425/429 和 5xx 指数退避重试，
有限度遵从 `Retry-After`；其他 HTTP 非 2xx（包括 3xx）终止当前轮。达到上限后失败，管理界面可在同一配置代次重新投递。
人工重试保留事件 UUID、正文和累计次数，开启新一轮预算。测试通知由 HTTP 管理端排队，实际外发仍由 worker 执行。
命令遇到失败/待重试结果返回退出码 1，数据库记录保留实际状态；成功、取消或无任务时返回 0。

投递是**至少一次**：接收方需原子记录 `(端点编号, 验签正文 id)` 去重。
日志按创建者隔离，端点、投递及逐次尝试都分页；只展示状态、HTTP 码、有限错误代码和时间，不展示响应内容或签名密钥。

### HMAC 协议与接收方

创建/轮换时一次性返回 `secret`，以后读取配置不返回它。它由服务端主密钥、端点 UUID 和随机轮换 nonce 通过 HMAC-SHA256 派生，
签名密钥本身不以明文存入数据库。主密钥变更需要同步接收方密钥；可使用独立 `signing_key` 避免 Django `SECRET_KEY` 轮换影响此协议。

| 请求头 | 内容 |
| --- | --- |
| `X-Ordloom-Hook` | 端点公开 UUID，用来选择接收方保存的密钥 |
| `X-Ordloom-Id` | 事件 UUID，与正文 `id` 相同，重试不变 |
| `X-Ordloom-Timestamp` | 当前尝试的 Unix 秒数，重试重新签名 |
| `X-Ordloom-Signature` | `v1=` + HMAC-SHA256 十六进制摘要 |

摘要输入是 `timestamp 的 ASCII 字节 + b'.' + 原始请求正文`，使用上面返回的密钥字符串作为 UTF-8 HMAC key。
接收方验签前不要重新序列化 JSON。包内 `verify_signature` 常量时间比较并默认检查 300 秒时效。
下面展示 Django 验签入口；注释位置需接入接收方自己的持久队列，再返回成功确认：

```python
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from ordloom.webhooks.worker import verify_signature

HOOK_KEYS = {'接收端配置的端点 UUID': '创建或轮换后保存的 secret'}

@csrf_exempt  # 此接收端以 HMAC 验证来源，不使用浏览器 Session 作为认证
@require_POST
def receive(request):
    hook = request.headers.get('X-Ordloom-Hook')
    key = HOOK_KEYS.get(hook)
    if not key or not verify_signature(key, request.headers.get('X-Ordloom-Timestamp'),
                                     request.body, request.headers.get('X-Ordloom-Signature')):
        return HttpResponse(status=403)
    try:
        event = json.loads(request.body)
        if event['id'] != request.headers.get('X-Ordloom-Id'):
            return HttpResponse(status=400)
    except (ValueError, KeyError, TypeError):
        return HttpResponse(status=400)
    # 接收方在自己的事务中以 (hook, event['id']) 唯一键持久排队，重复事件直接确认。
    return HttpResponse(status=204)
```

网络限制依据 [OWASP SSRF 指南](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)，
TLS 行为沿用 [Python HTTPSConnection](https://docs.python.org/3/library/http.client.html#http.client.HTTPSConnection) 的默认验证。
事务与保存点行为见 [Django 事务说明](https://docs.djangoproject.com/en/5.2/topics/db/transactions/)。

### 管理接口与隔离验收

均需当前 staff Session；写入要求 CSRF，列表每页 20 条，接口前缀随应用挂载点变化：

| 路径 | 用途 |
| --- | --- |
| `GET/POST /api/webhooks/` | 创建人/超级管理员列表与创建；可用 `archived=true` 查看归档 |
| `GET /api/webhooks/catalog/` | 当前模型目录、批准地址和尝试上限 |
| `GET/PUT/DELETE /api/webhooks/<id>/` | 详情、修改或归档；写入传当前 `revision` |
| `POST /api/webhooks/<id>/rotate/` | `{"revision":1}` 轮换密钥并取消旧队列 |
| `POST /api/webhooks/<id>/test/` | `{"revision":1,"request_id":"UUID"}` 幂等排入测试事件 |
| `GET /api/webhooks/<id>/deliveries/?page=1` | 投递分页，包含当时地址/配置代次和有限状态信息 |
| `GET /api/webhooks/<id>/deliveries/<delivery>/?page=1` | 投递详情和尝试分页 |
| `POST /api/webhooks/<id>/deliveries/<delivery>/` | `{"action":"retry"}` 或 `{"action":"cancel"}` |

创建内容为 `name`、批准的 `url`、1–20 个 `models`、`events=['saved','deleted']` 和可选 `enabled`（默认 false）。
修改冲突返回 409，不覆盖旧修订；归档恢复传 `{"revision":当前修订,"archived":false}`，保持停用。
所有 HTTP 请求只管理队列，生产路由不提供直接执行投递的端点。

仓库脚本 `scripts/dev_fields.py --webhooks --production --port=8660` 在临时 SQLite 和本机临时端口创建隔离接收器，
只向自己的 loopback 接收器发送：首次 503、之后 204，用于真实签名/重试验收。
`frontend` 下 `npm run test:webhooks` 使用该夹具（ego-browser，账号 `demo / demo-only`）；
夹具中的执行控制路由仅在该脚本存在，不进入安装包生产路由。
