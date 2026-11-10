# 工作区、组织与所有权

资源访问权限和业务数据权限分开计算。共享页面、数据集、报表、轮播或看板不会借用其他成员的数据权限。

## 协作工作区

先执行 `python manage.py migrate` 应用全部向前迁移（工作区 0024、组织成员 0025、所有权交接 0026），再显式启用：

```python
ORDLOOM_COLLABORATION = {
    'enabled': True,                 # 默认 False，保留原有创建人隔离
    'max_workspaces_per_user': 20,
    'max_members': 200,
    'max_shares_per_resource': 20,
}
```

启用后「页面搭建 → 团队协作」支持创建/编辑工作区、加入已有账号/用户组、调整角色及移除成员。
个人资源所有者/超级管理员从页面、数据集、报表、轮播和看板的「协作授权」逐项设置工作区 read/edit；资源也可经确认交由工作区持有。
五类资源界面按 read/edit/manage 能力显示只读、编辑和当前所有者/工作区管理操作；只读访问仍可配置运行参数并按当前账号权限预览或查询。
基础工作区 API 不依赖 GraphQL；
数据集/报表的实际查询仍需已有可选运行时。配置无效时关闭协作扩权，原创建人范围保持；协作 API 报配置错误。

工作区是配置资源的组织范围，支持独立账号和现有 Django 用户组。不会自动成为业务数据的租户边界，
也不会授予 Django 模型权限或更改项目已有 `ModelAdmin.get_queryset`、对象及字段规则。
个人资源由所有者/超级管理员逐项授权，加入工作区不会自动读到个人所有页面；工作区持有的资源按该工作区角色开放。

| 工作区成员角色 | 工作区内资源能力 |
| --- | --- |
| `viewer` | 读取已显式共享及工作区持有的配置；执行查询时仍检查自己的数据权限 |
| `editor` | 还可编辑工作区持有及被授予 `edit` 的资源；个人资源仅授予 `read` 时仍为只读 |
| `manager` | 同 editor，另外管理工作区名称、成员及工作区持有的资源；个人资源的分享/删除仍由其所有者控制 |
| 工作区当前所有者 | 始终有工作区管理权；仍需资源自身的共享授权才能编辑别人个人所有的内容 |

资源授权为 `read` 或 `edit`。有效编辑权限必须同时满足**同一个工作区**的 editor/manager 成员关系与 `edit` 授权，
不能把甲工作区的成员角色与乙工作区的授权拼在一起。重叠账号/用户组或多个工作区不会重复列出资源。
个人资源所有者保留原有权利，超级管理员保留全部管理权；无个人所有者且未由工作区持有的历史资源仅超级管理员可恢复，不接受普通协作扩权。

管理 API 使用 Session/CSRF，列表每页 20 条，所有标识支持十进制字符串：

| 端点 | 行为 |
| --- | --- |
| `GET/POST /api/workspaces/` | 当前可见工作区或创建工作区 |
| `GET/PUT/DELETE /api/workspaces/<id>/` | 读取；manager 修改；仅当前所有者/超级管理员删除；仍持有资源或待接交接时拒绝；写入需当前 `revision` |
| `GET/POST /api/workspaces/<id>/members/` | manager 查看成员或加入账号/用户组 |
| `PUT/DELETE /api/workspaces/<id>/members/<member>/` | manager 改角色/移除成员；需 `revision` |
| `GET/POST /api/collaboration/<kind>/<resource>/` | 仅当前资源管理者列出或新增工作区授权 |
| `PUT/DELETE /api/collaboration/<kind>/<resource>/<share>/` | 改访问级别或撤销；需 `revision` |
| `GET /api/collaboration/<kind>/<resource>/access/` | 当前资源的 `read/edit/manage` 能力，界面同时读取各资源载荷中的 `permissions` |

`kind` 仅支持 `page/dataset/report/playlist/board`，不接受任意模型名。新增授权需要本人是目标工作区成员。
创建工作区提交 `{"name":"经营团队","description":"配置协作"}`；成员提交 `{"user":"现有登录账号","role":"editor"}`，
`user` 按当前用户模型的 `USERNAME_FIELD` 精确匹配有效 staff；也可使用 `{"group":"已有用户组名称","role":"viewer"}`。
普通账号只能选择自己所属的组，超级管理员可选择全部组；不创建账号或改写 Django 用户组关系。
新增资源授权提交 `{"workspace_id":"12","access":"edit"}`。更新只提交相应可编辑字段与当前修订号，冲突返回 409。

配置保存的冲突保护：

- 仅启用协作时，各资源列表/详情/保存响应带 `permissions: {read,edit,manage}`；关闭后保留原载荷。
  界面能力只控制操作入口，服务端每次请求重新复核。数据集、看板继续使用已有整数 `revision`。
- 页面、报表和轮播在详情响应中带 `configuration_token`。PUT 时提交同一次读取的
  `base_configuration_token`；保存成功响应返回新令牌。令牌绑定资源类型、ID 和完整配置，不依赖时钟精度。
  检查与保存处于同一行锁事务；配置已变化返回 409，非法/缺少必需令牌返回 400，不覆盖现有配置。
- 当资源由工作区持有或存在有效的 `edit` 工作区授权记录时，当前管理者/超级管理员也必须提交令牌；个人资源仅只读共享不强制要求。
  协作关闭或个人资源未配置编辑共享的旧调用可继续省略令牌；已主动提交的令牌仍会校验。
  新界面启用协作后始终携带读取到的令牌，覆盖未设置编辑共享时的多窗口保存。
- 工作区/成员/授权保留未应用输入，冲突后显示当前已保存角色与修订号，需再次操作才会应用。
  页面/报表/轮播冲突保留草稿，「重新载入」在有修改时先确认放弃。成员与授权分页保留当前输入。
  只读数据集使用 `/datasets/<id>/preview/` 和当前草稿修订号，避免改走任意未保存定义；可编辑数据集预览前刷新资源能力。

行为边界：

- 读取配置会包含布局、查询定义、筛选和已配置参数。数据集的共享覆盖草稿、已有与未来版本；旧组件仍固定原发布号。
  不隐式共享页面绑定的数据集、引用报表或轮播中的页面；需要分别授权。查询和保存复用访问者自己的字段/对象/租户权限，
  不使用资源创建人的身份。归档数据集拒绝新增工作区授权或提高既有授权级别，既有组织范围仍按当前成员关系生效。
- 个人资源的删除、归档、公开分享、答卷及访问统计由当前所有者/超级管理员管理；工作区持有的资源由该工作区管理员管理。
  协作者修改页面时会撤销该页面已有公开数据授权，需当前管理者重新确认；公开静态页面仍遵守原分享设置。
  非本次确认账号修改页面也会撤销有效数据授权。重新确认/调整有效授权会使用确认者的权限；执行账号变化时轮换数据令牌，
  旧令牌不能继续读取之前管理员的数据。纯撤销不转移执行身份，审计保存执行账号标识，不保存令牌。
- 新增轮播选页仍要求当前操作者管理该页面。协作编辑可保留原选页、修改时长，但不能刷新他人页面的受保护链接代次；
  页面令牌轮换后旧公开轮播仍失效，协作者不能通过重新保存恢复它。
- 账号/组成员、角色或资源授权变化在后续请求重新计算，不缓存协作授权结果；启用协作时公开数据授权也不复用结果缓存。
  已返回或正在处理的数据不能撤回；当前页面是否立即刷新仍由已有组件更新策略决定。
- 删除未持有资源且无待接交接的工作区只撤销其授权，不删除页面或业务数据；资源删除级联清理授权，避免主键复用留下旧访问权。
  0026 后删除工作区所有者账号会清空所有者引用，保留工作区与其他成员；授权操作者删除仅清空操作归属，已批准授权保留。
  工作区持有的资源不依赖原个人账号。未交接个人资源仍遵循原模型删除规则：页面/数据集/报表/看板可成为待管理员恢复的记录，私人轮播仍按原级联规则处理。
  可信批量/原始 SQL 运维需保持成员恰为账号、用户组或有效组织来源之一、授权恰为一种资源；运行时也拒绝多目标或无目标的异常授权。
- 0025 已提供下面的宿主组织只读适配、实时层级与组织成员授权，0026 已支持工作区持有、确认交接与管理员恢复；仓库测试宿主的组织选择、成员撤销和确认交接已通过当前浏览器检查；其他业务工程映射与生产容量按部署验证。

源码见 `collaboration.py` / `api/collaboration.py`，专项测试：
`python scripts/test_backend.py ordloom.tests.test_collaboration`。
前端另有 `cd frontend && npm run test:collaboration-ui`：28 项实际 React/Ant Design DOM 组件检查（API 用夹具，Canvas 不在检查范围），
不能替代真实浏览器、真实 Session/CSRF 或宿主并发验收。
临时演示可加 `scripts/dev_fields.py --collaboration --production`；不写宿主数据库，不自动建立组织或授权。

## 宿主组织目录与层级

组织目录作为只读数据源接入，工作区成员仍由工作区管理员显式加入。管理员可以选择部门的直接成员，
或勾选「包含下级部门成员」。默认关闭；基础协作以及原来的账号/用户组授权均保留。
应用 0025 后配置宿主已有部门模型与成员关系，例如：

```python
ORDLOOM_ORGANIZATIONS = {
    'enabled': True,  # 同时需要 ORDLOOM_COLLABORATION['enabled'] = True
    'organization_model': 'company.Department',
    'membership_model': 'company.DepartmentMember',
    'key_field': 'public_id',  # UUIDField(unique=True, editable=False)，非空且不可重用
    'name_field': 'name',
    'parent_field': 'parent',  # 自关联 ForeignKey；平面目录明确设置 None
    'user_field': 'account',  # ForeignKey(settings.AUTH_USER_MODEL)
    'organization_field': 'department',  # ForeignKey(Department)
    'organization_active_field': 'is_active',  # BooleanField；无停用字段明确设置 None
    'membership_active_field': 'is_active',    # BooleanField；无停用字段明确设置 None
    'max_nodes': 2000,  # 1–10000，活动目录节点预算
    'max_depth': 32,    # 1–64，含当前节点
}
```

示例宿主关系（已有模型符合契约时仅需配置映射）：

```python
import uuid
from django.conf import settings
from django.db import models

class Department(models.Model):
    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=100)
    parent = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)

class DepartmentMember(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    class Meta:
        indexes = [models.Index(fields=['account', 'department', 'is_active'])]
```

两个宿主模型须为 default 数据库中的实体模型；组织模型使用单列整数、UUID 或最多 512 字的字符主键，
名称为文本、关系为相应 ForeignKey、停用标志为 BooleanField；`_su_org_member/_su_org_name` 为目录保留别名。
组织名称在 SQL 中截取前 100 字后传输，避免读取完整长文本；组织身份仍为不可重用的 UUID。
包不会创建/修改宿主部门、人员归属、账号、Django 用户组或模型权限。缺少稳定 UUID 的工程需由宿主补充身份字段，
不能把可复用的数字主键当作组织身份。字段设置变更由宿主自行管理迁移；本包仅新增自己的组织成员授权字段。
部门 UUID 不可编辑、不可复用；删除并复用数字主键会得到新的 UUID，旧授权继续失效。

启用后「团队协作 → 成员类型 → 组织部门」可搜索组织路径和分页选择。
普通账号可选本人直接所属部门及其活动下级，不能选择祖先或其他分支；超级管理员可选全部活动目录。
列表路径包含祖先名称以提供上下文，但不会提供宿主员工花名册、业务字段或任意模型查询。
名称与路径按本节的组织归属规则可见，其元数据范围独立于宿主组织管理页面的权限；其他业务字段仍使用原接口。
`GET /api/collaboration/organizations/?page=1&q=名称` 返回 `key/source/name/parent/path`，每页 20 条；
仍使用 Session，非 staff 和匿名拒绝，修改成员需要正常 CSRF。

加入组织提交：

```json
{"organization":{"source":"目录返回的来源指纹","key":"目录返回的UUID"},"role":"editor","include_descendants":false}
```

来源指纹绑定宿主模型、组织身份、关系与停用规则。授权后更换这些映射会使旧来源记录失效，需管理员显式撤销/重建，
不会将旧部门授权自动解释为另一套组织。部门名称变化实时显示，不改变授权身份。
成员更新继续提交当前 `revision`，可提交 `role` 和/或 `include_descendants`；省略角色时保留原角色。
从直接成员扩大至下级范围时重新检查操作者的可选部门范围，缩小或移除不受该扩展检查限制。
目录失效、停用或已删除的组织关系在界面标为不可用，保留明确撤销入口。

每次构造组织权限范围，用一个有界 SQL SELECT 同时读取活动树和当前账号的成员标记，在同一语句快照上计算祖先，
避免从多次读取的层级版本拼接路径。组织成员、停用、删除及移动在后续请求重新读取，不依赖同步任务或结果缓存。
未勾选下级时仅匹配直接部门成员；勾选后匹配当前活动祖先链。停用/默认 manager 不可见的父节点切断继承，
子节点的直接授权仍按自己的活动状态生效。整个活动目录循环、超预算、无效映射或查询失败时组织权限不生效，
原创建人及有效的账号/用户组授权继续工作；SQL 失败用保存点隔离，目录 API 明确返回 503。
已开始或已返回的请求数据无法撤回；业务查询仍叠加当前访问者的模型/模块/租户/对象/字段规则。
一个部门的角色不能与另一工作区的资源授权拼接，组织身份也不授予公开分享、删除资源或答卷管理权。

目录一次最多读取 `max_nodes + 1` 行，不会因分页放宽预算；超额时先调整宿主目录/索引并核验实际开销。
建议给宿主成员表的账号、部门与活动条件提供适合实际数据库的索引。此实现支持 UUID 身份与配置字段映射，
并不代替宿主组织 CRUD、任意外部目录协议、多数据库同步或无限规模树引擎。
0026 后工作区所有者与授权操作者的删除清空相应归属，工作区、既有协作授权与工作区持有的资源继续保留；所有权交接见下一节。

检查与验收：

```bash
python manage.py ordloom_check --json
python scripts/test_backend.py ordloom.tests.test_organizations
python scripts/test_organizations.py
```

专项覆盖实时组织撤销、层级/停用、数字主键复用与旧 UUID 授权隔离、来源变更、预算/循环、原生授权兜底，以及数据集当前模型/字段/QuerySet 权限。
真实 HTTP 脚本创建并清理自己的临时数据库/服务，执行 17 项 Session/CSRF/实时撤销检查；不会连接宿主工程。
组件检查使用模拟 API，不替代真实浏览器和宿主容量验收。临时演示可用 `scripts/dev_fields.py --organizations --production`：
creator 属于经营中心，viewer 属于其销售组，reviewer 属于独立团队；部门与成员是临时合成数据。

## 所有权交接与工作区持有

启用协作并应用全部迁移后，个人页面、数据集、报表、轮播与看板可交给另一个有效 staff 账号，
也可交由本人可见的工作区持有。工作区本身只能交给当前工作区管理员账号。
发起时仅创建交接单；接收账号，或接收工作区的当前管理员，查看已保存配置并确认后才改变所有权。
超级管理员可安排无所有者资源/工作区的恢复，目标账号仍需接收；恢复工作区前先为目标账号配置管理员角色。

| 资源归属 | 读取/编辑/管理 |
| --- | --- |
| 个人所有 | 当前个人所有者管理；其他成员仍需原有逐项 read/edit 授权 |
| 工作区持有 | viewer 读取；editor 编辑/发布；manager 管理资源、协作授权、公开分享、答卷及访问记录 |
| 历史无归属 | 仅超级管理员可安排恢复；普通成员不能自行接管 |

管理工作区持有的资源与接出其所有权是不同能力：接出仅该工作区当前所有者/超级管理员可发起，
普通 manager 可以确认资源进入工作区，不能自行将团队资产转为私人资产。个人资源原有权限保持兼容。
底层旧字段 `created_by` 在这五类资源及工作区中继续承载个人管理归属；交给账号时改为接收人，交给工作区时为空，
由 `owner_workspace` 指向工作区。`created_at`、发布版本的发布人/时间/定义不重写，交接操作另存无内容审计。
关闭协作不会把工作区资源还给原个人；普通账号对工作区资源暂停访问，超级管理员可管理。

使用入口：资源「协作授权 → 交接所有权」；工作区详情「交接工作区所有权」；「团队协作 → 所有权交接单」查看/接收/拒绝/撤销。
有未保存配置或未应用授权时，先保存/应用或放弃再发起。交接预览只读取保存配置、已配置参数与授权范围，
不会执行数据集/报表或展示实际业务结果。元数据仅在交接仍有效且接收资格/发起权限仍满足时提供；
其他账号不能凭交接单 UUID 读取配置。参数与原协作范围在预览中明确展示。

API 使用 Session/CSRF：

| 端点 | 行为 |
| --- | --- |
| `GET /api/ownership/context/<kind>/<id>/` | 当前所有者读取保存配置与本次 `guard` |
| `GET/POST /api/ownership/offers/` | 分页列出本人相关交接，或发起交接 |
| `GET /api/ownership/offers/<uuid>/` | 查看交接及仍有效的保存配置 |
| `POST /api/ownership/offers/<uuid>/` | `action=accept/reject/cancel` 与当前 `revision` |

`kind` 为 `workspace/page/dataset/report/playlist/board`。发起示例：

```json
{"kind":"page","resource_id":"12","guard":"context返回的令牌","destination":{"kind":"user","login":"接收账号"}}
```

工作区接收目标为 `{"kind":"workspace","id":"8"}`。标识保留为字符串，接收账号按当前用户模型的登录字段精确匹配。
`guard` 绑定资源身份、所有权修订、已保存配置与协作授权；工作区绑定其成员配置。
配置/授权改变、接收资格或发起人权限撤销后不能接收，返回 409 或范围内 403/404，原资源保持当前状态。
不把交接视为借用业务权限：接收后所有实际查询仍使用调用者自己的模型/模块/租户/对象/字段规则。
公开数据授权的确认者还须保有当前页面管理权，失去管理权后停止发放及执行授权，即使仍有数据集读取权。

接收页面/轮播本身时，关闭公开分享、轮换链接代次并撤销该页面的数据授权；新所有者需重新配置。
工作区所有者变更不改变工作区对资源的持有，仍按当前角色判断管理和原公开授权确认者资格。
个人导出计划与私有文件、外部服务凭据及其执行身份不自动转移；页面引用的数据集、报表及轮播选页需分别安排权限/交接。
数据集与看板递增原配置修订号，所有资源递增独立所有权修订号；页面/报表/轮播配置令牌包含所有权身份，旧窗口不能覆盖接管后的资源。
界面切回标签或本机接收成功后刷新权限，保留旧草稿的修订号/令牌；所有权变化要求重新载入，未保存输入保留。
数据集预览刷新权限也不会将旧草稿升级为其他窗口的新修订号。

工作区被删除会清除其成员及普通共享授权；仍持有资源或待接交接时通过 PROTECT 拒绝删除。
已有账号删除不清空工作区或已批准协作授权；保留的管理员可继续管理工作区资产，缺少管理员时由超级管理员安排恢复。
页面授权审计记录当前所有者/工作区快照，交接和删除追加记录；按该页面最后一次审计归属校验历史访问，
接管后可读取原历史，页面删除后仍由相应所有者/当前工作区管理员查看。工作区删除后无法再按其成员关系读取历史，超级管理员仍可查。

每个资源只保留一张当前交接单，终态或失效交接可被新交接替换，资源删除级联清理；完整操作另写无内容 LogEntry，
不在交接表复制业务结果或凭据。默认有效 24 小时、每账号最多 20 个在途交接，可在协作配置中设置
`handover_hours`（1–168）和 `max_pending_handovers`（1–100）。过期单不能接收，不因轮询续期。
控制表与账号须统一 default 数据库，路由不满足时拒绝处理；业务数据仍可遵循原访问层的数据库规则。

交接在同一事务中校验并锁定；PostgreSQL 先按顺序锁账号（NO KEY UPDATE，允许外键引用写入），再锁相关工作区、资源和交接单。
修订冲突、审计异常或保存失败不留半次接管。专用临时 PostgreSQL 的 52 项检查已通过，含同时接收只提交一次所有权修订及审计；这不代替实际宿主并发/容量验收。

```bash
python scripts/test_backend.py ordloom.tests.test_ownership
python scripts/test_ownership.py
# 可选：仅启动并清理自己专用的临时 PostgreSQL；具体依赖见脚本头部
python scripts/test_ownership_postgres.py
```

真实 HTTP 脚本验证 17 项跨账号接收、原权限撤销、工作区持有、真实账号删除保留与管理员恢复，使用随机身份校验自己的临时服务。
组件回归使用模拟 API，不替代真实浏览器及实际宿主接入/负载验收。预先明确资源交接与备份流程，再执行真实账号离职处理。
