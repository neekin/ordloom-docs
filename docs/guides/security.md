# 登录安全、恢复码与会话设备

管理接口使用 Django Session 与 CSRF。宿主自己的登录入口需要采用相应的 MFA 和会话策略。

## 登录验证码开关

### 登录连续失败锁定

同一账号 15 分钟内连续 5 次密码错误后,登录接口返回 429 并提示「账号已暂时锁定」,
锁定期间正确密码同样被拒绝;成功登录会重置计数。计数保存在共享 Django cache 中,
多实例部署一致生效;更换或清理 cache 后端会同时清除锁定状态。

拥有系统设置权限的账号：右上角用户菜单 →「系统设置」→ 打开「登录验证码」→ 保存。
它是整个站点的登录策略。默认超级管理员可修改，其他 Staff 账号需要显式授予
`ordloom.change_siteconfig`；普通账号不显示系统设置入口，接口也执行相同校验。

```python
from django.contrib.auth.models import Permission

permission = Permission.objects.get(
    content_type__app_label="ordloom", codename="change_siteconfig"
)
role.permissions.add(permission)  # role 是项目中负责站点管理的用户组
```

开启后登录接口校验会话绑定的单次图片验证码，默认 180 秒过期，可通过
`ORDLOOM_CAPTCHA_TIMEOUT` 设置秒数；刷新会替换旧验证码。
验证码加载失败可重试，登录失败保留账号输入，验证码也可以使用键盘刷新。

## 账号与密码

登录使用 Django 原生认证表单和 `AUTHENTICATION_BACKENDS`。输入名称、类型和长度来自
`AUTH_USER_MODEL.USERNAME_FIELD`，支持邮箱、工号等登录标识和 UUID 用户主键；
账号名称优先使用 `get_full_name()` / `get_short_name()`，其次使用 `get_username()`。
停用账号以及没有后台访问权限的账号无法进入工作台。

修改密码执行 `AUTH_PASSWORD_VALIDATORS`，界面展示项目的密码规则，并将错误定位到对应字段。
校验或请求失败保留输入，取消/完成后清理表单；修改成功保持当前会话，并按 Django 的会话机制
使其他会话失效。未设置本地密码的账号不显示本地密码修改入口。

请求层兼容 `CSRF_COOKIE_HTTPONLY`、`CSRF_USE_SESSIONS` 和自定义 `CSRF_COOKIE_NAME`，
登录后的 CSRF 令牌轮换也会同步到后续请求。登录配置、验证码和账号信息响应不缓存。

## TOTP 与登录网络范围

账号菜单的「安全设置」可扫码开启 TOTP；0018 后同时提供一次性恢复码，动态码或密码+恢复码可关闭，已启用时不能直接重新生成认证器密钥。
登录时密码与第二因素全部通过才清除失败计数；连续失败 5 次锁定 15 分钟。启用/关闭安全设置另有 5 次失败、5 分钟的限速。
TOTP 使用 SHA-1、6 位码、30 秒步长和前后各一步时钟容差；需要应用 `0011_usersecurity` 及后续迁移；恢复码和设备管理需 `0018_recovery_devices`。
可配置 `ORDLOOM_LOGIN_IP_ALLOWLIST = ['10.0.0.0/8', '192.168.1.5']` 限制登录，空列表不限制。
按 `REMOTE_ADDR` 判断，宿主反向代理应正确设置真实客户端地址；不会直接信任访问者提交的 X-Forwarded-For。

## 一次性恢复码与登录设备

```bash
python manage.py migrate
```

恢复码与设备管理属于核心 Django 能力，不要求 Strawberry/GraphQL、Channels 或外部密钥服务。

### TOTP 恢复码

「安全设置 → 两步验证与恢复码」首次开启 TOTP 后返回 10 份随机恢复码，每份 128 位随机量，完整内容只显示一次。
数据库只保存与账号绑定的 SHA-256 摘要及使用时间；摘要字段按原 `PasswordField` 规则只写，不会进入字段目录或安全状态响应。
旧的 TOTP 账号升级后不自动生成明文恢复码；使用当前密码和认证器动态码主动生成。

- 登录必须先通过账号密码与现有验证码/IP 策略，再提供 `totp` 或 `recovery_code` 之一；恢复码不能替代密码。
  成功登录时原子消耗一份，使用恢复码不会自动关闭 TOTP。连字符/空白分组和字母大小写可归一化，其他格式拒绝。
- 重新生成需要当前密码和动态码，或当前密码和另一份未使用恢复码；旧批次随事务失效。
  遗失认证器时可先用密码+恢复码登录，再用密码+另一份恢复码关闭旧 TOTP，随后重新扫码开启。
- 原有动态码关闭接口保持兼容；使用恢复码关闭必须同时提供密码，关闭后删除所有剩余码。
- 账号密码认证失败继续原限额；MFA 失败另按账号 PK 计数，用户名等价写法不能绕过连续 5 次/15 分钟锁定。
  设置和设备操作另有账号级 5 次/5 分钟重验证失败预算，多实例需要共享 cache。
- 安全变化、恢复码消耗、操作审计和可选站内通知共同提交，失败回滚；不记录明文密码、动态码、恢复码或认证器密钥。
  通知关闭时仍保留内容无关的 Django 操作记录。响应丢失后不能重新读取原批次，应在有验证方式时重新生成。
- 本地密码不可用的统一认证账号，敏感操作要求在宿主认证成功后的 5 分钟内进行，启用 TOTP 时仍需第二因素；超时请通过原身份服务重新登录。
  Ordloom 的 TOTP 登录验证适用于 `/api/login/`；宿主独立登录/SSO 入口应实施自己的 MFA 策略。

接口继续使用 staff Session 与 CSRF，均有 `no-store`：

| 路径 | 用途 |
| --- | --- |
| `GET /api/security/totp/` | 启用状态、剩余恢复码数、生成时间、设备开关；激活后不返回认证器密钥或恢复码 |
| `POST /api/security/totp/` | 原有 `provision/activate/disable`；新增 `regenerate`。开启或重置时一次返回 `recovery_codes` |
| `POST /api/login/` | 在原字段之外可提供 `recovery_code`，与 `totp` 互斥；恢复码不能重用 |

重置请求示例：`{"action":"regenerate","password":"当前密码","code":"六位动态码"}`；
恢复关闭示例：`{"action":"disable","password":"当前密码","recovery_code":"一份未使用恢复码"}`。
读接口与之后的响应只返回 `recovery_remaining`，不返回完整批次。勿把恢复码放在公开页面、组件配置或仓库中。
原则参考 [OWASP MFA 恢复建议](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html)。

### 可撤销会话设备

默认关闭，原 Session 行为保持不变。启用时将中间件放在 Session 和认证中间件之后：

```python
ORDLOOM_SESSION_DEVICES = {
    'enabled': True,
    'max_active': 20,       # 1–50，超过后退出最近最少活动的记录
    'max_records': 100,     # 1–500，且不少于 max_active；只保留最近这些会话记录
    'max_age_days': 14,     # 1–365，设备记录的固定最长有效期
    'touch_seconds': 60,    # 1–300，最近活动写入间隔
}
MIDDLEWARE = [
    # ...
    'django.contrib.sessions.middleware.SessionMiddleware',
    # CsrfViewMiddleware 等原配置保留
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'ordloom.middleware.SessionDevicesMiddleware',
    # ...
]
```

`ordloom_check --json` 校验配置和顺序。开启后，没有登记标识的旧会话需要重新登录，随后经 Django 认证成功信号登记；
原生 Django/SSO 成功登录也可登记 staff 会话。关闭配置不强制退出现有 Session。

- 「安全设置 → 登录设备」只显示本人的记录，超级管理员也不跨账号查看或退出设备。
  提供登录/活动/有效期、粗略浏览器系统标签、IPv4 `/24` 或 IPv6 `/64` 网段；不保存完整 User-Agent、IP 或 Session key。
  `REMOTE_ADDR` 为实际连接来源，不直接信任任意转发头；代理部署由宿主设置可信来源。
- 每次登录对应一个会话记录，并不识别真实硬件。最近活动不是实时在线，浏览器关闭或 Session 本身过期可能早于记录有效期。
  记录有效期固定为登录时 Session 有效期与 `max_age_days` 较短者，不随自动续期延长，重新认证可创建新记录。
- 退出指定其他设备，需要当前密码；若有 TOTP，还需动态码或一次性恢复码。当前设备使用原「退出登录」。
  「退出其他设备」会同时轮换当前 Cookie/登记标识，保留当前登录，阻止旧 Cookie 副本继续复用。
- 改密、TOTP 开关和恢复码重置会退出其他已登记会话并轮换当前会话。所有 HTTP 路由经过中间件复核，
  已有事件 WebSocket/GraphQL 订阅在下一次事件/签名权限复核时停止转发；不强制中断已通过检查的在途请求，也不立即关闭空闲 socket。
- 不依赖物理删除 Django Session 行，因此签名 Cookie、数据库、缓存和文件等 Session 后端均使用服务端登记状态判断。
  签名 Cookie 本身不能靠客户端退出实现服务端撤销，背景见 [Django Cookie Session 说明](https://docs.djangoproject.com/en/5.2/topics/http/sessions/#using-cookie-based-sessions)。
- 历史记录达到上限时清理最旧记录，缺失或已撤销标识始终要求重新认证；活跃会话达到上限时先退出最少活动的会话。
  元数据数据库不可用时不继续授权。使用凭据的外部数据服务和匿名公开授权独立管理，不受此 Session 开关替代。

设备接口（仍需本人的 Session/CSRF）：

| 路径 | 用途 |
| --- | --- |
| `GET /api/security/devices/?page=1` | 每页 20 条本人的会话记录、当前标记、状态及脱敏网络信息 |
| `POST /api/security/devices/<公开UUID>/` | 重验证后退出指定其他会话 |
| `POST /api/security/devices/` | `{"action":"revoke_others","password":"…","code":"…"}` 退出其他设备；`recovery_code` 可替代 `code` |

隔离验收：构建前端后使用 `scripts/dev_fields.py --security --notifications --production --port=8660`，
再在 `frontend` 运行 `npm run test:security-recovery`。验证只修改临时数据库中的演示账号，结束时关闭其 TOTP，真实浏览器和独立 HTTP 客户端分别验证登录与撤销。
