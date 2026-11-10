# 配置参考

以下为 2.0.0 开发版读取的配置名称，统一使用 `ORDLOOM_*`，无旧名称别名。

## 分享与后台任务（1.2.0）

| 设置 | 默认 / 行为 |
| --- | --- |
| `ORDLOOM_SHARE_LIMITS` | 默认开启；300 秒内同来源/资源 10 次、同来源跨资源 100 次失败预算 |
| `ORDLOOM_TASK_DIAGNOSTICS` | 默认关闭；启用后超级管理员只读查看安全执行元数据与队列汇总 |

完整配置、共享缓存要求和保留边界见 [分享密码与任务诊断](../guides/sharing-and-task-diagnostics.md)。

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
