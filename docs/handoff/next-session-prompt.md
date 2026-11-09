# 新对话启动提示词

把下面整段粘贴到新的 DSH 对话（创造模式）里。

---

你接手 **Fin Agent Workbench**（仓库：`XiRuize/fin-agent-workbench`，public，Apache-2.0）。

先按顺序读：

1. `HANDOFF.md`
2. `docs/design/ui-shell.md`
3. `docs/blueprint/m1-m2-workbench.md`
4. `docs/blueprint/m1-m2-workbench.json`（蓝图 payload）

背景：M0 已完成（FastAPI 假设领域服务 + JSON 契约 + 文档 + CI，7 个测试通过），**尚无 UI 代码**。UI 方向已确认：**左轨 + 单主画布 + 可折叠 Dock**，不再固定四栏；行情是独立模式，研究模式只留底部迷你 K 线。

请用 DSH 创造模式重建 M1/M2 蓝图（用 payload 或按 Markdown 重建），然后**只做 B1**：

- 验证 DSH client plugin 能否承载「模式轨 + 主画布 + 可折叠 Dock」；
- 产出可运行 demo（`spikes/dsh-workbench/`）与 `docs/adr/0003-dsh-plugin-vs-fork.md`；
- 明确结论：插件，还是 fork Web 端。

约束：

- 不要先写 UI；不要自己调用 `blueprint confirm` / `dispatch`，确认与分派由用户在面板发起。
- 不引入 qiankun / Ant Design / Tailwind；用 React 18 + TS、CSS Modules + DSH tokens、`react-resizable-panels`。
- 不引入第二套 agent 编排器；DSH 是唯一 agent loop。
- 不提交密钥、真实客户数据、未授权行情。

B1 完成后，按 `B2 工作台壳 → B7 模式路由 / B8 面板注册 → B3/B4/B5/B6 → B9/B10/B11 → C1/C2 → D1/D2` 的顺序推进；每个模块的 `tests / reviewer / human` 三层验证由用户 `/blueprint verify` 记录。

如果 B1 发现插件 API 不足，先写 ADR 0003 再 fork，不要静默绕过。
