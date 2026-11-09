# 模型列表与业务操作

## 复用 ModelAdmin

| 原生配置 / 钩子 | 在工作台中的作用 |
| --- | --- |
| `list_display` / `get_list_display()` | 列表列与方法列 |
| `search_fields` / `get_search_results()` | 服务端搜索 |
| `list_filter` / `SimpleListFilter` | 筛选面板 |
| `ordering` / `get_ordering()` | 默认排序与允许的排序行为 |
| `list_editable` / `get_changelist_formset()` | 行内编辑表单与校验 |
| `get_queryset()` | 当前账号的数据范围 |
| `actions` / `get_actions()` | 批量业务操作 |

可以使用 `@admin.display` 声明方法列的说明、布尔呈现和排序字段。显示用 HTML 会经过界面内容策略处理，任意原生模板控件不一定自动转为前端组件。

## 列表交互

支持分页、每页条数、排序、搜索、组合筛选、列显示、密度、跨页选择和失败重试。筛选条件会显示为可移除的标签。日期筛选提供常见时间范围；具体项目筛选仍以 Admin 返回的元数据为准。

行内修改执行原生字段及跨字段校验，失败保留用户输入。金额和大整数不应先转换成 JavaScript 浮点数再提交。

## 业务 Action

普通 Action 可继续写在 ModelAdmin 中：

```python
from django.contrib import admin

@admin.action(description="标记为进行中", permissions=["change"])
def activate_projects(modeladmin, request, queryset):
    queryset.update(status="active")
    modeladmin.message_user(request, "已更新所选项目")
```

把函数加入对应 Admin 的 `actions`。接口会检查选中对象的范围与权限；一批记录中包含不可用或无权限对象时，不会静默只处理其中一部分。

| Action 返回类型 | 界面行为 |
| --- | --- |
| 普通完成 / Django 消息 | 显示执行结果并刷新数据 |
| HTML / TemplateResponse | 在弹窗中继续填写中间表单 |
| 附件响应 | 下载文件 |
| JSON | 展示结果 |
| 重定向 | 提供结果链接 |

原生 Action HTML 来自项目自身模板，应照常转义业务输入。数据库事务不会自动撤销发送邮件、外部请求或存储写入；业务可用 `transaction.on_commit()` 安排成功后的外部动作。

## CSV 导出

列表导出遵守当前查询范围；选中记录时按选择导出，否则按搜索与筛选结果导出。请求失败可以保留选择重试。只写凭据不会进入 CSV，可能被电子表格作为公式解释的文本会做防护处理。

删除与恢复流程见[工作台、日志与回收站](dashboard-and-logs.md)。
