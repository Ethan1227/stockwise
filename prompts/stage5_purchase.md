# 阶段 5 · 采购计划（M5，🔗 联动 M3/M1）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`
> 注意：本阶段为页面类阶段，`auto_dev.sh` 会自动前置拼接 `fe_design.md`（通用前端设计约束）。

【阶段5 采购计划】目标：把确认过的备货建议汇总成可执行采购单，管预算、倒排交期、跟踪到货。

任务：
1. POST /api/purchase-orders/generate：入参勾选 SKU 列表 → 按 (supplier, dest_warehouse) 分组生成草稿单（po_no=PO-日期-序号，items_json 含 SKU/数量(优先人工调整值)/单价/金额），同一供应商同一目的仓合并。
2. 校验：合计金额超月预算 → 返回 warning 字段（不拦截）；交期倒排：对 settings 大促日历中未来最近的大促，若 入仓截止−今天 < 头程+上架 → items 标记 suggest_air=true 并给提示文案（海运最迟下单日/空运最迟下单日各算一个）。
3. 状态机：draft→confirmed→shipped→arrived；confirmed 时把数量写入对应 SKU 在途（inventory_snapshot.in_transit_qty 当日快照增量），arrived 时冲减在途、增加可售库存。
4. API：GET 列表（状态/供应商筛选）、PUT /{id}/confirm、/{id}/ship、/{id}/arrive、DELETE（仅 draft）、GET /{id}/export 导出 xlsx 采购单。
5. 前端页：筛选条+[从建议生成]主按钮（跳 M3 带勾选回传或弹选择 Dialog）；采购单卡片左缘 Indigo 色条、状态 Badge（待确认橙/紧急红/已确认绿）、明细表格、卡片底部小计+毛利估算+[确认下单][调整数量][删除]；页面底部汇总卡：单数/总金额/月预算 Progress 条（占用%）+ 交期倒排提醒文案。

验收：从 M3 勾选 3 个 SKU 能生成 2 张按供应商分组的草稿；预算进度条与倒排文案正确；confirmed→shipped→arrived 后在途与库存数字联动正确；导出的 xlsx 可发供应商。

【联动说明】读 M3 确认的建议（联动 M3），回写 M1 的库存快照（联动 M1）；被 M6 聚合、M7 问答引用。单据状态机独立，上游缺失时可手工新建草稿（降级）。

---

## 自动验收门（verify/stage5.sh）

同时编写 `verify/stage5.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. `POST /api/purchase-orders/generate` 传 3 个 SKU 生成 2 张按供应商分组的草稿。
2. confirm → 在途增加；arrive → 在途减少且库存增加。
3. 预算校验：改小预算后重新生成返回 warning 字段。
4. 导出 xlsx 200。
