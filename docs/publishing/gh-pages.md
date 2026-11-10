# 自托管发布(VitePress + gh-pages)

除 GitBook 外,手册也可以自托管:由 VitePress 构建,发布到本仓库的 `gh-pages` 分支,地址为
<https://neekin.github.io/ordloom-docs/>。内容源仍是 `docs/` 目录与 `SUMMARY.md` 导航,
两套发布方式共享同一份 Markdown。

## 本地构建与发布

```bash
npm install
npm run docs:build          # 产物在 docs/.vitepress/dist
git checkout gh-pages
cp -R docs/.vitepress/dist/* .
git add -A && git commit -m "publish: 手册更新"
git push origin gh-pages
```

## 自动发布(可选)

仓库提供 GitHub Actions 工作流(推送 main 后自动构建并发布到 gh-pages):

```yaml
# .github/workflows/deploy-docs.yml
on:
  push:
    branches: [main]
```

> 推送工作流文件需要本地 Git 凭据具备 `workflow` scope;
> 可执行 `gh auth refresh -h github.com -s workflow` 授权后推送,或直接在 GitHub 网页端创建该文件。

侧边栏由 `docs/.vitepress/config.mjs` 在构建时从 `SUMMARY.md` 生成;新增页面时按 SUMMARY 约定
登记即可,两套发布方式的导航保持一致。
