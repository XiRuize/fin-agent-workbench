# Contributing

感谢参与 Fin Agent Workbench。这个项目同时包含架构文档、JSON 契约、Python 领域服务和后续的 DSH Web 插件，提交前请先读 [docs/architecture.md](docs/architecture.md)。

## 开发环境

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -e "services/domain[dev]"
pytest services/domain/tests -q
```

前端依赖在 `apps/workbench` 落地后再补；当前没有 Node 构建步骤。

## 分支与提交

- `main` 保持可运行；不要直接 push。
- 分支：`feat/<issue>-<slug>`、`fix/<issue>-<slug>`、`docs/<slug>`。
- 提交信息使用 Conventional Commits：
  - `feat(domain): add hypothesis transition API`
  - `fix(domain): reject frozen -> draft`
  - `docs(adr): record four-pane layout decision`
- 一个 PR 只做一件事；附带「改了什么、为什么、怎么验证」。

## PR 检查清单

- [ ] `pytest services/domain/tests -q` 通过
- [ ] 新增/修改契约时同步更新 `packages/contracts/*.schema.json`
- [ ] 不提交密钥、真实客户数据、未授权行情数据
- [ ] 涉及架构决策时新增 `docs/adr/` 记录

## 代码约定

- Python 3.11+，类型标注优先，Pydantic v2。
- 领域层不依赖 DSH 运行时；DSH 通过 MCP/HTTP 调用领域层。
- 金额单位统一为「元」，比率用小数（0.12 表示 12%）。
- 时间统一 UTC，存储 ISO 8601；展示层再转本地时区。

## 安全

- 发现漏洞不要开公开 Issue，直接联系维护者。
- 工具调用必须可审计：谁、在哪个会话、用什么参数、返回什么。
- 浏览器/代码执行默认最小权限，网络出口按域名白名单。
