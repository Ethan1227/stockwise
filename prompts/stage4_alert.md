# 阶段 4 · 预警中心（M4，规则可插拔）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`
> 注意：本阶段为页面类阶段，`auto_dev.sh` 会自动前置拼接 `fe_design.md`（通用前端设计约束）。

【阶段4 预警中心】目标：测算完成后自动扫描规则，分级预警并通知，形成处理闭环。

任务：
1. alerts/registry.py 装饰器 @register_rule(code, default_level)；实现 4 条内置规则，阈值全部读 settings：缺货紧急（可售天数<头程）、缺货一般（<头程+安全）、滞销严重（周转>120天或库龄>180天）、滞销轻度（周转>60天）。每条规则产出 title/detail/advice（advice 带具体数字，如"立即采购450件，建议改空运"）。
2. 规则扫描挂在测算 pipeline 之后；同一 SKU 同 code 未处理的预警不重复创建。
3. alerts/notifier/：Notifier 接口 + 两个实现 站内信（写 alert 即站内）与邮件（SMTP，紧急级实时、一般/滞销按 settings 汇总周期）；发送结果写 alert.notify_log；SMTP 未配置时降级仅站内并记日志。
4. API：GET /api/alerts（type/level/status 筛选）、PUT /api/alerts/{id}（已处理/已忽略）、GET/PUT /api/settings/rules（阈值与开关读写）。
5. 前端页：顶部 Tab 徽章（缺货5/滞销8/全部）；预警卡片左缘 4px 语义色条 + 分级 Badge + 原因 + 建议 + 动作按钮（缺货→[生成采购单]跳 M5；滞销→[创建促销建议]占位）；底部规则配置区：每行 规则名/触发条件/通知方式/Switch 开关，[编辑规则]弹 Dialog 改阈值。

验收：用 mock 数据跑出 5 条缺货+8 条滞销（数量以 mock 实际为准）；阈值改小后重跑预警数变化；重复扫描不产生重复预警；注销任一规则不影响其余。

【可插拔说明】规则与通知器两级可插拔。联动：读 calc_result（M2）、[生成采购单]跳 M5。

---

## 自动验收门（verify/stage4.sh）

同时编写 `verify/stage4.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. 重跑测算后 `GET /api/alerts?type=缺货` ≥3 条且含 SK-2087 紧急级。
2. 滞销预警含 SK-0561 / SK-8830。
3. 再跑一遍预警总数不变（不重复创建）。
4. `PUT /api/settings/rules` 把滞销周转阈值改为 30 天后预警数变多。
