# API 与数据契约

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
    "description": "第一阶段需求整理"
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
