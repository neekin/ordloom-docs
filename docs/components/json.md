# JSON 编辑器

普通 `models.JSONField` 自动使用 JSON 编辑控件，无需替换为自定义存储字段。

```python
from django.db import models

settings = models.JSONField("项目配置", default=dict, blank=True)
```

## 编辑能力

支持格式化、压缩、类型与行数提示、语法错误定位、撤销以及只读选择复制。`false`、`0`、`null`、数组和对象按实际 JSON 字段规则处理。

格式化只改变空白；它不负责替项目改变数据类型、字段校验或自定义 encoder/decoder。

## 大整数与精确来源

JSON 数字可能超出 JavaScript 的安全整数范围。例如：

```json
{
  "external_id": 9007199254740993,
  "enabled": false,
  "options": null
}
```

自定义编辑器应优先使用详情元数据的 `json_source`、列表的 `value_sources` 或行内保存响应的 `value_source`。不要先 `JSON.parse()` 再通过 JavaScript Number 重编码，否则大整数可能已经改变。

内置编辑器使用原生字段准备的文本，保留数值写法、键顺序和转义。保存仍交给原生字段及 ModelForm 解析和校验。

## 动态字段与错误

在 ModelForm 的 `__init__` 中添加的 JSON 字段也参与绑定、校验与保存钩子。原生默认值及其文本来源来自同一次求值，避免可调用默认值产生不一致的回填。

语法错误时先修正编辑器提示，再保存。服务端字段或跨字段错误仍会回到表单中；编辑器提示通过不代表业务规则一定通过。

只写凭据和密码不会出现在 JSON 文本来源中。
