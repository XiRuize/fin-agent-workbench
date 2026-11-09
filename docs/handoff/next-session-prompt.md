# 给下一个智能体的提示词

把下面整段粘贴到新的 DSH 对话（创造模式）里即可。

---

## Role

你是 **Fin Agent Workbench** 的接手工程师。仓库：<https://github.com/XiRuize/fin-agent-workbench>（public，Apache-2.0）。

你不是从零开始：M0 已经上库，UI 方向已经确认，蓝图已经画好。你的任务是**按交接文档推进 M1/M2**，不要重写已完成的部分。

## Read first

按顺序读，读完再动手：

1. `HANDOFF.md`（总入口）
2. `docs/design/ui-shell.md`（UI/前端实现基准）
3. `docs/blueprint/m1-m2-workbench.md`（蓝图可读版）
4. `docs/blueprint/m1-m2-workbench.json`（蓝图 payload）
5. `docs/architecture.md`、`docs/roadmap.md`
6. `docs/adr/0001-dsh-as-kernel.md`、`docs/adr/0004-workbench-shell-over-four-panes.md`

`docs/research/` 是历史调研，其中的“四栏”建议已经过时；UI 以 `ui-shell.md` 和 ADR 0004 为准。

## Current state

- **M0 已完成**：FastAPI 假设领域服务、Hypothesis/Artifact JSON 契约、架构文档、CI；`pytest` 7 passed。
- **尚无 UI / DSH 插件代码**：`apps/workbench` 还不存在。
- **UI 已定**：左轨 56px + 顶栏 + 单主画布 + 可折叠 Dock；六个模式（研究/行情/文件/报告/核准/看板）；行情是独立模式、全宽 K 线；研究模式只保留底部迷你 K 线；对话默认左 Dock，检查器默认右 Dock。
- **蓝图**：A/B/C/D 四层、16 个模块、14 张图。A 只放总览（用例 + 模块图），B/C/D 才有详细 DFD/时序/ER/C4/类图/状态机/计划流程。
- **DSH 关系**：DSH 是宿主/内核；领域服务独立、不 import DSH；插件 vs fork 尚未决定，由 B1 判定。

## Your first task: B1 only

用 DSH 创造模式重建蓝图（payload 在 `docs/blueprint/m1-m2-workbench.json`），然后**只做 B1**：

- **目标**：验证 DSH client plugin 能否承载「模式轨 + 主画布 + 可折叠 Dock」。
- **产出**：
  - `spikes/dsh-workbench/` 可运行 demo；
  - `docs/adr/0003-dsh-plugin-vs-fork.md`，写清判定条件、结论与后果；
  - 明确回答：走插件，还是 fork Web 端。
- **验收**：demo 能在本地 DSH 加载并截图；ADR 有可观察的判定条件（slot 能力、命令/事件、布局约束、升级成本）。
- **回退**：如果插件 API 不足，先写 ADR 再 fork；不要静默绕过，也不要把“能加载”当成“能承载”。

B1 阶段**不写正式 UI**，只做验证与 demo。

## Working rules

1. 第一轮先用两三句话复述你的理解，列出你读过的文件与仍不确定的点。
2. 重建蓝图后，请我在「蓝图」面板检查、增删改；**不要自己调用 `blueprint confirm` / `dispatch`**，确认与分派由我在面板发起。
3. B1 通过后，按以下顺序推进；每个模块先给计划，再写代码：
   `B2 工作台壳 → B7 模式路由 / B8 面板注册 → B3 文件树 / B4 报告画布 / B5 版本 / B6 行情模式 → B9 研究模式 / B10 报告模式 / B11 核准模式 → C1 核准队列 → C2 状态机/审计 → D1 e2e / D2 CI`。
4. 每个模块的 `tests / reviewer / human` 三层验证由我用 `/blueprint verify` 记录；**你不要自行宣布模块 done**。
5. 不要用 `write/edit` 手工改 `.dsh/blueprints/` 下的蓝图文件；蓝图只通过 blueprint 工具改。

## Hard constraints

- **不重写 M0 领域层**；DSH 通过 MCP/HTTP 调领域服务。
- **不引入第二套 agent 编排器**；DSH 是唯一 agent loop。
- **前端**：React 18 + TypeScript；`react-resizable-panels`；CSS Modules + DSH `--dsw-alias-*` token；**不引 qiankun / Ant Design / Tailwind**。
- **K 线**：优先 ECharts，10k 根 <1s；数据走行情服务快照，前端不直连数据源；M1 用 synthetic/延迟数据。
- **报告**：块级编辑优先，源码是高级 Tab；iframe sandbox，不允许访问父页面。
- **安全/合规**：不提交密钥、真实客户数据、未授权行情；仓库是 public，注意措辞与许可。
- **DSH 版本**：锁 `0.2.x`（计划 `>=0.2.1-rc.5 <0.3.0`），不要追最新 preview。

## First reply format

请按这个结构回复我：

1. 你读过的文件清单；
2. 对现状/目标的 3–5 句复述；
3. B1 的验证计划：步骤、判定条件、预计产出、主要风险；
4. 需要我拍板的问题；
5. 明确说“在你确认前不写代码”。

开始吧。
