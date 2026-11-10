# 自助报表、看板与定时导出

选择指标、维度、筛选和图表，预览当前业务范围的结果；同一报表可以嵌入工作台、大屏、H5 和看板。

## 自助报表（业务报表）

升级后执行 `python manage.py migrate`，加载 `0009_report`。新增 `Report` 模型与 `/api/reports/` 端点，
复用数据集聚合层、字段目录与权限栈；需要启用可选 GraphQL 扩展。

- `GET/POST /api/reports/`、`GET/PUT/DELETE /api/reports/<id>/`：报表 CRUD，按创建人或超级管理员隔离。
  报表保存聚合 `definition`（仅支持聚合模式）与 `chart` 图表映射；定义经 `prepare` 规范化并冻结字段依赖。
  列表支持 `page`（每页 20 条）与 `q`（最多 100 字的名称搜索），先限定权限范围再筛选和分页。
- `POST /api/reports/preview/`：校验并执行未保存配置，返回定义、依赖与数据，不落库。
- `POST /api/reports/<id>/execute/`：执行已保存报表，始终按当前调用者的模型/对象/字段权限读取；
  模型字段或类型漂移时明确报错，不冒用创建人权限，不保存业务结果。
- 图表映射服务端校验：类目必须为维度输出、数值必须为数值型指标，表格列 1–20 列且引用输出字段，
  图表配置上限 8 KiB。前端入口在「页面搭建 → 业务报表」。

报表还支持「大数字」展示：选择数值型汇总指标，保留空的分组维度，可添加标题和最多 30 字的单位。
COUNT/SUM/AVG/MIN/MAX 等沿用同一聚合层；只接受单行完整汇总。示例：

```json
{
  "name": "订单总额",
  "definition": {
    "model": "sales.order",
    "mode": "aggregate",
    "groupBy": [],
    "metrics": [{"name": "total", "operation": "SUM", "field": "amount"}]
  },
  "chart": {"type": "stat", "value": "metrics.total", "unit": "元"}
}
```

将模型和字段替换为宿主白名单中的值。大数字不需要 `category`；标题省略时使用报表名称，单位只添加文字，不进行数值换算。
BigInt/Decimal 字符串原样展示，COUNT 空集显示 `0`，SUM 等空值显示 `—`；结果仍受数据库原有数值精度限制。
同一报表可加入工作台、大屏/H5、报表看板及显式只读离线快照；只保存查询/展示配置和引用，不将实时结果写入在线页面或工作台。
CSV/Excel 继续导出原始指标列和值，显示单位不进入数值。已有图表与表格报表继续兼容。

工作台编辑模式的「添加报表」与大屏/H5 报表组件使用同一分页/搜索选择器，支持类型化实参和真实数据预览。
工作台可添加同一报表的多个独立卡片，并通过卡片「参数」按钮修改实参；预览与配置验证失败会保留输入。
实参存于工作台卡片的 `reportParams` 或页面报表组件的 `props.reportParams`，例如 `{"minimum":"200.0001"}`，
最多 16 KiB；Decimal/BigInt 继续使用字符串。省略实参时保持原有默认参数行为，不强制改写旧文档。
新增或修改实参保存时验证报表归属、字段依赖、参数声明/类型及当前业务权限，但不执行或保存业务结果；
工作台添加/应用配置按钮先执行一次当前参数查询，确认可用后才将引用加入待保存布局。
切换引用/实参取消旧运行请求并隔离迟到结果，页面隐藏与后台标签失活时仍暂停读取。
报表声明发生变化后可刷新配置、清除已移除的实参或重置实参；实际查询始终重新检查当前定义和权限。
公开分享仍不执行私有报表，且分享载荷会移除 `reportParams`。此增强不增加数据库迁移。

### 报表组件的刷新策略

工作台卡片、大屏/H5 报表组件及看板卡片可保存可选 `reportRefresh`，例如：

```json
{"reportId":"21","reportParams":{},"reportRefresh":{"updateMode":"poll","refreshSeconds":60}}
```

大屏/H5 将这些字段置于报表组件的 `props`；报表看板置于各卡片。`updateMode` 支持 `manual`（手动）、
`poll`（定时请求）、`push`（系统通知）与 `auto`（通知与可选轮询）。间隔必须是 10–3600 的整数秒；
`poll` 必填，`auto` 不填则只响应模型通知，`manual` 不启用定时或订阅。UI 提供 30 秒、1 分钟和 5 分钟快捷项。
`push` 在事件服务未启用时按指定间隔或默认 30 秒兜底；已启用的事件服务自身可使用原有签名轮询传输。
初次显示及恢复激活均读取一次。旧引用省略 `reportRefresh` 时保留原有通知方式，不自动增加定时请求。

显示的更新时间是上次成功读取时间。网络失败保留该结果并标记过期；权限失效、报表删除、结构变化或权限范围检查失败清除旧值与时间。
隐藏/切走时暂停并取消，恢复后重读；参数变化隔离旧响应。页面或看板内相同报表与参数仅合并在途请求，最多 3 路报表并发，
每卡片慢请求期间最多合并一次补读，不缓存完成结果。每次请求仍使用当前账号权限，系统通知不携带业务结果。

服务端验证策略字段与间隔，保存新策略时同时复核当前查询权限/依赖/参数，不执行查询结果。
只保存引用、实参与策略，不存结果或运行时间戳；UUID 分享移除报表策略且不执行私有报表，离线副本移除在线报表调度。
不影响数据集固定发布版本或现有静态页面。当前浏览器已验证真实计时、WS 和网络过期；目标设备长时运行仍按部署验收。

开发验证：

```bash
uv run --python 3.12 --with 'django>=5.2,<5.3' --with pillow \
  --with 'strawberry-graphql-django>=0.96.3,<0.97' \
  python scripts/test_backend.py ordloom.tests.test_graphql ordloom.tests.test_graphql_queries ordloom.tests.test_datasets ordloom.tests.test_page_bindings
```

## 跨报表看板

执行 `python manage.py migrate` 加载 `0022_report_board`。在「页面搭建 → 报表看板」新建命名看板，
添加已保存的业务报表、填写每卡片参数并预览；编辑模式可调整顺序、1–3 列宽度和 240–720 像素高度。
支持查看、保存、复制、删除及跨页名称搜索。看板需要启用现有 GraphQL 数据层，未启用时接口继续返回 404。

- `GET/POST /api/report-boards/`：按创建人/超级管理员列出或新建看板，`page` 每页 20 条，`q` 搜索最多 100 字。
- `GET/PUT/DELETE /api/report-boards/<id>/`：详情、修改和删除。PUT 与 DELETE 均需当前 `revision`；
  修订过期返回 409，不覆盖新配置。创建人由服务器确定，不接受转移归属。
- 配置仅保存报表引用、实参、标题和布局：1–20 张卡片、总配置最多 48 KiB，每卡片实参最多 16 KiB。
  未支持的字段（包括 `result`、`data`）被拒绝。示例：

```json
{
  "name": "经营看板",
  "description": "按状态查看经营金额",
  "content": {
    "schemaVersion": 1,
    "cards": [{
      "id": "bd768592-29b5-4ba1-b330-5bc05876f807",
      "reportId": "12",
      "reportParams": {"minimum": "100.0000"},
      "title": "经营金额",
      "width": 2,
      "height": 400
    }]
  }
}
```

将示例中的 `reportId` 与参数替换为自己可管理的报表及其声明。更新时在请求顶层增加当前 `revision`，
删除仅提交 `{"revision":1}`。服务端保存会验证报表归属、依赖结构、参数类型及当前模型/QuerySet/对象/字段权限，
不执行或持久化业务结果。报表已删除、权限撤销或结构变化时，保存失败并保留原配置；可以移除失效卡片后再保存，或删除看板。

读取继续使用 `/api/reports/<id>/execute/`，权限与直接执行报表一致，不因看板引用而扩大权限。
每次读取使用报表当前保存定义；同一报表可以配多张不同参数卡片。看板最多 3 路并发读取，
仅合并当前看板中相同报表/参数的在途请求，不缓存已完成结果。单卡片失败不影响其他卡片，失败状态不显示示例数据。
切走工作区标签或隐藏浏览器时取消读取，返回后重读；可点击「刷新全部数据」，启用事件服务时也响应模型变更。
单个重复卡片取消不会中断其他消费者；布局变更不触发重新查询。独立看板按授权后台管理，不提供公开 URL，
已有工作台、大屏/H5 报表组件和数据集发布版本绑定保持原有行为。

## 报表定时导出

执行 `python manage.py migrate` 加载 `0023_report_exports`，并显式启用：

```python
ORDLOOM_REPORT_EXPORTS = {
    'enabled': True,                 # 默认 False；需要已有 GraphQL 运行时
    'retention_days': 7,
    'max_schedules_per_user': 20,
    'max_artifacts_per_user': 10,     # 全账号所有计划合计，不是每个计划
    'max_runs_per_user': 100,         # 已结束记录；另限每账号最多 20 个待执行/执行中任务
    'max_file_bytes': 2097152,
    'max_source_rows': 10000,
    'lease_seconds': 300,
    'max_attempts': 3,                # 中断任务的租约恢复次数；失败任务可手动重新排队
    'manual_per_minute': 10,
    # 'permission_context': 'myapp.exports.permission_request',
}
```

「业务报表」卡片的「定时导出」可配置计划名称、CSV/Excel、类型化参数，以及每日、每周或固定间隔；
可预览当前数据、保存、暂停/恢复、删除、立即加入队列、刷新执行记录并下载已生成文件。
修订冲突保留输入，需选择左侧计划重新载入；立即排队使用 UUID 重试去重。
当前构建已完成真实浏览器界面与 Canvas 复验，范围见仓库验收矩阵。

后台命令默认只预览。宿主使用现有 cron、systemd timer、Celery Beat 或其他调度器定期调用显式执行命令：

```bash
python manage.py ordloom_export_reports --json             # 只读检查
python manage.py ordloom_export_reports --apply --limit 100 --json
python manage.py ordloom_export_reports --prune-only --json
python manage.py ordloom_export_reports --prune-only --apply --json
```

例如每分钟调用一次 `--apply`。库不启动常驻线程，也不自动安装宿主定时任务；命令必须在事务外运行。
同一计划到期只建立一条任务，停机期间错过的周期合并为一次，下一次从恢复时计算；间隔须为 15–43200 分钟。
每日/每周使用 IANA 时区和当地时间，周一为 0；夏令时缺失时间跳过当天，重复时间只选择第一次。
执行记录采用随机租约和比较更新，进程中断后可恢复，迟到的旧进程不能覆盖新结果；编辑/暂停会取消在途任务。
查询异常写安全错误码，不将异常详情、字段值、文件字节或实参写入审计日志。出现失败任务时命令返回非零。

权限与快照约定：

- 普通 staff 仅管理本人计划和文件，超级管理员可管理全部。创建、修改、手动排队均验证报表归属、字段及实参，
  同时验证后台身份；超级管理员编辑别人的计划仍按原创建账号执行。权限已撤销时仍可暂停或删除计划。
- 后台重新读取当前账号，不转发浏览器 Cookie、Session、租户头或登录状态。
  依赖租户/区域等请求上下文的宿主应提供可信 `permission_context(user, schedule)`，返回 `HttpRequest`；
  `schedule` 在保存校验时可能尚未落库，不能依赖其主键。库会将 `request.user` 替换为新读出的账号。
  默认使用空 Session 请求；多租户宿主应先验证该上下文与预期业务范围一致，不能依赖浏览器当前选择。
- 每次排队冻结当时的报表定义、依赖和实参，执行读取当前授权数据。执行中捕获参与查询的源主键，
  实际聚合进一步限制在该清单内，避免范围在捕获后扩大；生成后再次复核创建账号和数据权限才发布文件。
- 下载同时复核创建账号与当前下载者，对历史查询做字段/类型检查，并检查所有贡献源记录仍在当前授权范围内。
  金额等业务值变化不改写历史文件；任一源记录被删除、软删除、移出租户、对象/字段拒读或源数据库改变则拒绝下载，需重新生成。
  权限检查使用当前源记录状态和主键身份，宿主应保持业务主键稳定。文件已返回或请求正在执行时不能撤回。
- 私有文件、历史定义和授权主键清单存于数据库，不写公开 `MEDIA_URL`，不提供匿名令牌或公开下载地址，
  历史列表只返回状态、时间、大小、行数和安全错误码。CSV 防公式注入，Excel 使用文本单元格保留 BigInt/Decimal 精度。
  导出包含全部维度和指标；`hasMore=true`、源记录或文件超限时明确失败，不静默输出截断文件。
- worker 清除过期或超出全账号文件数上限的字节/授权清单，再按历史条数清理已结束记录；失败/取消立即清除快照。
  过期后下载立即拒绝，物理清理需要运行命令；关闭功能后仍可用 `--prune-only --apply` 清理。
  删除报表、计划或创建账号会级联删除文件。数据库备份中的历史字节沿用宿主备份保留策略。

控制表目前要求 `default` 数据库，查询仍复用现有业务数据层和显式 SQL 权限范围适配；
不增加 Celery、Excel 或云函数依赖，不更改已有报表直接执行、数据集版本及组件绑定行为。

管理 API（Session/CSRF；全部相对当前挂载点）：

| 端点 | 行为 |
| --- | --- |
| `GET/POST /api/report-exports/` | 分页列出或创建；可用 `report_id` 限定当前可管理报表 |
| `GET/PUT/DELETE /api/report-exports/<id>/` | 查看、修改或删除；修改/删除需当前 `revision` |
| `GET/POST /api/report-exports/<id>/runs/` | 分页历史，或用 `revision` 与标准 UUID `request_id` 立即排队 |
| `GET /api/report-exports/runs/<id>/download/` | 当前权限验证后的私有下载；未就绪 409，过期 410 |

创建示例：`{"name":"每日经营","report_id":"12","params":{},"format":"xlsx","enabled":true,"cadence":{"kind":"daily","time":"09:00","timezone":"Asia/Shanghai"}}`。
周计划增加 `weekday:0` 并改为 `kind:"weekly"`；间隔配置为 `{"kind":"interval","minutes":60}`。
演示可使用 `scripts/dev_fields.py --datasets --report-exports --production`（临时 SQLite、合成记录）；
默认不自动执行队列。专项测试为 `python scripts/test_backend.py ordloom.tests.test_report_exports`。
`python scripts/test_report_exports.py` 使用临时 SQLite、真实 HTTP/Session/CSRF 和当前构建产物，
通过仅在演示脚本中的受保护控制端点调用同一管理命令，核对 CSV/Excel 排队及下载；结束清理自己的服务与数据库。
导出管理界面在元数据复核失败或离开面板时清除预览和历史入口，迟到结果不能恢复旧数据；
恢复面板先复核当前权限，未保存的输入和修订号保留。历史/下载检查失败隐藏旧下载入口；
排队失败重试沿用同一请求 UUID，成功后的新操作使用新编号。模拟 API 的回归入口为前端
`npm run test:collaboration-ui`，当前浏览器已复验计划配置、排队和真实下载；生产调度需由部署工程接入。
