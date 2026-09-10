# 阶段 7 · AI 问答助手（M7，🔗 联动 M2/M3/M4/M5）

> 来源：`docs/02_ClaudeCode分阶段提示词.md`
> 注意：本阶段为页面类阶段，`auto_dev.sh` 会自动前置拼接 `fe_design.md`（通用前端设计约束）。

【阶段7 AI问答助手】目标：Workbuddy 风格对话入口，用自然语言查备货结论、看依据、直接触发动作。

任务：
1. 后端 POST /api/chat：规则化意图识别（MVP 不上大模型）：关键词路由到 6 类 handler——本周补货清单（读 calc_result Top）、单SKU断货预测（可售天数+建议量+空运/海运两案）、滞销原因（读 alert+评分依据）、大促排期（交期倒排计算）、生成采购计划（调 M5 generate 返回草稿）、预算查询（读 M5 汇总）。每类 handler 返回 {answer_md, data_chips[], actions[]}；actions 仅两种：link(跳转页) 与 generate_po(调采购单接口)。回答末尾固定附"数据来自今日 HH:MM 测算，仅供参考"。
2. 未命中意图 → 返回兜底话术+建议问题列表。
3. 前端页（Workbuddy 布局）：左侧窄栏[+新对话]+最近对话列表（localStorage 存会话）；主区居中欢迎语"你好，{用户}。今天想了解什么备货问题？"+数据时间副标题；2×2 建议问题卡片（点击即发送）；对话气泡：用户右侧 Indigo 圆角气泡+头像，AI 左侧白色卡片（data_chips 渲染为彩色 Badge 行，actions 渲染为按钮）；底部圆角输入框+[全平台▾][深度分析]两个 Chip+圆形发送按钮。
4. actions 点击：link 跳路由；generate_po 调接口成功后 Toast 并给"去采购计划查看"。

验收：6 类示例问题各有正确回答（数据与对应页面一致）；data_chips/actions 渲染正确；generate_po 真能在 M5 看到草稿；未命中问题有兜底。

【联动说明】本模块是各域的"对话皮肤"：只调 M2~M5 公开 service/API，不复制任何业务逻辑；新增意图=新增一个 handler 注册。MVP 不接 LLM，后续可在 handler 层平滑替换为模型调用（接口不变）。

---

## 自动验收门（verify/stage7.sh）

同时编写 `verify/stage7.sh`，逐项检查以下脚本化验收点，全部通过退出码 0，脚本 stdout/stderr 写 `verify/last.log`：

1. 6 类固定问题 `POST /api/chat` 断言：补货清单回答含 Top SKU、断货问题含 SK-2087 与「空运」、滞销问题含 SK-0561。
2. `generate_po` 类问题回答后 M5 真的多出草稿。
3. 未命中问题返回兜底字段。
