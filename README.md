# Fin Agent Workbench

> 基于 [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) 的金融智能体工作台：把「研究 → 假设核准 → 报告生成 → 导出 → 回滚」放进一个四栏界面。

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-M0%20foundation-orange.svg)](docs/roadmap.md)
[![DSH](https://img.shields.io/badge/DeepSeek%20Harness-0.2%2B-4b6bfb.svg)](https://github.com/deepseek-ai/deepseek-harness)

> **Status: M0 — foundation.** 仓库正在搭建：协议、领域服务、架构文档先行，四栏 UI 与 DSH 插件随后接入。

---

## 为什么做这个

金融 Agent 的瓶颈通常不是「会不会聊天」，而是四件事：

1. **数字不可追溯**：模型写了一个目标价，却说不清用的是哪份财报、哪个公式、哪次计算。
2. **假设没有核准**：看多/看空逻辑埋在聊天记录里，没有人签字，也没法追责。
3. **报告不可回退**：改了三版之后，找不到「投委会通过的那一版」。
4. **工具权限失控**：浏览器、代码、数据接口全都交给一个 Agent，没有角色边界与审计。

Fin Agent Workbench 把这些问题当作一等对象：数字有 `source_id` / `compute_id`，假设有状态机与审批记录，报告有 Git 版本与 manifest，工具按角色授权。

---

## 它是什么

一个四栏的人机协同工作台：

```text
┌──────────────┬──────────────┬──────────────┬─────────────────────────┐
│  ① 对话       │  ② 假设核准   │  ③ 文件树     │  ④ 预览 / 修改           │
│              │              │              │                         │
│  研究请求     │  待审假设     │  sources/    │  报告预览               │
│  工具轨迹     │  证据正/反    │  analysis/   │  块级编辑               │
│  引用跳转     │  批准/驳回    │  deliverables│  版本对比 / 评论         │
└──────────────┴──────────────┴──────────────┴─────────────────────────┘
```

- **左一 · 对话**：与主分析智能体协作，工具调用、引用、子智能体状态可见。
- **左二 · 假设核准**：每条假设带证据、反证、可证伪条件、估值影响；人工批准后冻结版本。
- **左三 · 文件树**：`sources/`（只读原始件）、`analysis/`（底稿）、`deliverables/`（交付物）三根分区。
- **左四 · 预览/修改**：HTML/PPTX 预览、块级编辑、语义 diff、评论锚点，改动实时回流。

配套能力：一键导出 PDF/PPTX/DOCX、回合级版本回退、投研驾驶舱与运营看板。

---

## 架构

```text
┌──────────────────────────────────────────────────────────────────┐
│ L2 体验层   DSH Web Shell + 四栏工作台（React 插件 / fork）        │
├──────────────────────────────────────────────────────────────────┤
│ L1 领域层   FastAPI：假设 / 证据 / 数据 / 计算 / 渲染 / 导出       │
│              MCP Gateway：行情、公告、财报解析、估值、图表          │
├──────────────────────────────────────────────────────────────────┤
│ L0 内核     DSH：agent loop / tools / subagents / skills / sandbox │
│             存储：Postgres + 对象存储 + Git                         │
└──────────────────────────────────────────────────────────────────┘
```

**边界：**

- DSH 是唯一的 agent loop。领域层只提供工具与状态，不自己跑 agent。
- 所有数字由确定性代码计算，LLM 只负责解释与组织。
- 浏览器/代码/导出都通过受限工具槽执行，按角色授权并留审计。

更多设计见 [docs/architecture.md](docs/architecture.md)。

---

## 设计原则

1. **唯一编排器**：不在 DSH 之上再叠 LangGraph/CrewAI；审批用状态机，不用第二套 agent 框架。
2. **数字与叙事分离**：`compute_id` 可复算，`source_id` 可下钻；美工智能体没有数据权限。
3. **假设是一等对象**：`draft → submitted → under_review → approved/rejected → frozen`，每次变更写审计日志。
4. **回合即提交**：每个 agent turn 结束做一次 Git 快照；「大版本」= tag；回退开新分支，不 hard reset。
5. **许可优先**：默认 MIT / Apache-2.0；AGPL 与无 LICENSE 的组件不进闭源主链路。

---

## 仓库结构

```text
.
├── docs/
│   ├── architecture.md          # 三层架构与关键流程
│   ├── roadmap.md               # M0–M5 路线图
│   ├── adr/                     # 架构决策记录
│   └── research/                # 选型调研底稿
├── packages/
│   └── contracts/               # Hypothesis / Artifact JSON Schema
├── services/
│   └── domain/                  # FastAPI 领域服务（假设、审计）
├── .github/workflows/           # CI
├── CONTRIBUTING.md
└── LICENSE
```

后续会加入 `apps/workbench`（DSH 插件 / 四栏 UI）与 `infra/`（本地 compose）。

---

## 快速开始

### 领域服务

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e "services/domain[dev]"
uvicorn app.main:app --reload --app-dir services/domain
```

打开 <http://127.0.0.1:8000/docs> 查看 API。默认数据库 `services/domain/data/domain.db`，可用 `FINA_DB_PATH` 覆盖。

```bash
pytest services/domain/tests -q
```

### 契约

`packages/contracts/` 下的 JSON Schema 是前后端与 Agent 的共同契约，改字段先改 schema。

---

## 路线图

| 阶段 | 目标 |
|---|---|
| M0 | 仓库、架构、契约、假设领域 API |
| M1 | 四栏骨架、文件树懒加载、HTML 预览 |
| M2 | 假设核准 UI、EvalGate、审计时间线 |
| M3 | 数据网关、确定性估值、provenance |
| M4 | 报告 DSL、PDF/PPTX 导出、版本回退 |
| M5 | 投研驾驶舱、权限/合规、评测集 |

详见 [docs/roadmap.md](docs/roadmap.md)。

---

## 参与

- 先开 Issue 描述问题或需求，再开 `feat/<issue>-<slug>` 分支。
- 提交信息用 Conventional Commits：`feat(domain): add hypothesis transition API`。
- PR 必须通过 CI，并说明「改了什么、为什么、怎么验证」。
- 不提交密钥、真实客户数据或未授权的行情数据。

见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## License

[Apache-2.0](LICENSE)。第三方依赖与许可见 `THIRD_PARTY_NOTICES.md`（待补）。
