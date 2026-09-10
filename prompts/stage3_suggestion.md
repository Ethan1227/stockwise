# 阶段 3 · 备货建议表（M3，🔗 联动 M2）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`
> 注意：本阶段为页面类阶段，`auto_dev.sh` 会自动前置拼接 `fe_design.md`（通用前端设计约束）。

【阶段3 备货建议表】目标：核心决策页，让运营一行看懂"备不备、备多少、为什么"。

任务：
1. API：GET /api/suggestions（筛选：platform/score_band/status；按评分降序），每行返回 SKU/平台/分仓库存/在途/预测日销/可售天数/建议备货量/评分/评分依据/reason_text；PUT /api/suggestions/{sku}（人工改量或忽略，写 suggestion_override，列表优先显示人工值并标"已调整"）；GET /api/suggestions/export 导出 xlsx。
2. 前端页：筛选条（平台/类目/评分/状态下拉 + 搜索 + [重新测算]主按钮 + [导出Excel]）；表格行内：评分用 Badge 按分档着色（≥80红/60~79橙/40~59灰/<40蓝），可售天数<15天红色加粗，操作列[生成采购][忽略]；点击行展开 Drawer 显示评分依据：四个维度各一条 Progress 条（得分/满分+维度名）+ reason_text 全文 + 建议量计算公式代入过程。
3. [重新测算] 调 POST /api/calc/run 后自动刷新列表并 Toast 完成时间。

验收：页面与 原型图V2/02 视觉一致；筛选/导出/人工调整生效且刷新后保留；Drawer 中数字与 calc_result 一致。

【联动说明】只读 calc_result + 写 suggestion_override；[生成采购] 跳转 M5 并携带勾选 SKU 列表（M5 未交付时该按钮隐藏）。不感知引擎内部逻辑。

---

## 自动验收门（verify/stage3.sh）

同时编写 `verify/stage3.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. `GET /api/suggestions` 按评分降序、字段齐全。
2. `PUT /api/suggestions/SK-1023` 改量后再 GET 显示人工值且标「已调整」。
3. 导出接口返回 xlsx 且 Content-Type 正确。
4. `npm run build` 通过。
