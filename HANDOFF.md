# Handoff — Fin Agent Workbench

> 交接时间：2026-11-09  
> 用途：新对话（DSH 创造模式）接手本项目的唯一入口。先读这份，再读蓝图与 UI 规范。

---

## 0. 30 秒读懂

- **项目**：基于 DeepSeek Harness（DSH）的金融智能体工作台，做「研究 → 假设核准 → 报告 → 导出 → 回滚」的闭环。
- **当前阶段**：M0 已完成；M1/M2 已规划，**还没有开始写 UI 代码**。
- **下一步**：B1 的 3 天 spike，决定「DSH 插件」还是「fork Web 端」。
- **核心决策**：DSH 是宿主/内核；领域服务独立；UI 用「左轨 + 单画布 + 可折叠 Dock」，不再固定四栏。
- **仓库**：<https://github.com/XiRuize/fin-agent-workbench>（public，Apache-2.0）。

---

## 1. 仓库与当前状态

| 项 | 值 |
|---|---|
| 仓库 | `XiRuize/fin-agent-workbench`，public |
| 默认分支 | `main` |
| 最新提交 | `bc6a46e feat(m0): add architecture, contracts and hypothesis domain API` |
| 版本 tag | `v0.1.0-m0` |
| CI | 通过：<https://github.com/XiRuize/fin-agent-workbench/actions/runs/42573739006> |
| 领域服务测试 | `pytest services/domain/tests -q` → 7 passed |
| 本地克隆 | `<workspace>/fin-agent-workbench`（已在本机 clone） |

### M0 已有什么

- `README.md`：项目定位、模式化工作台、架构、路线图。
- `docs/architecture.md`：三层架构、六个领域服务、关键流程。
- `docs/roadmap.md`：M0–M5 里程碑。
- `docs/adr/0001`、`0002`（superseded）、`0004`：DSH 作为唯一 Kernel、四栏（已废弃）、工作台壳。
- `docs/research/`：63 个项目调研 + Nuwax 专项分析。
- `packages/contracts/`：Hypothesis、Artifact Manifest JSON Schema。
- `services/domain/`：FastAPI 假设领域服务（创建/查询/状态流转/审计事件）+ 7 个测试。
- `.github/workflows/ci.yml`：契约校验 + pytest。

### 还没有什么

- **没有任何 DSH 插件代码**，也没有 `apps/workbench`。
- 没有前端构建、没有 K 线、没有模式切换、没有审批 UI。
- 没有真实行情数据；M1 用合成/延迟数据。

---

## 2. 产品目标与非目标

**目标**

- 研究过程可追溯：每个数字有 `source_id` / `compute_id`。
- 假设是一等对象：`draft → submitted → under_review → approved / rejected / conditional → frozen`。
- 报告可交付、可回退：HTML/PDF/PPTX/DOCX，版本与产物哈希可查。
- 人机协同：模式切换 + 可折叠 Dock，而不是四个固定栏。

**非目标（当前）**

- 实时交易/下单/持仓。
- 通用 Agent 市场、计费、订阅、IM、移动端。
- 自研 agent loop、浏览器引擎、PDF 渲染器、Git。
- 多人实时协同（CRDT 放到 M5 之后）。

---

## 3. DSH 与本项目的关系

```text
fin-agent-workbench
├── apps/workbench      → 依赖 DSH 插件 API（宿主）
├── services/domain     → 不依赖 DSH，独立 FastAPI
└── packages/contracts  → 纯 JSON Schema，不依赖 DSH
```

- **DSH 是运行时宿主/内核**：会话、agent loop、子智能体、技能、沙箱、工具审批。
- **领域层不 import DSH**；DSH 通过 MCP/HTTP 调领域服务。
- **DSH session 不是业务事实源**；假设、证据、审批、artifact 版本在领域层与 Git。
- 插件兼容范围计划：`dsh >=0.2.1-rc.5 <0.3.0`；不追最新 preview。
- 插件 vs fork 由 B1 决定；ADR 0003 记录结论。

---

## 4. 已确认的 UI / 前端设计

> 完整规范：[docs/design/ui-shell.md](docs/design/ui-shell.md)

**一句话：左轨 56px + 顶栏 + 单主画布 + 可折叠 Dock + 状态栏。**

```text
┌────┬──────────────────────────────────────────────┬─────────────┐
│ 模 │ 顶栏：标的 / as-of / 搜索 / 助手 / 布局 / 导出   │  右 Dock     │
│ 式 ├──────────────────────────────────────────────┤  280–360px   │
│ 轨 │              主画布（按模式切换）                │  可折叠      │
│ 56 │                                              │             │
├────┴──────────────────────────────────────────────┴─────────────┤
│ 状态栏：数据新鲜度 · 模型 · token · 保存状态 · 版本                │
└──────────────────────────────────────────────────────────────────┘
```

**六个模式**：研究、行情、文件、报告、核准、看板（M1 先做前四个，文件复用研究组件，看板 M5 占位）。

| 模式 | 左 | 主画布 | 右 | 底 |
|---|---|---|---|---|
| 研究 | 文件树 240 + 对话 320 | 报告画布 | 假设/证据 280 | 迷你 K 线 160 |
| 行情 | 自选 220 | 全宽 K 线 + 成交量 + 指标 | 标的详情 280 | 指标切换 |
| 文件 | 文件树 280 | 预览/编辑 | 元数据 260 | — |
| 报告 | 大纲 200 | 块级预览/编辑 | 属性/评论 280 | 页面胶片条 |
| 核准 | 队列 300 | 假设详情 | 审计时间线 280 | 审批操作栏 |
| 看板 | 过滤器 200 | 指标网格（M5） | — | — |

**关键交互**

- `1–6` 切模式；`⌘J` 对话 Dock；`⌘B` 左面板；`⌘I` 右检查器；`F` Focus；`Esc` 退出。
- 折叠不卸载组件；布局按 `workspace + mode` 持久化。
- 深链：`#/research/:id`、`#/market/:symbol`、`#/report/:id?tab=preview`。
- K 线：ECharts，优先 10k 根 <1s；数据走行情服务，前端不直连数据源。

**前端约束**

- React 18 + TypeScript；`react-resizable-panels`；CSS Modules + DSH `--dsw-alias-*` token。
- **不引 Ant Design / Tailwind / qiankun**；模块边界用 `React.lazy` + panel registry。
- 参考 `dsh-media-desk` 的左轨/Studio/折叠逻辑；参考 Nuwax 的 panel registry / DesignViewer / 审批面板。

---

## 5. 蓝图（M1/M2）

> 完整可读版：[docs/blueprint/m1-m2-workbench.md](docs/blueprint/m1-m2-workbench.md)  
> 机器可读 payload：[docs/blueprint/m1-m2-workbench.json](docs/blueprint/m1-m2-workbench.json)

- 标题：**M1/M2 工作台壳、模式切换与假设核准闭环**
- 7 个需求栏目：目标 7、功能 15、非功能 8、约束 10、验收 8、风险 8、角色 5。
- 4 层：A 总览、B 工作台壳与模式（M1）、C 核准模式（M2）、D 验证与交付。
- 9 张图：用例、数据流、模块依赖、时序、ER、C4、类图、状态机、实施计划。
- **16 个模块**，依赖顺序：

```text
B1 DSH spike
  → B2 工作台壳
  → B7 模式路由 / B8 面板注册
  → B3 文件树 / B4 报告画布 / B5 版本 / B6 行情模式
  → B9 研究模式 / B10 报告模式 / B11 核准模式
  → C1 核准队列 → C2 状态机/审计
  → D1 e2e / D2 CI
```

### 模块表（简版）

| 编号 | 模块 | 依赖 |
|---|---|---|
| A1 | 工作台总控 | — |
| B1 | DSH 承载能力 spike | — |
| B2 | 工作台壳（左轨 + 顶栏 + Dock） | B1 |
| B7 | 模式路由与快捷键 | B2 |
| B8 | 面板注册与布局持久化 | B2 |
| B3 | 文件树面板 | B2 |
| B4 | 报告画布 | B2、B3 |
| B5 | Git 快照与回退面板 | B2 |
| B6 | 行情模式（全宽 K 线） | B7、B8 |
| B9 | 研究模式 | B7、B8、B3、B4 |
| B10 | 报告模式 | B7、B8、B4 |
| B11 | 核准模式 | B7、B8、C1 |
| C1 | 假设核准队列 | B2 |
| C2 | 状态机与审计时间线 | C1 |
| D1 | e2e 验收与性能基线 | B2/B7/B8/B3/B4/B5/B6/B9/B10/B11/C1/C2 |
| D2 | CI/构建/文档 | B2、B7 |

**验证规则**：模块的 `tests / reviewer / human` 三层只能由用户执行 `/blueprint verify` 记录；任一层 failed → `needs-rework`；三层 passed → `done`。不要让子代理自行宣称完成。

---

## 6. 研究结论（选型依据）

| 来源 | 借什么 | 不借什么 |
|---|---|---|
| **DSH** | 内核、会话、子智能体、技能、沙箱、插件系统 | 不把它当业务数据库 |
| **FinRobot** | 确定性计算 + 溯源 + 报告结构；V3 已转 DSH | 桌面端绑定 macOS、美股数据源 |
| **Nuwax** | Agent Computer 沙箱、ACP、MCP Gateway、会话状态机、DesignViewer、审批面板 | Java 全家桶、qiankun、全 Agent OS 范围 |
| **dsh-media-desk** | 左轨 + 单画布 + 可折叠 Dock、Studio 分栏、窄屏自动收起、DSH token | 环境光斑/重动效、自媒体业务模型 |

详细调研：[docs/research/oss-landscape.md](docs/research/oss-landscape.md)、[docs/research/nuwax-borrowings.md](docs/research/nuwax-borrowings.md)。

---

## 7. 新对话第一步（SOP）

1. **读三份文件**：`HANDOFF.md`（本文件）、`docs/design/ui-shell.md`、`docs/blueprint/m1-m2-workbench.md`。
2. **重建蓝图**：用 DSH 创造模式，读取 `docs/blueprint/m1-m2-workbench.json`，调用 `blueprint(action="create")`；不要手工改蓝图文件。
3. **只做 B1**：3 天 spike，回答「client plugin 能否承载模式轨 + 主画布 + Dock」；产出 `docs/adr/0003-dsh-plugin-vs-fork.md` 与可运行 demo。
4. **等用户确认蓝图**：用户在「蓝图」面板点「确认并分派」；不要自己调用 `confirm` / `dispatch`。
5. **按依赖分派**：B2/B7/B8 先行；B3/B4/B5/B6/B9/B10/B11 在文件边界不冲突时并行；C1/C2 随核准模式推进。
6. **验收**：每个模块跑测试、写证据；三层验证由用户 `/blueprint verify` 记录。

### 可直接粘贴给新对话的提示词

```text
你接手 Fin Agent Workbench。先读 HANDOFF.md、docs/design/ui-shell.md、docs/blueprint/m1-m2-workbench.md。

这是 M0 已完成的仓库：FastAPI 假设领域服务 + 契约 + 文档 + CI，尚无 UI。
请用 DSH 创造模式重建 M1/M2 蓝图（payload 在 docs/blueprint/m1-m2-workbench.json），
然后只做 B1：验证 DSH client plugin 能否承载「左轨 + 单主画布 + 可折叠 Dock」，
产出可运行 demo 与 docs/adr/0003-dsh-plugin-vs-fork.md。

不要先写 UI；不要自己调用 blueprint confirm/dispatch；不要引入 qiankun/AntD/Tailwind。
确认蓝图与 B1 结论后，再按 B2 → B7/B8 → 各模式模块的顺序推进。
```

---

## 8. 风险与开放问题

| 风险/问题 | 处理 |
|---|---|
| DSH 仍是 developer preview | 锁 `0.2.x`；B1 先验证；插件 API 不足则 fork |
| 仓库已 public | 不要提交密钥、客户数据、未授权行情；调研文档已公开，注意措辞 |
| K 线数据授权 | M1 用 synthetic/延迟数据；真实数据接持牌源 |
| 审批语义 | 「修改后批准」与「有条件批准」是否拆开，待 M2 产品确认 |
| 模式切换状态丢失 | `layoutStore` + keepMounted + 深链；D1 专门测 |
| 窄屏 Dock 层叠 | <1024 单 Dock 抽屉；<768 单列 |
| 报告块级编辑范围 | M1 只做 text/chart/table；表格先只读 |
| ADR 0002 已被取代 | 已记录 ADR 0004「工作台壳替代固定四栏」，0002 标记 superseded |

---

## 9. 文件索引

| 文件 | 用途 |
|---|---|
| [README.md](README.md) | 项目介绍（部分 UI 描述待更新） |
| [docs/architecture.md](docs/architecture.md) | 三层架构与关键流程 |
| [docs/roadmap.md](docs/roadmap.md) | M0–M5 路线图 |
| [docs/design/ui-shell.md](docs/design/ui-shell.md) | UI/前端实现基准 |
| [docs/blueprint/m1-m2-workbench.md](docs/blueprint/m1-m2-workbench.md) | 蓝图可读版 |
| [docs/blueprint/m1-m2-workbench.json](docs/blueprint/m1-m2-workbench.json) | 蓝图 payload |
| [docs/adr/](docs/adr/) | 架构决策记录 |
| [docs/research/](docs/research/) | 选型调研 |
| [services/domain/](services/domain/) | 假设领域服务 |
| [packages/contracts/](packages/contracts/) | JSON Schema |
| [scripts/export_blueprint.py](scripts/export_blueprint.py) | 导出蓝图 JSON/Markdown |

---

## 10. 一句话交接

**M0 已上库，UI 方案已定，蓝图已画好；新对话从 B1 spike 开始，不要重写领域层，不要回到固定四栏。**
