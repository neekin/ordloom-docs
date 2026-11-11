# CMS 与基础会员子应用

CMS/会员 0.1.0 基于 Ordloom 1.1.0 的 SDK v1，源码目录是 `apps/ordloom-cms` 和 `apps/ordloom-members`，包名分别为 `ordloom-cms`、`ordloom-members`，Python 模块为 `ordloom_cms`、`ordloom_members`。它们依赖第一阶段子应用 SDK，各自维护模型、迁移、Admin、ESM 入口与任务；无需修改 Ordloom 核心即可注册菜单和专用页面。两个子应用都可选装。

子应用依赖 `ordloom>=1.1.0,<2`，可直接从 PyPI 安装并自动解析核心依赖；不要求修改 Ordloom 核心源码。

## 安装到宿主

安装到宿主虚拟环境：

```bash
python -m pip install ordloom-cms==0.1.0 ordloom-members==0.1.0
```

保留宿主原来的 Django 认证、Session、CSRF、模板及 Ordloom 配置，按需增加：

```python
INSTALLED_APPS += [
    "ordloom_cms.apps.ExtensionConfig",
    "ordloom_members.apps.ExtensionConfig",
]

ORDLOOM_MEMBERS = {
    "registration_enabled": False,
    "session_seconds": 86400,
    "per_minute": 20,
    "user_factory": None,
}
```

在宿主 URLconf 中显式挂载公开入口。CMS 无默认根站点，具体地址包含站点标识：

```python
from django.urls import include, path

urlpatterns += [
    path("cms/", include("ordloom_cms.urls")),
    path("members/", include("ordloom_members.urls")),
]
```

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```

本批没有增加 Ordloom 核心迁移；两个子应用各有 `0001_initial`，会员关联 `AUTH_USER_MODEL`，不替换宿主 User。从 1.0.2 升级到 1.1.0 时，还需执行核心迁移至 0030。公开文件仍由宿主媒体存储提供，生产不要使用开发文件服务器。

## CMS：编辑与发布

后台「内容管理」包含内容站点、栏目、标签、文章与 SDK 内容概览。站点默认禁止公开访问；管理员填写站点标识、负责人和编辑成员后，具有 `ordloom_cms.publish_site` 的人员才可开放站点。可选域名只约束访问 Host，不创建域名、代理或 TLS 配置。

1. 创建栏目、标签和文章；正文使用原有 Markdown 编辑器，支持封面图片。
2. 在文章列表选中记录，执行「送审当前草稿」。修改正文、标题、摘要、栏目、封面或标签会恢复草稿状态，需要重新送审。
3. 具有 `ordloom_cms.publish_article` 和文章修改权限的人员执行「审核并发布」，生成不可变内容快照；重复发布相同最新内容不会新增版本。
4. 后续编辑保留原公开快照。通过「下线公开版本」立即取消公开读取，发布历史保留；内容概览显示最近 20 篇可见文章及各自最近 10 次发布的版本摘要。

发布内容包括标题、摘要、Markdown 正文、封面 URL、栏目和标签快照。公开 HTML 经 Markdown + 白名单清洗，禁止脚本、事件属性与危险协议。媒体文件本体未复制到版本；移动或删除文件会影响历史封面。栏目与标签名称变化不会追溯改写旧版本。站点和文章首次发布后不能通过管理表单修改公开标识，文章也不能改换站点。

文章的「公开 / 登录会员」范围及站点公开开关是**当前访问策略**，不会随内容快照恢复。编辑访问范围需要发布权限。后台 staff Session 不等于会员会话，不能直接阅读会员内容。CMS 单独安装时会员文章始终拒绝公开读取。

| 公开端点（使用上面的挂载方式） | 行为 |
| --- | --- |
| `/cms/main/` | 站点文章列表，`q` 搜索标题/摘要、`section` 栏目、`page` 分页 |
| `/cms/main/welcome/` | 已发布文章 HTML；会员文章缺少有效会员时返回 403 |
| `/cms/main/sitemap.xml` | 仅公开文章 URL，不包含会员文章，最多 10000 篇 |
| `/cms/api/v1/main/articles/` | 分页 JSON 列表，每页 20 篇，不暴露草稿或未授权会员内容 |
| `/cms/api/v1/main/articles/welcome/` | 已发布文章 JSON，含原 Markdown 与清洗后的 `body_html` |

公开接口只支持 GET，响应不缓存。页码范围 1–10000，搜索词最多 100 字，栏目标识最多 50 字；非法参数返回 404，不存在或关闭站点返回 404。会员访问不开放通用后台查询或 GraphQL 权限。

## CMS 权限

复用宿主 Django `view/add/change/delete` 模型权限和原有 ModelAdmin API，不另建管理登录。普通 staff 只可管理本人负责或被加入编辑成员的站点内容；超级管理员可管理全部。站点范围与宿主模型权限同时生效，加入编辑成员本身不会授予模型权限。拥有站点修改权限的编辑可维护该站点编辑成员。站点负责人仅超级管理员可在管理表单调整。

发布还需要 `publish_article`，开放站点还需要 `publish_site`。创建文章可自动记录当前账号；栏目、标签和文章只允许选择管理范围内的站点，栏目与标签必须属于文章站点。权限撤销或移出站点后，后续读取和操作重新校验。可在宿主继承对应 Admin 增加已有业务范围规则。

H5/大屏组件库增加公开的「内容入口」组件，配置标题、说明和**站内路径**；路径应与实际挂载方式一致，默认 `/cms/main/`。这是一张入口卡片，不会自动读取文章列表或开放任意 API，也不宣称支持在线内容数据绑定。

## 会员：注册、登录与个人中心

公开 `/members/` 提供注册（默认关闭）、登录、基础资料、修改密码与退出；后台「会员管理」提供会员、分组与 SDK 会员概览。会员分组仅用于业务分类，**不是** Django 用户组，不授予后台权限；停用分组后不再向会员展示。基础会员管理遵守宿主模型权限，不默认以创建人隔离整个客户库，额外组织隔离由宿主 Admin `get_queryset` / 对象权限继续约束。

会员关联宿主现有 User。注册只创建普通、非 staff、非 superuser 账号和会员档案；已有账号不能被注册流程认领。后台可给已有有效普通账号建立会员档案，档案创建后不能通过管理表单换绑账号。显示名称、联系邮箱、电话是会员资料，邮箱和电话**未经验证**，不应作为已认证凭据；修改联系邮箱不修改登录标识。

登录使用宿主 `authenticate` 和 `USERNAME_FIELD`。会员会话在同一个宿主 Django Session 中保存独立标记，不调用后台 `auth_login` / `auth_logout`；会员登录、改密和退出不会替换同浏览器已有后台身份，但共享宿主 Session 存储与 Cookie，并非第二套 Cookie。每次读取复核会员启用、User 活跃、非 staff、有效期及密码哈希；停用、到期、密码重置或升级为 staff 会使旧会员会话失效。改密保留当前会员会话，其他会员会话下次读取失效。

| `/members/api/v1/` 下的端点 | 请求与用途 |
| --- | --- |
| `session/` | GET；`data.member`、`csrf_token`、`registration_enabled` |
| `register/` | POST；`identity`、`password`，可选 `display_name/email/phone`；成功 201 |
| `login/` | POST；`identity`、`password` |
| `profile/` | POST；仅当前会员 `display_name/email/phone`，拒绝身份、启用与分组字段 |
| `password/` | POST；`old_password`、`new_password` |
| `logout/` | POST；清除会员标记 |

POST 使用 JSON 和宿主 CSRF：先 GET `session/` 取得 token，再在同源携带 Cookie 与 `X-CSRFToken` 请求；HTML 门户内置 CSRF。请求体最多 8 KiB，密码 10–128 字并执行宿主密码校验器。不要将 API 作为免 CSRF 的跨域身份接口。

注册、登录、改密和资料写入使用原共享 cache 的计数原语，按来源和账号固定 60 秒窗口限速；默认每窗口 20 次，范围 1–120。返回 429 + `Retry-After: 60`；缓存不可用时拒绝写入并返回 503，API 的频控故障可重试。多实例需使用共享 Redis；客户端地址使用 `REMOTE_ADDR`，代理信任配置由宿主负责。计数键使用 HMAC，不保存原始账号或 IP。会员会话时长可设 300–2592000 秒。

## 自定义 User 与扩展

已验证用户名用户及邮箱登录/UUID 主键用户。宿主 User 若有额外必填字段，配置可信账号工厂：

```python
def create_member_user(identity, password, profile):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    return User._default_manager.create_user(
        **{User.USERNAME_FIELD: identity},
        password=password,
        # 在宿主这里填充业务必填字段。
    )

ORDLOOM_MEMBERS = {
    "registration_enabled": True,
    "user_factory": "myproject.accounts.create_member_user",
}
```

工厂必须创建并返回与请求登录标识一致的普通活跃用户，不应修改既有用户或发送外部消息。账号与会员需路由至同一 default 数据库，创建在一个事务内；工厂失败不留下半个注册。应用模型、注册事务及发布事务以 default 数据库为当前支持范围。

`ORDLOOM_DISABLED_APPS = ["cms", "members"]` 可分别停用 SDK 目录、管理模块与公开入口，不删除数据。宿主未挂载公开 URL 时，后台模型与 SDK 页面仍可用，概览隐藏缺少的公开链接。

```bash
python manage.py ordloom_run_app_task ext:cms.audit --user 1
python manage.py ordloom_run_app_task ext:members.audit --user 1 --apply
```

两项任务检查当前账号可见范围，不修改业务记录；复用 SDK 权限、共享缓存租约与任务运行诊断。SDK 可见对象检查当前最多 1000 条，不代表无上限统计或持久审计。

## 验证与后续

本地验证入口：`scripts/test_products.py`（可选 `--email-user`、`--cms-only`、`--members-only`）、`scripts/test_ownership_postgres.py --products`、`scripts/test_products_install.py --output <新证据路径>`。临时浏览器宿主 `scripts/dev_products.py` 仅使用新建临时数据库与 loopback，不接触业务工程数据。

CMS/会员本身不包含复杂内容区块/页面主题、CMS 全文历史恢复与定时发布、附件版本副本、会员短信/邮件验证、找回密码、积分/等级/付费订阅或微信身份绑定。第三阶段独立 [商城 MVP](shop.md) 已复用会员档案实现商品、库存与订单；支付、退款和第三方回调需另行设计。云函数继续仅调研。

可选 [微信接入 MVP](wechat.md) 已通过会员会话来源校验接入公众号/小程序绑定与登录；会员基础包仍不自动创建或合并微信身份。普通密码会话保持原行为。
