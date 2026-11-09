# Roadmap

> 以「能跑通一条投研链路」为目标，不做大而全的 Agent OS。

## 里程碑

| 阶段 | 目标 | 关键交付 | 验收 |
|---|---|---|---|
| **M0** 基础 | 固定边界与契约 | README、架构、ADR、JSON contracts、假设领域 API、CI | `pytest` 通过；README 可读 |
| **M1** 四栏骨架 | 看见工作台 | DSH 插件/fork、四栏布局、文件树懒加载、HTML 预览 | 1440px 下四栏可用；树 1k 文件不卡 |
| **M2** 核准闭环 | 假设可签字 | 审批队列、状态机 UI、EvalGate、审计时间线 | 一条假设走完 draft→frozen |
| **M3** 领域层 | 数字可追溯 | 数据网关（OpenBB/AKShare/EDGAR）、DuckDB 快照、DCF/可比、provenance | 每个数字可下钻到 source/compute |
| **M4** 报告与导出 | 可交付 | 报告 DSL、块级编辑、PDF/PPTX/DOCX、artifact manifest、版本回退 | 一键导出；回退 1 分钟内 |
| **M5** 硬化 | 可运营 | 投研驾驶舱、权限/审计、评测集、部署 | 20 家公司 golden set；合规清单 |

## M0（当前）

- [x] 仓库、Apache-2.0、README
- [x] 架构与路线图
- [x] Hypothesis / Artifact 契约
- [x] 假设领域 API（SQLite + FastAPI）
- [x] CI（pytest）
- [ ] 第一个 DSH 插件 spike（M1 前置）

## M1 任务拆解

1. 3 天 spike：DSH client plugin 能否全屏接管；不行则 fork Web 端。
2. 四栏布局：`react-resizable-panels`，宽度 24/20/18/38，可折叠。
3. 文件树：按目录单层加载 + 虚拟滚动 + 面包屑 + 搜索。
4. 预览：iframe sandbox + `report.json` 渲染器（先支持 text/chart/table）。
5. Git 快照：每轮 agent 结束 commit，UI 显示最近 20 个版本。

## M2 任务拆解

1. 审批队列卡片：证据正/反、可证伪条件、估值影响、置信度。
2. 状态机 UI：批准 / 修改后批准 / 驳回（原因码）。
3. EvalGate：证据充分性、数字可追溯、合规、逻辑一致性四类 validator。
4. 审计时间线：谁、何时、从什么状态到什么状态、依据哪些证据。
5. 审批后冻结 artifact 版本。

## 非目标（本阶段不做）

- 实时交易、下单、持仓管理。
- 通用 Agent 市场、计费、订阅、IM、移动端。
- 自研可视化 DAG 工作流编辑器（用 `blueprint-studio` 的结构化蓝图）。
- 多人实时协同（CRDT 放到 M5 之后）。

## 指标

| 指标 | 目标 |
|---|---|
| 数字可追溯率 | 100% |
| 引用覆盖率 | ≥ 95% |
| 报告一次通过率 | ≥ 70% |
| 审批平均时长 | < 30 分钟 |
| 导出成功率 | ≥ 99% |
| 回退恢复时间 | < 1 分钟 |
