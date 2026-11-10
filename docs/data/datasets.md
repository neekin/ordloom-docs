# 数据集、发布版本与组件绑定

数据集保存查询定义。发布版本冻结定义，读取结果和权限仍保持实时；通过工作室完成选择、预览、保存与发布。

## 数据集草稿与发布版本

数据集接口与可视化工作室复用现有查询引擎和 Session/CSRF。仍需启用
`ORDLOOM_GRAPHQL` 并安装可选依赖；关闭时数据集接口返回 404，核心功能不加载 Strawberry。
升级后执行 `python manage.py migrate`，应用 `0007_visualdataset`，新增 `VisualDataset` 与 `VisualDatasetVersion`。

默认普通 staff 只能管理和执行自己的数据集，超级管理员可管理全部，包括创建人已删除的数据集。
0024 的可选协作工作区可显式授予配置读取/编辑，查询仍使用访问者自己的数据权限；删除及归档仍为创建人/超级管理员操作。
数据集归属不授予业务数据权限：保存、发布、预览和按版本执行均检查当前账号的模型、QuerySet、
对象与字段规则。执行身份始终是当前调用者，不冒用创建人或发布人，不提供匿名业务数据读取。

以下地址均位于配置的挂载点下，例如 `/admin/api/datasets/`：

| 接口 | 用途 |
| --- | --- |
| `GET/POST api/datasets/` | 分页列表、新建有效草稿 |
| `GET api/datasets/catalog/` | 当前账号可查询的模型、字段、类型和查询能力，REST 元数据使用 snake_case |
| `POST api/datasets/preview/` | 预览未保存的 `definition` 和 `params`，不创建或修改数据集 |
| `GET/PUT/DELETE api/datasets/<id>/` | 查看/更新草稿；只有未发布的数据集可删除 |
| `POST api/datasets/<id>/preview/` | 按草稿修订号预览，检查当前权限 |
| `POST api/datasets/<id>/publish/` | 发布指定草稿修订号，返回版本号与指纹 |
| `GET api/datasets/<id>/versions/` | 分页列出历史版本，摘要不包含完整定义 |
| `GET api/datasets/<id>/versions/<number>/` | 查看不可变的发布快照及字段依赖 |
| `POST api/datasets/<id>/restore/` | 将历史定义复制为新草稿，不改写任何发布版本 |
| `POST api/datasets/<id>/execute/` | 指定发布版本执行，不接受临时修改查询结构 |

列表使用 `?page=1`，每页 20 条。业务数据与查询结果不保存在草稿或版本中。
元数据按数据集归属可见；失去模型权限后仍可查看自己的查询定义，但不能借此执行查询。

新建请求示例：

```json
{
  "name": "已付款订单",
  "description": "按金额筛选的订单明细",
  "definition": {
    "schemaVersion": 1,
    "model": "sales.order",
    "mode": "records",
    "fields": ["id", "number", "amount", "paid"],
    "filters": {
      "where": {"amount": {"gte": {"$param": "minimumAmount"}}, "paid": {"eq": true}}
    },
    "orderBy": [{"field": "created_at", "direction": "DESC"}],
    "limit": 20,
    "parameters": {"minimumAmount": {"type": "Decimal", "default": "100"}}
  }
}
```

`mode: "records"` 必须明确选择 `fields`；它们使用原生字段名，结果字段仍采用 camelCase。
`mode: "aggregate"` 使用现有 `metrics`、`groupBy`、`orderBy` 和 `timezone`，不接受 `fields`。
例如指标 `[{"name":"orders","operation":"COUNT"},{"name":"revenue","operation":"SUM","field":"amount"}]`，
可按 `[{"field":"paid"}]` 分组并按 `[{"field":"revenue","direction":"DESC"}]` 排序。
省略的查询上限和聚合时区在保存时填入，发布后不会随新的默认设置悄悄变化；平台调低硬性限额时，
旧定义若超限会明确报错，不自动改变原配置。

新建响应返回字符串 `id`、`revision: 1`、`latest_version: 0`、完整规范化定义及字段依赖。
PUT 可更新名称、说明和完整 `definition`，必须携带当前 `revision`；定义不做隐式深度合并。
每次保存将 revision 加一，旧修订请求返回 HTTP 409 / `CONFLICT`，失败不覆盖草稿。
创建人由登录账号决定，不能通过请求转移归属。

对数据集 12 发布 `POST api/datasets/12/publish/`、请求体 `{"revision":1}`：

- 同一草稿修订重复发布返回同一版本，支持请求重试；即使已经保存新草稿，也可重试获取此前已发布的版本。
- 新修订发布得到递增的版本号。发布事务、条件更新和唯一约束共同避免版本覆盖；失败不会留下半发布状态。
- 快照冻结定义、参数声明、字段类型依赖与 SHA-256 指纹；版本只读，不提供覆盖或删除接口。
- `latest_version` 只用于管理摘要；执行必须明确指定版本号。修改草稿和发布新版本都不会改变旧版本定义。
- `POST restore/` 请求体为 `{"revision":2,"version":1}`，生成 revision 3 的草稿；再次发布产生新版本，不回退或复用版本号。
- 已发布的数据集禁止删除，防止引用失效；未发布草稿可用 DELETE 请求体 `{"revision":1}` 删除。

运行预览：`POST api/datasets/12/preview/`，请求体 `{"revision":1,"params":{"minimumAmount":"200"}}`。
运行发布版本：`POST api/datasets/12/execute/`，请求体 `{"version":1,"params":{"minimumAmount":"200"}}`。
运行时只可提供声明的 `params`，以及明细 `offset` 和不超过保存上限的 `limit`，不能更换模型、字段、条件或指标。
聚合不支持 offset。预览和执行均返回现有明细/聚合结果结构；发布版本另返回版本号、模式与指纹。

也可通过已有只读 GraphQL 端点执行发布版本：

```graphql
query {
  visualDataset(id: "12", version: 1, params: {minimumAmount: "200"}, limit: 20) {
    datasetId
    version
    fingerprint
    mode
    data
  }
}
```

`data` 为 JSON，保留原查询的 ID、BigInt、Decimal 字符串和布尔/日期格式。
新接口不增加 GraphQL Mutation，也不改变原模型明细、按 ID 和聚合接口。

参数仅能通过 `filters` 中的 `{"$param":"参数名"}` 绑定到标量操作值或集合，不允许绑定整棵条件树或查询结构。
声明最多 20 个，名称须以字母开头，最多 64 位字母/数字/下划线，且每项必须实际使用。
`type` 支持 String/Boolean/ID/BigInt/Decimal/Float/Date/DateTime/Time/UUID/Duration，及对应 `[String!]` 等集合类型；
类型必须与绑定操作精确匹配，值继续经过原 GraphQL 类型、时间/数值和查询限额校验。
`required` 默认为 true；有 `default` 时可省略参数，无默认值的必填参数必须在执行时提供。
`required:false` 且无默认值时按 null 处理，仅适用于接受 null 的条件。未知参数、错误类型及必填 null 被拒绝。
保存和发布使用类型样例验证无默认值的必填参数，不执行结果查询；预览和执行必须提供有效实参。

字段依赖覆盖输出列、筛选、排序、分组和指标；运行时会重新检查权限及结构。
字段撤销开放、类型/精度改变、时区模式改变或快照指纹不符时返回 `SCHEMA_CHANGED`，不会静默重解释旧版本。
可编辑并保存新草稿后重新发布。版本冻结的是查询配置，业务结果会随数据和当前权限变化。
配置定义最多 48 KiB，管理请求最多 64 KiB；保留原查询的条件、分组、扫描与请求操作限额。
REST 错误代码位于 `context.code`，GraphQL 位于 `errors[].extensions.code`；内部异常不返回客户端。
常规 ORM 写入也禁止覆盖或删除快照；宿主直接 SQL、底层写入与迁移脚本仍属于可信运维范围。

## 数据集归档与恢复

应用 `0017_dataset_archive` 迁移后，数据集工作室提供「在用数据集 / 已归档 / 全部数据集」筛选。
归档不删除数据，不改写草稿定义、字段依赖或不可变发布快照；恢复后重新开放编辑和新增引用。

```bash
python manage.py migrate
```

- 创建人或超级管理员可归档/恢复；不读取业务数据，业务源字段权限撤销后仍可整理元数据。GraphQL 功能和模型注册配置仍须有效。
- 归档后草稿名称、说明、定义、保存、预览、发布、历史恢复为草稿及删除均冻结；仍能查看版本、比较差异和使用关系。
  工作室的未保存输入在确认归档时放弃，取消归档确认则保留输入。
- 已有固定版本 REST/GraphQL 查询、后台大屏/H5、轮播、公开授权和服务凭据继续按当前权限读取；归档不会停止现有集成。
  要停止业务读取，请撤销对应公开授权/服务凭据或数据权限。
- 保存已有页面时，同一个组件 ID 引用同数据集与同发布版本可保留、修改布局/映射/类型化参数，继续复核当前字段权限。
  复制页面、增加组件或切换固定版本属于新引用，已归档时拒绝；多个组件共享预览缓存也不能绕过检查。
- 已配置公开/服务授权可保留、撤销、恢复或轮换；新增归档数据集或其他版本的授权范围拒绝。
  公开授权即使以 `revoked:true` 暂存也不能新增归档范围，服务直接模型字段授权不受数据集归档影响。
- 归档/恢复检查当前 `revision`，实际状态变更递增修订号并与 Django 操作记录同事务提交；同状态、同修订的重试不重复记账。
  来源校验期间发生归档的草稿保存或发布不能覆盖归档状态；发布事务再次检查状态。普通引用保存按本次校验读取的状态判断，已通过校验的在途保存可能稍后完成。
- 恢复不授予额外权限，也不自动升级组件或创建新快照；已有快照响应、指纹、序号及使用索引保持不变。
  已发布数据集始终禁止删除，未发布数据集需要先恢复再删除；此生命周期策略由管理 API 实施，可信 ORM/SQL 运维需自行保持修订号和状态一致。

| 接口 | 行为 |
| --- | --- |
| `GET /api/datasets/?archived=false` | 默认在用列表，每页 20 条；`true` 归档，`all` 全部，先按账号与状态筛选再分页 |
| `POST /api/datasets/<id>/archive/` | `{"revision":3,"archived":true}` 归档，`false` 恢复 |
| `GET /api/datasets/<id>/` | 含 `archived` / `archived_at`；归档后仍按创建人/超级管理员读取 |
| `GET /api/datasets/<id>/versions/` | 版本列表额外提供 `dataset_archived` / `dataset_name`；单版本接口保留原不可变快照结构 |

管理写入沿用 staff Session、CSRF 和可选 GraphQL 开关，归档冲突返回 409，冻结操作返回 `context.code=ARCHIVED`。
既有 `items/page/total`、快照、执行及静态页面契约保持兼容，旧数据迁移后默认在用。
真实界面验收见 `frontend` 的 `npm run test:dataset-archive`，后端启动参数为
`scripts/dev_fields.py --datasets --data-services --production --port=8660`（隔离 SQLite、合成业务记录）。

## 可视化数据集与组件绑定

「我的页面 → 业务数据模板」新增零售经营大屏、服务工单大屏与移动经营简报。选择已授权模型，
将分类/状态、金额（经营模板必填）、日期和明细编号映射到现有字段，即可预览实际业务查询结果。
创建操作在同一事务中生成 3–4 个数据集及各自的不可变 v1，再生成绑定页面，不修改业务记录，
不把预览结果存进页面。页面默认关闭公开分享，组件默认手动更新；后续可在编辑器配置轮询或系统通知。
预览、创建和后续执行均复用当前账号权限，动态对象/字段规则同样生效；列表、分组和日期结果遵守现有限额。
模板中的“返回范围”表示实际有限结果，完整范围与 `hasMore` / `hasNextPage` 可在预览中检查。

接口：`GET/POST /api/data-templates/` 与 `POST /api/data-templates/preview/`。
提交 `{"template":"commerce-screen","name":"经营看板","model":"sales.order","fields":{"category":"status","value":"amount","date":"created_at","label":"code"}}`；
模型及字段必须已开放，日期与明细字段可省略；`service-screen` 不使用 `value`，`business-h5` 用于移动简报。

在「页面搭建 → 我的页面 → 数据集工作室」中，选择模型及明细字段，或配置分组维度和统计指标。
界面支持 AND/OR/NOT 条件组、按类型输入的筛选值、多字段排序、日期粒度、时区和类型化参数。
筛选字段、操作、值来源、参数选择和条件组合为必选项；占位项不能清空已有条件，删除筛选请使用「删除筛选条件」或「删除条件组」。
「预览数据」查询当前未保存的定义，不写入数据集；保存草稿后再发布固定版本。历史版本可恢复为新草稿。
数据集列表、版本列表与绑定选择均支持分页；无权限或未开放的模型不会出现在可用数据源目录中。
版本列表在每页额外返回 `latest_version`，保留原有 `items`、`page`、`total`；翻到旧版本页后仍提示实际最新版本，
不会自动升级已绑定组件。修改预览定义、实参或绑定版本，以及关闭配置面板时，会取消未完成的预览请求；
即使服务端已经完成查询，迟到响应也不会覆盖新的配置或恢复已清空的结果。

每个发布版本提供「比较差异」：可对照当前草稿（包括未保存修改），或切换到其他发布版本。
比较展示模型、字段、筛选、排序、聚合、参数与已保存字段依赖的变化，不执行业务查询。
输出字段移除/类型变化、必填参数与参数类型变化会提示绑定升级检查；未保存草稿不会被描述为已确认类型兼容。
差异超过 200 项时可显示全部。绑定面板显式切换版本后，可用「比较绑定升级差异」对照原绑定与目标版本。
比较不修改任何草稿、发布快照或组件；应用升级仍须预览并重新校验映射、实参与当前权限。

### 依赖与使用关系

工作室的「依赖与使用」按发布版本展示源模型字段、页面组件与间接引用的轮播，支持分页。
`GET /api/datasets/<id>/usage/` 接受 `version`（省略为所有发布版本）、`section=pages|playlists`、`page`，每页 20 项。
所有计数和明细先限定当前账号可管理的页面、轮播及数据集；普通 staff 不会看到其他人的引用，超级管理员可看全部。
接口只返回引用元数据，不含运行实参、业务结果或分享令牌；授权标签仅反映配置，实际执行继续复核当前权限。
未指定版本时字段依赖来自已保存草稿，选择具体版本时来自该发布快照；报表独立存储查询，不属于数据集版本的引用。

`0013_visual_usage` 为现有 JSON 文档回填 `VisualDatasetUsage` 与 `VisualPlaylistPage` 索引。
页面/轮播正常 `save()` 与索引在同一事务保存，删除会清理引用；索引不是新的权限来源，运行时仍以页面与原权限链为准。
可信批量导入、QuerySet `update()`、`bulk_create/update` 和原始 SQL 不触发模型保存钩子，导入后运行：

```bash
python manage.py ordloom_reindex_visual --check --json  # 只检查，有差异返回非零退出码
python manage.py ordloom_reindex_visual --json          # 重建派生索引，不改源文档/版本/更新时间
# 多数据库工程可传 --database <alias>，索引与源文档必须位于同一数据库
```

### 运行数据库驱动示例

在仓库根目录执行以下命令。示例使用隔离的临时 SQLite 和合成业务记录，不连接宿主项目数据库：

```bash
bash scripts/sync-dist.sh
uv run --python 3.12 --with 'django>=5.2,<5.3' --with pillow \
  --with 'strawberry-graphql-django>=0.96.3,<0.97' \
  python scripts/dev_fields.py --visual-examples --production
```

打开 `http://127.0.0.1:8650/`，使用 `demo / demo-only` 登录。会预置 3 张页面和 12 个已发布数据集，
可在模型管理中修改业务金额，再点击页面「刷新数据」验证汇总、趋势和明细变化。日期示例分布在多个日期，
生成页面仅保存查询与映射；停止脚本即清理数据库与媒体。需要通知测试时另装 `channels daphne` 并加 `--events`。

大屏或 H5 编辑器中选中组件，进入右侧「数据」页签：

1. 选择自己的数据集（超级管理员可选全部）及明确的发布版本。
2. 填写声明的运行参数，将输出字段映射到组件需要的角色。
3. 预览查询结果和实际组件，确认后应用绑定并保存页面。

文本、指标卡、进度条、排行榜、表格及全部 11 类 ECharts、7 类 AntV 图表支持绑定。
饼图使用 `chartType: "pieSolid"`；原有 `chartType: "pie"` 继续显示环形图，已有页面与报表无需转换。
报表的 `chart.type` 使用相同值，两者沿用类目/数值映射和当前权限；离线只读快照保留所选形状。
明细字段使用查询输出的 camelCase 名；聚合字段为 `dimensions.<维度名>` 和 `metrics.<指标名>`。
表格可配置列顺序、标题；关系图映射起点/终点/权重，层级图映射 1–3 层维度和数值。
文本、指标和进度取第一行；图表、排行、表格使用返回的有限结果集，不自动拉取全部分页。

绑定保存于组件的可选 `dataBinding` 属性，例如：

```json
{
  "datasetId": "12",
  "version": 1,
  "params": {"minimumAmount": "200"},
  "mapping": {"category": "dimensions.paid", "value": "metrics.revenue"}
}
```

页面保存重新校验数据集归属、发布快照、当前业务权限、参数、字段及映射类型，不查询或保存业务结果。
未映射的样式和静态属性继续生效；原有无绑定页面无需转换。撤销、重做、复制和 JSON 导入导出保留绑定配置，
不包含查询结果。升级发布版本须显式选择，草稿修改或发布新版本不会自动改变现有页面绑定。

文本和表格保留 BigInt/Decimal 字符串精度，正确区分 0、false 和 null。
图表会将有效数值转换为 JavaScript Number，可能舍入小数；超出安全范围、非数值或不适用的空值会提示错误，
进度/仪表盘要求 0–100。加载、空结果和错误有独立状态，失败时可重试，不用示例数据冒充业务结果。

授权后台的编辑、预览及轮播在进入时执行绑定；编辑器提供「刷新数据」。同屏相同数据集版本和参数合并在途请求，
刷新、卸载与轮播切屏会取消所属请求，旧响应不会覆盖新配置。不持久缓存业务结果。
绑定的可选 `updateMode` 支持 `manual`（手动）、`poll`（定时请求）、`push`（系统通知）与 `auto`（请求和通知）。
`poll` 必须设置 `refreshSeconds`（10–3600 整数秒）；`push` 在事件扩展关闭时按该间隔兜底，默认 30 秒。
旧绑定不含 `updateMode` 时沿用原有行为。手动组件不响应模型事件，定时请求组件不订阅事件，彼此独立。
隐藏时暂停定时任务，恢复可见立即刷新；网络错误保留实际业务结果并标记过期，权限失效或结构漂移清除结果。
公开单页/轮播默认显示授权提示；仅明确开启页面数据授权后读取绑定字段，公开端使用安全的定时兜底，
不连接管理员事件总线。0024 已提供可选协作及工作区/资源授权界面（当前浏览器已验证组织授权、撤销与确认交接）；页面公开数据授权和独立报表见后续章节。

本阶段没有新增数据库迁移；已有数据集工程沿用 `0007_visualdataset`。关闭可选 GraphQL 后静态编辑、分享、表单与轮播仍可使用，
可移除已有绑定，但保存新的业务绑定需要重新启用扩展。
