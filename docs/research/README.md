# Research Notes

> 内部调研底稿，用于选型与架构决策，不代表最终实现。

| 文档 | 内容 |
|---|---|
| [oss-landscape.md](oss-landscape.md) | 63 个开源项目的分模块调研：规划、信源、文件树、主智能体、报告、UI、导出、版本、看板 |
| [nuwax-borrowings.md](nuwax-borrowings.md) | Nuwax 及生态仓库的专项借鉴：Agent Computer、ACP、MCP Gateway、会话状态机、审批节点、DesignViewer |

> **2026-11-09 更新**：UI 已从「固定四栏」改为「左轨 + 主画布 + 可折叠 Dock」，见 [design/ui-shell.md](../design/ui-shell.md) 与 [ADR 0004](../adr/0004-workbench-shell-over-four-panes.md)。本目录中的四栏建议是历史调研，不再作为实现依据。

引用原则：

- 只借架构与交互模式，不复制与项目许可不兼容的代码。
- 调研中的 Star/许可数据有时效性，引入前重新核对。
- 结论与当前 [architecture.md](../architecture.md) 冲突时，以 architecture 为准，并更新 ADR。
