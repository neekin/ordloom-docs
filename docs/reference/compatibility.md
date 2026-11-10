# 环境、命名与能力边界

## 运行环境

| 项目 | 要求 |
| --- | --- |
| 发行包 | `ordloom==1.0.1` |
| 核心 | Python 3.9+、Django 4.2+，版本组合须满足 Django 自身要求 |
| 可选数据层 | `ordloom[graphql]==1.0.1`，Python 3.10+、Django 5.2+ |
| 安装产物 | 包含已构建前端；普通接入不需要 Node.js |
| 多进程限速/观测 | Web 与任务进程使用同一原子共享缓存 |
| 跨进程推送 | 配置 ASGI、Channels 和共享 channel layer |

## 接入命名

| 接入项 | 名称 |
| --- | --- |
| Python / Django 应用 | `ordloom` |
| URL | `include('ordloom.urls')` |
| Django 设置 | `ORDLOOM_*` |
| 字段外观 | `ordloom_fields` |
| 模型字段 | `ordloom.components.fields` / `ordloom.editor.fields` |
| 管理命令 | `ordloom_*` |
| 模板与静态资源 | `ordloom/` |
| 迁移应用标签 | `ordloom` |
| 应用表 | `ordloom_*` |
| 有效权限前缀 | `ordloom.<codename>` |

## 验证范围

发布检查包含后端 API 与权限、前端单元/DOM、PostgreSQL、Redis 跨进程、原生浏览器及新 wheel 安装。
隔离安装检查实际导入、迁移、表、ContentType、权限、collectstatic 和管理路由；文档检查导航、链接及代码示例语法。
这些检查不等同任意宿主插件、生产容量、真机安装或长期大屏运行均已验收。

## 能力边界

- 模型和字段权限始终由 Django 及宿主规则执行，界面隐藏不代替授权。
- GraphQL 字段显式白名单；SQL 权限范围适配需要宿主提供等价规则，不自动翻译任意 Python 策略。
- SQLite 与 PostgreSQL 的精确数值表现不同，详见 [字段与精度](../data/field-types.md)。
- 地图提供经纬度取点，不提供 POI 搜索；外部图片、视频和默认瓦片依赖相应服务。
- 上传独立于数据库事务，取消编辑不会自动删除已上传文件。
- 离线业务快照采用导出副本语义，无法离线复核或撤回权限，不自动同步。
- 维护命令由宿主调度，诊断缓存不提供实时进程心跳；在线代码执行和云函数不属于本版能力。
