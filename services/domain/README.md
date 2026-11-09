# Domain Service

假设（Hypothesis）与审批状态的领域服务。M0 只做最小闭环：创建、查询、状态流转、审计事件。

## 运行

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

默认数据库 `data/domain.db`，可用 `FINA_DB_PATH` 覆盖。API 文档：<http://127.0.0.1:8000/docs>。

## API

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查 |
| POST | `/api/v1/hypotheses` | 创建假设（draft） |
| GET | `/api/v1/hypotheses?status=draft` | 列表/过滤 |
| GET | `/api/v1/hypotheses/{id}` | 详情 |
| POST | `/api/v1/hypotheses/{id}/transitions` | 状态流转 |
| GET | `/api/v1/hypotheses/{id}/events` | 审计事件 |

### 创建

```bash
curl -X POST http://127.0.0.1:8000/api/v1/hypotheses \
  -H 'Content-Type: application/json' \
  -d '{
    "thesis": "储能出货超预期将带动 2027 年毛利修复",
    "confidence": 0.62,
    "evidence_for": [{"source_id": "S-18", "locator": "p.42"}],
    "evidence_against": [{"source_id": "S-21", "locator": "p.7"}],
    "falsifiers": ["2026Q4 储能毛利率 < 18%"],
    "valuation_impact": {"metric": "target_price", "from": 238, "to": 268}
  }'
```

### 流转

```bash
curl -X POST http://127.0.0.1:8000/api/v1/hypotheses/<id>/transitions \
  -H 'Content-Type: application/json' \
  -d '{"to_status": "submitted", "actor": "agent:valuation"}'
```

## 状态机

```text
draft → submitted → under_review → approved → frozen
                         ├────────→ rejected → draft
                         └────────→ conditional → approved / rejected
```

业务规则：

- 提交前至少一条 `falsifiers`（可证伪条件）。
- `approved` 后只能 `frozen`，冻结后不可修改。
- 每次流转写 append-only `hypothesis_events`。

## 设计说明

- SQLite 只是 M0 的本地实现；接口按 Postgres 迁移设计。
- payload 是 canonical JSON，`status` 列只用于过滤，二者在同一事务更新。
- 时间统一 UTC；金额单位「元」，比率小数。
- 领域层不 import DSH；DSH 通过 MCP/HTTP 调这里。
