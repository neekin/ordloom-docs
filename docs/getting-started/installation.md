# 安装与接入

## 环境

插件声明支持 Python 3.9 及以上、Django 4.2 及以上。Python 与 Django 本身也需要兼容；本手册的可运行示例使用 Python 3.10+ 与 Django 5.2。

发行包内置已构建的前端资源，常规安装不需要 Node.js。需要修改前端组件时再准备源码构建环境。

```bash
pip install ordloom==1.0.1
```

发行包包含前端产物。Django 注册和 Python 导入均为 `ordloom`。

可选 GraphQL 数据层需要 Python 3.10+、Django 5.2+：

```bash
pip install 'ordloom[graphql]==1.0.1'
```

先使用核心模型管理，按业务需要再启用数据集、协作和外部集成；可选配置见 [配置参考](../reference/settings.md)。

## 注册应用

在现有 Django 项目中保留 Admin 所需应用和中间件，并增加插件应用：

```python
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "ordloom",
    "projects",
]
```

会话、认证、消息与 CSRF 中间件应正常启用；模板配置应包含 Django Admin 的标准 context processors。[完整示例配置](https://github.com/neekin/ordloom-docs/blob/main/examples/quickstart/config/settings.py)可直接参考。

## 挂载入口

插件入口写在原生 Admin 之前：

```python
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", include("ordloom.urls")),
    path("admin/", admin.site.urls),
]
```

默认接管该挂载点下的管理界面路径。若希望未匹配的业务页面回退原生 Admin，配置 `ORDLOOM_FULL_TAKEOVER = False`。

也可以将插件挂到 `/console/`，原生 Admin 留在 `/admin/`。页面会根据挂载位置生成 API 前缀。

## 初始化并登录

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

访问 `/admin/`。普通登录账号需要处于启用状态并拥有后台访问资格；菜单内容还取决于各模型权限。

插件自身迁移建立布局、页面、数据集及其他功能表，不会把你的业务模型迁移到另一套 ORM。

下一步：[创建第一个业务模块](quickstart.md)。生产静态文件与媒体文件配置见[部署与升级](../development/deployment.md)。
