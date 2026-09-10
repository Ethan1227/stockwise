# 阶段 0 · 工程骨架（M0）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`

【阶段0 工程骨架】目标：搭好可运行的双进程骨架，为后续所有阶段提供地基。

任务：
1. 按 CLAUDE.md 第 2 节目录结构初始化 backend（FastAPI+SQLAlchemy+Alembic+APScheduler）与 frontend（Vite+React+TS+Tailwind+shadcn/ui+Recharts+TanStack Query），前端代理 /api 到 8000。
2. 建全部 9 张表（见 01_系统设计.md 第 3 节），写首个 Alembic 迁移。
3. settings 表预置默认参数：基线权重 0.5/0.3/0.2、四修正器档位、安全天数 10、头程海运 35 天/空运 10 天、上架 5 天、预警阈值四项、月采购预算 140000、大促日历（黑五 2026-11-27，入仓截止 11-10）。
4. 健康检查 GET /api/health；种子脚本 `python -m app.core.seed --mock` 把 mock/ 下全部 CSV 导入对应标准表。
5. 前端只完成布局壳：侧边栏+顶栏+空路由页面占位，设计规范见 CLAUDE.md 第 5 节。

验收：后端启动建表成功、seed 脚本导入 mock 数据无报错；前端能打开带导航的空壳；npm run build 通过。

【可插拔说明】本阶段为地基，不可拔；但它不感知任何业务模块，后续模块均以注册方式挂入。

---

## 自动验收门（verify/stage0.sh）

同时编写 `verify/stage0.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. `GET /api/health` 返回 200。
2. `alembic upgrade head` 无错。
3. `python -m app.core.seed --mock` 退出码 0。
4. `npm run build` 通过。
