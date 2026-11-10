# 模型目录、GraphQL 与数据权限

以已注册的 `sales.Order` 为示例。请使用宿主实际存在的模型与字段；可视化工作室也通过同一权限链查询。

## 可选 GraphQL 数据层

提供模型自动注册、字段目录、强类型分页明细、按 ID 查询、通用筛选、排序和聚合。GraphQL 默认关闭，
启用后继续复用管理接口与数据权限。本扩展需要 Python ≥ 3.10、Django ≥ 5.2。

```bash
pip install 'ordloom[graphql]==1.0.0'
```

在宿主项目中启用，并明确列出允许开放的模型字段；模型必须已经注册到 Django Admin：

```python
ORDLOOM_GRAPHQL = {
    "enabled": True,
    "models": {
        "sales.order": {
            "fields": ["id", "number", "amount", "paid", "created_at"],
        },
    },
    "max_page_size": 100,        # 默认 100，可配置 1–1000
    "max_permission_scan": 1000, # 对象/动态字段权限扫描上限，可配置 1–10000
    "max_filter_depth": 5,      # 筛选树深度，可配置 1–10
    "max_filter_nodes": 100,    # 筛选节点和操作数量，可配置 1–500
    "max_aggregate_groups": 100, # 每次最多返回的分组，可配置 1–1000
}
```

也可以让模型随其 ModelAdmin 自动发现，settings 中只需设置 `{"enabled": True}`：

```python
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    ordloom_graphql = {
        "fields": ["id", "number", "amount", "paid", "created_at"],
    }
```

同一模型的 settings 声明优先于 ModelAdmin 声明；将该模型配置为 `False` 可关闭开放。
`fields` 必须是字段白名单，不接受 `__all__`，不会因为模型新增字段而自动扩大开放范围。
不支持的自定义字段或计算展示列会在 Django system check 中明确报错。

接口地址为挂载点下的 `api/graphql/`，例如 `/admin/api/graphql/`。
使用现有 Django 登录会话，仅已启用的 staff/superuser 可访问。查询只接受 POST JSON，
保留 Django CSRF；浏览器应携带 CSRF cookie 对应的 `X-CSRFToken` 请求头。

查询有权限的模型和字段目录：

```graphql
query {
  visualDataCatalog {
    key
    label
    queryField
    detailField
    aggregateField
    maxPageSize
    maxAggregateGroups
    fields {
      name
      graphqlName
      label
      kind
      graphqlType
      nullable
      primaryKey
      choices { value label }
      relatedModel
      multiple
      filterOperators
      sortable
      aggregateOperations
      groupable
      dateGranularities
    }
    supportsFiltering
    supportsSorting
    supportsAggregation
    supportsPush
  }
}
```

目录按当前请求过滤。`nullable` 表示数据库字段是否允许 null；GraphQL 输出字段均可为空，
使对象相关的字段拒读可以返回局部错误，而不清除整条记录。GraphQL 的 Schema 固定包含已配置的
字段，introspection 不代替授权；直接请求已知字段仍执行同样的权限检查。

查询名从 `app_label.model_name` 自动生成，并在 `queryField` / `detailField` 返回。
例如 `sales.order` 对应 `salesOrder` / `salesOrderById`：

```graphql
query Orders($id: ID!) {
  salesOrder(offset: 0, limit: 20) {
    items { id number amount paid createdAt }
    totalCount
    offset
    limit
    hasNextPage
  }
  salesOrderById(id: $id) { id number amount }
}
```

字段名采用 camelCase；主键统一为字符串 ID，兼容 0、UUID 和字符串主键；金额用 Decimal
字符串，整数用 BigInt 字符串，避免 JavaScript 数值精度损失。布尔值和 JSON 保留原类型，
日期/时间采用 ISO 格式。数据库本身已经丢失的精度无法由传输层恢复。

读取遵守 `has_module_permission()`、`has_view_permission()`、原始完整 request、
`get_queryset(request)` 和软删除范围。字段白名单还会与原生字段布局、排除字段、动态表单及
凭据识别规则取交集。`readonly_fields` 仍可以读取；密码/密钥字段禁止开放，
请求期间才被识别为密码的动态字段也不会返回值。

需要附加按用户或按对象的字段限制时，可实现只会收窄白名单的钩子：

```python
def get_graphql_fields(self, request, obj=None):
    fields = ["id", "number", "paid", "created_at"]
    if request.user.has_perm("sales.view_order_amount"):
        fields.append("amount")
    return fields
```

自定义对象查看权限会先过滤，再执行用户条件、排序、计数和分页；超出 `max_permission_scan` 时返回
`POLICY_SCOPE_REQUIRED`，避免静默漏检或扫描全表。可通过原来的 `get_queryset(request)`
缩小候选范围。无权查看的对象与不存在的对象均返回 null。

关联字段继续只返回授权后的 ID 或 ID 列表：检查关联模型的查看权限、QuerySet、
软删除范围及原生表单的可选范围；不开放任意嵌套关系遍历。关联结果超过读取上限时明确报错。

每次查询单独保存权限计算状态，不跨用户共享结果缓存；响应禁止缓存。
请求上限为 64 KiB、2000 个 GraphQL tokens、8 层查询深度和 20 个数据操作。
分页默认最多 100 条；错误通过 GraphQL `errors[].extensions.code` 返回，包括
`FORBIDDEN`、`FORBIDDEN_FIELD`、`INVALID_ARGUMENT`、`POLICY_SCOPE_REQUIRED`、
`QUERY_TOO_LARGE` 等。内部异常消息不返回客户端。关闭扩展时端点返回 404，
缺少依赖或配置有误时 system check 提示原因，原有 API 不依赖此扩展。


## 通用筛选与排序

原明细查询增加可选 `filters`、`orderBy`，不传参数时继续按主键稳定分页。
`filters.where` 根据已开放字段生成强类型输入：条件字段采用 camelCase；
`AND`、`OR` 为子条件数组，`NOT` 为单个子条件，同层各条件按 AND 组合。

```graphql
query {
  salesOrder(
    filters: {
      where: { amount: { gte: "100", lt: "1000" }, paid: { eq: true } }
      OR: [
        { where: { number: { startsWith: "WEB-" } } }
        { where: { number: { inList: ["VIP-001", "VIP-002"] } } }
      ]
      NOT: { where: { number: { eq: "WEB-CANCELLED" } } }
    }
    orderBy: [{ field: "amount", direction: DESC }, { field: "created_at", direction: ASC }]
    limit: 20
  ) {
    items { id number amount paid createdAt }
    totalCount
    hasNextPage
  }
}
```

- 基础操作：`eq`、`ne`、`inList`、`notIn`、`isNull`。`eq: null` / `ne: null` 用于判断数据库空值；其他操作不接受 null。
- 数值、日期、时间和时长增加 `gt`、`gte`、`lt`、`lte`；文本增加 `contains`、`iContains`、`startsWith`、`endsWith`。
- `inList` / `notIn` 每次接受 1–100 个不含 null 的值，文本筛选值不超过 2000 字；空条件、空 AND/OR 和空集合返回明确错误。`ne`、`notIn` 和 `NOT` 沿用 Django 排除语义，对非 null 条件取反时可包含 null 记录。
- 筛选值遵守字段类型。BigInt 接受整数或十进制整数字符串；Decimal 建议使用字符串。NaN/Infinity 和超出有符号 64 位范围的整数筛选被拒绝。
- `orderBy.field` 使用目录的原生 `name`（如 `created_at`），最多 5 个、不重复；空值始终排最后，并自动补主键打破并列，保持跨页顺序稳定。
- 开启 `USE_TZ` 时 DateTime 筛选必须携带时区；关闭时接受无时区时间。Time 字段不接受时区偏移。

多值关联、原始 JSON 和文件字段保留原有读取能力，不支持直接查询运算或任意 ORM lookup。
数据集与报表可显式声明 JSON 标量子字段，见「JSON 子字段」。
正向单值关联按目标主键查询，见「单值关联字段」。
`DurationField` 的筛选、排序、分组与聚合见下节「持续时间字段」。
目录逐字段返回 `filterOperators`、`sortable`、`aggregateOperations`、`groupable` 和 `dateGranularities`。
目录只列出当前账号可读字段；Schema 中存在输入字段不代表账号可以使用它。

## 分组与聚合

每个模型增加 `<queryField>Aggregate`，目录通过 `aggregateField` 返回名称；例如 `salesOrderAggregate`。
它复用明细的 `filters`。下面的例子按付款状态和月份统计授权范围内的订单：

```graphql
query {
  salesOrderAggregate(
    filters: { where: { amount: { gte: "0" } } }
    groupBy: [
      { field: "paid" }
      { field: "created_at", name: "month", granularity: MONTH }
    ]
    metrics: [
      { name: "orders", operation: COUNT }
      { name: "revenue", operation: SUM, field: "amount" }
      { name: "average", operation: AVG, field: "amount" }
      { name: "minimum", operation: MIN, field: "amount" }
      { name: "maximum", operation: MAX, field: "amount" }
    ]
    orderBy: [{ field: "revenue", direction: DESC }]
    timezone: "Asia/Shanghai"
    limit: 50
  ) {
    rows { dimensions metrics }
    totalCount
    hasMore
  }
}
```

- 需要 1–20 个指标，最多 3 个分组维度和 5 个结果排序键。维度/指标名称须为 1–64 位字母、数字或下划线，字母开头且互不重复；分组名默认使用字段的 camelCase 名。
- `COUNT` 省略字段时计记录数；指定字段时计非 null 值，支持 `distinct: true`。`SUM`/`AVG` 用于数值和时长，`MIN`/`MAX` 用于数值、文本、日期时间和时长；实际操作以目录为准。
- `groupBy.field`、指标 `field` 使用原生字段名；聚合 `orderBy.field` 使用自定义的维度或指标名称。未指定排序时按维度升序，空值在后；指定排序时仍补齐维度打破并列。
- 日期支持 YEAR/QUARTER/MONTH/WEEK/DAY，日期时间还支持 HOUR/MINUTE；默认 VALUE 按原值分组。WEEK 从周一开始。时区默认跟随 Django 当前时区，可使用 IANA 名覆盖；`USE_TZ=False` 时不能指定时区。
- `rows` 中每行包含 JSON 对象 `dimensions` 与 `metrics`。整数、计数和 Decimal 以字符串返回，浮点数和布尔值保留原类型，日期时间采用 ISO 格式。整数 AVG 也返回 Decimal 字符串；实际精度仍受数据库运算能力影响，SQLite 的小数计算不保证精确财务统计。
- `totalCount` 为**授权且筛选后的源记录数**，采用 BigInt 字符串，不是分组数量。返回行数受 `limit` 和 `max_aggregate_groups` 限制；`hasMore` 表示还有分组，不返回未限定数量的结果。
- 无分组的空结果返回一行：COUNT 为 `"0"`，其余指标为 null；分组空结果返回空数组。统计基于去重后的授权主键，Admin QuerySet 中的多对多连接不会重复累计同一记录。

筛选、排序、维度和指标也执行字段权限检查。遇到自定义表单、对象相关字段布局或
`get_graphql_fields` 等动态规则时，先按 `max_permission_scan` 扫描授权候选记录；
任一候选记录不允许读取所用字段，就拒绝本次查询并返回 `FORBIDDEN_FIELD`，不会先按该字段筛选再跳过检查。
扫描超限返回 `POLICY_SCOPE_REQUIRED`；可通过 Admin 的 SQL QuerySet 缩小范围。
使用原生权限方法、默认表单和原生字段方法时，走 SQL 范围与聚合，不受 Python 扫描条数限制。
原 QuerySet 的注解仍保留给明细对象、权限方法与动态表单使用。

### 大范围对象权限的 SQL 适配

宿主可在 `ModelAdmin` 实现 `get_graphql_query_scope(request, *, queryset, fields)`，
显式提供与现有对象权限及运算字段权限**等价**的 SQL 范围。无此方法，或返回 `None`，继续使用原来的有界检查。
不会自动把任意 Python 权限代码转换成 SQL；此钩子只能由可信宿主代码提供，不能由页面配置上传 SQL 或代码。

`queryset` 是已应用 Admin、Manager、租户和软删除规则、尚未应用调用者筛选条件的基础范围。
`fields` 为不可变集合，包含原生筛选、排序、分组及指标字段；数据集校验还包含配置的输出字段。
它不代表 GraphQL 响应中选中的所有字段。空集合要求证明对象可见范围，仍可用于列表、详情及关联 ID。

例如，宿主原有规则为“仅可看所属区域；保密记录不可读取金额”，可使用如下等价适配。
`request.allowed_region_ids` 必须由宿主根据当前账号建立可信上下文，示例字段需替换为实际模型字段：

```python
from ordloom.graphql.scopes import SQLPermissionScope

class OrderAdmin(admin.ModelAdmin):
    def has_view_permission(self, request, obj=None):
        return super().has_view_permission(request, obj) and (
            obj is None or obj.region_id in request.allowed_region_ids
        )

    def get_graphql_fields(self, request, obj=None):
        fields = {field.name for field in self.model._meta.concrete_fields}
        if obj is not None and obj.confidential:
            fields.discard('amount')
        return fields

    def get_graphql_query_scope(self, request, *, queryset, fields):
        authorized = queryset.filter(region_id__in=request.allowed_region_ids)
        approved = fields
        if 'amount' in fields and authorized.filter(confidential=True).exists():
            approved = fields - {'amount'}
        return SQLPermissionScope(queryset=authorized, fields=approved)
```

正常证书的 `fields` 必须与请求集合完全一致；少一个字段返回 `FORBIDDEN_FIELD`，额外字段属于无效配置。
拒读判断必须覆盖**调用者筛选之前的完整授权对象范围**：不能删除保密对象后再声称金额可用，
也不能随所请求的运算字段改变对象可见范围来规避拒绝。无法提供等价证明的策略应返回 `None`。

返回 QuerySet 必须惰性、同模型且同数据库，不能切片、`values()`、union、加行锁、使用字段级 distinct 或窗口注解。
普通注解可保留；窗口权限策略可返回 `None` 继续走原检查。
平台将证书范围与原始范围取交集，按主键去重执行计数及聚合，证书不能扩大已有范围或字段白名单。
返回明细的对象和字段仍执行原 `has_view_permission` 与动态字段检查；宿主仍需保证计数和聚合范围与旧规则一致。

无效证书或钩子异常返回 `POLICY_SCOPE_INVALID`（数据集 REST 为 503），不返回底层异常内容；
原路径扫描超限仍返回 `POLICY_SCOPE_REQUIRED`。组件收到这两类权限校验失败会清除旧结果，普通临时网络故障仍保留结果并标记过期。
目录新增 `supportsSqlPermissionScope` / `maxPermissionScan`（REST 为 `supports_sql_permission_scope` / `max_permission_scan`），
前者只表明安装了钩子，不保证每次请求都能适配。安装钩子的公开授权查询始终实时执行，不复用结果缓存。
固定数据集版本、页面归属及服务身份范围保持原语义；适配没有新增迁移，也不要求安装 Strawberry 才能导入证书类型。
回归见 [`test_sql_scopes.py`](https://github.com/neekin/simpleui-antd/blob/main/django/ordloom/tests/test_sql_scopes.py)，隔离双数据库验证见 [容量文档](https://github.com/neekin/simpleui-antd/blob/main/docs/capacity.md)。

当前目录根据字段类型开放筛选和排序，聚合已实现，`supportsPush` 仍为 false。
数据集保存、版本与可视化绑定见下节；组件支持独立更新策略，事件通知通过可选扩展启用。
