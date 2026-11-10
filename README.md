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

当前稳定发行版为 **ordloom 1.2.0**，安装使用 `pip install ordloom`。本版包含分享密码限速和后台任务运行诊断；Django 模块与配置键继续兼容。旧包环境按 [切换说明](docs/getting-started/installation.md#从旧发行包切换) 先卸载旧发行包，再安装新包。

发行页：[PyPI](https://pypi.org/project/ordloom/1.2.0/)；新增能力与默认开关见 [分享密码与任务诊断](docs/guides/sharing-and-task-diagnostics.md)。

## 本地检查

```bash
python scripts/check_docs.py
pip install -r examples/quickstart/requirements.txt
python examples/quickstart/manage.py test projects --noinput
```

GitBook 入口位于 `docs/README.md`，目录位于 `docs/SUMMARY.md`。仓库同时提供站点级与单空间 Git Sync 配置，详见同步指南。
