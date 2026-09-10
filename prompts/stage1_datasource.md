# 阶段 1 · 数据中心与数据源适配器（M1，✅ 可插拔）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`

【阶段1 数据中心】目标：把四类散乱数据归集进标准表，提供 CSV 导入 API 与页面。

任务：
1. 实现 datasources/base.py：DataSourceAdapter 抽象类（source_code、fetch(path)->原始行、normalize(行)->标准记录、validate(记录)->错误列表）；registry.py 提供 register()/list()/run(source_code)。
2. 实现 6 个 CSV 适配器（各自独立文件）：amazon_orders、daily_sales 聚合进 daily_sales；walmart_orders 同理；inventory → inventory_snapshot；competitor、trends、env_score → external_signals（signal_type 分别为 competitor/trend/env）。列映射以 mock/ 下对应 CSV 表头为准，做表头校验与行级错误报告。
3. 数据校验规则：缺 SKU/日期非法/数值为负 → 该行进错误报告不入库；某 SKU 本期无数据 → 标记沿用上一期（写 data_flags）。导入幂等：同 source+日期 重复导入覆盖不重复。
4. API：POST /api/import/{source}（multipart 上传）、GET /api/import/logs、GET /api/datasources（各数据源上次同步时间与状态）。
5. 前端「数据中心」页：6 张数据源卡片（名称/状态灯/上次时间/上传按钮/最近导入日志），上传后 Toast 展示成功行数与错误明细。

验收：用 mock/ 六个 CSV 逐个上传成功；故意上传缺列文件得到明确错误提示；重复上传不产生重复数据；注销任一适配器（registry 注释掉）后其余适配器与页面正常。

【可插拔说明】本模块完全可插拔：新增数据源=新增适配器文件+注册一行。联动方：M2 测算引擎读取其产出的标准表；若 M1 整体缺失，M2 仅能基于 sku_master 空跑（降级）。

---

## 自动验收门（verify/stage1.sh）

同时编写 `verify/stage1.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. 六个 mock CSV 依次 `curl -F file=@mock/xxx.csv /api/import/{source}` 返回成功，且写入行数 = 文件行数 - 1。
2. 重复导入 `inventory_snapshot.csv`，库存表行数不变（幂等）。
3. 上传缺列文件返回 400 + 错误明细。
4. `GET /api/datasources` 返回 6 个源状态。
