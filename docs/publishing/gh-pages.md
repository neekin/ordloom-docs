# 发布 VitePress 手册

手册由 VitePress 构建，站点地址为 [Ordloom Docs](https://neekin.github.io/ordloom-docs/)。源内容位于 `docs/`，侧栏从 `SUMMARY.md` 生成；首页品牌、Logo、图标与样式保留在 VitePress 配置和主题中。

## 构建与预览

```bash
npm ci
python scripts/check_docs.py
npm run docs:build
npm run docs:preview
```

站点基础路径为 `/ordloom-docs/`。重新构建后重启预览进程，验证首页、导航、图片和版本链接。

## 发布分支

将构建目录 `docs/.vitepress/dist/` 发布到本仓库 `gh-pages` 分支。使用独立临时 worktree 或 CI checkout，保留该分支现有历史，避免在源工程切换分支覆盖未提交文档；产物包含 `.nojekyll`。

在 GitHub Pages 设置中选择 `gh-pages` 的根目录。仓库当前没有自动构建工作流；推送源文档并不会自动更新站点，需要显式提交构建产物。也可由维护者配置 CI，但应在仓库中真实落地后再描述为已自动发布。

新增页面需同步 `docs/SUMMARY.md` 并通过检查。完整目录约定见 [VitePress 文档结构](structure.md)。
