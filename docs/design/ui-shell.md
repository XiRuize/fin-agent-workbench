# UI Shell Spec（M1）

> 状态：已确认，作为 M1 前端实现基准。  
> 参考：[dsh-media-desk](https://github.com/woniuniuniu/dsh-media-desk) 的「左轨 + 单画布 + 可折叠 Dock」与 [Nuwax](https://github.com/nuwax-ai/nuwax) 的模块化面板 / DesignViewer 交互。  
> 核心决策：**废弃固定四栏；页面切换 = 模式切换 + 子视图 Tab + 面板折叠。**

---

## 1. 设计原则

1. **一个主画布**：同一时间只呈现一个模式；需要并排时，用模式内部的 2–3 个可折叠面板，而不是全局四栏。
2. **对话是 Dock，不是固定栏**：默认左侧 320px，可折叠、换边、浮层；Focus 模式隐藏。
3. **图表优先拿宽度**：行情是独立模式，K 线占满画布；研究模式只保留底部迷你 K 线。
4. **折叠不丢状态**：宽度、滚动、选中项、展开状态按 `workspace + mode` 持久化。
5. **DSH 原生质感**：用 `--dsw-alias-*` token，1px 边框、12–16px 圆角、轻阴影，不引重型组件库。
6. **键盘优先**：模式、Dock、Focus、命令面板都有快捷键。

---

## 2. 壳的尺寸

```text
┌────┬──────────────────────────────────────────────┬─────────────┐
│ 模 │ 顶栏 48px：标的 / as-of / 搜索 / 助手 / 布局 / 导出 │             │
│ 式 ├──────────────────────────────────────────────┤  右 Dock     │
│ 轨 │                                              │  280–360px   │
│ 56 │              主画布（flex）                    │  可折叠      │
│ px │                                              │             │
├────┴──────────────────────────────────────────────┴─────────────┤
│ 状态栏 26px：数据新鲜度 · 模型 · token · 保存状态 · 版本             │
└──────────────────────────────────────────────────────────────────┘
```

- 模式轨 56px，图标 + tooltip + 待审徽标。
- 顶栏 48px，左侧面包屑/标的名，右侧全局动作。
- 状态栏 26px，常驻但不抢视觉。
- 左 Dock 320px（默认对话），右 Dock 280px（检查器）；宽度可拖拽 240–420。
- 面板间距 8px；主画布内边距 12–16px。

---

## 3. 模式

| 模式 | 左面板 | 主画布 | 右 Dock | 底部 |
|---|---|---|---|---|
| **研究 research** | 文件树 240 + 对话 320 | 报告画布 | 假设/证据检查器 280 | 迷你 K 线 160 |
| **行情 market** | 自选/搜索 220 | 全宽 K 线 + 成交量 + 指标 | 标的详情 280 | 指标切换条 |
| **文件 files** | 文件树 280 | 文件预览/编辑器 | 元数据/版本 260 | — |
| **报告 report** | 大纲 200 | 块级预览/编辑 | 属性/评论 280 | 页面胶片条 |
| **核准 approval** | 待审队列 300 | 假设详情/证据正反/估值 | 审计时间线 280 | 审批操作栏 |
| **看板 dashboard** | 过滤器 200 | 指标网格（M5 实现） | — | — |

> M1 优先：研究、行情、报告、核准；文件复用研究模式的文件树+画布；看板只保留路由占位。

---

## 4. 切换与折叠

### 快捷键

| 键 | 动作 |
|---|---|
| `1–6` | 切换模式 |
| `⌘/Ctrl + J` | 显示/隐藏对话 Dock |
| `⌘/Ctrl + B` | 显示/隐藏左面板 |
| `⌘/Ctrl + I` | 显示/隐藏右检查器 |
| `F` | Focus 模式（隐藏所有 Dock） |
| `Esc` | 退出 Focus / 关闭浮层 |
| `⌘/Ctrl + K` | 命令面板 |
| `[` / `]` | 收起/展开当前面板 |

### 状态模型

```ts
type ModeId = 'research' | 'market' | 'files' | 'report' | 'approval' | 'dashboard';
type Slot = 'left' | 'right' | 'bottom';

interface PanelState {
  visible: boolean;
  size: number;      // px
  slot: Slot;
  order: number;
}

interface WorkbenchLayout {
  mode: ModeId;
  panels: Record<string, PanelState>;
  focus: boolean;
  chatSide: 'left' | 'right';
}
```

- 持久化 key：`fin.layout.v1:${workspaceId}`。
- `focus: true` 时 Dock 全部隐藏，只留主画布；`Esc` 恢复上次布局。
- 面板折叠为 32px 图标条，不卸载组件；`keepMounted` 的面板保留滚动与表单状态。
- 切换模式时保留每个模式自己的布局与滚动位置。

### 深链

```text
#/research/:reportId
#/market/:symbol?tf=1d&ind=ma,macd
#/report/:reportId?tab=preview
#/approval/:hypothesisId
```

刷新后恢复：模式、实体、Tab、面板宽度/折叠。

---

## 5. 面板注册

```ts
export interface PanelDef {
  id: string;
  title: string;
  icon?: React.ReactNode;
  defaultSlot: Slot;
  defaultSize: number;
  minSize: number;
  maxSize: number;
  collapsible: boolean;
  keepMounted?: boolean;
  component: React.LazyExoticComponent<React.ComponentType<PanelProps>>;
}
```

- `panelRegistry` 只注册“可独立渲染”的面板；模式负责组合。
- 面板只通过 props/context 拿数据，不直接读全局 store。
- 面板不感知自己属于哪个模式，便于复用（文件树同时用于 research/files）。
- 面板内部不得写 `position: fixed`；浮层统一走 `DockHost`。

---

## 6. 行情模式（K 线）

```text
┌──────────┬──────────────────────────────────────────┬─────────────┐
│ 自选/搜索 │ 周期 1D 1W 1M 5m 15m 30m 60m  指标 MA MACD RSI │ 标的详情     │
│ 220px    ├──────────────────────────────────────────┤ 280px       │
│          │ K 线主图（MA5/10/20/60）                   │             │
│          ├──────────────────────────────────────────┤             │
│          │ 成交量                                     │             │
│          ├──────────────────────────────────────────┤             │
│          │ MACD / RSI 副图（切换）                     │             │
└──────────┴──────────────────────────────────────────┴─────────────┘
```

- 图表：ECharts，三组 `grid` 共享 `axisPointer` 与 `dataZoom`；`large: true`。
- 数据：`GET /api/v1/market/bars?symbol&timeframe&from&to&as_of&indicators=ma,macd,rsi`。
- 返回：`{symbol, timeframe, as_of, source, synthetic, bars:[{ts,o,h,l,c,v}], indicators:{...}}`。
- 空数据：显示 `n.a.` 与“数据未覆盖”，不画假线。
- 合成数据：右上角 `synthetic` 徽标；真实数据源接好后移除。
- 性能：10k 根 < 1s；只渲染可视窗口；切换指标不重新请求 bars，除非需要新指标。
- 交互：十字光标、滚轮缩放、拖拽平移、双击复位；`F` 全屏图表。
- 研究模式底部迷你 K 线：只画收盘线 + 成交量，点击进入行情模式并带上 symbol。

---

## 7. 响应式

| 宽度 | 行为 |
|---|---|
| ≥ 1280 | 完整三区：左面板 + 画布 + 右 Dock；对话可再占左 Dock |
| 1024–1279 | 同时只开一个侧 Dock；另一个变浮层；对话默认收起 |
| 768–1023 | 模式轨 48px；面板全部变抽屉；画布全宽 |
| < 768 | 单列；只读/轻量操作；K 线工具栏收进“更多” |

- 用 `ResizeObserver` 监听根容器，不用 `window.innerWidth`。
- 窄屏切换模式不重建画布；抽屉关闭保留状态。
- 禁止横向滚动。

---

## 8. 视觉系统

- **颜色**：只用 DSH token：`--dsw-alias-bg-base`、`label-primary/secondary/tertiary`、`border-l2/l4`、`button-primary-fill`。
- **字体**：系统字体；数字用 `font-variant-numeric: tabular-nums`；标题 20/28，正文 13/14，辅助 12。
- **间距**：8px 网格；面板内边距 12/16；卡片圆角 12；Dock 圆角 16。
- **边框**：1px `--dsw-alias-border-l2`；不用重阴影，浮层用 `--dsw-elevation-soft`。
- **动效**：120–180ms ease；折叠用宽度/透明度过渡；`prefers-reduced-motion` 关闭。
- **深色模式**：完全跟随 DSH；不写死颜色。
- **空状态**：一句话 + 一个动作，不用大插画。

---

## 9. 前端架构

```text
apps/workbench/src/
├── shell/            # WorkbenchRoot, ModeRail, TopBar, StatusBar, DockHost
├── modes/            # research / market / files / report / approval / dashboard
│   └── registry.ts   # ModeId -> lazy component + default layout
├── layout/           # PanelDef, PanelHost, ResizeHandles, layoutReducer
├── state/            # layoutStore, sessionStore, marketStore, approvalStore
├── features/         # file-tree, preview, versions, approval, market
├── router/           # hash route <-> mode/entity/tab
├── styles/           # tokens.css, shell.css, mode css modules
└── app.tsx
```

- **模式懒加载**：`React.lazy` + `Suspense`；hover 预取下一个模式 chunk。
- **状态**：Zustand；服务端状态用 TanStack Query；流式用 SSE。
- **路由**：hash 路由，DSH 插件内不依赖 BrowserRouter。
- **样式**：CSS Modules + DSH tokens；不引 Ant Design / Tailwind。
- **图标**：`lucide-react`（MIT）。
- **拖拽**：`react-resizable-panels`；不自研拖拽引擎。
- **测试**：Vitest + Testing Library；Playwright 做模式切换/折叠/K 线 e2e。

### 组件树

```text
<WorkbenchRoot>
  <ModeRail />
  <WorkbenchMain>
    <TopBar />
    <ModeCanvas><ModeRenderer /></ModeCanvas>
    <StatusBar />
  </WorkbenchMain>
  <DockHost slot="left" />
  <DockHost slot="right" />
  <CommandPalette />
</WorkbenchRoot>
```

---

## 10. 性能与可访问性

- 模式切换 < 100ms：chunk 预取、避免整页重渲染、`startTransition`。
- 文件树：虚拟滚动；单层请求；2s 节流刷新。
- K 线：ECharts `large`、可视窗口裁剪、指标增量更新。
- 焦点管理：模式切换后焦点回到画布标题；Dock 打开聚焦输入框；`Esc` 关闭。
- ARIA：`aria-current` 标记当前模式；折叠按钮 `aria-expanded`；图表提供文字摘要。
- 颜色对比度 ≥ 4.5:1；不只靠颜色表达状态。

---

## 11. 借鉴清单

**dsh-media-desk**
- 左轨 + 顶部玻璃胶囊导航 + 单画布。
- Studio：左侧约 300px 对话、右侧自适应稿面；对话可关，“助手”按钮再开。
- `focused` 隐藏 Dock；`<1020` 自动收起；`<780` 单列。
- DSH token 主题、克制动效、本地优先、`⌘Z` 撤销。

**Nuwax**
- 模块/面板注册与懒加载边界。
- DesignViewer 的“选中 → 属性面板 → pendingChanges → 写回”交互，用于报告块级编辑。
- 审批/干预：队列 + 详情 + 审计时间线。
- 状态栏展示模型、成本、数据新鲜度。

---

## 12. 待确认

1. 对话默认左 Dock 是否合适，还是右侧更贴近投研习惯？
2. 行情模式默认显示左自选 + 右详情，还是默认全屏 K 线、两侧收起？
3. 报告块级编辑第一版是否只做 text/chart/table，表格先只读？
4. 文件模式是否需要在 M1 就独立入口，还是先复用研究模式？
5. 移动端只读是否可接受？
