# ADR 0001：以 DSH 作为唯一 Agent Kernel

- 状态：Accepted
- 日期：2026-11-09

## 背景

我们需要会话、工具调用、子智能体、技能、沙箱、审批与 Web UI。自研一套通用 agent runtime 的成本远高于金融领域本身；同时，金融工作台又需要深度定制四栏 UI 与审批对象。

候选：

1. 自研 agent loop + UI。
2. 用 LangGraph/CrewAI 作为编排层，自建 UI。
3. 用 DSH 作为 kernel，领域层与 UI 作为插件/服务。

## 决策

选 **3**：DSH 是唯一的 agent loop；领域能力以 MCP/HTTP 工具接入；UI 以 DSH client plugin 起步，插槽不足时 fork Web 端（MIT）。

## 理由

- DSH 已具备会话、子智能体、技能、沙箱、工具审批、Web/headless。
- 一切皆插件，模型/工具/沙箱/UI 可替换，避免锁死。
- MIT，允许 fork 与商用。
- FinRobot V3 已转向 DSH，路线有外部验证。

## 后果

**正面**

- 不需要维护第二套状态机、工具权限、重试逻辑。
- 领域层可以独立测试、独立部署。

**负面**

- DSH 仍是 developer preview，升级可能破坏插件 API；需要锁版本与回归测试。
- 四栏布局可能需要 fork Web 端，带来上游合并成本。

## 不采用的方案

- **LangGraph/CrewAI 作为运行时**：会与 DSH 形成两套状态、两套权限、两套重试；只借其状态图/角色卡概念。
- **自研 agent loop**：重复造轮子，且难以在短期达到 DSH 的工具/沙箱完整度。

## 复核条件

- DSH 插件 API 无法承载四栏，且 fork 成本超过 4 周。
- DSH 出现无法绕过的许可/安全/合规问题。
