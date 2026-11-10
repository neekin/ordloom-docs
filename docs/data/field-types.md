# JSON、关联、时长与精确数值

读取、筛选、分组与聚合分别由字段能力目录声明。字段适配始终继承源字段及关联目标的当前权限。

## JSON 子字段

数据集工作室和报表构建器可将已开放的原生 JSONField 中的对象键、数组位置声明为类型化列，
用于明细、筛选、排序、分组和标量类型允许的聚合。配置保存在各自的 `definition.jsonFields`，
不会推断或修改全局模型目录、模型 Schema 或业务记录，也不接受代码、SQL 或 ORM lookup。

例如，业务 JSON 为 `{"stats":{"amount":"12.50"},"daily":[{"units":"9007199254740993"}]}`，
在已有模型与源字段白名单下可配置：

```json
{
  "model": "sales.order",
  "mode": "records",
  "jsonFields": [
    {"name": "price", "source": "preferences", "path": ["stats", "amount"], "type": "Decimal"},
    {"name": "dailyUnits", "source": "preferences", "path": ["daily", 0, "units"], "type": "BigInt"}
  ],
  "fields": ["id", "price", "dailyUnits"],
  "filters": {"where": {"price": {"gte": "10"}}},
  "orderBy": [{"field": "price", "direction": "DESC"}]
}
```

模型与 `preferences` 应替换为宿主实际开放字段；`fields`/排序/分组/指标使用声明名称，
筛选及明细输出沿用 camelCase 规则。标量为 `String/Boolean/BigInt/Decimal/Float`，
参数也用相应标量或其列表；发布版本冻结路径、类型及源 JSON 字段依赖，草稿修改不影响旧版本。
发布快照仍冻结查询配置，不冻结结果、权限或业务 JSON 类型。

- 每定义最多 20 列、每路径 1–8 层。对象键为 1–64 字字符串，支持 Unicode、点和数字键，
  不含双引号、反斜线及控制字符；数组序号为 0–1000000 整数。字符串 `"0"` 与整数 `0` 明确区分。
  名称以英文字母开头，最多 64 位字母/数字/下划线，不含双下划线，不能覆盖模型字段、属性、
  宿主 QuerySet 注解或其他列的 camelCase 名称。
- 精确整数、小数的**源 JSON 值使用字符串**：BigInt 为规范十进制有符号 64 位整数，
  不接受前导零、`-0`、小数或指数；Decimal 最多 26 位整数与 12 位小数，不接受指数。
  `Float` 使用有限 JSON 数字，文本和布尔值必须是对应 JSON 类型，不自动将文本转为布尔值或数字。
  BigInt/Decimal 沿用字符串传输；图表继续检查有限值及安全数值范围。
- 缺失路径、JSON null 和 SQL null 返回空值。已有非空值或路径容器类型不符合声明时，
  预览/执行返回 `INVALID_VALUE`，不会静默转零；检查覆盖**用户筛选之前的完整授权对象范围**。
  保存/发布验证结构与权限，不扫描实际值类型，允许修复源数据后重新预览，无需重发相同查询。
- 当前支持 PostgreSQL 与 SQLite。PostgreSQL Decimal 使用 `numeric(38,12)`；SQLite 的 Decimal
  转换和聚合使用其原生数值计算，大额或高精度小数会出现约 15 位有效数字及二进制舍入限制。
  JSON 中用字符串保存并不能消除 SQLite 查询计算损失。需完整小数精度时使用已验证的 PostgreSQL，
  并验收实际数据规模；BigInt 字符串在两个数据库中均保持 64 位整数精度。查询展开超过数据库参数预算
  返回 `QUERY_TOO_LARGE`，减少列、路径或条件后重试；原有无 JSON 子字段查询不受此扩展限制。
- 子字段继承**整个源 JSON 字段**的权限，不提供键级独立授权。模型/模块、Admin QuerySet、
  租户/软删除、对象、动态表单、私密/PasswordInput 字段规则继续生效。SQL 权限证明收到原始源字段名称，
  权限钩子读取原始模型对象，声明的列不会变成权限判断所用的对象属性。
  固定数据集服务授权仍授予该版本完整输出，公开页面仍仅返回映射字段；外发前均复核当前权限。
  含子字段的公开查询始终实时执行，避免已有结果缓存掩盖当前值类型变化；原生查询缓存规则不变。
- 大屏/H5、报表沿用现有映射及预览，轮询/模型变更重读策略不变。历史报表导出下载继续检查
  当前配置、字段及贡献记录权限，不因源 JSON 当前值类型变化重算或破坏已生成文件。

专项：`python scripts/test_backend.py ordloom.tests.test_json_projection`；
真实 Session/CSRF 与隔离合成数据：`python scripts/test_json_projection.py`（需可选 GraphQL 依赖）；
专用临时 PostgreSQL：`python scripts/test_ownership_postgres.py --json-fields`（还需 psycopg）。
演示可用 `scripts/dev_fields.py --json-fields --production`；不写实际宿主数据库，无新增宿主迁移。
JSON 编辑器 DOM 回归使用模拟 API，不能替代真实浏览器、Canvas 或宿主数据库验收。

## 单值关联字段

作为业务字段的正向 ForeignKey/OneToOne 支持 `eq/ne/inList/notIn/isNull`、排序、原值分组及 COUNT（含 distinct）。
输入为目标记录的主键 `ID`，参数可用 `ID` 或 `[ID!]`；即使外键存储 `to_field="code"`，仍按目标主键操作及返回。
空值保持 Django 的排除语义，排序始终将 null 放最后。关系本身作为根模型主键时继续按原根 ID 行为处理。
多对多不参与这些运算，不接受任意 `owner__name`、ORM lookup 或关系遍历；SUM/AVG/MIN/MAX 也不用于关联 ID。

```graphql
query ByTeam($team: ID!) {
  projectRecord(
    filters: {where: {owner: {eq: $team}}}
    orderBy: [{field: "owner", direction: ASC}]
  ) { items { id owner } totalCount }
}
```

`projectRecord/owner` 需替换为宿主已开放模型的 `queryField` 和字段。UUID、整数及字符主键保留身份；
不能把显示名称或存储业务码冒充主键。目录的 `filterValueType` / REST `filter_value_type` 为 `ID`，
界面按 ID 匹配运行参数，并允许关联 ID 作为图表类目、COUNT 作为数值。查询定义和组件中不保存实际结果。

权限在用户筛选前判定：

- 根模型沿用当前模型/模块、Admin QuerySet、软删除、对象与字段规则。目标需已注册 Django Admin 且可查看，
  使用目标 Admin 范围、对象权限及源字段 ModelForm 的 queryset 选项，不借用创建人或超级管理员身份。
- 对完整授权根范围中参与运算的字段，任一非空关联值不可见、已悬空或不在表单选项中，整体返回 `FORBIDDEN_FIELD`。
  不能先用名称/参数过滤掉该记录后绕过校验，也不会把不可见 ID 合并成可统计的 null 组。
  没有参与筛选/排序/分组/计数的只读关联继续按原规则返回可见 ID 或 null，旧明细发布版本保持兼容。
- 静态原生表单用 SQL 集合核对，源数据可超过 Python 扫描预算；动态 ModelForm/字段布局采用已有
  `max_permission_scan`（默认 1000）。目标自定义对象权限也在原范围中有界检查，可用目标自己的 SQL 范围适配。
  单独的根 SQL 证明不能替代目标权限或逐对象表单选项。跨数据库的目标或选项范围拒绝处理。
- 关联权限范围不可验证时返回 `POLICY_SCOPE_INVALID`，组件清除旧结果；真实权限变化在下次请求重新检查。
  窗口排名权限先在原目标范围判断，避免按单个外键筛选后重新编号而放行不可见目标；
  服务身份对目标主键字段布局的判断也保持原窗口范围。
- 外部服务的模型字段授权还需明确包含目标模型主键，不能利用关联运算绕过原服务字段白名单；
  显式固定数据集版本的完整查询授权继续按原契约执行，仍复核当前 Django 权限。

新定义仅对实际关联运算追加 `dependencies.relationOperands`，冻结目标主键与引用字段的结构；改变引用键/类型后
原版本返回 `SCHEMA_CHANGED`，需修订发布。旧的只读关联依赖不重写。含关联依赖的公开数据授权不复用结果缓存，
目标范围变化后立即重读或拒绝，避免仅依据根模型权限复用旧关联 ID。

私有数据集/报表执行响应可带 `models`，包括根模型和关联目标模型；已有 `model` 保留。
大屏、H5 和报表组件订阅这些模型的变更，替换绑定时清理旧订阅，在途通知合并后重读。
事件只覆盖已显式注册到 GraphQL、启用事件且当前可读的模型；需要目标变更触发重读时，也应显式开放目标模型
至少主键字段。未开放的目标仍可按 Django 权限读取关联 ID，但不产生目标模型通知，可选择轮询更新。
匿名公开页面继续使用原定时更新，不订阅模型通知。

专项 `python scripts/test_backend.py ordloom.tests.test_relations` 共 23 项；
`python scripts/test_relations.py` 使用自己专用的临时服务、真实 Session/CSRF 和合成记录，验证 19 项查询、版本、
大屏/H5/报表映射、目标权限变化及变更签名。`scripts/test_ownership_postgres.py --relations` 使用专用临时
PostgreSQL 跑 122 项关联、通用查询、服务字段与 SQL 权限检查；依赖见脚本头部，不接受外部数据库。
演示可用 `dev_fields.py --relations --events --production`；无新增宿主迁移，不写宿主数据。
DOM 检查使用模拟 API，不代替真实浏览器、Canvas、真实宿主字段与容量验收。

## 持续时间字段

已开放的 `DurationField` 保持原明细接口：`graphqlType: String`，值沿用 Django 的时长字符串，旧发布版本不改写。
筛选输入另用 `Duration` 标量，目录通过 `filterValueType`（REST：`filter_value_type`）声明；不能根据明细的 `String` 类型猜测筛选参数。
支持等值、集合、空值、范围、排序、原值分组及 COUNT/SUM/AVG/MIN/MAX，所有运算字段沿用当前模型、对象、租户和字段权限；
SQL 权限适配也必须证明时长字段的读取能力。

- 输入使用 ISO 8601 天/小时/分钟/秒，如 `PT1H30M`、`P2DT3H`、`PT0.000001S` 或 `-PT0.000001S`。
  最多六位小数秒，范围为有符号 64 位微秒；不接受年/月/周、数字秒、指数写法及更细精度，不静默截断或舍入实参。
- 参数声明使用 `Duration` 或 `[Duration!]`，如 `{"minimum":{"type":"Duration","default":"PT1H"}}`；
  同时在 `filters` 中绑定 `{"where":{"elapsed":{"gte":{"$param":"minimum"}}}}`。`String` 参数不能绑定到时长操作。
- 聚合中时长维度及非 COUNT 指标以**秒的十进制字符串**返回，如 `"5400"`、`"-0.000001"`；
  目录的 `aggregateUnit`（REST：`aggregate_unit`）为 `seconds`，COUNT 仍为数量。输出字段路径保持原规则。
  工作室、预览、字段映射及报表支持这类数值；界面列名标明「秒」，可用于图表、指标、排行和其他数值组件。
  原明细时长文本仍可映射到文本/表格，不能直接作为图表数值。
- 序列化用整数分解保留微秒，不经过浮点或宿主 Decimal 上下文。SUM/MIN/MAX 的实际容量仍取决于数据库；
  SQLite 按整数微秒存储，SUM 超过其 64 位范围明确返回 `INVALID_VALUE`，不会显示为零或空成功结果。
  PostgreSQL 的 interval 容量与 SQLite 不同。AVG 使用数据库原生计算，再按 Django 的微秒精度转换；
  SQLite 在很大时长求 AVG 时会先转为浮点，可能损失微秒（例如单值 `9007199254.740993` 秒的平均数为 `9007199254.740992`）。
  需要微秒级平均值精度时使用已验证的 PostgreSQL，仍须针对实际数据量和精度验收。
- 数据库数值/interval 溢出返回 `INVALID_VALUE`；SQL 执行使用保存点，失败不会损坏同一外层事务中的后续查询。
  没有新增包内模型或宿主迁移；示例的 `elapsed` 只存在于测试业务模型。

```graphql
query Elapsed($minimum: Duration!) {
  supportTicketAggregate(
    filters: {where: {elapsed: {gte: $minimum}}}
    groupBy: [{field: "status"}]
    metrics: [{name: "averageSeconds", operation: AVG, field: "elapsed"}]
    orderBy: [{field: "averageSeconds", direction: DESC}]
  ) { rows { dimensions metrics } totalCount hasMore }
}
```

示例 `supportTicket` 需替换为宿主真实开放模型的 `queryField`，`elapsed/status` 替换为已开放字段，变量如 `{"minimum":"PT1H"}`。
专项：`python scripts/test_backend.py ordloom.tests.test_durations`（13 项）；真实 HTTP：`python scripts/test_durations.py`（18 项）。
`dev_fields.py --durations --production` 提供临时合成时长记录，不写宿主数据；`scripts/test_ownership_postgres.py --durations`
使用经归属校验的专用临时 PostgreSQL 复验时长、通用查询和 SQL 权限（60 项通过），依赖与命令见脚本头部；不接受外部数据库。
组件检查使用模拟 API，不替代真实浏览器或实际宿主验收。
