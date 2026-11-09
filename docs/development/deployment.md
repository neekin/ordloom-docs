# 部署与升级

## 普通 Django 部署

发行包已包含前端构建产物。安装或升级依赖后，在项目环境执行：

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

按项目原有流程重启应用服务，并检查 `/admin/api/health/`；如果挂载点不是 `/admin/`，相应调整地址。

1.0.3 相对前一版本没有新增数据库迁移，但首次安装和未来升级仍应按项目流程执行迁移检查。

## 静态资源

发布时同时部署入口和全部内容 hash 资源，不要只覆盖 `index.js`。工作台、列表、地图、编辑器及 Worker 都可能按需加载。

入口 HTML 使用重新验证缓存策略，固定入口通过版本参数区分；内容 hash 文件可以采用长期缓存。CDN、代理或对象存储配置应保留正确路径和 MIME 类型。

旧缓存导致界面仍是旧版本时，先确认服务端包版本、`collectstatic` 结果以及实际加载的资源路径。

## 媒体与存储

`MEDIA_URL` 与实际 storage URL 前缀应一致。生产文件由媒体服务、对象存储或项目网关提供；Django 示例中的 `static(settings.MEDIA_URL, ...)` 仅用于开发环境。

自定义 storage 应能通过 `storage.url("")` 或项目 `MEDIA_URL` 识别自身地址。跨域文件还要考虑浏览器图片、视频和下载所需的访问配置。

## CSP 与 Worker

Markdown 解析使用 Worker。同源静态部署应允许对应 Worker；跨域静态托管通常还需要静态服务 CORS、脚本来源和 `worker-src blob:`。

按自己部署域名编写精确来源规则。不要为了消除一个资源错误就全局关闭 CSP 或 CSRF。

## 修改前端源码后

在配套源码仓库中：

```bash
cd frontend
npm ci
npm run build
```

项目提供 `scripts/sync-dist.sh` 将构建产物同步到 Django 包。构建 Python 发行包前应先同步，并从干净的构建目录打包，避免旧的 hash 文件混入产物。

## 升级验证

验证登录、核心模型读取和保存、关联明细、上传、用户权限、密码策略、CSV 和懒加载编辑器。检查浏览器是否出现脚本、资源路径或 Worker 错误。

发行包兼容标识与当前品牌状态见[版本与兼容](../reference/compatibility.md)。
