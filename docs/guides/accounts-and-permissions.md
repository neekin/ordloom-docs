# 账号与权限

## 登录账号

工作台使用 Django 原生认证与会话。登录字段来自 `AUTH_USER_MODEL.USERNAME_FIELD`，可以是用户名、邮箱或项目自己的工号字段；不要求用户模型一定存在 `username`。

账号需要启用并拥有后台访问资格。显示名称按用户模型提供的姓名、简称和登录标识取得，主键可以使用 UUID。

## 模型与对象权限

| 权限 | 界面表现 |
| --- | --- |
| 查看 | 列表与只读详情 |
| 新增 | 新增表单；没有查看权限时进入专门录入页 |
| 修改 | 编辑、允许的行内修改与相关写操作 |
| 删除 | 删除及符合权限规则的回收站操作 |

菜单不是权限边界。服务端仍会检查模型、对象、关联明细及当前请求的数据范围。

多租户项目应在自己的 Admin 中限制 queryset：

```python
def get_queryset(self, request):
    queryset = super().get_queryset(request)
    if request.user.is_superuser:
        return queryset
    return queryset.filter(workspace=request.user.workspace)
```

其中 `workspace` 是业务自定义字段，并非插件内置租户系统。自定义对象权限和回收站查询也应保留同样的数据边界。

## 用户管理与密码

原生 `UserAdmin` 新建表单、密码表单和 `AUTH_PASSWORD_VALIDATORS` 继续生效。用户密码显示设置状态，不回填编码密码，也不把它当作普通文本保存。

有权限的管理员可以在独立弹窗重置密码；资料草稿与密码弹窗分别处理。先重置密码再保存旧资料草稿，不会将密码覆盖回旧值。

自己的密码修改入口位于账号菜单；失败保留已输入的新密码供修正，成功后保持当前会话。停用自己的账号或移除后台资格后会返回登录页。

## 登录验证码

「账号菜单 → 系统设置」可以设置整个站点的图片验证码策略。超级管理员或拥有 `ordloom.change_siteconfig` 的账号可以修改；这不是单个用户的个人偏好。

验证码绑定会话、单次消费，默认 180 秒过期。登录失败或验证码刷新后需要使用新验证码。

支持 HttpOnly CSRF Cookie、会话保存 CSRF 与自定义 Cookie 名称。自建客户端应按照[API 数据契约](../reference/api.md)处理返回的令牌。

业务 API 密钥等字段请使用[业务凭据控件](../components/secrets.md)，不要混用用户密码重置流程。
