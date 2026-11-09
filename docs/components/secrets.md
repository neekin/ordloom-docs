# 业务凭据

业务访问密钥、回调 Token 等使用 `PasswordField`，或在实际表单中使用只写密码控件。

```python
from simpleui_antd.components import fields

api_key = fields.PasswordField("访问密钥", max_length=160, blank=True)
```

已有凭据不通过详情、列表、CSV 或 JSON 文本来源回填；界面只显示设置状态。

## 三种保存意图

| 操作 | 提交含义 |
| --- | --- |
| 留空 | 保留现有凭据 |
| 输入新内容 | 替换现有凭据 |
| 点击明确清除 | 以 JSON `null` 表示清除；保存前可以撤销 |

必填和只读规则仍生效。可选字段才提供适当的清除入口，保留操作不会再次清洗或重写已有值。

自定义控件可读取元数据中的 `preserve_blank`、`secret_set`、`secret_can_clear`。列表行内编辑还应使用各记录自己的 `editor_meta`，不能把某条记录的设置状态复用于全部记录。

## 存储与用户密码的区别

`PasswordField` 仍遵守项目的 CharField 存储与保存钩子，**它本身不提供数据库加密**。需要加密存储时，由项目字段、存储层或业务保存逻辑实现。

用户账号密码应由原生 UserAdmin 和 Django 密码哈希机制管理，不应替换成业务凭据字段。对应操作见[账号与权限](../guides/accounts-and-permissions.md)。
