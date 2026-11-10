# 工作台、日志与回收站

## 个人工作台

工作台展示业务统计、图表、快捷入口与最近操作。点击「自定义工作台」可以排序、调整宽度、隐藏卡片，并保存为当前账号的布局。

取消编辑恢复已经读取的布局；布局加载失败时先重试读取，再进行修改，避免覆盖尚未加载的个人偏好。

统计与趋势使用当前请求可访问的模型 queryset。`ORDLOOM_ANALYSIS = False` 可关闭统计类卡片，`ORDLOOM_HOME_INFO = False` 可隐藏服务器信息。

## 操作记录

日志页支持分页、操作者、动作、关键词筛选与模型跳转。默认展示当前账号业务范围中仍能访问的对象，包括可访问的回收站记录。

对象永久删除后，原始 Django `LogEntry` 可能仍保留，但默认业务范围不会继续展示该对象名称。如果业务必须保留归档审计，可在 Admin 中实现 `get_log_queryset(request)`，返回已经按组织、租户和查看权限过滤的日志查询。

## 启用软删除

模型包含 `deleted_at`，或兼容的 `deleted` 字段时可以启用回收站；不要求继承插件模型基类。

```python
from django.db import models

class Document(models.Model):
    name = models.CharField(max_length=80)
    deleted_at = models.DateTimeField(null=True, blank=True)
```

默认删除写入删除时间，列表和导出排除已删除记录。`ModelAdmin.ordloom_soft_delete = False` 可以显式关闭这项识别。

## 恢复与永久删除

回收站支持搜索、分页、选择恢复、选择永久删除和清空。恢复检查修改权限，永久删除检查删除权限；永久删除前展示关联影响及保护情况。

清空作用于该账号可访问的整个回收站，不只作用于当前页或当前搜索结果。存在受保护关联时不会部分清空。

如果默认 manager 隐藏已删除记录，应提供保留业务范围的回收站查询：

```python
def get_trash_queryset(self, request):
    return Document.all_objects.filter(workspace=request.user.workspace)
```

`all_objects` 与 `workspace` 均由项目自行实现。软删除与恢复可通过 `soft_delete_model(request, obj)`、`restore_model(request, obj)` 自定义；硬删除沿用原生删除钩子。
