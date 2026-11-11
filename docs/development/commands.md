# 初始化、维护命令与任务诊断

Ordloom 不内置任务调度器。使用项目自己的 cron 或任务平台串行执行维护命令，写入型命令按其帮助信息显式执行。

`ordloom_check --probe`、`ordloom_check_tasks`、`ordloom_export_submissions` 与 `ordloom_reindex_submissions` 自 1.0.1 起提供；配置、显式执行和资源边界见 [运维与答卷指南](../guides/operations-and-submission-exports.md)。1.0.2 的手动质量门禁和持续运行工具见 [稳定性指南](../guides/resilience-and-release-gates.md)。

## 宿主工程初始化与升级

先按接入说明配置应用和 URL。以下命令由已经获得宿主运维权限的操作者运行；默认输出计划，`--apply` 才写入。
支持 `--database <alias>`、`--json` 和文本输出，错误返回非零退出码，错误信息不包含数据库凭据或配方内容。

### 迁移计划与升级执行

```bash
python manage.py ordloom_upgrade --json
# 核对 pending 列表，将下方值替换为上一步的 plan_id
python manage.py ordloom_upgrade --apply --plan-id '<plan_id>' --json
python manage.py collectstatic --noinput
python manage.py ordloom_check --json
python manage.py ordloom_reindex_visual --check --json
```

升级计划覆盖所选数据库中**全部已安装应用的待执行向前迁移**，包括 Django 认证/会话及宿主业务迁移，等同常规 `migrate` 的范围。
每项标明 `app/name/scope`（`package` 或 `host`）；预览只读取迁移历史、代码和配置，不建表或补写站点配置。
签名绑定数据库目标、迁移源码、当前应用历史及目标节点；数据库、迁移文件或应用历史变化后，旧 `plan_id` 不能执行。
执行前运行 Django 工程检查，再调用标准迁移命令及 `post_migrate`；分支冲突、向后计划或不完整的应用数据库路由会拒绝。

宿主部署流程需要串行安排迁移进程；签名复核不是跨进程数据库锁。迁移事务按各迁移声明及数据库能力执行，
失败时可能已有迁移提交，命令不自动回退；修复后重新预览当前状态。`applied` 表示迁移执行完成，`ok` 还检查包、URL 和可选配置，
迁移成功但接入检查失败会返回非零。静态收集、重启和对外发布由宿主部署流程执行，命令不会改写 `settings.py` 或 `urls.py`。

### 默认配置与静态示例

```bash
python manage.py ordloom_init --json           # 仅预览站点默认配置
python manage.py ordloom_init --apply --json   # 缺失时创建，已有验证码设置保留
python manage.py ordloom_init --list-templates --json
python manage.py ordloom_init --user '<已有账号>' --json
python manage.py ordloom_init --user '<已有账号>' --apply --json
# 可选择静态模板，多个 --template 合并为一批
python manage.py ordloom_init --user '<已有账号>' --name team-demo \
  --template screen:antv --template h5:survey --apply --json
```

`--user` 使用当前认证模型的 `USERNAME_FIELD`，兼容用户名与邮箱等自定义账号；必须是已存在、有效的 staff/超级管理员。
命令不创建账号、默认密码、组或权限。没有 `--user` 时仅处理站点配置；指定账号后默认生成运营大屏与滚动叙事 H5 两张静态示例，
也可选择打包的 11 套模板，安装宿主无需 Node.js。模板来自编辑器同一份定义，素材通过宿主静态存储解析；生产环境应先完成 `collectstatic`。
页面名称带「静态示例」标识，图中数字为样例，未绑定业务数据；生成页面默认关闭分享，表单默认停止收集。

0020 的 `InitializationBatch` 按账号和 `--name`（默认 `starter-v1`）保存配方指纹与页面/数据集/报表 ID。
相同配方重复执行返回原记录，不覆盖名称、布局、分享设置或验证码开关；被删除或移出归属的页面只报告不可用，不自动补建。
同名批次改用其他配方返回 `BATCH_CONFLICT`，请使用新名称；不根据页面名称猜测是否为历史示例，也不修复被手工删除的批次记录。
可将预览的 `plan_id` 传给初始化的 `--plan-id` 校验配置与字段定义仍一致；默认静态模板变化或业务数据源结构变化时需重新预览。

### 业务数据配方

启用已有 GraphQL 模型/字段白名单后，保存本地配方 JSON（最多 64 KiB，每批 1–3 套；名称不可重复）：

```json
{
  "schemaVersion": 1,
  "templates": [{
    "template": "commerce-screen",
    "name": "经营看板",
    "model": "sales.order",
    "fields": {"category": "status", "value": "amount", "date": "created_at", "label": "code"}
  }]
}
```

```bash
python manage.py ordloom_init --user '<已有账号>' --name commerce-v1 --recipe ./recipe.json --json
python manage.py ordloom_init --user '<已有账号>' --name commerce-v1 --recipe ./recipe.json \
  --apply --plan-id '<plan_id>' --json
```

模板键与字段要求沿用「业务数据模板」：`commerce-screen`、`service-screen`、`business-h5`。
业务模式使用同一 ModelAdmin、QuerySet、对象/字段权限和查询限额；校验后生成草稿、不可变 v1 和绑定页面，默认手动更新且关闭分享。
不会修改业务记录或保存查询结果；权限校验可能按现有对象规则读取业务对象。创建后再次核对发布查询与预览签名，变化则回滚整批。
一批中的页面、版本、索引、站点配置和批次记录同事务提交，任一创建失败全部回滚。
当前业务配方要求应用模型统一位于 `default`；静态初始化、诊断与迁移支持显式数据库别名，复杂业务路由可沿用宿主 API 创建流程。

### 独立报表示例配方

`--report-recipe` 使用已启用的 GraphQL 模型/字段白名单和同一报表校验层，生成个人私有 `Report`。
它与 `--template`、`--recipe` 互斥，文件最多 64 KiB、每批 1–10 个报表，名称须唯一：

```json
{
  "schemaVersion": 1,
  "reports": [{
    "name": "订单状态统计",
    "description": "按状态汇总订单金额",
    "definition": {
      "model": "sales.order",
      "mode": "aggregate",
      "groupBy": [{"field": "status", "name": "state"}],
      "metrics": [{"name": "total", "operation": "SUM", "field": "amount"}]
    },
    "chart": {"type": "bar", "category": "dimensions.state", "value": "metrics.total"}
  }]
}
```

```bash
python manage.py ordloom_init --user '<已有账号>' --name report-demo-v1 \
  --report-recipe ./reports.json --json
python manage.py ordloom_init --user '<已有账号>' --name report-demo-v1 \
  --report-recipe ./reports.json --apply --plan-id '<plan_id>' --json
```

将示例模型和字段改为宿主已开放的名称。`definition` 支持报表原有筛选、排序、分组、指标、类型化参数和 JSON 标量列；
`chart` 沿用报表图表/表格映射约定。必填参数仅保存声明，查看报表时仍须传入实参。预览返回配置摘要，不执行汇总或保存业务结果；
权限检查可能读取授权范围内的原始对象。预览和创建分别校验当前账号、模型/模块、QuerySet、对象及字段权限，工厂不能替换账号。

该模式仅在 `default` 数据库创建私有报表、缺失的站点配置及初始化批次，复用 0020。
配方、规范化定义、字段依赖和图表共同参与计划签名；创建前结构或权限变化会拒绝，失败回滚整批。
相同账号/批次重试不覆盖报表编辑，被删除或转交的报表只标记不可用；切换配方或初始化模式须使用新 `--name`。
JSON 输出包含 `mode: "reports"`、`reports` 摘要及 `created_reports`，原页面模式的输出与指纹格式保持兼容。

专项检查：`python scripts/test_backend.py ordloom.tests.test_report_initialization`；
真实临时宿主管理命令：`python scripts/test_report_initialization.py`；PostgreSQL 并发检查在隔离运行器中使用 `--report-init`。
这些检查不会连接用户宿主或迁移用户数据库。

### 数据配方的权限上下文

默认 CLI 请求只包含指定账号和空会话。如果权限逻辑需要租户、组织或其他中间件上下文，应在宿主配置可信请求工厂：

```python
# settings.py
ORDLOOM_SETUP_REQUEST_FACTORY = 'project.setup_context.request_for_owner'

# project/setup_context.py
from django.http import HttpRequest

def request_for_owner(*, user, using):
    request = HttpRequest()
    request.method = 'POST'
    request.session = {}
    request.tenant = user.tenant   # 使用宿主已有的账号/租户关系
    return request
```

工厂须返回 `HttpRequest`，仅补充上下文；命令重新加载指定账号作为 `request.user`，不接受工厂替换认证主体。
缺少宿主要求的上下文时校验失败，不猜测或放宽租户范围。工厂和现有权限钩子应保持只读。

仓库验收脚本使用临时宿主工程和 SQLite，不连接已有项目数据库：

```bash
python scripts/test_host_setup.py
python scripts/test_host_setup.py --serve --port=8662  # 验收后临时提供 /control/ 挂载点
```

## 后台任务运行诊断

默认关闭，复用超级管理员的全局管理权限；普通 staff、匿名访问或单独 Bearer 凭据不能读取全局任务记录。
启用后在账号菜单打开「后台任务运行诊断」，或使用 `GET <挂载前缀>/api/task-diagnostics/?database=default`。该入口只读、不缓存，不提供执行/重试/删除任务操作。

```python
ORDLOOM_TASK_DIAGNOSTICS = {
    'enabled': True,                  # 默认 False
    'history_size': 10,                # 每任务/数据库最近 10 次，允许 1–30
    'retention_seconds': 604800,       # 默认 7 天，允许 60–2592000 秒
    'running_timeout_seconds': 3600,   # 执行超期提示，允许 1–86400 秒
    'stale_after_seconds': {           # 可省略；按实际调度周期调整
        'webhooks': 300,
        'report_exports': 900,
        'report_cleanup': 86400,
        'audit_retention': 86400,
        'share_visits': 86400,
    },
}
```

观测 `ordloom_deliver_webhooks`、`ordloom_export_reports`、其 `--prune-only` 文件清理模式、`ordloom_prune_audit` 和 `ordloom_prune_share_visits`。
仅显式 `--apply` 写入运行记录；默认预览不写遥测，已有参数、JSON 输出及退出码保持兼容。
仍由宿主 cron/任务平台运行原命令，诊断页不会调度任务。启用观测不会替代 Webhook、导出或留存功能自身的开关。

运行记录复用默认共享缓存，按任务/数据库隔离并使用独立执行标识，迟到的旧执行不会覆盖较新的执行。
仅保存开始/结束 UTC 时间、耗时、状态、固定错误码和允许的整数计数，兼容宿主 `USE_TZ=False`。
不保存命令参数、查询结果、文件路径、目标地址、响应正文、凭据或原始异常；诊断配置/缓存故障不会中断原业务命令。
队列摘要从数据库只读取数量，包括待处理、执行中、失败、到期和失效租约。报表导出/清理服务仍限 `default` 数据库；支持数据库参数的其他命令按选定别名观测。

缓存历史受数量、TTL 和逐出约束，不能代替持久审计或进程心跳。
「尚无执行记录」「近期未观测到执行」「执行超时或中断待核对」均需结合调度器核对，不推断进程已经停止或实时在线。
非已识别的共享缓存会提示跨进程共享能力未确认；缓存异常显示记录不可用，队列不可用时单独提示。
阈值只用于界面提示，不自动重试或发送告警；`stale_after_seconds` 的值允许 1–2592000 秒。

隔离回归见 `test_share_limits.py`、`test_task_diagnostics.py`；实际 Redis 双进程检查见仓库 `scripts/test_batch1_cache.py`。
真实浏览器与发布边界见 [验收矩阵](https://github.com/neekin/simpleui-antd/blob/main/docs/roadmap-acceptance.md)。
