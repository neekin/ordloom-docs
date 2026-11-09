# 运行完整示例

文档仓库附带一个完整 Django 示例，使用公开发行的插件安装，不依赖私有源码仓库。

## 启动

```bash
git clone https://github.com/neekin/ordloom-docs.git
cd ordloom-docs/examples/quickstart
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

Windows 使用 `.venv\Scripts\activate` 激活虚拟环境。然后访问 <http://127.0.0.1:8000/admin/>。

## 建议体验顺序

1. 在「团队」中新增产品、研发等团队。
2. 新建项目，填写预算，切换流程状态，把团队从待选区移到已选区。
3. 在资料分组中编辑富文本、Markdown 和 JSON，尝试格式化或切换预览。
4. 添加任务明细，再一次保存主表与明细。
5. 返回列表，体验筛选、搜索和行内状态修改。
6. 在顶栏切换主题、深色模式和信息密度。
7. 新建普通 Staff 账号，分配不同权限后检查其实际菜单和操作范围。

## 示例包含的文件

| 文件 | 作用 |
| --- | --- |
| `config/settings.py` | 应用、中间件、静态文件、媒体文件及品牌设置 |
| `config/urls.py` | 管理入口和本地媒体服务 |
| `projects/models.py` | 团队、项目及任务明细 |
| `projects/admin.py` | 列表、分组、穿梭框、编辑器及上传配置 |
| `projects/tests.py` | 验证菜单注册与文档字段实际保存 |

本地 SQLite、媒体目录和收集后的静态目录均已忽略，不会随文档提交。示例配置仅用于本地运行；生产环境按[部署指南](../development/deployment.md)设置密钥、数据库和资源服务。

## 检查示例

在示例目录运行：

```bash
python manage.py check
python manage.py test projects --noinput
```

[浏览示例代码](https://github.com/neekin/ordloom-docs/tree/main/examples/quickstart)。
