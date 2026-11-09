# Architecture

> 状态：M0 草案。目标是先固定边界与契约，再逐层实现。

## 1. 目标与非目标

**目标**

- 一个以 DSH 为唯一 agent kernel 的金融研究工作台。
- 研究过程可追溯：每个数字有来源/计算 ID，每条假设有证据与审批记录。
- 报告可交付、可回退：HTML/PDF/PPTX/DOCX，版本与产物哈希可查。
- 人机协同：模式化工作台里完成对话、核准、文件管理与预览修改。

**非目标（当前阶段）**

- 不做通用 Agent 市场、计费、IM、移动端。
- 不做实时交易/下单；输出定位为研究辅助与内部决策支持。
- 不自研 agent loop、浏览器引擎、PDF 渲染器或 Git。

## 2. 三层架构

```text
┌──────────────────────────────────────────────────────────────────┐
│ L2 体验层   DSH Web Shell + 模式化工作台（左轨 / 画布 / Dock）      │
│             对话 │ 假设核准 │ 文件树 │ 预览与修改                  │
├──────────────────────────────────────────────────────────────────┤
│ L1 领域层   FastAPI：假设 / 证据 / 数据 / 计算 / 渲染 / 导出       │
│             MCP Gateway：行情、公告、财报解析、估值、图表          │
├──────────────────────────────────────────────────────────────────┤
│ L0 内核     DSH：agent loop / tools / subagents / skills / sandbox │
│             存储：Postgres + 对象存储 + Git                         │
└──────────────────────────────────────────────────────────────────┘
```

### L0：DSH 内核

- 负责会话、agent loop、子智能体、技能、工具审批、沙箱。
- 不承载金融业务状态；业务状态在 L1。
- 通过 MCP/HTTP 调领域工具，工具返回统一 `{ok, data, error, provenance}`。

### L1：领域层

按职责拆成六个服务（MVP 可以先在一个 FastAPI 进程内，按模块分目录）：

| 服务 | 职责 | MVP |
|---|---|---|
| Hypothesis | 假设对象、状态机、审计事件 | ✅ 本仓库已起步 |
| Evidence | 来源、快照、定位、引用 | 下一步 |
| Market Data | PIT 行情/财报/公告，快照与缓存 | 下一步 |
| Compute | DCF/WACC/可比/敏感性，确定性算子 | 下一步 |
| Artifact | 报告 DSL、版本 manifest、导出任务 | 下一步 |
| Approval | 审批队列、EvalGate、通知 | 下一步 |

### L2：体验层

「左轨 + 单主画布 + 可折叠 Dock」，React + `react-resizable-panels`：

| 区域 | 职责 | 数据源 |
|---|---|---|
| 模式轨 | 研究 / 行情 / 文件 / 报告 / 核准 / 看板 | 路由 + layout store |
| 主画布 | 当前模式的报告、K 线、审批详情或文件预览 | 各模式模块 |
| 左 Dock | 对话、文件树 | DSH session / Workspace API |
| 右 Dock | 假设证据、属性、审计时间线 | Hypothesis/Approval/Artifact |

详见 [design/ui-shell.md](design/ui-shell.md) 与 [ADR 0004](adr/0004-workbench-shell-over-four-panes.md)。

## 3. 关键流程

### 3.1 一次研究运行

```text
用户请求
  → DSH Lead 生成 research blueprint（问题/假设/数据需求/交付物）
  → 子智能体：Data → Valuation → Risk → Bull/Bear
  → 每个数字写入 provenance（source_id + compute_id）
  → 生成 hypothesis 列表（draft）
  → 进入审批队列
```

### 3.2 假设核准

```text
draft → submitted → under_review → approved / rejected / conditional
approved → frozen
rejected → draft（修订后重新提交）
```

- `submitted` 前必须至少有一条可证伪条件。
- `approved` 冻结当前 `artifact_version`，写审批事件。
- `conditional` 带约束条件（如「毛利率 > 18% 才生效」），由审批人填写。

### 3.3 报告生成与导出

```text
dossier.json + brand.json
  → Designer Agent 生成 report.json（块级结构）+ HTML
  → 左四预览 / 块级编辑 / 评论
  → 导出任务：PDF（Playwright）、PPTX（PptxGenJS）、DOCX（docx）
  → artifact manifest：git_commit + 文件哈希 + 模板版本
```

### 3.4 版本回退

- 每个 agent turn 结束：工作区 Git 快照。
- 每次人工保存：一次 commit。
- 每次导出：manifest 绑定 commit。
- 「大版本」：annotated tag，如 `v1.0-ic-approved`。
- 回退：从 tag 开新分支 + 恢复工作区，不 hard reset。

## 4. 数据契约

- `packages/contracts/hypothesis.schema.json`
- `packages/contracts/artifact-manifest.schema.json`

原则：

- 契约先于实现；前后端/Agent 共用同一份 schema。
- 金额单位「元」，比率小数，时间 UTC ISO 8601。
- 所有外部事实带 `source_id`、`as_of`；所有计算带 `compute_id`。

## 5. 安全与合规

- **工具权限按角色**：Data 只读、Valuation 无网络、Designer 无数据访问。
- **沙箱**：代码执行在独立 sandbox，`sources/` 只读，网络默认关闭。
- **审计**：假设状态变更、审批、导出、回退都写 append-only 日志。
- **数据**：不提交真实客户数据/未授权行情；商用数据源需持牌。
- **输出定位**：研究辅助，不构成个性化投资建议；保留免责声明与人工复核记录。

## 6. 待决问题

1. DSH 客户端插件能否承载「模式轨 + 主画布 + Dock」，还是必须 fork Web 端？
2. 多租户 SaaS 还是单机/团队私有部署？
3. 报告以 HTML 为源，还是以结构化块为源？（当前倾向：块为源，HTML 为渲染产物）
4. 审批持久化用 Postgres 状态机，还是 P1 引入 Temporal？
5. 数据源组合：OpenBB + AKShare + EDGAR 的商用条款与缓存策略。
