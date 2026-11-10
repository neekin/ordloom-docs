# Markdown 编辑器

`MDTextField` 保存 Markdown 原文，适合知识库、技术文档、协作说明。

```python
from ordloom.editor.fields import MDTextField

notes = MDTextField("协作文档", blank=True)
```

## 视图与格式

提供原文、预览、对照和全屏视图，支持标题、列表、链接、图片、代码、表格与任务列表。预览采用 GFM 解析与安全清理，不执行文档中的脚本。

解析在独立 Worker 中进行。失败或超时可以重试，原文录入不依赖预览成功。

## 保留原文

`MDTextField` 默认关闭原生表单的首尾空白裁剪，以保留代码缩进、行尾双空格和末尾换行。列表行内编辑与 CSV 导出也使用 Markdown 原文。

普通 `TextField` 可以通过外观配置使用 Markdown 编辑器：

```python
ordloom_fields = {
    "notes": {"type": "markdown", "rows": 14, "placeholder": "编写协作文档…"}
}
```

此时空白处理仍遵守该字段的实际 ModelForm；仅更换界面类型不会改变项目原有的 `strip` 规则。

## 图片与只读

图片复用字段和记录权限检查，限制可用 `max_upload_size_mb` 调整。上传位置随继续编辑而调整；原选区已经失效时，不把图片强行写入新内容。

只读默认呈现安全预览，也可查看原文复制。临时禁用后恢复编辑，会恢复之前使用的编辑视图。

部署 CSP 时允许同源 Worker。跨域静态托管还需要对应的 CORS、脚本来源与 `worker-src blob:` 配置，见[部署与升级](../development/deployment.md)。
