#!/bin/bash
# ============================================
# Example: Using run_qa_agent.sh
# ============================================
#
# 这个示例展示如何使用 run_qa_agent.sh 生成高质量的 Q&A 数据
#

# 切换到 examples 目录
cd "$(dirname "$0")"

# ============================================
# 示例 1: 基本用法
# ============================================
echo "Example 1: Basic Q&A Generation"
echo "================================"
echo ""

INPUT_FILE="sample_qa_input.jsonl" \
OUTPUT_FILE="output_qa_basic.jsonl" \
AGENTS_DIR="../agents" \
SKILLS_DIR="../skills" \
WORKERS=2 \
bash run_qa_agent.sh

echo ""
echo ""

# ============================================
# 示例 2: 自定义 Agent 和 Skills
# ============================================
echo "Example 2: Custom Agent and Skills"
echo "==================================="
echo ""

INPUT_FILE="sample_qa_input.jsonl" \
OUTPUT_FILE="output_qa_custom.jsonl" \
AGENT_NAME="qa-expert" \
AGENTS_DIR="../agents" \
SKILLS="enhanced-response-generation,data-validator" \
SKILLS_DIR="../skills" \
WORKERS=2 \
bash run_qa_agent.sh

echo ""
echo ""

# ============================================
# 示例 3: 使用不同的 CLI 模型
# ============================================
echo "Example 3: Different CLI Model"
echo "==============================="
echo ""

INPUT_FILE="sample_qa_input.jsonl" \
OUTPUT_FILE="output_qa_opus.jsonl" \
AGENTS_DIR="../agents" \
SKILLS_DIR="../skills" \
CLI_MODEL="opus" \
WORKERS=2 \
bash run_qa_agent.sh

echo ""
echo ""

# ============================================
# 示例 4: 完整配置
# ============================================
echo "Example 4: Full Configuration"
echo "=============================="
echo ""

INPUT_FILE="sample_qa_input.jsonl" \
OUTPUT_FILE="output_qa_full.jsonl" \
BACKEND="cli" \
TASK="query_response" \
AGENT_NAME="qa-expert" \
AGENTS_DIR="../agents" \
SKILLS="enhanced-response-generation" \
SKILLS_DIR="../skills" \
CLI_CMD="claude" \
CLI_MODEL="sonnet" \
CLI_TIMEOUT=600 \
WORKERS=4 \
MAX_RETRIES=3 \
PROGRESS_THRESHOLD=100 \
SPLIT_MAX_LINES=10000 \
bash run_qa_agent.sh

echo ""
echo "All examples completed!"
