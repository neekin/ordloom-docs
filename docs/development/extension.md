# 扩展字段组件

前端扩展需要使用配套源码构建。字段渲染器注册在应用启动模块或其导入的注册文件中。

## 注册组件

在 `src/bootstrap.jsx` 或独立注册模块中：

```jsx
import { InputNumber } from 'antd'
import { registerField } from './components/widgets.jsx'

registerField('currency', function Currency({ field, modelKey, ...control }) {
  return <InputNumber {...control} stringMode precision={field.precision ?? 2}
    style={{ width: '100%' }} />
})
```

`Form.Item` 会提供 `value`、`onChange`、`id` 等受控属性。包装组件需要将这些属性传给实际输入，避免界面变化但表单没有取得值。

后端选择该类型：

```python
ordloom_fields = {
    "budget": {"type": "currency", "precision": 2}
}
```

`type` 只选择交互，不替代后端字段或 ModelForm 的清理规则。

## 控件契约

- 接受并回显服务端传入的值，变更时调用 `onChange`。
- 尊重 `disabled`、只读元数据和表单 `id`，转发表单相关无障碍属性。
- 提交可 JSON 序列化且符合字段语义的值；精确数字应使用字符串。
- 外部回填、重置、切换记录时清理旧的临时状态。
- 不把未完成的上传或旧记录响应写入新草稿。

## 异步任务与上下文

`useFieldPending(pending)` 可把上传等异步工作报告给表单，让保存等待完成。`useFieldScope()` 提供主记录、inline 和明细行上下文，传给 `api.fieldOptions` 或 `api.upload` 的第四个参数。

不要绕过已有客户端另建一个不传上下文的上传入口。只读、动态字段和对象权限都可能因当前记录而不同。

## 主题与构建

使用主题变量与 AntD token，避免写死白底、深色文字。产品品牌文案集中于 `src/brand.js`，不应散布到每个组件。

`src/main.jsx` 保持轻量的版本化入口；React、业务上下文及组件在带内容 hash 的启动模块加载。将注册逻辑放进启动模块，有助于保持懒加载模块使用同一个 React 与 Form 上下文。
