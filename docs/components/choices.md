# 选择与关联字段

## 单选与分段选择

普通带 `choices` 的字段会按实际类型生成选择控件。使用专用字段可明确选择交互：

```python
from ordloom.components import fields

status = fields.RadioField(
    max_length=16, choices=[("draft", "草稿"), ("done", "完成")], default="draft"
)
stage = fields.SegmentedField(
    max_length=16, choices=[("draft", "草稿"), ("active", "进行中")], default="draft"
)
```

这些字段保存实际选项值，不保存显示名称。

## 多选与穿梭框

`ManyToManyField` 使用标识数组；`TransferField` 是多对多字段的穿梭选择外观。示例中的 `Team` 是项目模型：

```python
teams = fields.TransferField(
    Team, blank=True, titles=["可选团队", "协作团队"], filterable=True
)
```

关联查询复用实际 ModelForm 的 queryset，支持搜索、分页与大量已选标签回填。不要在前端自行拼接一个绕过服务端数据范围的候选集合。

`CheckboxField` 基于 CharField，以逗号分隔字符串存储；它与多对多字段的数组契约不同。选项值本身应避免使用逗号。

## 树与层级路径

```python
REGIONS = [
    ("east", "华东", None),
    ("hangzhou", "杭州", "east"),
    ("shanghai", "上海", "east"),
]
organization = fields.TreeSelectField(max_length=32, choices=REGIONS, default="east")
region = fields.CascaderField(max_length=64, choices=REGIONS, default="east/hangzhou")
```

树选择保存节点值，例如 `hangzhou`；级联选择保存完整路径，例如 `east/hangzhou`。三元组中的第三项是父节点值，根节点使用 `None`。

## 自动补全与原生权限选择

`AutoCompleteField` 使用候选项帮助填写文本。原生 `FilteredSelectMultiple`，例如 UserAdmin 的权限选择，会使用穿梭框；权限搜索支持代号、模型与应用名称。

大整数和字符主键应按接口返回的原值传递，不要转换为 JavaScript 浮点数。自建客户端可用 `ids_json` 传递包含逗号、斜杠等字符的标识数组。
