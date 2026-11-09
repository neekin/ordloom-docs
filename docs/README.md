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

## 从这里开始

1. [安装并接管管理入口](getting-started/installation.md)。
2. [为一个业务模型配置列表和表单](getting-started/quickstart.md)。
3. [运行可直接体验的完整示例](getting-started/example.md)。
4. [浏览 32 种字段组件](components/overview.md)，再按需要接入编辑器、上传和关联选择。

## 版本与命名

手册描述 1.0.3 已发布能力与当前源码中的品牌调整。**Ordloom 是产品品牌**；安装包 `django-simpleui-antd`、模块 `simpleui_antd` 和现有配置前缀仍是兼容入口，请按文档中的实际命令安装。当前没有要求用户迁移数据库表名或修改已有权限代号。

新品牌界面的整理尚未重新发布到 PyPI，1.0.3 安装后的部分界面可能显示历史名称。设计探索图也不等同于已经交付的页面布局，详见[版本与兼容](reference/compatibility.md)和[设计方向](appendix/design.md)。
