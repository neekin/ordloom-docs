# 接入 GitBook

本公开仓库可以独立连接 GitBook，产品源码的可见性由原开发仓库继续管理。

## 推荐：站点级 Git Sync

1. 在 GitBook 中创建文档站点并连接 GitHub。
2. 选择 `neekin/ordloom-docs`、`main` 分支，Project directory 使用仓库根目录。
3. 采用仓库中的 `gitbook-docs.yaml`，将手册空间映射到 `./docs`。
4. 首次同步选择以 GitHub 的手册内容为导入来源，确认导航后再发布站点。

站点配置的 `ordloom-handbook` 是稳定空间 key。已有站点调整标题或 URL 时，不要随意改动该 key。

## 单空间同步

根目录 `.gitbook.yaml` 指向 `./docs/`。如果界面要求直接映射空间目录，则选择 `docs`，使用其中的 `.gitbook.yaml`。

不要将 `docs` 同时当作映射目录、又重复设置为其下的内容 root；否则路径会错误地变成 `docs/docs`。

## 内容约定

- `docs/README.md`：手册首页。
- `docs/SUMMARY.md`：导航，每个 Markdown 页面只出现一次。
- `docs/.gitbook/assets/`：文档图片。
- `examples/quickstart/`：可运行示例，通过公开 GitHub 链接从手册访问。

修改后先运行 `python scripts/check_docs.py`，涉及示例时再执行示例测试，随后提交并推送。连接 Git Sync 后即可同步；本仓库没有预先绑定或伪造一个 GitBook 空间 ID。

首次连接的账号授权与最终站点地址由 GitBook 账号侧完成。

配置依据：[GitBook 官方 Content configuration](https://gitbook.com/docs/docs-as-code/git-sync/content-configuration)。
