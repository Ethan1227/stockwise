# 阶段 2 · 测算引擎（M2，修正器可插拔）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`

【阶段2 测算引擎】目标：实现每日测算 pipeline，把"拍脑袋"变成透明公式。

任务：
1. engine/pipeline.py：按 SKU 顺序执行 基线日销 → 修正器链 → 预测日销 → 备货评分 → 建议备货量 → 写 calc_result（含 factors_json、score_detail_json、人话 reason_text）。
2. 基线日销：近30天×0.5 + 近90天×0.3 + 去年同期×0.2（缺去年数据转 0.6/0.4；is_stockout_day 的天数剔除出分母）。权重从 settings 读。
3. engine/modifiers/ 四个修正器，各自独立文件+注册：
   - trend_modifier：读 external_signals(trend) 近30天环比 → 档位映射 1.2/1.1/1.0/0.9
   - competitor_modifier：主要竞品缺货 +0.1、大幅降价 -0.1
   - event_modifier：距大促30~60天且去年大促热销 ×1.3；普通临近 ×1.1
   - env_modifier：人工评分 -2~+2 映射 0.9~1.1
   每个修正器返回 (系数, 人话依据)，依据拼入 reason_text。档位参数全部读 settings。
4. 备货评分：缺货紧迫 40（可售天数 vs 备货周期）+ 销售健康 25（近30天趋势与稳定性）+ 外部信号 25（四系数综合偏离）+ 资金效率 10（毛利率×周转）。分档 ≥80 立即补货 / 60~79 常规 / 40~59 观望 / <40 停止补货。
5. 建议备货量 = 预测日销×(生产+头程+上架+安全天数) − 可售库存 − 在途，负取 0，按 MOQ 向上取整。SKU 参数（lead_prod_days 等）读 sku_master，缺省读 settings 默认值。
6. 提供 POST /api/calc/run 手动触发与 APScheduler 每日 06:30 自动触发（同一入口）。
7. pytest：用 mock 数据对 3 个 SKU 手工验算对拍（基线、系数、评分、备货量逐项断言）；注销任一修正器后该 SKU 该项系数=1.0 且 reason_text 注明"该信号缺失"。

验收：POST /api/calc/run 返回成功；calc_result 与手工验算一致；reason_text 可读；修正器注销降级验证通过。

【可插拔说明】修正器级可插拔。引擎整体与 M1 联动（读 daily_sales/inventory_snapshot/external_signals/sku_master），被 M3/M4/M6/M7 联动（读 calc_result）。引擎不 import 任何上层模块。

---

## 自动验收门（verify/stage2.sh）

同时编写 `verify/stage2.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. `pytest tests/test_engine.py` 全过（含 3 个 SKU 手工对拍）。
2. `POST /api/calc/run` 后 `calc_result` 行数 = `sku_master` 行数。
3. 抽 SK-2087：`forecast_daily` 在 [8.7, 10.7] 区间、`reason_text` 非空。
4. SQL 断言注销 `trend_modifier` 后该系数 = 1.0。
