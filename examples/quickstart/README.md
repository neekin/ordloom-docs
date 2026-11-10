# 可运行的 Ordloom 接入示例

本分支示例面向尚未发布的 `ordloom==2.0.0`，请先安装当前开发源码或本地 wheel。示例展示团队、项目、预算、状态、富文本、Markdown、JSON、附件以及任务明细；Django 应用名为 `ordloom`。

使用 Python 3.10 或更新版本；以下命令在本目录执行。

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Windows 激活环境时使用 `.venv\Scripts\activate`。

打开 <http://127.0.0.1:8000/admin/>，使用自己创建的管理员账号登录。先新增团队，再创建项目；编辑项目时可以添加任务明细和上传文件。

示例只用于本地体验：SQLite、上传文件与收集后的静态文件都在当前目录内，并已加入忽略规则。示例的 `DEBUG` 与本地开发密钥不应直接用于生产部署。

运行接入检查：

```bash
python manage.py check
python manage.py test projects --noinput
```

文档使用新产品品牌，公开包的部分固定文字仍可能显示历史名称；这不影响本例的模型、表单和权限接入。
