#!/bin/bash
# Smoke test for direct Claude CLI trajectory analysis.

set -euo pipefail

REPO_ROOT="/volume/pt-coder/users/tuney/Script/HyperDistill"
INSTANCE_PATH="/volume/pt-coder/users/tuney/posttrain_data/tb-traj-reorganized-v2/break-filter-js-from-html"
TASK_NAME="$(basename "$INSTANCE_PATH")"
EXPECTED_MARKDOWN="$INSTANCE_PATH/analysis_${TASK_NAME}.md"
PROMPT_FILE="/tmp/test_prompt_final.txt"
OUTPUT_LOG="/tmp/claude_final_output.txt"
MODEL="//cpfs01/models/Kimi-K2.5"

rm -f "$EXPECTED_MARKDOWN" "$PROMPT_FILE" "$OUTPUT_LOG"

cat > "$PROMPT_FILE" <<EOF
Please analyze the TerminalBench trajectories in this directory:

Instance Path: $INSTANCE_PATH

This directory contains multiple model trajectories (subdirectories like \`model__trial_id\`).
Each trajectory subdirectory has:
- \`agent/trajectory.json\` - Full conversation trace
- \`config.json\` - Configuration
- \`result.json\` - Execution results and metrics
- \`exception.txt\` - Error details (if failed)

Your task:
1. Explore the trajectory data with your file tools.
2. Perform a cross-model comparative analysis.
3. Focus on performance differences, strategic variations, and model capabilities.
4. Save the complete markdown report to:
   $EXPECTED_MARKDOWN
5. After saving, return the same markdown content in your final response.
EOF

if [ "$MODEL" == "sonnet" ]; then
  export ANTHROPIC_BASE_URL="https://console.siflow.cn/siflow/auriga/litellm182/"
  export ANTHROPIC_AUTH_TOKEN="sk-g2Fiaif9vFqzDt6hnvozYg"
  export ANTHROPIC_API_KEY=""
  export CLAUDE_CODE_DISABLE_EXPERIMENTAL_BETAS=1
elif [ "$MODEL" == "MiniMax-M2.5" ]; then
  export ANTHROPIC_BASE_URL="https://siflow-longmen.siflow.cn/siflow/longmen/skyinfer/gji/minimax-m2-5/1/8000/"
  export ANTHROPIC_API_KEY="sk-siflow"
elif [ "$MODEL" == "//cpfs01/models/Kimi-K2.5" ]; then
  export ANTHROPIC_BASE_URL="http://gw-aszye4rq8xcwbvpxzu-vpc.cn-hangzhou.pai-eas.aliyuncs.com/api/predict/vllm_kimi_k25_cc/"
  export ANTHROPIC_AUTH_TOKEN="MGY2ZWU3MGM5OTk5ODg4N2QzYjRiMDdlNmM2ZjQ2YjZjMGVkNzBlNw=="
  export ANTHROPIC_API_KEY=""
fi

echo "Testing direct Claude CLI in print mode..."
(
  cd "$REPO_ROOT"
  PROMPT="$(cat "$PROMPT_FILE")"
  IS_SANDBOX=1 claude \
    --print \
    --no-session-persistence \
    --dangerously-skip-permissions \
    --add-dir "$INSTANCE_PATH" \
    --model "$MODEL" \
    "$PROMPT"
) 2>&1 | tee "$OUTPUT_LOG"

echo ""
echo "========================================="
echo "Checking results..."
echo "========================================="

if [ -f "$EXPECTED_MARKDOWN" ]; then
  echo "✓ SUCCESS!"
  ls -lh "$EXPECTED_MARKDOWN"
  echo ""
  echo "Markdown preview (first 40 lines):"
  sed -n '1,40p' "$EXPECTED_MARKDOWN"
else
  echo "✗ File not created"
  ls -la "$INSTANCE_PATH/" | grep analysis || echo "No analysis files"
  exit 1
fi
