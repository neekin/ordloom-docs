# API 与数据契约

1.1.0 的 CMS 公开只读文章接口与会员 Session/CSRF API 由宿主显式挂载，路由、请求字段和边界见 [CMS 与会员 API](../guides/cms-and-members.md)。这些接口不授予通用后台写入权限。

商城另提供公开商品目录、当前会员订单及后台库存调整，使用 Session/CSRF、UUID 幂等编号与服务器核价，见 [商城 API](../guides/shop.md)。订单和库存不接受通用字段更新。

微信入口包括公众号 OAuth、小程序 code 交换、自己的绑定和平台签名回调；只有平台消息端点免 CSRF，身份写入沿用会员 Cookie/CSRF。见 [微信 API](../guides/wechat.md)。OpenID 与平台 session_key 不作为客户端会员凭据。

接口相对于插件挂载点。例如挂载到 `/admin/` 时，下面的 `/api/me/` 实际为 `/admin/api/me/`。

`model_key` 使用 `app_label.model_name`，例如 `projects.project`。下表管理接口保留 Django Session 与 CSRF 机制，外部只读数据服务的 Bearer 凭据不能替代管理会话。

## 常用接口

| 方法 | 相对地址 | 用途 |
| --- | --- | --- |
| GET | `/api/config/` | 登录及界面公开配置、CSRF 信息 |
| POST | `/api/login/` | 登录 |
| POST | `/api/logout/` | 退出 |
| GET | `/api/me/` | 当前账号与能力 |
| GET | `/api/captcha/` | 刷新验证码 |
| POST | `/api/password/` | 修改自己的密码 |
| GET / POST | `/api/account-password/<model_key>/` | 原生用户密码表单，使用 object_id 查询 |
| GET | `/api/menu/` | 当前账号的可访问菜单 |
| GET | `/api/meta/<model_key>/` | 字段、权限、默认值、分组和明细配置 |
| GET | `/api/list/<model_key>/` | 列表 |
| GET | `/api/detail/<model_key>/` | 详情，使用 object_id 查询 |
| GET | `/api/options/<model_key>/<field_name>/` | 关联选项 |
| POST | `/api/save/<model_key>/` | 主表及提交的关联明细保存 |
| POST | `/api/cell/<model_key>/` | 行内编辑 |
| GET | `/api/export/<model_key>/` | CSV 导出 |
| POST | `/api/delete-preview/<model_key>/` | 删除影响预览 |
| POST | `/api/delete/<model_key>/` | 删除 |
| GET | `/api/trash/<model_key>/` | 回收站 |
| POST | `/api/trash/<model_key>/restore/` | 恢复 |
| POST | `/api/trash/<model_key>/purge/` | 永久删除 |
| POST | `/api/upload/` | Multipart 文件上传 |
| GET | `/api/inline/<model_key>/<inline_key>/` | 明细读取 |
| POST | `/api/inline/<model_key>/<inline_key>/save/` | 单组明细保存 |
| POST | `/api/action/<model_key>/` | 原生业务 Action |
| GET / PUT | `/api/dashboard/` | 个人布局 |
| GET | `/api/dashboard-data/` | 工作台业务数据 |
| GET | `/api/log/` | 操作记录 |
| GET | `/api/health/` | 健康状态与版本 |
| GET | `/api/task-diagnostics/?database=default` | 默认关闭；超级管理员只读任务历史与队列汇总 |

任务诊断不提供执行、重试或删除 API。公开页面/轮播、公开数据与表单的密码限速共用预算；超限为 429 与 `Retry-After`，缓存故障为通用 503，详见 [指南](../guides/sharing-and-task-diagnostics.md)。

系统设置保存使用 `PUT` 或 `POST /api/config/save/`，需要站点配置修改权限。

## 页面与数据入口

| 方法 | 相对地址 | 内容 |
| --- | --- | --- |
| GET / POST | `/api/pages/` | 按当前资源范围读取或创建页面 |
| GET | `/api/share/<uuid>/` | 公开入口，继续核对状态、令牌和密码 |
| POST | `/api/share/<uuid>/submit/` | 公开页面表单提交与去重 |
| GET | `/api/pages/<id>/submissions/` | 当前资源管理范围内的答卷 |
| GET / POST | `/api/screen-playlists/` | 大屏轮播管理 |
| POST | `/api/graphql/` | Session/CSRF 下的受限只读 GraphQL |
| GET | `/api/datasets/catalog/` | 模型、字段与运算能力目录 |
| GET / POST | `/api/datasets/` | 数据集管理 |
| POST | `/api/datasets/<id>/publish/` | 发布不可变查询版本 |
| POST | `/api/datasets/<id>/execute/` | 显式版本、参数及当前权限执行 |
| GET / POST | `/api/reports/` | 自助报表管理 |
| POST | `/api/reports/<id>/execute/` | 报表执行 |
| GET / POST | `/api/report-boards/` | 跨报表看板管理 |
| POST | `/api/data/graphql/` | 独立只读服务凭据的受限 GraphQL |
| POST | `/api/data/datasets/<id>/versions/<number>/` | 独立只读服务执行固定版本 |

所有路径相对于实际挂载点。详细定义、实参与预算见 [GraphQL](../data/graphql.md)、[数据集](../data/datasets.md)、[报表](../data/reports.md) 和 [只读服务](../data/events-and-services.md)。
资源管理权不会自动授予源模型的业务数据权限；外部服务的 Bearer 不能访问管理写入接口，公开分享也不能执行私有报表。

答卷后台导出入口为 `GET/POST /api/pages/<id>/submission-exports/`、`GET/DELETE /api/pages/<id>/submission-exports/<run_id>/` 与 `GET /api/pages/<id>/submission-exports/<run_id>/download/`。这些接口自 1.0.1 起提供，权限、创建请求和预算见 [后台导出指南](../guides/operations-and-submission-exports.md)。任务告警通过宿主命令发送，不新增网页执行 API。

## 1.1.0 API 与配置扩展

1.1.0 新增 `GET/POST /api/pages/<id>/versions/`。GET 支持 `offset` 分页或 `version` 历史详情；POST 使用 `publish`、`restore` 或 `rollback` 操作，要求最新草稿修订、指纹及当前发布指针，协作工程还需配置令牌。角色与冲突规则见 [页面版本 API](../guides/p2-page-versions.md#api)。

原页面详情增加草稿修订、当前发布版本与未发布修改标识；公开分享、表单、取数和通知读取当前公开快照。公开入口不提供历史版本选择或发布能力。

图表增加可选 `values`、`series`，数据集绑定增加 `interaction`，报表引用增加 `reportInteraction`；后两项仅接受已有输出字段与已声明标量参数，见 [联动契约](../guides/p2-chart-linkage.md)。问卷章节、分步与类型化条件保存在原页面/题目配置，见 [问卷协议](../guides/p2-survey-steps.md)。

原 `GET /api/task-diagnostics/` 增加安全运行汇总和告警外发历史，权限仍限有效超级管理员；不新增网页执行能力。配置与观测边界见 [运行指标](../guides/p2-operations.md)。

## JSON 响应

成功：

```json
{"ok": true, "data": {"id": 1}}
```

失败：

```json
{"ok": false, "error": "校验失败", "errors": {"name": ["该名称已存在"]}}
```

部分错误还包含 `context`，例如验证码是否已经启用。除了检查 HTTP 状态，也应检查 `ok`。

## 登录与 CSRF

登录前读取配置，登录后读取账号信息，并按返回的 `csrf_token`、`csrf_cookie_name` 管理后续请求。登录会轮换 CSRF；不要把旧令牌永久缓存。

写入请求携带会话与 `X-CSRFToken`。已有前端客户端处理了 HttpOnly、会话 CSRF、自定义名称和会话切换取消，扩展组件优先复用该客户端。

## 主表保存

以下结构对应[第一个业务模块](../getting-started/quickstart.md)中的模型：

```json
{
  "data": {
    "name": "客户门户升级",
    "status": "draft",
    "budget": "12000.50",
    "description": "模型目录与明细需求整理"
  }
}
```

新增不传 `id`；编辑时在外层提供原始 `id`。`data` 必须是对象，合法空表单使用 `{"data": {}}`。JSON 请求使用 `application/json` 或 `+json`；上传和原生 Action 表单继续使用相应表单格式。

金额、大整数主键和字符主键按原值传递，不转换为浮点数。字段内部的 JSON、布尔和空值由实际表单解析。

## 分页、筛选与标识

列表常用参数为 `q`、`page`、`page_size`、`order_by`，单页上限 100。筛选通过 `f_<key>` 传递，但值必须来自接口元数据中的实际选项，不能直接假设 `f_status=draft` 就是该项目的筛选编码。

特殊主键优先使用详情查询形式：`/api/detail/projects.project/?object_id=...`。对查询值正确 URL 编码；旧的主键路径形式也继续兼容。

关联解析与导出可使用 `ids_json`，其内容是 JSON 数组，例如 `["crm/2026,a", "partner#1"]`。空数组表示明确的空选择；损坏的 JSON 不会退回到导出全部记录。

JSON 精确文本来源、凭据意图、明细上下文请使用各组件章节的契约。自定义客户端不能只复制视觉控件而省略服务端权限检查。

## 1.0.1 公开票据与数据扩展

`POST /api/share/<uuid>/events/` 按现有分享密码、独立链接和数据授权领取一次性票据；WebSocket `/ws/public-page-events/` 在首帧认证，只发送组件失效信号。模板预览/创建增加可选 `jsonFields`，报表 `chart.type` 支持 `antv:*` 与角色映射。详细请求、范围和默认开关见 [1.0.1 指南](../guides/conditional-pages-and-antv-reports.md)。

## 1.0.2 故障恢复与调度契约

已启用通知的公开分享 `content.dataGrant` 增加可选 `eventRevision`，票据请求可通过 `revision` 原样回传。它是不可解释的配置校验标识，不授予数据权限；原有客户端不传该字段仍可使用旧契约。当前分享入口、密码和授权验证后，配置变化返回 HTTP 409 与 `context.code: PUBLIC_PAGE_CHANGED`，新客户端重新获取分享内容后再申请票据。

公开取数和票据的临时故障返回安全 JSON 503 与 `Retry-After: 2`；共享额度耗尽返回 429 与等待提示。WebSocket 的 `retry` 指示重新取票，`refresh` 指示重新加载配置，`revoked` 指示清除旧结果并停止；消息不包含模型或业务字段。生命周期关闭 4000 可续票，配置关闭 4001 需重载，1013 可退避重试，真实撤权 4403 不自动恢复。

API 客户端会把 `Retry-After` 交给只读调度层，写请求不增加自动重试。三路并发、消费者取消、读取超时、公开映射隔离与刷新模式的详细规则见 [稳定性指南](../guides/resilience-and-release-gates.md)。


## 子应用 SDK v1（1.1.0 起）

员工目录 `GET /api/extensions/`、公开静态目录 `GET /api/extensions/public/`、前端资源 `GET /api/extensions/<app>/asset/`、专用页数据 `GET /api/extensions/<app>/pages/<page>/`。菜单与服务端数据分别校验权限，公开目录仅含显式公开组件；无网页任务执行接口。详见 [接入指南](../development/subapplications.md)。

`GET /api/extensions/directory/` 为重新鉴权的只读应用目录和行业配方，普通 staff 只看授权应用，超级管理员额外查看停用声明。安装参考信息为本地发行包介绍，不提供匿名安装状态或在线安装/命令执行。见[生态开放](../development/ecosystem.md)。

P1 增强保留上述协议；`GET /api/task-diagnostics/` 在原 `alert_deliveries` 中新增可选 `admission`，返回入队意图状态计数与最近 10 条安全元数据。权限仍限当前有效超级管理员，`admitted` 表示已进入队列，不能当作机器人发送成功。无 HTTP 补偿/任务执行入口；由宿主命令定时执行，见 [P1 指南](../guides/p1-admission-and-contracts.md)。
