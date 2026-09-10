# 前端设计约束（页面类阶段自动前置拼接）

> 本文件由 `auto_dev.sh` 在 stage3~stage7 执行前自动前置拼接进提示词。对应 `docs/02_ClaudeCode分阶段提示词.md` 的「通用前端设计提示词」。

【前端设计约束】本项目前端必须严格遵循 CLAUDE.md 第 5 节设计规范，实现前先把 theme.ts 中的设计 token 落地为 Tailwind 配置（colors: bg/card/sidebar/primary/danger/warning/success/info/ink/sub）。整体布局：左侧 15rem 深色侧边栏（Logo「智备货 StockWise」、菜单：工作台总览/数据中心/备货建议表/预警中心/采购计划/AI问答助手/系统设置，激活项 #2A2C52 底 + 左缘 4px #6366F1 高亮条），顶部白色栏（页面标题+副标题、搜索框、通知铃铛带红点、圆形头像），内容区白色圆角 12px 卡片 + #E6E9F2 细描边。组件用 shadcn/ui（Table/Badge/Switch/Progress/Dialog/Toast/Button/Card），图表用 Recharts，配色只用语义色，禁止自造色值。视觉基准：原型图V2 对应页面截图。
