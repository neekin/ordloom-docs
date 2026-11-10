# 序衡 Ordloom 使用手册

Ordloom 是面向 Django Admin 的业务工作台插件，提供统一外观、模型管理、复杂表单、关联明细和内容编辑能力。

本仓库公开维护产品手册、可运行示例和 GitBook 配置。

![Ordloom](docs/.gitbook/assets/ordloom-cover.svg)

- [阅读手册](docs/README.md)
- [安装与接入](docs/getting-started/installation.md)
- [运行完整示例](examples/quickstart/README.md)
- [32 种字段组件](docs/components/overview.md)
- [GitBook 同步方式](docs/publishing/gitbook.md)

## 文档版本

本分支手册对应 **Ordloom 2.0.0 开发版，尚未发布**。发行包、Python 模块、Django 应用、配置、管理命令、表名及权限标签已统一命名；按全新库接入，不提供旧名称兼容层或历史库升级工具。

当前开发版请使用本地源码或 wheel，安装步骤见 [接入说明](docs/getting-started/installation.md)。分享限速与任务诊断的默认开关见 [指南](docs/guides/sharing-and-task-diagnostics.md)。

## 本地检查

```bash
python scripts/check_docs.py
pip install -r examples/quickstart/requirements.txt
python examples/quickstart/manage.py test projects --noinput
```

GitBook 入口位于 `docs/README.md`，目录位于 `docs/SUMMARY.md`。仓库同时提供站点级与单空间 Git Sync 配置，详见同步指南。
