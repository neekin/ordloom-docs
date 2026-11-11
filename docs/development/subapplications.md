# 子应用 SDK v1、脚手架与独立示例

SDK v1 从 Ordloom 1.1.0 提供；生成包和独立示例要求 `ordloom>=1.1.0,<2`。SDK 本身不新增业务模型，1.1.0 核心另含 0028/0029/0030，示例包维护自己的 `0001_initial`。现有页面、数据集、分享、权限与任务命令继续使用原协议。

## 从一个独立包开始

```bash
pip install "ordloom>=1.1.0,<2"
python manage.py ordloom_startapp news /path/to/ordloom-news --label 新闻中心
pip install -e /path/to/ordloom-news
```

目标父目录需存在，目标目录需不存在。命令不覆盖已有工程，不向现有业务工程写模型或设置。新包包含 pyproject、README、AppConfig、Note 示例模型与迁移、ModelAdmin、清单、前端源码及随包分发的静态 ESM 文件。生成器不需要连接数据库。

在宿主加入应用后运行标准迁移：

```python
INSTALLED_APPS = [
    # 宿主已有 Django 应用……
    "ordloom",
    "ordloom_news.apps.ExtensionConfig",
]
```

```bash
python manage.py migrate
python manage.py check
python manage.py collectstatic --noinput
```

为 staff 赋予 `ordloom_news.view_note` 后，可以看到「新闻中心 → 业务概览」，在大屏/H5 编辑器的「子应用」分类添加公告组件。示例模型的普通成员只看自己创建的记录，超级管理员可查看全部；模型新增、修改仍使用宿主 Django 权限。专用页面按当前账号、ModelAdmin QuerySet、对象查看权限和字段布局读取，撤权后后续读取拒绝并清除页面结果。

仓库 `examples/ordloom-demo/` 提供相同协议的独立示例，可单独打包安装，与生成的 news 应用共同安装；没有复制 Ordloom 后台，不需要修改核心源码或核心前端构建。

## 应用清单与发现

AppConfig 显式声明 `ordloom_application = "ordloom_news.extension.application"`。只发现 `INSTALLED_APPS` 中带此属性的应用，不执行在线安装，不扫描远端目录。普通 Django 应用保持原行为。

```python
from ordloom.sdk import Application, AppPage, CanvasWidget, AppTask

application = Application(
    id="news",
    label="新闻中心",
    version="0.1.0",
    asset="ordloom_news/extension.js",
    pages=(),
    widgets=(),
    tasks=(),
)
```

| 声明 | SDK v1 范围 |
| --- | --- |
| `Application` | 应用 ID/版本/标签、本地前端入口、依赖应用 ID、SDK 版本与宿主最小/最大版本 |
| `AppPage` | 菜单与专用页面、明确权限、可选 ModelAdmin 模型约束、只读 GET 数据处理器 |
| `CanvasWidget` | 命名空间类型、组件尺寸、默认值、属性 schema、权限及显式公开展示开关 |
| `AppTask` | 固定处理函数、权限、可选模型约束、观测周期与短租约 |

应用 ID 为 1–20 位小写字母/数字/下划线，字母开头；页/组件/任务 ID 最多 12 位。应用须无重复 ID，依赖须存在且无循环；`sdk_version` 为 1，版本范围用 `x.y.z`。Django system check `ordloom.E080` 检查清单、命名空间、依赖、前端文件与版本兼容。SDK v1 以应用 ID 验证依赖存在，依赖包版本同时由 pyproject/pip 约束。

清单、处理函数与前端脚本属于受信任的安装代码，具有普通 Django 应用的权限，不能把用户输入当作导入路径或脚本。应用启停由部署配置管理：

```python
ORDLOOM_DISABLED_APPS = ["news"]
```

停用后菜单、专用页、任务和新组件配置关闭；已有画布保留原配置与占位，不能新增或修改该组件属性，继续编辑其他部分不丢失配置。再次启用恢复组件；卸载不自动清理数据，应按宿主迁移依赖处理。

## 前端专用页面与搭建组件

前端入口导出 `activate(sdk)` 并返回 `pages`、`widgets` 注册表，键与清单 ID 对应。SDK 注入宿主 `React` 与有限 `ui`（Card、Alert、Button、Space 等）；无需捆绑另一套 React，也不依赖全局注册变量。专用页接收 `{data}`，组件接收 `{props}`。

示例源码位于 `frontend/extension.js`，分发文件位于 Python 包的 `static/<应用模块>/extension.js`。示例为直接可运行 ESM，不需 Node 构建；复杂插件可自行打包成单入口 ESM，再随 wheel/sdist 分发。SDK v1 暂只提供单文件入口，依赖应打包进入该文件；CSS 可使用组件样式或包内统一实现，暂未提供额外 CSS/拆分 chunk 协议。

Ordloom 通过同源、受清单约束的资源接口加载入口，目录携带资产哈希，过期资产请求返回 409。脚本路径限已安装应用静态目录，浏览器不能提交任意模块 URL。公开组件的入口代码可公开读取，私人地址、密钥和业务结果应保留服务器。

组件类型为 `app:news.banner`。属性支持 text、textarea、color、number、boolean、select，最多 32 项，可声明必填、长度、数值范围及选项；保存和发布时服务端重新验证。SDK v1 子应用组件提供声明式静态配置与渲染，暂不接入通用 GraphQL 绑定或组件自定义业务写入；已有内置组件的数据绑定保持原行为。

`public=True` 显式允许公开展示声明的静态配置；默认 `False`，分享单页/轮播时清除组件属性并显示占位。公开目录仅提供显式公开组件的渲染元数据，不包含专用页、权限标识或业务数据。页面分享密码、令牌、有效期、发布版本继续生效。

## 权限与业务数据

页面、组件配置和任务声明必须指定 Django 权限。每次专用页面读取与任务执行都复核有效 staff/超级管理员身份和 `has_perms`；声明 `model` 后还须通过原 ModelAdmin 模块和查看权限。菜单隐藏不是服务端授权。

SDK 提供 `visible_objects(request, model, limit=1000)`，复用当前 ModelAdmin QuerySet 和逐对象查看权限；超过预算明确失败，不伪造完整统计。`readable_records(request, model, fields, limit=1000)` 额外要求显式标量字段、逐对象字段布局检查，并排除关系/JSON/二进制与凭据字段。它不是通用客户业务 API，也不替代应用自己的业务规则或数据权限适配；处理器应使用这些帮助函数或原宿主服务查询。

专用页面在激活且可见时每 15 秒重读，离开或隐藏时取消，失败/拒绝清除旧值，迟到响应不覆盖新状态；可以手动刷新。插件组件异常有局部错误边界。SDK v1 不提供第三方脚本沙箱，宿主只安装可信包。

## 任务、共享缓存与诊断

```bash
# --user 是宿主账号主键，支持 UUID；默认只预览，不调用处理函数
python manage.py ordloom_run_app_task ext:news.heartbeat --user 1 --json
python manage.py ordloom_run_app_task ext:news.heartbeat --user 1 --apply --json
```

SDK v1 任务限定 `default` 执行上下文，复用现有共享缓存短租约；缓存异常时拒绝执行，不回退到不受控运行。租约按期过期，不由旧执行者删除，避免删除新租约。租约不是永久互斥或任务队列，超过租约时仍可能重入，业务处理函数须幂等。命令不自动安装调度器或网页执行入口；由宿主 cron/任务平台调度。

开启 `ORDLOOM_TASK_DIAGNOSTICS` 后，任务出现在原超级管理员诊断页，保留现有有限历史、固定计数、失败观测和缓存失效行为。处理函数返回 processed 等原白名单计数，原始结果、业务值和异常文本不进入命令 JSON 或诊断缓存。现有任务告警可按同样观测规则评估子应用任务；没有宣称子应用已拥有持久任务队列。

依赖租户、站点或组织请求上下文时配置可信工厂；无法构造当前权限应明确拒绝：

```python
# 返回 HttpRequest，user 必须是传入账号，宿主显式填入可信租户上下文
ORDLOOM_APP_TASK_CONTEXT = "myproject.contexts.application_task_request"
```

## 接口与验收

- `GET /api/extensions/`：当前员工可用的专用页和组件目录。
- `GET /api/extensions/public/`：仅显式公开组件的静态目录。
- `GET /api/extensions/<app>/asset/?v=<哈希>`：受本地清单约束的入口文件。
- `GET /api/extensions/<app>/pages/<page>/`：重新鉴权后的专用页数据。

安装包、脚手架生成包和组合安装验证见 `scripts/test_extension_install.py`；后端契约见 `test_extension_sdk.py`；前端单元与真实 React DOM 见 `extension-model.test.js` 和 `npm run test:extension-ui`。独立安装检查在临时虚拟环境和 SQLite 中执行，不接触现有宿主数据。第二阶段 [CMS 与基础会员](../guides/cms-and-members.md)、第三阶段 [商城 MVP](../guides/shop.md) 已基于 SDK 实现，第四阶段[微信接入](../guides/wechat.md)现已完成，商城支付及微信业务扩展仍为计划；云函数继续保持仅调研。

SDK 首个发行版为 1.1.0，脚手架与示例的依赖下限已经同步；Ordloom 1.0.x 不包含 SDK。示例与生成包用于开发参考，按本地源码或自建分发流程安装。

第五阶段现提供[应用目录、第三方兼容检查与行业配方](ecosystem.md)：可选的应用说明/分发包/依赖版本声明、只读权限目录、DB-free 升级基线门禁、公开测试工具和带测试的脚手架、独立 wheel/sdist 验收工具，以及四套可生成独立宿主的行业配方。原 SDK v1 清单保持兼容；本地通过记录不代表安全审计或官方背书。

P1-2 已增加实际分发 ESM 的强制运行检查、逐应用覆盖报告及保留旧数据的升级 fixture；生成包/示例各 7 项测试，支持 Email/UUID User 与后台命名空间。`--baseline` 仍是声明比较；真实迁移用 `--previous-package` 和 `UpgradeFixture`，见 [运行与升级验收](../guides/p1-admission-and-contracts.md)。同批 P1-1 新增核心 0030 告警入队补偿迁移，升级源码须一并 migrate/collectstatic；没有改变原 SDK v1 运行协议。
