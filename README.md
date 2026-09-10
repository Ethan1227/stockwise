# 智备货 StockWise

面向亚马逊/沃尔玛跨境卖家的智能备货决策系统。核心链路：**数据归集 → 每日测算 → 备货建议 / 缺货滞销预警 / 采购计划 → 执行回写**。

> 技术栈：后端 FastAPI + SQLAlchemy + PostgreSQL/SQLite；前端 React 18 + Vite + Tailwind；Docker 化部署；AI 问答接入 DeepSeek LLM。
> 详细设计见 `docs/01_系统设计.md`，部署见 `docs/03_部署文档.md`，待完善清单见 `docs/04_待完善清单.md`。

---

## 一、LLM 接入说明

### 1. 涉及 LLM 的功能清单

| 功能模块 | 是否使用 LLM | 说明 |
|---|---|---|
| **AI 问答助手（M7）** | ✅ 使用 | DeepSeek 生成自然语言回答 |
| 测算引擎（M2） | ❌ 不用 | 确定性公式（基线/修正器/评分） |
| 预警中心（M4） | ❌ 不用 | 规则引擎 |
| 采购计划（M5） | ❌ 不用 | 单据状态机 |
| 数据源/建议/工作台 | ❌ 不用 | 确定性逻辑 |

> 全系统**只有 AI 问答助手**使用 LLM，其余均为确定性规则，不依赖 LLM。

### 2. LLM 配置（环境变量）

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `DEEPSEEK_API_KEY` | 空 | DeepSeek API Key（**必填**，不填则走兜底） |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | 模型名 |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | OpenAI 兼容 API 地址 |

```bash
export DEEPSEEK_API_KEY="sk-xxxxxxxx"   # 或 docker compose 的 .env / environment
```

### 3. 兜底策略（LLM 不可用时）

AI 问答助手采用**「规则化意图识别 + 模板回答」作为兜底**，保证 LLM 断连也能正常回答：

1. 先用关键词路由到 6 类固定意图（补货清单 / 断货预测 / 滞销 / 大促 / 生成采购 / 预算）。
2. 命中意图后由 handler 拉取业务数据，产出**精确的模板回答**（`answer_md` + `data_chips` + `actions`）。
3. 再调用 DeepSeek 把模板回答改写为自然语言。
4. **若 LLM 调用失败**（无 Key / 网络失败 / 超时 / 返回异常）→ 直接返回模板回答，回答字段 `llm` 标记为 `fallback`。

返回体示例：`{answer_md, data_chips, actions, suggestions, llm}`，其中 `llm` 为 `deepseek-v4-flash`（LLM 命中）或 `fallback`（兜底）。

---

## 二、问答路由技能库（Skill）与 SSE 流式

### 1. 技能库层级

AI 问答助手内置「问答路由技能库」（`app/services/skill_registry.py`），层级为 **领域 → 技能 → 数据源**，覆盖全部业务功能：

| 领域 | 技能 | 数据源（API / 表 / MCP） |
|---|---|---|
| 测算与建议 | 备货建议 | `calc_result` 表 / `GET /api/suggestions` / `sku_master` |
| 预警中心 | 断货预测 | `calc_result` / `GET /api/alerts?type=缺货` / `inventory_snapshot` |
| 预警中心 | 滞销分析 | `GET /api/alerts?type=滞销` / `inventory_snapshot` |
| 设置中心 | 大促排期 | `settings.promotion_calendar` |
| 采购管理 | 采购计划 | `GET/POST /api/purchase-orders` / `purchase_order` 表 |
| 采购管理 | 预算查询 | `settings.monthly_budget` / `purchase_order(draft)` |

> 数据源类型：`api`（REST 接口）、`table`（数据库表）、`mcp`（MCP 工具，预留扩展）。

### 2. 路由策略

```
用户问题 → 关键词匹配技能库 → 拉取对应数据(API/表) → 组装「数据 + 关键词」上下文 → LLM 生成回答
```

### 3. SSE 流式 + 思考过程

- 端点：`POST /api/chat/stream`（`text/event-stream`）。
- 事件序列：`thinking`（思考过程）→ `token`（流式回答）→ `llm`（模型/fallback）→ `meta`（chips/actions）→ `done`。
- 前端「AI 问答助手」页实时流式展示，**思考过程可点击箭头收纳/展开**。

**思考过程示例**（问题「本周要补什么货？」）：

```
[意图识别] 命中技能「备货建议」（测算与建议）
[命中关键词] 要补
[可查询数据源] calc_result；GET /api/suggestions；sku_master
[数据摘要] 拉取 5 条结构化数据
[调用模型] deepseek-v4-flash
```

---

## 三、问答对测试范例

> 触发方式：`POST /api/chat`，body `{"text": "<问题>"}`。前端入口「AI 问答助手」页。

| # | 用户问题 | 意图 | 预期回答要点 |
|---|---|---|---|
| 1 | `本周要补什么货？` | 补货清单 | 按评分降序列出 Top SKU，含 **SK-1023**（高分） |
| 2 | `SK-2087 会断货吗？` | 断货预测 | 含 **SK-2087**、可售天数约 4.9 天、建议**改空运** |
| 3 | `哪些产品滞销？` | 滞销原因 | 含 **SK-0561**（库龄 210 天）、**SK-8830** |
| 4 | `黑五大促排期？` | 大促排期 | 含黑五日期 2026-11-27 + 入仓截止 11-10 |
| 5 | `生成采购计划` | 生成采购 | 返回生成的草稿单，M5 采购计划页可见 |
| 6 | `预算还剩多少？` | 预算查询 | 月预算 ¥140000 + 草稿占用金额 |
| 7 | `今天天气怎么样？` | 兜底 | 返回建议问题列表（未命中意图） |

**测试命令（curl）**：

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"text":"本周要补什么货？"}'
```

**LLM 命中 vs 兜底对比**：

- 配置 `DEEPSEEK_API_KEY` 后：回答为自然语言，返回体含 `"llm":"deepseek-v4-flash"`。
- 不配置 Key（或断网）：回答为模板文本，返回体含 `"llm":"fallback"`，内容仍含精确数据。

---

## 四、快速开始

```bash
# 后端
cd backend
uv venv .venv --python 3.12 && source .venv/Scripts/activate
uv pip install -r requirements-dev.txt
alembic upgrade head && python -m app.core.seed --mock
export DEEPSEEK_API_KEY="sk-xxxxxxxx"
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev

# 一键加载全部 mock 数据 + 测算 + 预警
cd backend && python -m app.core.load_mock

# Docker 全套（PostgreSQL + 后端 + 独立调度 + 前端）
DEEPSEEK_API_KEY="sk-xxxxxxxx" docker compose up -d --build
```

测试：`cd backend && pytest`（33 个用例）。
