# 金融智能体工作台 · 开源项目调研与选型（v0.1）

> 调研时间：2026-11-09　范围：GitHub 开源项目 + DeepSeek Harness（DSH）插件生态
> 方法：逐个核对仓库元数据与 LICENSE 原文；Star 仅作热度参考，不构成质量结论。
> 结论口径：**能直接复用** > **可借设计** > **仅作对标**。每项只给一个亮点、一个缺点。

---

## 0. 结论先行

1. **不要从零搓通用 Agent 运行时。** DSH 就是那个"可自托管的 Claude 式平台"：MIT、Web + headless、一切皆插件（模型／工具／沙箱／会话存储／UI／agent loop 都可换），子智能体、技能、审批、MCP 都是现成的。你们要自研的是**垂直工作台**，不是 harness。
2. **这条路线已经被验证。** FinRobot 的 V3 明确写着"DeepSeek-Harness, in development"；V2 用 PydanticAI + FastAPI + React/Tauri 做桌面投研工作台。说明"DSH 内核 + 金融领域层 + 专用 UI"是成立的产品形态。
3. **你们不是从零开始。** 工作区里的 `blueprint-studio` 已经是"规划蓝图 + 版本历史 + 人工确认 + 子智能体派发"的 DSH 插件；`finfraud-radar` 已经有"时点数据 + 证据链 + 确定性规则 + 回测"。这两个项目就是本方案的地基，下一步是**金融化、四栏化、可导出、可回退**。
4. **编排器只能有一个。** 不要再把 LangGraph／CrewAI／AutoGen 作为运行时叠在 DSH 上；三套状态机会导致工具权限、重试、审批、回滚全部对不齐。它们只提供设计模式，不提供第二套内核。
5. **先过许可关。** AGPL（Firecrawl、Metabase、Skyvern）与无 LICENSE 的仓库（Anthropic Skills 整仓、部分社区插件）不要进闭源主链路；MIT／Apache-2.0 优先。

**一句话选型：DSH 做内核，`blueprint-studio` 做规划与版本骨架，FastAPI 领域层做数据/计算/证据，React 四栏做工作台，HTML→PDF/PPTX 做交付。**

---

## 1. 目标架构

```
┌──────────────────────────────────────────────────────────────────┐
│ L2 体验层：DSH Web Shell + 四栏工作台（React 插件 / fork）         │
│  左一 对话 │ 左二 假设核准 │ 左三 文件树 │ 左四 预览与修改          │
├──────────────────────────────────────────────────────────────────┤
│ L1 金融领域层：Python FastAPI sidecar（或 Node 插件 + MCP）        │
│  数据网关 │ 确定性计算 │ 证据库 │ 审批状态机 │ 渲染导出 │ 看板查询  │
├──────────────────────────────────────────────────────────────────┤
│ L0 内核：DSH（agent loop / tools / subagents / skills / sandbox）  │
│  存储：Postgres（元数据）+ S3/MinIO（大文件）+ Git（版本）          │
└──────────────────────────────────────────────────────────────────┘
```

### 九模块 → 自研／复用

| 模块 | 建议 | 自研的部分 | 复用的部分 |
|---|---|---|---|
| 任务规划蓝图 | 扩展 `blueprint-studio` | 金融研究 schema、检查规则、派发模板 | 版本历史、语义 diff、确认后派发子智能体 |
| 浏览器与爬虫 | 三件套组合 | 站点适配、快照留证、合规白名单 | Playwright、Crawl4AI、Docling |
| 分级文件树 | 虚拟工作区 | 三根分区、元数据、权限、检索 | react-arborist／dsh-file-explorer、OpenDAL |
| 主智能体 | DSH 原生 | 角色卡、工具槽、预算、审计 | DSH 子智能体、沙箱、MCP |
| 报告美工 | 结构化块 + HTML | 模板体系、品牌、自检清单 | Anthropic 文档 Skills、ECharts、PptxGenJS |
| 四栏 UI | DSH 插件／fork | 四栏交互、审批卡、评论锚点 | blueprint-studio 全屏 Studio、CopilotKit 模式 |
| 一键导出 | 渲染服务 | 模板版本、任务队列、字体包 | Playwright／Gotenberg、docx、PptxGenJS |
| 大版本回退 | 回合即提交 | 时间线 UI、里程碑、审计 | Git／isomorphic-git、blueprint 版本归档 |
| 数据看板 | 双轨 | 投研驾驶舱指标与布局 | DuckDB-WASM、ECharts、Superset |

---

## 2. 先盘点你们已经有的（不要重复造）

| 已有项目 | 已经解决的事 | 可直接复用的部分 | 缺口 |
|---|---|---|---|
| `blueprint-studio`（Apache-2.0，v0.4.4） | 一句话→需求列／八类图／人工编辑／版本历史／语义 diff／一键恢复／确认后按模块派发子智能体 | `normalize` + 稳定 ID 合并、版本归档、语义 diff、`session.prompt` 派发、全屏 Studio 的 Host/Client 两半架构 | 软件工程语义，不是金融研究；蓝图按 session 存，不是工作区级；没有四栏 |
| `finfraud-radar`（Apache-2.0） | A 股财报舞弊：PIT 时点、证据链、确定性规则、回测、风险面板 | `Signal → Evidence → Finding → Report` 契约、快照 schema、确定性评分、零依赖 Node 实现 | 只做舞弊；合成样本；不产出研报／不收口审批 |
| `dsh-book-reader`（MIT） | 本地 PDF／DOCX／EPUB 解析、书架与阅读面板、本地优先 | PDF 对象表／ToUnicode 解析、侧栏面板、本地存储与安全边界 | 阅读器，不是分析工作区 |
| `dsh-bookweave`（MIT） | 侧栏阅读工作区、摘录、论点-证据卡片、IndexedDB 本地优先 | "结论在上、理由在下"的论证链卡片、选区批注、章节分析交互 | 面向书籍，不是投研假设 |

**结论：`blueprint-studio` 的"规划 + 版本 + 人工确认 + 派发"就是本工作台的中枢。建议 fork 成 `research-blueprint`，把七列改成：研究问题／核心假设／证据（正/反）／估值影响／催化剂／风险／合规；把八类图换成：逻辑链、估值桥、情景树、时间线、对比矩阵。**

---

## 3. 分模块项目清单

### M0 底座：DSH 与插件生态

> 选型结论：DSH 直接做内核；社区插件只选 MIT／Apache 且自己读过代码的。四栏布局若官方插槽不够，fork Web 端（MIT 允许）。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [DSH](https://github.com/deepseek-ai/deepseek-harness)（MIT） | 开源 agent harness | 一切皆插件，模型/工具/沙箱/UI/agent loop 均可替换，Web + headless 双形态 | developer preview，破坏性变更频繁；插件拥有本机权限，安全边界弱 | 唯一 agent 内核；用 skills 承载分析师 playbook |
| [awesome-dsh-plugin](https://github.com/LingHXiao/awesome-dsh-plugin)（索引） | 插件目录 | 近万条插件条目按 UI／文档／工作流／Git 分类，能快速找到现成件 | 收录≠审计，大量单人项目，维护与许可参差 | 先逛"UI Enhancements / Docs & Rendering / Workflow"三节 |
| [dsh-coding-workspace](https://github.com/Aealen/dsh-coding-workspace)（许可待核） | 编码工作台 | 停靠面板、分屏编辑器、diff、git worktree，最接近四栏骨架 | 面向代码，不含审批/假设语义；改造要读源码 | 只借布局与 diff 交互，不整包引入 |
| [dsh-task-monitor](https://github.com/3450892121/dsh-task-monitor)（许可待核） | 右栏监控 | 聚合 git 状态、后台任务、skills、MCP、artifacts、访问页面 | 只读监控不能编辑；信息密度过高 | 做"运行状态"浮层，不占主栏 |
| [DeptAI-UI-DSH](https://github.com/01men/DeptAI-UI-DSH)（许可待核） | 协作前台 | 部门看板 + 工单 + 审批，把"人签字"搬进面板 | 通用工单模型，缺金融证据/估值绑定；早期项目 | 借"审批队列 + 状态流转"的交互 |
| [dsh-preset-deep](https://github.com/anticbv/dsh-preset-deep)（许可待核） | 研究预设 | 强制每个计划给出至少两条可证伪证据，并给事实打来源标签 | 纯 prompt 约束，无结构化状态，模型可绕过 | 把"可证伪"写进假设 schema 与校验器 |
| [dsh-gungnir](https://github.com/Jonah-Wu23/dsh-gungnir)（许可待核） | 完成度验证 | 用退出码/产物校验目标是否真的完成，防"假完成" | 工程验证强、语义审核弱；金融结论仍要人工 | 借"完成即证据"的思路做报告 QA |

**怎么用：** 先把 DSH 当"内核 + 会话 + 工具总线"，不要改它的 agent loop；所有金融能力以 **skill（提示词/流程）** 与 **MCP/HTTP 工具（数据/计算/渲染）** 两种形态接入。这样模型可换、DSH 可升级，领域资产不被锁死。

---

### M1 任务规划与编排

> 选型结论：规划用 `blueprint-studio` 的结构化蓝图，不引入第二套运行时；需要跨天审批再上 Temporal。LangGraph/CrewAI 只借"状态图/角色卡"的表达。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [LangGraph](https://github.com/langchain-ai/langgraph)（MIT） | 有状态 agent 图 | 显式状态图 + checkpointer + interrupt，天然支持人在回路与"时光旅行"回滚 | 低层框架，持久化/重试/UI 全要自己搭；与 DSH 二选一会增加复杂度 | 借"节点/边/中断/检查点"概念设计审批状态机 |
| [CrewAI](https://github.com/crewAIInc/crewAI)（MIT） | 角色化多智能体 | Role/Goal/Task 抽象最直观，半天能拼出分析师+风控+撰写流水线 | 复杂分支容易"漏出抽象"，确定性与可观测性弱 | 借角色卡模板，不把它当运行时 |
| [AutoGen](https://github.com/microsoft/autogen)（仓库元数据 CC-BY-4.0） | 对话式多智能体 | 群聊/辩论模式成熟，适合 bull/bear 原型 | 许可元数据非标准 MIT（需逐目录核对）；API 多次重构，迁移成本高 | 只借"多空辩论"的对话编排 |
| [MetaGPT](https://github.com/geekan/MetaGPT)（MIT） | SOP 多智能体 | 把公司流程写成 SOP，产物结构化，适合学习"角色→交付物" | 面向软件公司，金融适配远；2026-01 后基本停更 | 借"SOP + 交付物"思路，不引代码 |
| [Temporal](https://github.com/temporalio/temporal)（MIT） | 持久化工作流 | Signal 人工审批 + 自动重试 + 事件历史，审批可跨天/跨重启 | 要部署服务与数据库，概念重；MVP 阶段过度设计 | P1 需要"审批等三天"时再接 |
| [HumanLayer](https://github.com/humanlayer/humanlayer)（Apache-2.0） | 人工审批层 | 把审批做成 API/Slack/邮件触点，与 agent 执行解耦 | 偏托管产品，自托管与深度定制有限；无金融审批语义 | 借"审批即外部事件"的接口设计 |

**怎么用：** 蓝图对象就是计划，审批状态机就是编排。状态建议：`draft → submitted → under_review → approved / rejected / conditional → frozen`。每次状态变更写 append-only 审计日志，并绑定 artifact 版本。

---

### M2 浏览器操作与信源获取

> 选型结论：静态页 `Crawl4AI/Trafilatura`，JS/登录页 `Playwright`，年报/招股书 `Docling`。Firecrawl 只在许可可接受时用；所有抓取必须留 HTML 快照 + 哈希 + 抓取时间。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [Playwright](https://github.com/microsoft/playwright)（Apache-2.0） | 浏览器自动化 | 事实标准，trace/截图/PDF 一套搞定，适合做可复现取证 | 资源重、易被反爬；LLM 直接驱动时选择器脆弱 | 关键站点写确定性脚本；agent 只做兜底 |
| [browser-use](https://github.com/browser-use/browser-use)（MIT） | LLM 浏览器 agent | 自然语言驱动，DOM+视觉混合，复杂站点上手快 | 非确定性高、token 贵；高危操作必须外加审批与只读策略 | 做"探索未知站点"的兜底，不做主链路 |
| [Stagehand](https://github.com/browserbase/stagehand)（MIT） | 代码+自然语言浏览器 | 动作可缓存重放，比纯 vision agent 更可控 | 与 Browserbase/TS 生态绑定；复杂认证仍要写代码 | 借"act/extract/observe"三原语 |
| [Crawl4AI](https://github.com/unclecode/crawl4ai)（Apache-2.0） | LLM 友好爬虫 | 异步爬取 + 正文抽取 + markdown 输出，自托管免费 | 强 JS 站点仍需浏览器；抽取质量随模板漂移 | 做资讯/公告批量抓取 |
| [Firecrawl](https://github.com/mendableai/firecrawl)（AGPL-3.0） | 抓取/搜索/爬站 | scrape/search/crawl 一体化，markdown 质量领先 | AGPL 网络 copyleft，闭源 SaaS 商用需单独授权；自托管资源大 | 仅内部工具或先谈商业授权 |
| [Docling](https://github.com/docling-project/docling)（MIT） | 文档版面解析 | PDF/年报版面 + 表格结构还原，直接喂给 RAG/分析 | 大文件慢、GPU 更佳；跨页复杂表格仍会错行 | 财报/招股书入库第一步，配人工抽检 |
| [Scrapy](https://github.com/scrapy/scrapy)（BSD-3-Clause） | 爬虫框架 | 成熟、可扩展、适合大规模定时抓取 | 不渲染 JS；Twisted 异步模型学习曲线陡 | 做公告/新闻的定时增量抓取 |
| [Trafilatura](https://github.com/adbar/trafilatura)（Apache-2.0） | 正文抽取 | 正文/元数据质量高，轻量，适合批量 | 无 JS 渲染，复杂版式会漏 | 作为 Crawl4AI 之外的轻量备选 |

**怎么用：** 建"信源注册表"：域名、许可/robots、抓取频率、解析器、快照路径。每次抓取落 `sources/<source_id>/<sha256>.html` + `meta.json`（URL、时间、状态码、哈希），报告里只引用 `source_id`，保证可回溯。

---

### M3 分级文件树与存档

> 选型结论：不要直接把宿主机文件系统暴露给 UI。建"虚拟工作区"三根：`sources/`（只读原始件）、`analysis/`（可写底稿）、`deliverables/`（版本化交付物）。树 UI 用 `react-arborist` 或 `dsh-file-explorer`，存储用 S3/MinIO + Postgres 元数据。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [dsh-file-explorer](https://github.com/439436269-ctrl/dsh-file-explorer)（许可待核） | 侧栏文件树 | 懒加载工作区树 + 文本/Markdown/图片内嵌预览，几乎就是第三栏起点 | 单树、无多根分区与版本标记；小社区插件 | 先试装；不够就换 react-arborist 自研 |
| [react-arborist](https://github.com/brimdata/react-arborist)（MIT） | React 树组件 | 虚拟化、拖拽、键盘导航齐全，API 清爽 | 纯 UI，无权限/版本/搜索后端；大目录要自己做懒加载 | 第三栏的主力组件 |
| [code-server](https://github.com/coder/code-server)（MIT） | 浏览器 VS Code | 文件树/编辑器/终端/diff 开箱即用 | 重、攻击面大；面向代码而非投研档案 | 只给"高级编辑"模式，不默认暴露 |
| [filebrowser](https://github.com/filebrowser/filebrowser)（Apache-2.0） | Web 文件管理 | 单二进制，权限/分享/预览齐全，适合资料库后台 | 无内容版本与语义标签；Go 单体定制难 | 做管理员侧的资料库，不做主 UI |
| [OpenDAL](https://github.com/apache/opendal)（Apache-2.0） | 存储抽象 | 一套 API 抽象 S3/本地/GCS/Azure，Rust 核多语言绑定 | 偏底层，缺元数据/检索/权限 | 领域层统一读写对象存储 |

**怎么用：** 文件节点带 `kind`（source/analysis/deliverable）、`version`、`hash`、`source_id`、`status`。树支持按"公司/报告期/主题"三种视图切换；右键菜单：在预览打开、引用到对话、对比版本、下载。

---

### M4 主智能体、代码工具槽与子智能体

> 选型结论：用 DSH 原生 agent + 子智能体。代码执行放 E2B 或 DSH 沙箱；工具协议用 MCP。OpenHands 只借"沙箱+diff"的产品化经验，不整体嵌入。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [OpenHands](https://github.com/All-Hands-AI/OpenHands)（MIT） | 全栈 agent runtime | 沙箱、浏览器、编辑器、git diff、microagents 全都有，产品化最完整 | Docker 重、偏 coding；UI 与 runtime 耦合深 | 借"每轮 diff + 沙箱"的设计 |
| [smolagents](https://github.com/huggingface/smolagents)（Apache-2.0） | 代码型 agent | CodeAgent 用 Python 代码当动作，表达力强，核心极小 | 代码执行安全依赖沙箱；长任务规划弱 | 借"代码即动作"的工具槽设计 |
| [SWE-agent](https://github.com/SWE-agent/SWE-agent)（MIT） | 代码修复 agent | ACI（agent-computer interface）设计极佳，工具输出为模型优化过 | 面向代码基准，金融表格场景要重写工具层 | 借"工具输出格式"的设计 |
| [E2B](https://github.com/e2b-dev/E2B)（Apache-2.0） | 代码沙箱 | Firecracker 微虚拟机，启动快，适合"限定代码工具槽" | 自托管复杂、成本不低；网络出口与合规要自己配 | 跑 pandas/估值脚本的隔离环境 |
| [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)（MIT） | 工具协议 | 工具/资源/提示统一协议，DSH、Claude、IDE 都能接 | 规范演进快，认证/多租户/审计不成熟 | 数据/计算/渲染都包成 MCP server |

**工具槽建议（按角色授权，不按对话授权）：**

```yaml
tool_slots:
  python_analysis:   # 估值/统计
    runtime: e2b | dsh-sandbox
    mounts: { sources: ro, work: rw }
    network: none
    timeout: 120s
    packages: [pandas, numpy, scipy, statsmodels]
  sql_query:         # 快照查询
    engine: duckdb
    scope: snapshot_id
    read_only: true
  chart_render:      # 图表
    input: vega-lite | echarts-option
    output: svg/png
  doc_render:        # 报告
    input: report.json | html
    output: pdf/pptx/docx
```

**子智能体建议（最多两层，共享文件黑板而非聊天）：**

| 角色 | 工具 | 输出契约 | 约束 |
|---|---|---|---|
| Lead（分析） | plan / delegate / ask_user | 研究计划 + 结论 | 不直接算数 |
| Data | market_data / filings / web | `Source[]` + 快照 | 只读，无写权限 |
| Valuation | python_analysis / sql_query | `ValuationResult` | 无网络 |
| Risk | sql_query / news | `RiskItem[]` | 只读 |
| Bull / Bear | read_workspace | `Argument` | 禁止调用数据工具 |
| Compliance | read_workspace / rule_check | `ComplianceVerdict` | 可否决 |
| Designer | read_workspace / doc_render | `ReportArtifact` | 无数据访问，不能改数字 |

---

### M5 金融垂直参考实现

> 选型结论：`FinRobot` 是最近的对标（V3 已转 DSH），重点借"确定性计算 + 溯源 + 报告结构"；`TradingAgents` 借多空辩论；`OpenBB/AKShare` 做数据网关。不要直接套它们的交易结论。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [FinRobot](https://github.com/AI4Finance-Foundation/FinRobot)（Apache-2.0） | 金融 agent 平台 | "模型推理、代码算数、系统校验"三层分离；32 个确定性估值算子 + 56 个分析师 playbook + 13 章研报；V3 已转 DSH | V2 桌面端仅 macOS Apple Silicon；数据源偏美股；社区小 | 抄领域层设计与报告结构，不抄 UI |
| [TradingAgents](https://github.com/TauricResearch/TradingAgents)（Apache-2.0） | 多智能体交易 | bull/bear/judge 多空辩论 + 风险经理，天然对应"假设核准" | 偏交易信号与回测，不产出可交付研报；LLM 调用密集 | 借辩论角色与裁决规则 |
| [ai-hedge-fund](https://github.com/virattt/ai-hedge-fund)（MIT） | 投资人格代理 | 巴菲特/芒格等人格代理 + 组合决策，业务叙事直观 | 教育性质，数据与回测简化；人格化 prompt 不能作合规依据 | 借"多视角并列"的展示 |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB)（Apache-2.0） | 开放数据平台 | 统一 100+ 数据源，Apache-2.0，可直接做数据网关 | 包重、provider 质量参差；很多数据要自有 key，再分发受上游条款约束 | 数据网关首选候选 |
| [AKShare](https://github.com/akfamily/akshare)（MIT） | A 股/宏观数据 | 覆盖极广、免费、中文文档友好 | 爬虫实现，源站改版就失效；无 SLA | A 股数据快取，必须缓存 + 降级 |
| [gpt-researcher](https://github.com/assafelovic/gpt-researcher)（Apache-2.0） | 深度研究 | planner/executor + 引用聚合，长报告生成快，工程结构清晰 | 偏 web 公开信息，缺财报表格与估值；引用偶有错配 | 借"计划-检索-写作-引用"流水线 |
| [EDGARtools](https://github.com/dgunning/edgartools)（MIT） | SEC filings | XBRL/表格结构化提取，美股财报必备 | 仅美国市场；SEC 限流与解析边界要处理 | 美股财报入库 |

**金融领域层的最小闭环：**

1. **PIT 数据**：所有事实带 `as_of`、`announce_date`、`source_id`；回测严格截断，禁止未来函数。
2. **确定性计算**：DCF/WACC/可比/敏感性全部代码算，LLM 只解释；每个数字带 `compute_id`。
3. **证据链**：`Signal → Evidence → Finding → Thesis`，每条结论可下钻到原文定位。
4. **审计算子**：复算、勾稽、异常波动、单位/口径检查；不过审计不出报告。

---

### M6 金融报告美工与生成

> 选型结论：报告不要做成"一整页自由 HTML"，而是"结构化块 + 少量自定义 HTML"。图表用 ECharts，版式用 Tailwind/设计 token，导出用 PptxGenJS/Playwright。提示词蓝本用 Anthropic 文档 Skills。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [Anthropic Skills](https://github.com/anthropics/skills)（整仓无 LICENSE；文档类声明 Apache-2.0） | 文档生成技能 | 生产级 docx/pptx/pdf/xlsx 技能与 Agent Skills 规范，是最好的"报告美工"蓝本 | 整仓无 LICENSE，仅 README 声明文档类 Apache-2.0；不能整包照搬 | 逐目录确认许可，借 SKILL.md 结构与自检清单 |
| [Slidev](https://github.com/slidevjs/slidev)（MIT） | Markdown 幻灯片 | Markdown + Vue 组件 + 主题系统，适合代码生成演示 | 偏技术分享，打印/PPTX 导出弱；金融长报告要深度定制 | 做 IC 路演的快速版式 |
| [Typst](https://github.com/typst/typst)（Apache-2.0） | 现代排版 | 编译极快、排版精细，适合模板化长报告与批量生成 | 生态/组件少，CJK 字体与复杂表格要手写；非 WYSIWYG | 做"印刷级"PDF 长报告 |
| [ECharts](https://github.com/apache/echarts)（Apache-2.0） | 图表库 | 金融图表全（K 线、瀑布、桑基），中文生态好，SVG/Canvas 双渲染 | 配置项庞大，"少而准"的报告图表规范要自己封装 | 统一图表主题与导出 |
| [PptxGenJS](https://github.com/gitbrent/PptxGenJS)（MIT） | PPTX 生成 | 生成真正可编辑的 PPTX，表格/图表/母版都能写 | 布局引擎原始，复杂排版靠坐标硬编码；维护节奏偏慢 | 做"可编辑交付版" |

**报告 DSL 建议：**

```json
{
  "meta": { "title": "宁德时代 2026 中期策略", "template": "ic-16x9", "brand": "cn-broker-a" },
  "pages": [
    {
      "action_title": "储能第二曲线被低估，上调目标价至 268 元",
      "blocks": [
        { "type": "chart", "spec_id": "chart-03", "source_ids": ["S-12", "S-18"] },
        { "type": "table", "spec_id": "table-01", "source_ids": ["C-07"] },
        { "type": "text", "md": "…", "claim_ids": ["H-02"] }
      ]
    }
  ]
}
```

> 关键决策：**块级可视化编辑**（改标题、换图、调顺序）比"HTML 所见即所得"可靠得多；自定义 HTML 只给 hero 页/特殊版式，作为受控块。

---

### M7 四栏工作台 UI 与人机协同

> 选型结论：四栏固定布局不需要重型 dock 框架，`react-resizable-panels` 足够；要可拖拽/浮窗再上 Dockview。交互范式借 Magentic-UI，组件借 CopilotKit，审批节点借 Dify。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [Magentic-UI](https://github.com/microsoft/magentic-ui)（MIT） | 人机协同 agent 应用 | 计划审批、逐步确认、随时接管、浏览器+本地文件，HITL 最完整开源参考 | 微软实验项目，近期活跃度下降（最近提交 2026-09），模型/沙箱绑定深 | 抄"计划审批 + 动作守卫 + 接管"交互 |
| [CopilotKit](https://github.com/CopilotKit/CopilotKit)（MIT） | React agent UI | 审批、中断、生成式 UI 组件齐全，接 agent 快 | 前端框架绑定强，复杂工作台仍要自研；部分能力依赖托管 | 借 useCopilotAction / 审批组件 |
| [Dify](https://github.com/langgenius/dify)（修改版 Apache-2.0） | LLM 应用平台 | 可视化 workflow + 人工审批节点 + RAG，非技术也能改流程 | 多租户/品牌附加限制；作工作台底座太重，UI 难深度定制 | 只借"审批节点"的产品化表达 |
| [Dockview](https://github.com/dockview/dockview)（MIT） | 停靠布局 | 专业级拖拽/分屏/浮窗，适合可定制工作台 | 四栏固定布局用它偏重；API 学习成本高 | P2 做"可保存布局"时再上 |
| [Fragments](https://github.com/e2b-dev/fragments)（Apache-2.0） | 开源 Artifacts | 沙箱内生成/预览/迭代应用，前后端一体 | 绑定 E2B 与 Next.js；金融报告多为静态 HTML/图表，栈偏重 | 借"生成→预览→迭代→导出"闭环 |

**四栏交互规格（建议）：**

| 栏位 | 默认宽度 | 核心交互 | 数据源 |
|---|---|---|---|
| 左一 对话 | 24% | 流式、工具卡、@文件、引用跳转 | DSH session |
| 左二 假设核准 | 20% | 卡片队列、j/k/a/r 快捷键、证据下钻、条件批准 | approval service |
| 左三 文件树 | 18% | 三根分区、搜索、右键、拖入对话、版本徽标 | workspace API |
| 左四 预览/修改 | 38% | 预览/源码/对比/评论四 Tab、块级编辑、批注锚点 | artifact service |

实时改动：单人用"本地乐观更新 + 300ms 防抖 + SSE 广播"；多人再上 Yjs/Automerge。**不要一开始做 CRDT。**

---

### M8 一键导出

> 选型结论：HTML 是唯一源，PDF 用 Playwright（像素级）或 Gotenberg（服务化），PPTX 用 PptxGenJS，DOCX 用 docx/Pandoc。导出是异步任务，必须记录模板版本与产物哈希。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [Gotenberg](https://github.com/gotenberg/gotenberg)（MIT） | 文档转换服务 | Docker 化 HTML/Office→PDF，页眉页脚/合并/水印开箱即用 | 额外服务与 Chromium 内存；中文字体要挂载 | 服务化导出首选 |
| [docx](https://github.com/dolanmiu/docx)（MIT） | DOCX 生成 | TypeScript 直接生成 DOCX，表格/样式/页眉页脚 API 完整 | 分页与复杂版式弱；与 HTML 预览存在两套排版漂移 | Word 交付版 |
| [Pandoc](https://github.com/jgm/pandoc)（GPL-2.0） | 万能转换 | Markdown/HTML/DOCX/PDF 互转，模板生态大 | GPL 分发合规；PDF 依赖 LaTeX，重且排版不可控 | 内部转换，不分发二进制 |
| [LibreOffice](https://github.com/LibreOffice/core)（MPL-2.0） | 套件/无头转换 | DOCX/PPTX→PDF 保真度高，服务器端成熟 | 体积大、启动慢；字体缺失导致版式漂移 | 保真转换兜底 |
| [WeasyPrint](https://github.com/Kozea/WeasyPrint)（BSD-3-Clause） | HTML→PDF | CSS Paged Media，分页/页眉页脚纯 CSS 控制 | 不执行 JS，flex/grid 支持有限 | 打印样式简单的长报告 |

**一键导出流水线：**

```
选择版本 + 模板 + 格式
  → 冻结 artifact manifest（commit + 文件哈希）
  → 渲染 HTML（注入字体/图表/水印）
  → Playwright 截图自检（溢出/缺字/空白页）
  → PDF / PPTX / DOCX
  → 产物哈希 + 导出日志 + 下载
```

---

### M9 大版本回退

> 选型结论：**回合即提交**。每个 agent turn 结束对工作区做一次 Git 快照；"大版本"= milestone tag；回退=从 tag 开新分支，绝不 hard reset。结构化数据多时再上 Dolt。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [Git](https://github.com/git/git)（GPL-2.0）/ [isomorphic-git](https://github.com/isomorphic-git/isomorphic-git)（MIT） | 版本控制 | 提交/分支/tag/diff 完整；isomorphic-git 纯 JS 可在 Node/浏览器跑 | Git 不适合二进制大文件；isomorphic-git 大仓库性能与边缘特性不足 | 每轮 commit + tag，LFS/对象存储放二进制 |
| [jj](https://github.com/jj-vcs/jj)（Apache-2.0） | 新一代 VCS | 自动快照 + 一流 undo/回退，天然适合"每步可回滚" | 新 VCS，团队学习成本与托管/CI 生态不足 | 内部实验，不建议首发 |
| [Dolt](https://github.com/dolthub/dolt)（Apache-2.0） | SQL 版本库 | branch/merge/diff 像 Git 一样管结构化数据 | 生态小众、运维重；复杂 merge 仍需人工 | 估值表/假设表版本化 |
| [Automerge](https://github.com/automerge/automerge)（MIT） | CRDT | 协同编辑 + 完整历史，适合第四栏多人改稿 | 文档大时内存/同步成本高；冲突语义对表格不直观 | P2 多人实时编辑 |

**版本模型：**

```json
{
  "artifact_id": "report-600519-2026H1",
  "version": 12,
  "git_commit": "a1b2c3d",
  "tag": "v1.0-ic-approved",
  "files": [{ "path": "report.html", "sha256": "…" }],
  "inputs": ["snapshot:2026-06-30", "source:S-18"],
  "model": "deepseek-chat",
  "prompt_version": "designer@1.4",
  "approved_by": "user:alice",
  "created_at": "2026-11-09T10:00:00+08:00"
}
```

> 回退 UI 要展示"改了什么"（语义 diff）而不是只有 commit 号。`blueprint-studio` 已经实现了需求/节点/边的语义 diff，可直接移植到报告块。

---

### M10 数据看板

> 选型结论：客户侧看板用 DuckDB-WASM + ECharts/Tremor 嵌进工作台；内部运营用 Superset；Metabase 注意 AGPL。不要用 Grafana 做业务 BI。

| 项目（许可） | 定位 | 亮点 | 缺点 | 怎么用 |
|---|---|---|---|---|
| [dsh-chart-lab](https://github.com/66-zhimeng/dsh-chart-lab)（许可待核） | 对话内图表 | 数据集加载 + 图表类型/维度/聚合/Top-N 切换，导出 CSV/PNG | 面向探索小数据，不是报告级编排；品牌化弱 | 做"随手探索"的轻量图表卡 |
| [Superset](https://github.com/apache/superset)（Apache-2.0） | SQL BI | Apache 顶级项目，图表全、RBAC/行级权限成熟 | 部署重、UI 偏传统；嵌入要二次开发 | 内部运营/分析师看板 |
| [Metabase](https://github.com/metabase/metabase)（AGPL + 商业） | 自助 BI | 最易上手，非技术用户可自助提问 | AGPL + 商业功能分层；闭源嵌入需商业授权 | 仅内部试用，不进产品 |
| [Perspective](https://github.com/finos/perspective)（Apache-2.0） | 高性能表格 | WASM 表格/透视，支持流式更新，适合行情/持仓大表 | 偏计算表格，图表与叙事弱；API 复杂 | 做"可交互数据表"组件 |
| [Evidence](https://github.com/evidence-dev/evidence)（MIT） | 代码化 BI | Markdown+SQL 报表可进 Git、可 review | 构建时生成，交互性弱；不适合实时监控 | 做"每周市场周报"静态看板 |
| [DuckDB-WASM](https://github.com/duckdb/duckdb-wasm)（MIT） | 浏览器 OLAP | 前端直接查 Parquet/CSV，零后端即可做看板 | 受浏览器内存限制；并发/权限模型几乎没有 | 客户侧看板的查询引擎 |

**双轨看板：**

- **投研驾驶舱**（每家公司）：价格/估值带、估值桥（DCF→目标价）、可比矩阵、敏感性热力图、新闻情绪、假设状态。
- **运营看板**（团队）：任务队列、审批 SLA、来源新鲜度、单报告成本、导出成功率、回退次数。

---

## 4. 推荐技术栈

| 层 | MVP（4–6 周） | 进阶（P1/P2） | 说明 |
|---|---|---|---|
| Agent 内核 | DSH 0.2.x | 同左，锁版本 | 不引入第二套编排器 |
| 规划 | fork `blueprint-studio` → `research-blueprint` | 加 Temporal 持久化审批 | 复用版本/ diff / 派发 |
| 领域服务 | Python FastAPI + DuckDB + Pydantic | 拆数据/计算/渲染三个服务 | 金融库生态在 Python |
| 数据 | OpenBB（海外）+ AKShare（A 股）+ EDGAR | 接付费源（Wind/Choice/FMP） | 全部落 PIT 快照 |
| 文档解析 | Docling + `dsh-book-reader` 的 PDF 解析 | OCR/表格专用模型 | 年报/招股书优先 |
| 浏览器 | Playwright + Crawl4AI | Stagehand 兜底 | 留 HTML 快照 |
| 文件树 | react-arborist | dsh-file-explorer 试装 | 虚拟工作区三根 |
| 编辑器 | CodeMirror 6 | Monaco（大文件/代码） | 块级编辑为主 |
| 布局 | react-resizable-panels | Dockview（可保存布局） | 四栏固定先够用 |
| 报告 | 结构化块 + ECharts + Tailwind | Typst 长报告 | 一套 DSL，多端渲染 |
| 导出 | Playwright PDF + PptxGenJS | Gotenberg 服务化 | 记录模板版本 |
| 版本 | Git（isomorphic-git） | jj / Dolt | 回合即提交 |
| 审批 | Postgres 状态机 + SSE | HumanLayer/Temporal | 审批是对象，不是消息 |
| 看板 | DuckDB-WASM + ECharts | Superset（内部） | 双轨 |

---

## 5. 七个决定成败的设计点

### 5.1 唯一编排器

DSH 是唯一的 agent loop；领域服务只提供工具，不自己跑 agent。LangGraph/CrewAI 的"节点、边、中断"只作为画状态机的参考。否则会出现：同一份工具权限在两套系统里不一致、审批在 A 系统通过但 B 系统不知道、回滚只能回一半。

### 5.2 数字与叙事分离

所有数字由确定性代码产生，LLM 只负责解释与组织。每个数字带 `compute_id` 与 `source_id`；美工 agent **没有**数据工具权限，不能重算、不能补数。这是 FinRobot 最值得抄的一条。

### 5.3 假设是一等对象

不要用聊天记录当审批记录。假设必须是结构化对象：

```json
{
  "id": "H-2026-001",
  "thesis": "储能出货超预期将带动 2027 年毛利修复",
  "status": "under_review",
  "confidence": 0.62,
  "evidence_for": [{ "source_id": "S-18", "locator": "p.42", "quote": "…" }],
  "evidence_against": [{ "source_id": "S-21", "locator": "p.7", "quote": "…" }],
  "falsifiers": ["2026Q4 储能毛利率 < 18%", "海外订单增速 < 20%"],
  "valuation_impact": { "metric": "target_price", "from": 238, "to": 268 },
  "created_by": "agent:valuation",
  "artifact_version": 12
}
```

状态机：`draft → submitted → under_review → approved / rejected / conditional → frozen`。每次变更写 append-only 审计日志；批准即冻结 artifact 版本。

### 5.4 四栏与"实时改动"

- 固定四栏，允许折叠；左二在无待审时收成窄条。
- 左四四个 Tab：预览 / 源码 / 对比 / 评论。
- 编辑分两级：**块级编辑**（改标题、换图、调顺序、改结论）与**源码编辑**（自定义 HTML/CSS）。不要把整页 HTML 做成 contenteditable。
- 评论锚到 `block_id`，不是像素坐标；agent 收到的是结构化反馈（"把 chart-03 换成瀑布图，并补 2027 年"）。
- 实时：本地乐观更新 + 防抖保存 + SSE；冲突时提示"以哪个版本为准"。

### 5.5 版本模型

- 每轮 agent 结束：`git commit -m "turn:<n> <summary>"`。
- 每次人工保存：一次 commit。
- 每次导出：artifact manifest（commit + 哈希 + 模板版本）。
- "大版本"= annotated tag（如 `v1.0-ic-approved`）。
- 回退 = 从 tag 建新分支 + 恢复工作区 + 通知 agent，**不删除历史**。
- UI：时间线 + 语义 diff + 一键恢复 + "对比当前"。

### 5.6 导出流水线

HTML 是唯一源；PDF/PPTX/DOCX 都是派生产物。导出任务异步化，带进度与失败重试；导出前自动截图自检（空白页、文字溢出、缺字、图表越界）。字体必须随包分发（思源黑体/宋体），否则服务器与本地版式会漂移。

### 5.7 看板双轨

客户看板嵌在产品里，数据来自快照，查询在浏览器/边缘完成；内部运营看板用 Superset，不暴露给客户。两套指标口径统一到同一个 metrics 层，避免"客户看到 12%，运营看到 13%"。

---

## 6. 金融报告美工智能体：提示词骨架

```markdown
# Role
你是顶级券商研究所的视觉总监 + 前端工程师。你只负责"把给定的研究结论排成可交付的报告"，
不负责研究、不重算数字、不补充事实。

# Input
- dossier.json：论点、假设、证据、估值结果、风险、来源定位（每个数字带 compute_id/source_id）
- brand.json：主色/辅色/中性色、字体、logo、页脚免责声明
- template：ic-16x9 | memo-a4 | one-pager

# Output
单文件 HTML（内联 CSS/JS，无外部网络依赖），按 template 分页；
另输出 report.json（块级结构），供预览器做块级编辑。

# Hard rules
1. 所有数字只能引用 dossier；缺数据写 "n.a." 并标注，不得推算。
2. 每张图表必须有：action title、单位、来源脚注（source_id）、as_of 日期。
3. 每页只讲一个论点；图表 ≤ 2 个；正文 ≤ 120 字。
4. 中文排版：思源黑体/宋体，行高 1.6，数字用等宽，避免孤行与挤压。
5. 配色不超过 1 主色 + 1 强调色 + 3 中性色；不用 3D、不用彩虹色。
6. 免责声明与合规页脚必须保留，不得缩小到不可读。

# Workflow
1. 读 dossier，列出 5–7 个"必须被记住的结论"。
2. 为每个结论选一个 exhibit（图/表/文），写 action title。
3. 先出文字版大纲，再出 HTML；每页渲染后截图自检。
4. 自检：溢出、错位、缺字、对比度、图表误导、来源缺失。
5. 修正后输出终稿 + report.json + 导出清单。

# Self-check rubric
- 信息层级：3 秒能否看懂本页结论？
- 数据诚信：每个数字是否可下钻？
- 版式：对齐、留白、网格是否一致？
- 可读性：最小字号 ≥ 9pt，对比度 ≥ 4.5:1。
- 一致性：页码、页眉、脚注、单位是否统一？
```

> 提示词不是越长越好。把"不能做什么"（不重算、不补数、不改来源）写成硬约束，比堆形容词有效。

---

## 7. 许可与合规风险

| 许可类型 | 项目 | 处理建议 |
|---|---|---|
| AGPL-3.0 | Firecrawl、Metabase、Skyvern、Grafana | 闭源 SaaS 主链路不要用；确需使用则独立服务 + 法务评估 + 准备源提供义务 |
| GPL-2.0 | Git、Pandoc | 作为独立 CLI 调用通常可控；分发修改版二进制需合规 |
| 修改版 Apache-2.0 | Dify | 多租户/品牌限制，商用前读附加条款 |
| 无 LICENSE / 不明 | Anthropic Skills 整仓、部分 DSH 社区插件、部分 UI 仓库 | 不复制代码；只借思路；逐目录确认 |
| CC-BY-4.0 | AutoGen 仓库元数据 | 代码/文档许可逐目录核对，不要默认 MIT |
| MIT / Apache-2.0 | 本报告大多数项目 | 保留 NOTICE/LICENSE，建立依赖清单 |

**金融合规额外注意：**

- 数据再分发：OpenBB/AKShare 的上游条款可能禁止转售；商用换持牌数据源。
- 数据出境与个人信息：跨境数据、用户画像、研报分发要按业务地法规评估。
- 投顾资质：输出定位为"研究辅助/内部决策支持"，避免个性化投资建议；保留免责声明与人工复核记录。
- 审计留痕：谁在什么时间批准了哪个版本、依据哪些证据，必须可导出。

---

## 8. 落地路线（建议 8 周）

| 阶段 | 目标 | 交付 |
|---|---|---|
| W1–2 | 四栏骨架 + 文件树 + 预览 | DSH 插件/fork、三根工作区、Git 每轮快照、iframe 预览 |
| W3–4 | 假设核准 + 报告 v1 + PDF 导出 | 假设 schema/状态机、审批卡、块级报告 DSL、Playwright PDF |
| W5–6 | 领域层 + 数据 + 确定性计算 | FastAPI sidecar、OpenBB/AKShare、DCF/可比、provenance、PPTX |
| W7–8 | 看板 + 评估 + 合规 | 投研驾驶舱、20 家公司 golden set、许可清单、渗透/权限测试 |

**验收指标：**

| 指标 | 目标 |
|---|---|
| 数字可追溯率 | 100%（每个数字有 source/compute id） |
| 引用覆盖率 | ≥ 95% 结论有定位 |
| 报告一次通过率 | ≥ 70%（人工复核） |
| 审批平均时长 | < 30 分钟 |
| 导出成功率 | ≥ 99% |
| 回退恢复时间 | < 1 分钟 |
| 单报告成本 | 有基线，按季度下降 |

---

## 9. 开放问题（需要产品/合规拍板）

1. **单机桌面还是多租户 SaaS？** DSH 桌面端适合单机；多租户要补认证、隔离、配额、审计，Tauri 不是答案。
2. **交付物优先级？** 可编辑 PPTX vs 像素级 PDF vs Word 批注版，决定渲染管线投入。
3. **数据源预算？** 免费源（AKShare）能跑通 Demo，但生产要靠持牌源与缓存层。
4. **是否需要多人实时协同？** 不需要就别上 CRDT；需要就尽早定 Yjs/Automerge。
5. **DSH 插件插槽是否够四栏？** 先做 3 天 spike：client plugin 能否全屏接管；不行就 fork Web 端（MIT 允许）。

---

## 10. 参考索引

- DSH：<https://github.com/deepseek-ai/deepseek-harness>
- DSH 插件索引：<https://github.com/LingHXiao/awesome-dsh-plugin>
- FinRobot：<https://github.com/AI4Finance-Foundation/FinRobot>
- TradingAgents：<https://github.com/TauricResearch/TradingAgents>
- OpenBB：<https://github.com/OpenBB-finance/OpenBB>
- Magentic-UI：<https://github.com/microsoft/magentic-ui>
- Anthropic Skills：<https://github.com/anthropics/skills>
- CopilotKit：<https://github.com/CopilotKit/CopilotKit>
- Gotenberg：<https://github.com/gotenberg/gotenberg>
- DuckDB-WASM：<https://github.com/duckdb/duckdb-wasm>
- Nuwax 专项借鉴：[Nuwax_借鉴分析.md](Nuwax_借鉴分析.md)（Agent Computer 沙箱、ACP 多引擎、MCP 网关、会话状态机、审批节点、DesignViewer）

> 说明：Star 数、许可与活跃度均为 2026-11-09 抓取；快速迭代项目（尤其 DSH 插件）请在引入前重新核对 LICENSE 与 API 兼容性。
