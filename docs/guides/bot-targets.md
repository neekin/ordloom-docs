# 钉钉与飞书机器人配置

模型 Webhook 增加两种自定义群机器人文本适配，默认仍关闭。复用 0015 队列、当前创建者权限、租约、历史和管理入口，
。当前已验证本机协议接收器，尚未向真实群发送消息；机器人应用、双向聊天与自定义消息模板不在此能力内。

## 服务端配置

启用现有 GraphQL 模型白名单和 Webhook 后，由宿主维护以下配置。凭据使用宿主已有环境变量或秘密管理方式提供：

```python
import os

ORDLOOM_WEBHOOKS = {
    'enabled': True,
    'bot_targets': {
        'ops-ding': {
            'provider': 'dingtalk',
            'label': '运维钉钉群',
            'url': os.environ['ORDLOOM_DING_WEBHOOK_URL'],
            'secret': os.environ['ORDLOOM_DING_SIGNING_SECRET'],
            'keyword': '系统通知',
        },
        'ops-feishu': {
            'provider': 'feishu',
            'label': '运维飞书群',
            'url': os.environ['ORDLOOM_FEISHU_WEBHOOK_URL'],
            'secret': os.environ['ORDLOOM_FEISHU_SIGNING_SECRET'],
        },
    },
    # 原有通用目标可同时保留：
    # 'allowed_targets': ['https://receiver.example.com/ordloom/events'],
}
```

- 最多 100 个机器人目标。标识为字母开头的 1–64 位字母、数字、下划线或连字符；显示名称 1–100 字。
- 钉钉 URL 为机器人提供的完整地址，例如 `https://oapi.dingtalk.com/robot/send?access_token=<token>`，
  查询参数仅允许一个 `access_token`。不要预先拼接 `timestamp` 或 `sign`；每次尝试会重新计算。
- 飞书 URL 例如 `https://open.feishu.cn/open-apis/bot/v2/hook/<token>`，不接受查询参数。
- `secret` 是平台机器人页面生成的签名密钥；可省略以使用平台已有 IP/关键词策略。提供时需为 16–256 字符。
  `keyword` 是可选的固定文本前缀，最多 100 字，不接受控制字符或 `<>&`，不会提供 @ 全员配置。
- 默认 HTTPS；使用显式批准的内网代理/测试接收器时，仍受原 `allow_http`、`allowed_networks`、全部 DNS 地址校验、
  固定连接 IP、TLS 主机名校验和不跟随重定向规则约束。该代理须兼容对应平台协议。
- 多 worker/实例应使用共享缓存，并统一凭据和配置。凭据更新按宿主流程重启或重载所有 worker。

这些完整机器人 URL 不应放入通用 `allowed_targets`；通用目标会按原接口展示完整地址。
机器人配置通过 `bot_targets` 明确批准，不需要再添加到 `allowed_targets`。只有机器人目标时也可启用扩展。

## 后台操作与权限

在「账号菜单 → 模型 Webhook」选择带平台名称的目标，再选择已授权模型和保存/删除事件。
普通 staff 仍只管理本人端点及历史，超级管理员可管理全部；实际投递复核端点创建者当前模型/字段可见权限。
服务端保存 `bot:ops-ding` 等引用，目录和端点响应只包含标识、平台与显示名称；机器人 URL、令牌和签名密钥不写入端点、队列或管理响应。

机器人通知为固定文本，只含模型名、模型事件、发生时间和稳定的事件 UUID；不含源对象 ID、字段值、请求上下文或账号凭据。
后台「测试通知」仅排队，仍须由宿主显式运行 `ordloom_deliver_webhooks --apply`。
机器人密钥由宿主配置管理，界面不展示通用 Webhook 的一次性密钥或轮换按钮；原通用目标继续保留这些行为。

平台目标的实际 URL、平台类型、签名密钥和关键词参与私有配置指纹。待投递记录保存引用及带服务端主密钥的 HMAC 指纹，
读取历史时移除该指纹。配置变化后旧任务取消，避免把旧事件转发到新群或使用新凭据签署旧队列；
只改显示名称保留队列。后台更换目标则沿用配置代次和旧队列取消逻辑。已在网络中的请求仍无法撤回。

## 投递结果与节流

两种平台都要求 HTTP 成功且业务码为整数 `0` 才记成功：钉钉读取 `errcode`，飞书读取 `code`。
响应最多读取 8 KiB + 1 个越界探测字节，并使用同一网络截止时间；超额、非 JSON、重复键或非法状态不会记成功。
平台原始响应及错误文案仅短暂解析，不写历史、不返回界面；历史只保留 HTTP 状态与固定错误类别。

| 情况 | 处理 |
| --- | --- |
| HTTP 408/425/429/5xx 或网络失败 | 原有有界退避与重试上限 |
| 飞书 11232/11233/99991400 | 平台限流，按原有退避及 `Retry-After` 重试 |
| 其他非零业务码 | 失败并等待配置复核，可在后台明确重新投递 |
| 无有效整数业务码、响应不合法或超额 | `platform_response` 失败 |
| 目标撤回、当前权限撤销或配置指纹变化 | 取消，禁止网络请求 |

同一完整机器人 URL 共享最小发送间隔：钉钉 4 秒、飞书 1 秒。共享缓存的原子 `add` 实现跨端点等待；
等待期间返回 `deferred`，不消耗网络尝试数或重试额度。此策略是本实现的保守间隔，不代替平台配额和宿主流量验收。
独占临时 Redis 的 5 项检查已验证两个独立 worker 仅放行一个、别名共用等待、真实到期后恢复，以及缓存键不含地址或令牌。
连接失败后的重试仍可能造成重复群消息；稳定事件编号仅帮助人工识别，平台自定义机器人不提供本服务的去重保证。

## 协议依据与检查

2026-11-10 核对以下官方来源：

- [钉钉自定义机器人安全设置](https://open.dingtalk.com/document/robots/customize-robot-security-settings)：毫秒时间戳，
  用密钥对时间戳、换行与密钥组成的消息计算 HMAC-SHA256，Base64 后作为 URL 参数编码。
  官方页面由动态客户端加载；本轮同时读取该客户端引用的 [官方正文源](https://icms-document.oss-cn-beijing.aliyuncs.com/zh-CN/dingtalk/robots/topics/customize-robot-security-settings.html)。
- [钉钉官方接口参数](https://api.alidayu.com/docs/api.htm?apiId=37246) 用于核对文本结构与业务码字段，
  [当前群聊发送指南](https://open.dingtalk.com/document/orgapp/custom-bot-to-send-group-chat-messages) 及其
  [官方正文源](https://icms-document.oss-cn-beijing.aliyuncs.com/zh-CN/dingtalk/orgapp/topics/custom-bot-to-send-group-chat-messages.html) 用于核对签名发送与频控说明；未使用 TOP 网关作为目标。
- [飞书自定义机器人指南](https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot)：秒时间戳，
  时间戳、换行与密钥作为 HMAC 密钥，对空消息签名；时间戳和签名放入 JSON。
  [官方消息错误码说明](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/im-v1/guide/faq) 用于核对限流类别。

实现选择固定文本、服务端凭据、配置指纹、发送间隔及其他业务码终止策略，属于本项目设计。
以上协议检查和本机接收器均不能证明实际机器人凭据有效或群内已收到通知。

```bash
python scripts/test_backend.py ordloom.tests.test_webhook_bots ordloom.tests.test_webhooks
python scripts/test_webhook_bots.py
# PostgreSQL 临时数据库，不接受外部数据库：
python scripts/test_ownership_postgres.py --bots
# 独占临时 Redis，两个独立进程；仅需 Django 与测试用 redis 客户端：
uv run --python 3.12 --with 'django>=5.2,<5.3' --with redis python scripts/test_webhook_bot_cache.py
# React/Ant Design 的 jsdom 交互检查，不包含浏览器/Canvas：
cd frontend && npm run test:collaboration-ui
```

真实 HTTP 检查只启动并关闭自身的临时 Django 工程与 loopback 接收器，覆盖两类签名、200 业务失败、限流重试、
通用 Webhook 兼容、CSRF 和账号隔离，不向外部群发消息。真实群接收与当前浏览器界面验收仍需在授权测试环境完成。
