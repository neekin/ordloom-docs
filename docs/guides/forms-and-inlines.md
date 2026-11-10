# 表单与关联明细

## 主表单

表单复用实际 ModelForm，包括 `get_form()`、实例化时动态字段、关联 queryset、字段清理与跨字段校验。保存沿用 `save_form()`、`save_model()` 和 `save_related()`。

用 `fieldsets` 组织信息；有两个或更多分组时可切换滚动与分步查看。分步切换保留已填写内容，失败后定位到具体字段。

```python
fieldsets = [
    ("基本信息", {"fields": ["name", "budget", "status"]}),
    ("内容资料", {"fields": ["body", "attachment"]}),
]
ordloom_fields = {
    "name": {"placeholder": "请输入项目名称"},
    "body": {"rows": 12},
    "attachment": {"accept": ".pdf,.txt", "max_upload_size_mb": 20},
}
```

## 普通关联明细

```python
from django.contrib import admin
from .models import Project, Task

class TaskInline(admin.TabularInline):
    model = Task
    extra = 0

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    inlines = [TaskInline]
```

子模型不需要单独注册到 Admin。明细可复用文件、时间、JSON、多选和内容编辑器，权限、关联查询和上传沿父记录与 inline 上下文处理。

主表与明细在同一次保存中提交。全部表单及 FormSet 校验通过后，才执行数据库保存与审计钩子；校验失败保留输入并提示具体明细行。

## 原生 FormSet 能力

支持跨行 `clean()`、唯一性校验、数量上下限、`get_formset_kwargs()`、`get_formsets_with_inlines()`、动态只读规则和 `save_formset()`。

如果启用 FormSet 的 `can_order`，界面提供上移、下移，项目可以在保存钩子中读取 `ordered_forms` 并写入自己的顺序字段。不要仅开启排序就假设某个业务字段会自动持久化。

## 通用关联明细

使用 `GenericTabularInline` 或 `GenericStackedInline`，并配置模型实际使用的 `ct_field` 与 `ct_fk_field`。需要模型本身正确声明 GenericForeignKey；控件不会替你建立通用关联模型。

查询按内容类型和所属主记录共同隔离，内部关联字段不作为普通可编辑字段暴露。

## 只读与草稿

服务端保护使用 `readonly_fields` 或 ModelForm 字段的 `disabled=True`。仅设置外观选项 `disabled` 不等同于服务端权限规则。

退出时比较实际草稿：改回原值、撤销或增删新明细后恢复初始状态，不会继续误报未保存修改。不同明细组独立跟踪；文件上传尚未完成时仍会保护关闭与保存操作。

`Ctrl/Cmd+Enter` 可保存当前表单。嵌套密码弹窗会独立处理快捷键，避免同时提交背后的资料表单。
