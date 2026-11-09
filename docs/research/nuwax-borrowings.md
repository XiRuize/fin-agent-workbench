# Nuwax 专项借鉴分析

> 调研时间：2026-11-09　对象：[nuwax-ai/nuwax](https://github.com/nuwax-ai/nuwax) 及其生态仓库
> 结论口径：**借架构与交互模式，不借技术栈与产品范围**。

---

## 0. 一句话结论

Nuwax 是一个"企业级 Agent OS"的**完整参考架构**：智能体创建/分发、知识库、记忆、模型代理、MCP、插件、沙箱、计费、市场全都做了。它最值得我们抄的不是代码，而是 **Agent Computer 沙箱、ACP 多引擎适配、MCP 网关、会话状态机、AgentFlow 的审批/评估节点、DesignViewer 的源码映射编辑** 这六个设计。它的 Java + 微前端 + 全功能栈太重，不适合作为我们的起点。

- **亮点：** 把 Agent OS 的全链路（沙箱、工具网关、审批、可视化编辑、桌面端）都跑通了，是少见的"完整参考"。
- **缺点：** 企业级全家桶 + 微前端 + V1/V2 双轨带来明显代码债，且完全没有金融领域能力（PIT、估值、证据链、报告）。

---

## 1. Nuwax 是什么

| 仓库 | 角色 | 规模/许可 |
|---|---|---|
| [nuwax](https://github.com/nuwax-ai/nuwax) | Web 前端 / Agent OS 主界面 | 900★，TypeScript，Apache-2.0；仓库约 1.6GB |
| [nuwax-backend](https://github.com/nuwax-ai/nuwax-backend) | Java 后端，21 个业务模块 | 39★，Java 17 + Spring Boot 3.3.8，Apache-2.0 |
| [nuwaclaw](https://github.com/nuwax-ai/nuwaclaw) | 桌面端 Agent 客户端，ACP 多引擎 | 36★，Electron + React + Rust，Apache-2.0 |
| [rcoder](https://github.com/nuwax-ai/rcoder) | 沙箱/容器调度 + Agent 运行时 | 5★，Rust，Apache-2.0（LICENSE 已核） |
| [mcp-proxy](https://github.com/nuwax-ai/mcp-proxy) | MCP 聚合/协议转换 | 9★，Rust，MIT/Apache-2.0 双许可 |
| [nuwax-file-server](https://github.com/nuwax-ai/nuwax-file-server) | 沙箱/桌面端文件服务 | 4★，Apache-2.0 |
| [vite-plugin-design-mode](https://github.com/nuwax-ai/vite-plugin-design-mode) | 网页可视化编辑 Vite 插件 | 1★，package.json 标 MIT，但仓库无 LICENSE 文件 |
| [run_code_rmcp](https://github.com/nuwax-ai/run_code_rmcp) | 执行 JS/TS/Python 脚本 | 4★，Apache-2.0 |

**产品定位：** 不是"聊天机器人"，而是"智能体开发 + 运行 + 分发"的平台。后端模块覆盖 `agent / compose / sandbox / mcp / file / knowledge / memory / model-proxy / connector / eco-market / custom-page / userapp / bill / pricing / subscription / credit / pay / im / log / user / system`。

**关键事实：**
- 前端 React 18 + Umi Max + qiankun 微前端；会话域做了 V2 重构，五个入口复用 `UnifiedChatSession`。
- 后端 Java 17 + MySQL + Milvus + Redis + Elasticsearch + K8s；DDD 分层、CQRS、策略/仓储模式。
- 桌面端 NuwaClaw 用 ACP 接 Claude Code、Codex、Gemini、Cline、Goose、Qwen 等引擎。
- 沙箱 RCoder 用 HTTP/SSE + gRPC + ACP，支持 Docker/K8s、VNC 桌面、文件服务、权限审批、断线续传。
- 许可：Apache-2.0，但**白标、OEM、移除版权声明需要商业授权**（`COMMERCIAL_LICENSE.md`）。

---

## 2. 最值得借鉴的八个设计

### 2.1 Agent OS 的模块分解：拿它当"能力清单"

**Nuwax 怎么做：** 把平台拆成 21 个模块，运行（agent/compose/sandbox/mcp/file）、知识（knowledge/memory）、模型（model-proxy/connector）、商业（eco-market/custom-page/userapp/bill/pricing/subscription/credit/pay）、组织（user/im/log/system）。

**我们怎么用：** 不要全做。用它当 checklist，明确我们缺什么：
- MVP 必须有：`agent / sandbox / mcp / file / knowledge / memory / model-proxy`。
- P1 再加：`connector / userapp / eco-market`（插件/技能市场）。
- P2 才考虑：`bill / pricing / subscription / credit / pay / im`。

**注意：** 模块多不等于架构好。Nuwax 的 21 个模块是多年产品堆出来的；我们按"领域层 6 个服务"起步即可。

---

### 2.2 Agent Computer：把"代码工具槽"做成独立沙箱服务

**Nuwax 怎么做：**
- RCoder 是控制面：HTTP/SSE 接客户端，gRPC 接容器内 `agent_runner`，ACP 接 Agent 引擎。
- 支持 Docker 与 K8s 双运行时；每个会话绑定 `sandboxId`，可云端、可个人电脑（NuwaClaw）。
- Computer Agent 提供容器化桌面（VNC、音频、输入法透传），文件服务提供工作区/Git/技能/开发服务器接口。
- 有独立的权限审批文档与 SSE 断线续传。

**我们怎么用：**
- 在 L1 领域层加一个 `SandboxService` 接口，而不是把代码执行散落在 agent 工具里：

```text
create(workspace_id, policy) -> sandbox_id
attach(sandbox_id) -> endpoint
exec(sandbox_id, cmd, timeout, env) -> {stdout, stderr, exit}
upload/download(sandbox_id, path)
snapshot(sandbox_id) -> image_id
destroy(sandbox_id)
```

- 每个会话固定 `sandbox_id`，发送后锁定，不允许中途切换（Nuwax 的 sandbox 选择规则就是这么做的）。
- 挂载：`sources/` 只读、`work/` 可写、网络默认关闭、包白名单。
- MVP 用 E2B 或 DSH 沙箱实现；需要私有化/Docker/K8s 再参考 RCoder，不要一上来自己写调度器。

**注意：** RCoder 是 Rust + gRPC + 容器编排，重。我们借"控制面/数据面分离 + 每会话沙箱 + 文件服务 + 权限审批"的形，不借实现。

---

### 2.3 ACP 多引擎适配：别把产品锁死在一个 Agent 上

**Nuwax 怎么做：** NuwaClaw 通过 ACP（Agent Client Protocol）统一接入 Claude Code、Codex、Gemini、Cline、Goose、Qwen、OpenCode 等；引擎隔离执行、可动态切换、不重启应用。

**我们怎么用：**
- 主分析 agent 继续用 DSH（它的会话、子智能体、技能、沙箱更适合我们）。
- 但定义一个 `EngineAdapter` 边界：`start / send / stream / cancel / approve / resume`。
- P2 可以把"代码型子智能体"接到 Claude Code/Codex（ACP），把"分析型主智能体"留在 DSH。这样既不锁死，也不在 MVP 阶段增加复杂度。

**注意：** 多引擎意味着多套权限、计费、日志、上下文格式；MVP 不要做。先把 DSH 用透。

---

### 2.4 MCP 网关：把工具接入变成"一个安全边界"

**Nuwax 怎么做：** `mcp-proxy` 支持 stdio、SSE、Streamable HTTP，多服务器聚合、协议转换、断线重连；NuwaClaw 和沙箱都用它。

**我们怎么用：**
- 建一个 workspace 级 MCP Gateway，统一挂载：行情、公告、财报解析、估值计算、图表渲染、导出。
- 每个角色只看到 allowlist 里的工具；网关做鉴权、限流、审计、超时、重试。
- 工具返回统一包裹 `{ok, data, error, provenance}`，不让每个 MCP server 各写一套。

**注意：** MCP 规范演进快，别把核心状态放在 MCP server；网关只做"工具边界"，业务状态仍在领域层。

---

### 2.5 会话运行时与状态机：四栏工作台最容易被低估的部分

**Nuwax 怎么做：**
- 会话域拆成 `domain`（纯模型）→ `runtime`（传输/存储/续流）→ `react`（页面消费），五个入口复用 `UnifiedChatSession`。
- 页面级 `modelScopes` 让多会话互不串状态。
- 活跃态只有一个权威 hook：`send-optimistic` 置 true；FINAL_RESULT/ERROR/轮询终态/连接死亡/用户停止/会话切换等 11 种场景置 false；用"终态 ack + 3s 保活 + 终态 sweep"防止按钮卡死和状态复活。
- SSE 有断线续传、终态兜底轮询、消息队列（AI 回复中可继续发，FIFO 自动消费）。

**我们怎么用：**
- 左一对话和左二审批共享**一个**会话状态机，不要在三个组件里各自 `isLoading`。
- 状态建议：`idle → sending → streaming → awaiting_terminal → done / stopped / error`；终态一到先"落死"状态，再写消息，再做后续。
- 必须有：终态 ack、3s 保活、断线重连、重复终态幂等、过期连接只清自己的消息。
- 用 Nuwax 的状态转换表当测试用例清单（网络断、重复 FINAL、旧连接迟到、轮询兜底）。

**注意：** 这是 Nuwax 文档里最"血泪"的部分：他们曾经因为三个消费方共用一个信号，出现按钮卡"会话中"、消息队列不消费、轮询不恢复。我们直接抄它的状态机，不要重新踩。

---

### 2.6 AgentFlow 的 EvalGate + HumanInteraction：直接映射"假设核准"

**Nuwax 怎么做：**
- `EvalGate`：N 个 validator（规则 + LLM judge），失败可回跳到指定节点并追加提示词。
- `HumanInteraction`：`ask` 与 `approve` 双模式，支持 approve / edit + approve / reject。
- 节点间用全局 `RunContext`，不是每条线都显式传参；有 checkpoint（`thread_id=runId`）。

**我们怎么用：**
- 把"假设核准"做成一个真正的节点，不是聊天里的一句"可以吗"：
  - `EvalGate`：证据充分性、数字可追溯、合规、逻辑一致性四类 validator；不过就退回对应子智能体并追加反馈。
  - `HumanInteraction`：批准 / 修改后批准 / 驳回；驳回必须带原因码。
- 审批结果写回 `Hypothesis` 对象与 `artifact_version`，并触发下游"冻结版本 + 继续写作"。

**注意：** AgentFlow 是可视化 DAG，我们不需要再造一个 X6 画布（他们光 X6 就 39k 行）。把 EvalGate/HumanInteraction 作为**后端状态机节点**实现即可。

---

### 2.7 DesignViewer：左四"预览与修改"的最佳参考

**Nuwax 怎么做：**
- `vite-plugin-design-mode` 在编译时向 DOM 注入 `data-xagi-info`（文件/行/列）和 `data-xagi-element-id`。
- iframe 内点选元素 → postMessage 给 DesignViewer → 右侧面板改 Tailwind 类/静态文本 → `pendingChanges` 累积 → `applyDesignChanges()` 写回源码。
- 支持双击编辑静态文本、列表项同步、组件识别、实时预览、批量保存。

**我们怎么用：**
- 不给整页 HTML 做 contenteditable；给报告 DSL 的每个 block 加 `block_id` + `source_path`（JSON Pointer）。
- 左四点选图表/段落 → 右侧属性面板（标题、图表类型、颜色、数据口径、顺序）→ 生成 patch → 重新渲染 iframe → 保存为新版本。
- "源码编辑"作为高级模式，只对自定义 HTML block 开放。
- 把"待保存变更"做成 pendingChanges 列表，支持批量应用/丢弃，和 Nuwax 的交互一致。

**注意：** 这个插件只支持 React/Vue 3 + Vite 源码，不适用于静态报告；package.json 写 MIT 但仓库没有 LICENSE 文件，复制代码前先补齐许可声明。

---

### 2.8 文件树懒加载：他们踩过的性能坑，我们别再踩

**Nuwax 怎么做：**
- 最初是"全量递归拉整树 + 无缓存 + 整树重渲染"，流式 2s 节流、每次写操作、打开预览都触发全量拉取，几千文件就撑不住。
- 后来改成"单层查询 `recursive:false` + 面包屑目录浏览器 + 2s 节流刷新当前层"，请求量从 O(整树) 降到 O(当前目录)。
- 但树组件**没有虚拟滚动**，仍是遗留问题。

**我们怎么用：**
- 从第一天就做：懒加载单层 + 虚拟滚动 + 面包屑 + 搜索索引 + 版本徽标。
- 三根分区（sources/analysis/deliverables）各自独立分页，不要一次拉全工作区。
- 文件变更用"时间戳信号 + 节流刷新当前层"，不要每次 agent 写文件就重拉整树。

**注意：** 这是"事后改造"的典型；我们直接按终态设计。

---

### 2.9 其他可借的小点

| 点 | Nuwax 做法 | 我们怎么用 |
|---|---|---|
| Skills 打包 | 后端 `skills/` 下每个技能有 `SKILL.md + references/ + scripts/ + templates/` | 分析师 playbook、报告模板、数据字典都按这个结构版本化 |
| 服务级备份/回退 | `nuwax-cli auto-backup run`、`rollback [BACKUP_ID]` | 用于平台升级回滚；**不要**拿它当报告版本回退 |
| 宿主桥 | `utils/hostBridge` 统一浏览器/桌面 webview 能力 | 四栏工作台若同时跑 Web/桌面，需要类似的 host bridge |
| 微前端 | qiankun 持久实例、隐藏保活 | 团队多、模块独立部署时再考虑；小团队别上 |
| 权限审批 | RCoder 有独立 permissions 文档 | 代码执行/浏览器操作/导出都走统一审批与审计 |

---

## 3. 不建议照搬的五件事

1. **Java + Spring Boot + MySQL + Milvus + Redis + ES + K8s 的全家桶。** 对一个金融分析工作台 MVP 太重；我们的 Python/TS 领域层 + Postgres + 对象存储更轻。Nuwax 的模块边界可以借，技术栈不必。
2. **qiankun 微前端 + 五入口 + V1/V2 双轨。** 他们的架构文档自己列了：53 个 >1000 行文件、3 套 SSE 实现、微应用补丁 3k 行。这是产品扩张的债，不是最佳实践。
3. **可视化 DAG 工作流编辑器。** AntV X6 相关代码 39k 行；我们已有 `blueprint-studio` 的结构化蓝图，够用。需要审批节点就在后端状态机里加，不要再造画布。
4. **全 Agent OS 范围。** 计费、订阅、积分、支付、IM、移动端、应用市场，都不是我们 MVP 的事；做了会稀释金融深度。
5. **白标/OEM 前不读商业许可。** Nuwax 是 Apache-2.0，但移除版权、白标、OEM 要商业授权；`vite-plugin-design-mode` 只在 package.json 写 MIT、仓库里没有 LICENSE 文件。代码可以看，复制前先补齐许可声明。

---

## 4. 对我们架构的六条具体修改

| # | 修改 | 落到哪里 |
|---|---|---|
| 1 | L1 增加 `SandboxService`，每会话固定 sandbox_id，文件服务 + 终端 + 网络策略 + 审批 | 领域层 / MCP 工具 |
| 2 | L1 增加 `MCP Gateway`，统一工具接入、allowlist、审计、重试 | 领域层 |
| 3 | 会话状态机单点化：终态 ack + 3s 保活 + 断线续传 + 消息队列 | 左一 / 左二 |
| 4 | 假设审批改为 `EvalGate + HumanInteraction`：validator 不过则回退并追加反馈 | 左二 / 审批服务 |
| 5 | 左四改为"块级选中 + 属性面板 + pendingChanges + 批量保存" | 报告 DSL / 预览器 |
| 6 | 文件树从第一天做懒加载 + 虚拟滚动 + 三根分区 | 左三 |

另外把"平台版本回退"和"报告版本回退"分成两条轴：
- 平台：镜像/配置/数据库迁移的回滚（参考 Nuwax CLI backup）。
- 报告：Git commit + tag + artifact manifest（我们原方案）。

---

## 5. 两周行动清单

| 时间 | 动作 | 产出 |
|---|---|---|
| D1–D2 | 读 RCoder 的 `agent-sessions`、`permissions`、`computer-agent` 文档 | 一页《SandboxService ADR》 |
| D3–D4 | 把 Nuwax 的活跃态状态转换表改写成我们的会话状态机 | 状态机图 + 12 条异常用例 |
| D5–D6 | 用 E2B/DSH 沙箱做 `exec + upload + snapshot` 最小闭环 | 可运行的代码工具槽 |
| D7 | 评审 Nuwax 许可（主仓商业条款、rcoder、design-mode、mcp-proxy） | 许可清单 |
| W2 | `EvalGate` 审批原型 + 报告块级编辑 spike + MCP Gateway spike | 三个 demo |

---

## 6. 许可与风险

| 对象 | 许可 | 风险 |
|---|---|---|
| nuwax / nuwax-backend / nuwaclaw | Apache-2.0 + 商业授权条款 | 白标、OEM、移除版权需商业授权 |
| rcoder | Apache-2.0（LICENSE 已核） | 保留 NOTICE |
| mcp-proxy | MIT / Apache-2.0 双许可 | 任选其一，保留声明 |
| nuwax-file-server / run_code_rmcp | Apache-2.0 | 保留 NOTICE |
| vite-plugin-design-mode | package.json 标 MIT，无 LICENSE 文件 | 复制前补齐许可声明 |

**一句话：** Nuwax 是很好的"产品架构参考"，不是"代码基座"。把它的沙箱、网关、状态机、审批节点、可视化编辑五个模式吃透，比 fork 它更有价值。
