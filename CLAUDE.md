# CLAUDE.md — 智备货 StockWise 工程约束（所有开发阶段必读）

> 本文件是项目的最高工程约束。各阶段提示词只描述"做什么"，"怎么做"一律以本文件为准。若阶段提示词与本文件冲突，以本文件为准。

## 1. 项目一句话

面向年营收约 500 万、主营亚马逊+沃尔玛的跨境卖家的智能备货决策系统。核心链路：**数据归集 → 每日测算 → 备货建议 / 缺货滞销预警 / 采购计划 → 执行回写**。

## 2. 技术栈（固定，不得更换）

- **后端**：Python 3.12 + FastAPI + SQLAlchemy 2.x + Pydantic v2 + Alembic 迁移 + APScheduler（进程内定时）
- **数据库**：SQLite（默认，单文件 `data/stockwise.db`）；连接串走环境变量 `DATABASE_URL`，可切 PostgreSQL
- **前端**：React 18 + Vite + TypeScript + Tailwind CSS + shadcn/ui + Recharts + TanStack Query
- **单仓结构**：

```
stockwise/
├── CLAUDE.md
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口，只挂 router
│   │   ├── core/              # 配置、DB session、调度器、异常处理
│   │   ├── models/            # SQLAlchemy 模型（一表一文件）
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── datasources/       # 【可插拔】适配器：base.py registry.py csv_*.py api_*.py
│   │   ├── engine/            # 【可插拔】测算引擎：pipeline.py modifiers/ scoring.py
│   │   ├── alerts/            # 【可插拔】规则：registry.py rules/ notifier/
│   │   ├── services/          # 建议/采购/看板/问答 编排服务
│   │   └── api/               # 路由，一模块一文件
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/ui/     # shadcn 组件
│       ├── pages/             # 一页面一目录
│       ├── api/               # 封装 fetch，一模块一文件
│       └── theme.ts           # 设计规范常量（见第5节）
├── mock/                      # 模拟单据 CSV（导入测试用）
└── data/                      # SQLite 文件、上传文件
```

## 3. 编码硬规则

1. **可插拔三契约**（违反即返工）：
   - 数据源：`datasources/base.py` 定义 `DataSourceAdapter` 抽象类（`fetch()`/`normalize()`/`source_code`），新增数据源 = 新文件 + 在 `registry.py` 一行注册，**禁止改动已有适配器**。
   - 修正器：`engine/modifiers/base.py` 定义 `Modifier.factor(sku, ctx) -> (float, reason_str)`；修正器之间禁止互相 import；任一注销后引擎按 1.0 降级并记录。
   - 预警规则：装饰器 `@register_rule(code=..., default_level=...)`；阈值一律从 settings 读，**禁止硬编码数字**。
2. **配置与参数**：所有业务参数（权重 0.5/0.3/0.2、系数档位、阈值、备货周期默认值、采购预算、大促日历）只存 `settings` 表 + `core/config.py` 默认值，页面可改。代码中出现魔法数字视为缺陷。
3. **结果落表**：测算结果只写 `calc_result`，页面/预警/问答只读该表或公开 service 方法，**禁止前端直接拼计算逻辑**。
4. **降级原则**：任何外部数据缺失 → 沿用最近一期 + `data_flags` 标记 + 页面提示；流程不得中断报错。
5. API 统一返回 `{code, data, message}`；错误用 HTTP 状态码 + 业务 code；所有写操作记录操作人。
6. 中文注释、中文字段说明；提交粒度小，每阶段可独立运行验证。

## 4. 质量底线（每阶段 Definition of Done）

- 该阶段 API 有 pytest 用例（引擎计算类必须有手工验算对拍用例）；
- `curl` 或页面可走完该阶段主流程；
- 新增可插拔单元附"注销后降级"验证；
- 不引入新警告；前端 `npm run build` 通过。

## 5. 前端设计规范（与高保真原型 V2 一致，强制）

| Token | 值 | 用途 |
|---|---|---|
| bg | #F4F6FB | 页面底色 |
| card | #FFFFFF / 描边 #E6E9F2 / 圆角 12px | 卡片 |
| sidebar | #1B1C3B，激活项 #2A2C52 + 左缘 4px Indigo | 深色侧边导航 |
| primary | #6366F1（浅底 #EEF0FE） | 主按钮、链接、强调 |
| danger/warning/success/info | #EF4444 / #F59E0B / #10B981 / #3B82F6（各配 10% 浅底） | 语义色 |
| text | #1F2430 主 / #8A90A6 次 | 文字 |
| 评分徽章 | ≥80 红底 / 60–79 橙底 / 40–59 灰底 / <40 蓝底 | 备货评分 |

- 布局：左侧固定 15rem 深色导航（Logo「智备货 StockWise」+ 7 个菜单项），顶部白色栏（页面标题+副标题、搜索、通知、头像），内容区卡片式栅格。
- 组件一律用 shadcn/ui 组合；表格、徽章（Badge）、开关（Switch）、进度条（Progress）、对话框、Toast 直接用其变体。
- 页面视觉以 `原型图V2/` 五张图为唯一基准，不自由发挥。

## 6. 开发与验收环境

- 后端 `uvicorn app.main:app --reload`（8000），前端 `npm run dev`（5173，代理 /api → 8000）。
- 首次启动自动建表 + 可选导入 `mock/` 示例数据（`python -m app.core.seed --mock`）。
- 定时任务默认 `06:30`，可用环境变量覆盖；开发期提供 `POST /api/calc/run` 手动触发。
