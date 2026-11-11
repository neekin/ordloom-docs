# 配置参考

开发源码提供可选 `ORDLOOM_MEMBERS` 注册开关、会话时长、共享缓存频控与宿主账号工厂，完整默认值见 [CMS 与会员配置](../guides/cms-and-members.md)。默认不开放注册，CMS 站点另有公开开关。

`ORDLOOM_SHOP` 控制可选商城目录/下单开关、待确认截止时间和频控额度，见 [商城配置](../guides/shop.md)。目录与下单均默认关闭，会员停用时商城连带停用。

`ORDLOOM_WECHAT` 控制可选微信接入、可信公开源站、服务端凭据引用、时间窗口与留存；默认关闭，凭据不通过后台输入/回传。见 [微信配置与平台要求](../guides/wechat.md)。

以下为 Ordloom 1.1.0 读取的配置名称，统一使用 `ORDLOOM_*`。

## 分享与后台任务

| 设置 | 默认 / 行为 |
| --- | --- |
| `ORDLOOM_SHARE_LIMITS` | 默认开启；300 秒内同来源/资源 10 次、同来源跨资源 100 次失败预算 |
| `ORDLOOM_TASK_DIAGNOSTICS` | 默认关闭；启用后超级管理员只读查看安全执行元数据与队列汇总 |

完整配置、共享缓存要求和保留边界见 [分享密码与任务诊断](../guides/sharing-and-task-diagnostics.md)。

1.0.1 的 `ORDLOOM_TASK_ALERTS`、`ORDLOOM_SUBMISSION_EXPORTS` 默认关闭；`ORDLOOM_SUBMISSION_SEARCH_ROWS` 默认 100000，详见 [P1 运维与答卷指南](../guides/operations-and-submission-exports.md)。这些增强自 1.0.1 起提供。

## 数据、协作与集成开关

以下能力按宿主需要启用；界面可见性不代替数据权限。

| 设置 | 默认 / 内容 | 指南 |
| --- | --- | --- |
| `ORDLOOM_GRAPHQL` | 默认关闭；字段白名单、查询预算与能力目录 | [模型与权限](../data/graphql.md) |
| `ORDLOOM_PUBLIC_EVENTS` | 默认关闭；按页授权的同源短期票据、失效通知、心跳与限速 | [公开通知](../guides/conditional-pages-and-antv-reports.md) |
| `ORDLOOM_EVENTS` | 默认关闭；失效通知、签名与订阅预算 | [事件与服务](../data/events-and-services.md) |
| `ORDLOOM_REPORT_EXPORTS` | 默认关闭；导出调度、留存、文件和源记录预算 | [报表与导出](../data/reports.md) |
| `ORDLOOM_COLLABORATION` | 默认关闭；工作区、角色与逐资源授权 | [协作](../guides/collaboration.md) |
| `ORDLOOM_ORGANIZATIONS` | 默认关闭；宿主组织、成员与稳定身份映射 | [组织接入](../guides/collaboration.md) |
| `ORDLOOM_DATA_SERVICES` | 默认关闭；独立服务身份、只读字段和固定版本授权 | [只读服务](../data/events-and-services.md) |
| `ORDLOOM_WEBHOOKS` | 默认关闭；批准目标、后台权限上下文与机器人 | [Webhook](../guides/webhooks.md) |
| `ORDLOOM_PWA` | 离线程序和业务快照分别显式开启 | [离线](../guides/offline.md) |
| `ORDLOOM_SESSION_DEVICES` | 默认关闭；会话设备、中间件及保留数量 | [会话安全](../guides/security.md) |
| `ORDLOOM_SHARE_ANALYTICS` | 默认关闭；分享入口访问记录及预算 | [分享](../guides/sharing.md) |
| `ORDLOOM_AUDIT_RETENTION` | 默认永久保留；可配置分批清理周期 | [审计留存](../guides/notifications-and-audit.md) |

使用手册中相应模块的完整字典示例配置；不要仅为了显示菜单开启缺少依赖或调度的能力。

## 1.1.0 新增配置

以下增强从 Ordloom 1.1.0 提供：

| 设置 | 默认 / 行为 |
| --- | --- |
| `ORDLOOM_TASK_ALERTS.external_targets` | 空列表；最多 10 个批准的 `bot:<标识>`，不接受任意 URL |
| `ORDLOOM_TASK_ALERTS.external_owner` | 未配置；外发负责人必须是当前有效超级管理员 |
| `ORDLOOM_TASK_ALERTS.external_retry_seconds` | 30（1–3600）秒；入队补偿指数退避，单次最多 3600 秒 |
| `ORDLOOM_TASK_ALERTS.external_max_attempts` | 12（1–100）；每轮入队尝试上限，失败需显式重试 |
| `ORDLOOM_TASK_ALERTS.external_max_age_seconds` | 86400（60–604800）秒；原事件补偿期限，手动重试不续期 |
| `ORDLOOM_RUNTIME_METRICS` | 默认关闭；共享缓存分钟桶与安全汇总，缓存不可用不阻断原请求 |

完整例子、告警故障隔离、指标窗口和权限见 [任务告警外发与运行指标](../guides/p2-operations.md)。页面版本、图表联动和问卷分步不新增独立开关；页面版本需要 0028 迁移，其使用方式见 [路线图](roadmap.md)。

入队补偿需要核心 0030 迁移；复用原 default 数据库和共享缓存。关闭、撤权或改变原目标配置后取消旧意图，显式失败重试不恢复取消事件。命令、状态与第三方验收协议见 [P1 入队补偿与运行升级验收](../guides/p1-admission-and-contracts.md)。

## 站点与工作空间

| 设置 | 默认 / 行为 |
| --- | --- |
| `ORDLOOM_SITE_TITLE` | 未提供时取 `admin.site.site_header` |
| `ORDLOOM_SITE_SUBTITLE` | 管理工作空间 |
| `ORDLOOM_LOGO` | 可配置文字或图片路径 |
| `ORDLOOM_DEFAULT_THEME` | 首次进入及恢复默认时使用的主题 |
| `ORDLOOM_HOME_TITLE` | 首页标签标题，默认「首页」 |
| `ORDLOOM_HOME_ICON` | 首页图标，默认 `fa fa-home` |
| `ORDLOOM_HOME_PAGE` | 默认打开的模型管理地址 |
| `ORDLOOM_INDEX` | 默认打开地址的兼容别名 |
| `ORDLOOM_HOME_INFO` | 是否显示服务器信息，默认 True |
| `ORDLOOM_ANALYSIS` | 是否显示统计 / 图表，默认 True |
| `ORDLOOM_ICON` | 菜单图标开关，默认 True |
| `ORDLOOM_LOADING` | 初始加载提示开关，默认 True |
| `ORDLOOM_CONFIG` | 自定义菜单字典 |

主题 key：`default`、`midnight`、`violet`、`teal`、`forest`、`amber`、`crimson`、`light`。

## 自定义菜单

```python
ORDLOOM_CONFIG = {
    "system_keep": True,
    "menus": [
        {
            "name": "业务协作",
            "icon": "fa fa-folder",
            "models": [
                {"name": "项目", "url": "/admin/projects/project/"},
                {"name": "团队", "url": "/admin/projects/team/"},
            ],
        },
    ],
}
```

地址应对应实际注册模型。自定义菜单仍受权限限制，不会让无权模型自动变为可访问。

## 接管、上传与验证码

| 设置 | 默认 |
| --- | --- |
| `ORDLOOM_FULL_TAKEOVER` | True，接管挂载点下管理界面路径 |
| `ORDLOOM_MAX_UPLOAD_SIZE_MB` | 50，服务端上传总上限 |
| `ORDLOOM_CAPTCHA_TIMEOUT` | 180，验证码有效秒数 |

登录验证码是否启用由站点配置表保存，在有权限的账号菜单中修改；不是通过这里新增一个不存在的布尔设置。

## 字段与 Admin 扩展点

- `ordloom_fields`：主表或 inline 字段外观。
- `ordloom_soft_delete = False`：关闭软删除自动识别。
- `get_trash_queryset(request)`：自定义回收站数据范围。
- `soft_delete_model(request, obj)` / `restore_model(request, obj)`：软删除、恢复逻辑。
- `get_log_queryset(request)`：符合业务范围的日志查询。

原生 ModelAdmin、ModelForm 和 FormSet 钩子继续承担业务规则，详见[表单与关联明细](../guides/forms-and-inlines.md)。


## 子应用 SDK 设置（1.1.0 起）

`ORDLOOM_DISABLED_APPS` 为停用的子应用 ID 列表，默认空列表。`ORDLOOM_APP_TASK_CONTEXT` 可设置可信的 `factory(user, using)` 导入路径，构造任务的宿主权限上下文。现有 `ORDLOOM_TASK_DIAGNOSTICS` 控制任务观测，缓存继续使用宿主 default cache。

子应用不自动引入租户边界、客户权限或远程代码执行。完整清单与配置见 [子应用 SDK](../development/subapplications.md)。

`ORDLOOM_APP_RECIPES` 扩展纯声明行业配方；与内置合计最多 32 项，只含 ID、标签、说明、必选/可选应用、步骤和边界，不接受执行代码或导入路径。示例见[生态开放与配方](../development/ecosystem.md)。
