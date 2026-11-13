# 活动报名子应用

独立 `ordloom-events` 包，Python 模块为 `ordloom_events`，基于子应用 SDK，并显式依赖 `ordloom-members`。发行包版本为 0.1.0，要求 Ordloom 1.1.0+ 与会员应用 0.1.0+；安装会自动解析核心与会员依赖。

## 安装与开放入口

```bash
python -m pip install ordloom-events==0.1.0
```

保留原 Django/Ordloom 配置，按需添加：

```python
INSTALLED_APPS += [
    "ordloom_members.apps.ExtensionConfig",
    "ordloom_events.apps.ExtensionConfig",
]

ORDLOOM_EVENTS = {
    "signup_enabled": False,
    "public_enabled": False,
    "per_minute": 20,
}
```

```python
from django.urls import include, path

urlpatterns += [
    path("members/", include("ordloom_members.urls")),
    path("events/", include("ordloom_events.urls")),
]
```

```bash
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check
```

为员工授予 `ordloom_events` 模型权限后，菜单出现「活动报名 → 活动概览」；搭建器「子应用」分类出现「活动入口」组件（显式公开，可放入分享的 H5 活动页，属性为标题、说明与门户路径）。

## 报名流程

- 活动按创建人隔离：普通员工只管理自己创建的活动及其报名，超级管理员可管理全部；状态按 草稿 → 报名中 → 已截止/已结束 流转，非法迁移在保存时拒绝。
- 会员在 `/events/` 门户查看报名中的活动并报名；会员身份完全复用会员应用会话，会员停用、会话到期或改密后即失去报名能力。
- `signup_enabled` 默认关闭；开启后报名、取消与重复报名（幂等恢复）经 CSRF 与共享缓存限速保护，名额校验在事务内完成，取消名额即时释放。
- `public_enabled` 默认关闭；开启后匿名可读报名中活动的最小目录（标题、时间、地点、剩余名额），不含报名名单。
- 每个报名记录生成唯一签到码，仅对本人与授权员工可见；员工在后台对报名记录执行「登记签到」，记录签到时间。

## 截止扫描任务

「报名截止扫描」任务自动关闭超过报名截止时间的报名中活动，并在开场前 24 小时内向活动创建人发送站内通知；关闭与提醒均按活动与时间去重，任务由宿主调度：

```bash
python manage.py ordloom_run_app_task ext:events.deadline --user 1 --apply --json
```

## 权限与边界

活动报名复用宿主 Django 权限、会员会话与站内通知中心；报名接口不接受匿名写入，也不自动注册会员。微信身份不会自动写入报名名单，如需会员绑定微信请另行安装 `ordloom-wechat`。活动不包含支付、购票或短信提醒。

本地验证（隔离源码宿主）：

```bash
python scripts/test_products.py --events-only
python scripts/test_products.py --email-user
```

安装验收与完整组合（含微信生态）见[生态开放指南](../development/ecosystem.md)。
