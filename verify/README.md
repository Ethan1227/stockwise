# verify/ — 验收门脚本

每个阶段的 `verify/stageN.sh` 由 Claude Code 在各阶段执行时**自动编写**（阶段提示词末尾固定追加了该指令），本目录初始为空。

脚本约定：
- 命名：`verify/stage0.sh` … `verify/stage7.sh`，外加 `verify/e2e.sh`。
- 脚本把 stdout/stderr 写到 `verify/last.log`（编排器 `auto_dev.sh` 依赖它做失败追问）。
- 全部检查通过 → 退出码 0；任一项失败 → 退出码非 0。
- `verify/e2e.sh`：全新环境 seed → 全量导入 → calc/run → 建议/预警/采购/看板/问答 全链路 curl 走一遍，生成 `验收报告.md`。

各阶段验收点见 `../03_全自动开发方案.md` 第 3 节。
