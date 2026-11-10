# VitePress 文档结构

本仓库通过 VitePress 构建使用手册，发布到 GitHub Pages。产品源码的可见性继续由独立开发仓库管理。

## 目录约定

- `docs/README.md`：保留品牌首页布局，构建时映射为站点首页。
- `docs/SUMMARY.md`：章节导航，每个 Markdown 页面只列一次；VitePress 从中生成侧栏。
- `docs/.vitepress/config.mjs`：站点标题、首页映射、基础路径和搜索。
- `docs/.gitbook/assets/`：已有素材目录，路径保持有效。
- `docs/assets/`：新增使用截图。
- `docs/public/`：直接发布的站点图标等资源。
- `examples/quickstart/`：可运行示例，通过公开仓库链接从手册访问。

## 本地预览与检查

```bash
npm ci
python scripts/check_docs.py
npm run docs:dev
npm run docs:build
npm run docs:preview
```

重新构建后重启预览服务，使新产物和图片被正确加载。提交前检查链接、导航、代码示例和实际页面，保持首页品牌、Logo 及字体图标配置。

在线发布见 [GitHub Pages 部署](gh-pages.md)。
