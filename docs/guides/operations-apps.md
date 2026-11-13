# 运营子应用：到期提醒、工单服务台与资产台账

三个面向内部运营的独立子应用包：`ordloom-reminders`（到期提醒）、`ordloom-tickets`（工单服务台）与 `ordloom-assets`（资产台账），均基于子应用 SDK，Python 模块分别为 `ordloom_reminders`、`ordloom_tickets`、`ordloom_assets`。发行包版本为 0.1.0，要求 Ordloom 1.1.0+；三者只依赖核心，不依赖会员或其他业务包，也没有公开 URL，全部能力在后台与任务命令中使用。

## 安装

```bash
python -m pip install ordloom-reminders==0.1.0 ordloom-tickets==0.1.0 ordloom-assets==0.1.0
```

三包可单装或组合，按需添加：

```python
INSTALLED_APPS += [
    "ordloom_reminders.apps.ExtensionConfig",
    "ordloom_tickets.apps.ExtensionConfig",
    "ordloom_assets.apps.ExtensionConfig",
]
```

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```

为员工授予对应模型权限（如 `ordloom_reminders.view_reminder`、`ordloom_tickets.view_ticket`、`ordloom_assets.view_asset`）后，菜单出现「到期提醒 → 到期概览」「工单服务台 → 工单概览」「资产台账 → 资产概览」；大屏/H5 搭建器的「子应用」分类出现三个静态入口组件（属性为标题与说明，不接数据绑定）。

## 到期提醒

事项按负责人隔离：普通员工只能管理自己的事项，超级管理员可管理全部。「到期扫描」任务扫描任务账号可见范围内启用且进入提醒窗口（到期日减去提前天数）的事项，向负责人发送站内通知；通知按事项与到期日去重，重跑不重复投递，仅投递给有效员工账号。任务由宿主调度：

```bash
python manage.py ordloom_run_app_task ext:reminders.scan --user 1 --apply --json
```

扫描范围受 SDK 1000 条对象预算约束；提醒依赖站内通知中心（`ORDLOOM_NOTIFICATIONS`），不含邮件或即时消息外发。

## 工单服务台

普通员工可见自己提交或被指派的工单；状态按 待处理 → 处理中 → 已解决 → 已关闭 流转，非法迁移（如直接从待处理跳到已解决）在保存时拒绝；已解决时间自动记录。回复记录只增不改，内部备注与对外回复同表区分。「SLA 超时检查」任务对超过处理时限的未解决工单向负责人（未指派时为提交人）发送站内通知，按工单与时限去重：

```bash
python manage.py ordloom_run_app_task ext:tickets.sla_scan --user 1 --apply --json
```

## 资产台账

台账为共享登记簿，按模型模块权限管理，不做逐对象隔离。资产状态变更（在库/在用/维修中/已报废）在同事务自动写入不可变流水，动作（领用/归还/报修/报废）由状态变化推导，流水对所有人只读，只能由状态变更与「登记盘点」产生；后台列表提供「登记盘点」action，同一天重复登记不产生重复流水。「盘点提醒」任务对在用且超过 `ORDLOOM_ASSETS={'inventory_days': 90}` 天未盘点的资产向保管人发送站内通知，按资产与月份去重：

```bash
python manage.py ordloom_run_app_task ext:assets.inventory --user 1 --apply --json
```

概览页的最近流水读取复用注册 ModelAdmin 的 QuerySet 与查看权限；无流水查看权限的员工看到空列表，不影响资产概览。

## 权限与边界

三个应用复用宿主 Django 权限与站内通知中心，不新增认证体系；SDK 专用页为只读，业务写入全部走 ModelAdmin 与核心编辑接口，并受对象范围约束。停用应用使用 `ORDLOOM_DISABLED_APPS=['reminders']`（或 `tickets`/`assets`），菜单、页面、组件配置与任务同时关闭。

本地验证（隔离源码宿主）：

```bash
python scripts/test_products.py --reminders-only
python scripts/test_products.py --tickets-only
python scripts/test_products.py --assets-only
python scripts/test_products.py --email-user
```

后续增强候选：到期提醒的周期性事项与提醒升级、工单的 SLA 分级策略与升级链、资产的采购与折旧字段；均按真实业务需求排期。
