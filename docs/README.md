# 序衡 Ordloom

为 Django 项目提供清晰、统一的业务管理空间。

Ordloom 基于 React 19 与 Ant Design 6，读取已注册的 `ModelAdmin`，把模型、权限、表单和业务操作呈现在一个工作台中。后端继续执行 Django 的 queryset、ModelForm、FormSet 和保存钩子。

## 可以用它做什么

| 场景 | 使用的能力 |
| --- | --- |
| 项目、客户、订单管理 | 搜索、筛选、分页、行内编辑、批量操作 |
| 主从业务录入 | fieldsets、普通/通用关联明细、整体校验与事务保存 |
| 内容与知识库 | 富文本、Markdown、图片、文件、JSON |
| 组织与账号管理 | 原生 UserAdmin、项目密码策略、自定义登录字段、权限感知界面 |
| 不同品牌的后台 | 主题、明暗模式、站点名称、Logo、密度及工作台布局 |
| 页面公开分享与运维 | 分享密码失败限速、超级管理员只读任务运行诊断 |
| 业务数据分析 | 模型字段目录、GraphQL 筛选聚合、数据集发布版本、报表与看板 |
| 大屏与移动页面 | 拖拽搭建、ECharts/AntV、滚动动画、组件数据绑定与轮播 |
| 问卷与线索收集 | 12 类题目、提交校验、答卷快照、CSV/Excel 与汇总 |
| 团队和系统集成 | 工作区、组织目录、所有权、通知、Webhook、只读服务与离线快照 |

## 从这里开始

1. [安装并接管管理入口](getting-started/installation.md)。
2. [为一个业务模型配置列表和表单](getting-started/quickstart.md)。
3. [运行可直接体验的完整示例](getting-started/example.md)。
4. [浏览 32 种字段组件](components/overview.md)，再按需要接入编辑器、上传和关联选择。
5. [开放模型数据](data/graphql.md)，在 [数据集工作室](data/datasets.md) 保存查询并绑定组件。
6. [搭建大屏与 H5](guides/visual-pages.md)，或使用 [报表与看板](data/reports.md) 分析业务数据。
7. 按部署需要启用 [协作](guides/collaboration.md)、[变更通知与只读服务](data/events-and-services.md)、[离线](guides/offline.md) 和 [维护命令](development/commands.md)。

## 版本与接入

本手册对应 **Ordloom 1.0.0**。发行包和模块为 `ordloom`，可选数据层为 `ordloom[graphql]`；表使用 `ordloom_*`，迁移应用标签和权限前缀为 `ordloom`，设置为 `ORDLOOM_*`，管理命令为 `ordloom_*`。

完整能力清单、默认开关及部署边界见 [发布说明](releases/1.0.0.md)、[配置参考](reference/settings.md) 和 [环境要求](reference/compatibility.md)。
