#!/usr/bin/env bash
set -euo pipefail

# 智备货 StockWise · 全自动开发编排器
#
# 运行模式：
#   ./auto_dev.sh                          # 等价于 all
#   ./auto_dev.sh all                      # 全流程无人值守
#   ./auto_dev.sh stage4_alert             # 单阶段重跑（人工介入后续跑）
#   RESUME_FROM=stage5_purchase ./auto_dev.sh all   # 断点续跑
#
# 前置要求：git 仓库已初始化（git init），否则 commit/tag/reset 会失败。

STAGES=(stage0_skeleton stage1_datasource stage2_engine stage3_suggestion
        stage4_alert stage5_purchase stage6_dashboard stage7_chat)

MODE="${1:-all}"

# 页面类阶段自动前置拼接前端设计约束
is_frontend_stage () {
  case $1 in
    stage3*|stage4*|stage5*|stage6*|stage7*) return 0 ;;
    *) return 1 ;;
  esac
}

run_stage () {
  local name=$1
  local prompt_file="prompts/$name.md"
  [ -f "$prompt_file" ] || { echo "[错误] 缺少提示词文件 $prompt_file"; exit 1; }

  local prompt
  if is_frontend_stage "$name"; then
    prompt="$(cat prompts/fe_design.md)

---

$(cat "$prompt_file")"
  else
    prompt="$(cat "$prompt_file")"
  fi

  for attempt in 1 2 3; do
    echo "== $name 第 $attempt 次执行 =="
    if ! claude -p "$prompt" --dangerously-skip-permissions; then
      echo "== $name 第 $attempt 次执行失败（claude 退出码非 0）=="
    elif [ -f "verify/$name.sh" ] && bash "verify/$name.sh" 2>&1 | tee verify/last.log; then
      git add -A && git commit -m "$name done" && git tag "$name-done"
      echo "== $name 通过验收 =="
      return 0
    else
      echo "== $name 验收失败（verify/$name.sh 未生成或退出码非 0）=="
    fi

    # 失败：把验收日志拼成追问，进入下一轮重试
    if [ -f verify/last.log ]; then
      claude -p "上一阶段验收失败，日志如下，请修复后重新实现：$(tail -100 verify/last.log)" \
             --dangerously-skip-permissions || true
    fi
  done

  git reset --hard HEAD~1 2>/dev/null || true
  echo "$name 三次未过，已回滚，需人工介入" | tee FAILED.flag
  exit 1
}

main () {
  command -v git >/dev/null && git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
    || { echo "[错误] 当前不是 git 仓库，请先 git init 再运行"; exit 1; }

  local -a to_run=()

  if [ "$MODE" = "all" ]; then
    if [ -n "${RESUME_FROM:-}" ]; then
      local started=false
      for s in "${STAGES[@]}"; do
        if [ "$started" = "true" ] || [ "$s" = "$RESUME_FROM" ]; then
          started=true; to_run+=("$s")
        fi
      done
    else
      to_run=("${STAGES[@]}")
    fi
  else
    to_run=("$MODE")
  fi

  for s in "${to_run[@]}"; do run_stage "$s"; done

  if [ -f verify/e2e.sh ]; then
    bash verify/e2e.sh   # 全链路冒烟 + 生成验收报告
  else
    echo "提示：verify/e2e.sh 尚未生成，应在 S7 阶段由 Claude Code 编写"
  fi
}

main "$@"
