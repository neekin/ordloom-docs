# 第一个业务模块

以项目管理为例，完成「模型 → 注册 Admin → 列表与表单」的接入。

## 1. 定义模型

在 `projects/models.py` 中定义普通 Django 模型：

```python
from django.db import models

class Project(models.Model):
    name = models.CharField("项目名称", max_length=80)
    status = models.CharField(
        "状态", max_length=16,
        choices=[("draft", "草稿"), ("active", "进行中"), ("done", "已完成")],
        default="draft",
    )
    budget = models.DecimalField("预算", max_digits=14, decimal_places=2, default=0)
    description = models.TextField("说明", blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "项目"

    def __str__(self):
        return self.name
```

不必为了列表、数字输入或下拉选择更换字段基类。需要评分、地图、富文本等专用控件时，再使用[组件字段](../components/overview.md)。

## 2. 注册 Admin

在 `projects/admin.py` 中配置：

```python
from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["name", "status", "budget"]
    list_display_links = ["name"]
    list_editable = ["status"]
    search_fields = ["name", "description"]
    list_filter = ["status"]
    ordering = ["-id"]
    fieldsets = [
        ("基本信息", {"fields": ["name", "status", "budget"]}),
        ("补充说明", {"fields": ["description"]}),
    ]
    simpleui_antd_fields = {
        "name": {"placeholder": "例如：客户门户升级"},
        "budget": {"precision": 2},
        "description": {"rows": 5, "span": 2},
    }
```

这里的 `simpleui_antd_fields` 是现有字段外观配置入口；产品改名不要求修改已有配置键。

## 3. 迁移并打开页面

```bash
python manage.py makemigrations projects
python manage.py migrate
```

重新打开工作台后，菜单会按应用显示「项目」。可以新增记录、搜索名称、筛选状态、在列表修改状态，并打开编辑表单查看分组。

## 4. 为普通账号授权

在用户组或用户权限中分配 `projects` 应用下的项目查看、新增、修改、删除权限。仅新增权限的账号进入专门录入页，不会因此获得列表和详情访问权限。

项目原有的 `get_queryset()`、`has_view_permission()`、`has_change_permission()` 等规则继续执行。实际的数据范围设计见[账号与权限](../guides/accounts-and-permissions.md)。

需要可以立即运行的项目？继续阅读[完整示例](example.md)。
