# 序衡 Ordloom 使用手册

Ordloom 1.2.0 是面向 Django 的管理工作台、可视化页面搭建和业务数据分析库。

本仓库公开维护产品手册、可运行示例和 VitePress 站点。

![Ordloom](docs/.gitbook/assets/ordloom-cover.svg)

- [阅读手册](docs/README.md)
- [安装与接入](docs/getting-started/installation.md)
- [运行完整示例](examples/quickstart/README.md)
- [32 种字段组件](docs/components/overview.md)
- [数据集与组件绑定](docs/data/datasets.md)
- [大屏与 H5](docs/guides/visual-pages.md)
- [1.2.0 CRM 与九应用生态](docs/releases/1.2.0.md)
- [1.1.0 SDK 与子应用生态](docs/releases/1.1.0.md)
- [1.0.2 稳定性更新说明](docs/releases/1.0.2.md)
- [公开通知恢复与读取调度](docs/guides/resilience-and-release-gates.md)
- [VitePress 文档结构](docs/publishing/structure.md)

## 文档版本

本手册对应 **Ordloom 1.2.0**。发行包、Python 模块和 Django 应用为 `ordloom`，设置为 `ORDLOOM_*`，字段/Admin 扩展点与管理命令为 `ordloom_*`。

使用 `pip install ordloom==1.2.0` 安装，或使用 `ordloom[graphql]==1.2.0` 启用可选数据层。完整步骤见 [接入说明](docs/getting-started/installation.md)，默认开关和运行边界见各模块指南。

## 本地检查

```bash
python scripts/check_docs.py
pip install -r examples/quickstart/requirements.txt
python examples/quickstart/manage.py test projects --noinput
```

VitePress 首页位于 `docs/README.md`，侧栏从 `docs/SUMMARY.md` 生成。运行 `npm run docs:build` 构建；发布步骤见文档结构与 GitHub Pages 指南。
