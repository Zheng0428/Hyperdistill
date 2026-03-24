#!/bin/bash
# ============================================
# Q&A Generation with Agent & Skill System
# ============================================
#
# 使用 CLI Backend + QA Expert Agent + Enhanced Response Generation Skill
# 生成高质量的问答数据
#
# 使用方式:
#   1. 修改下方配置区域的变量
#   2. 运行: bash run_qa_agent.sh
#
# 环境变量覆盖:
#   INPUT_FILE=/path/to/input.jsonl OUTPUT_FILE=/path/to/output.jsonl bash run_qa_agent.sh
#
# ============================================

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# 配置区域（可通过环境变量覆盖）
# ============================================

# Backend 类型: cli (使用 claude subprocess)
BACKEND=${BACKEND:-"cli"}

# 任务类型
TASK=${TASK:-"query_response"}

# Agent 配置
AGENT_NAME=${AGENT_NAME:-"qa-expert"}
AGENTS_DIR=${AGENTS_DIR:-"./agents"}

# Skill 配置
SKILLS=${SKILLS:-"enhanced-response-generation"}
SKILLS_DIR=${SKILLS_DIR:-"./skills"}

# CLI 配置
CLI_CMD=${CLI_CMD:-"claude"}
CLI_MODEL=${CLI_MODEL:-"sonnet"}  # 会被 agent 的 model 字段覆盖（如果有）
CLI_TIMEOUT=${CLI_TIMEOUT:-600}

# 输入输出文件
INPUT_FILE=${INPUT_FILE:-""}
OUTPUT_FILE=${OUTPUT_FILE:-""}

# 并发配置
WORKERS=${WORKERS:-4}  # CLI backend 默认 4 个并发

# 进度控制
PROGRESS_THRESHOLD=${PROGRESS_THRESHOLD:-100}
SPLIT_MAX_LINES=${SPLIT_MAX_LINES:-100000}

# 数据过滤
MAX_TEXT_LENGTH=${MAX_TEXT_LENGTH:-""}

# 重试配置
MAX_RETRIES=${MAX_RETRIES:-3}

# ============================================
# 参数校验
# ============================================

if [ -z "$INPUT_FILE" ]; then
    echo "Error: INPUT_FILE is not set"
    echo ""
    echo "Usage:"
    echo "  INPUT_FILE=/path/to/input.jsonl OUTPUT_FILE=/path/to/output.jsonl bash run_qa_agent.sh"
    echo ""
    echo "Input file format (JSONL):"
    echo '  {"id": "1", "query": "What is async/await in JavaScript?"}'
    echo '  {"id": "2", "query": "How does Python GIL work?"}'
    echo ""
    exit 1
fi

if [ -z "$OUTPUT_FILE" ]; then
    echo "Error: OUTPUT_FILE is not set"
    exit 1
fi

if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file does not exist: $INPUT_FILE"
    exit 1
fi

# 检查 agents 和 skills 目录
if [ ! -d "$AGENTS_DIR" ]; then
    echo "Error: Agents directory does not exist: $AGENTS_DIR"
    exit 1
fi

if [ ! -d "$SKILLS_DIR" ]; then
    echo "Error: Skills directory does not exist: $SKILLS_DIR"
    exit 1
fi

# 检查 agent 文件
AGENT_FILE="${AGENTS_DIR}/${AGENT_NAME}.md"
if [ ! -f "$AGENT_FILE" ]; then
    echo "Error: Agent file does not exist: $AGENT_FILE"
    echo ""
    echo "Available agents in ${AGENTS_DIR}:"
    ls -1 "${AGENTS_DIR}"/*.md 2>/dev/null | xargs -n 1 basename | sed 's/.md$//' | sed 's/^/  - /'
    echo ""
    exit 1
fi

# 检查 skill 文件（支持多个 skills，逗号分隔）
IFS=',' read -ra SKILL_ARRAY <<< "$SKILLS"
for skill in "${SKILL_ARRAY[@]}"; do
    skill=$(echo "$skill" | xargs)  # trim whitespace
    SKILL_FILE="${SKILLS_DIR}/${skill}.md"
    if [ ! -f "$SKILL_FILE" ]; then
        echo "Error: Skill file does not exist: $SKILL_FILE"
        echo ""
        echo "Available skills in ${SKILLS_DIR}:"
        ls -1 "${SKILLS_DIR}"/*.md 2>/dev/null | xargs -n 1 basename | sed 's/.md$//' | sed 's/^/  - /'
        echo ""
        exit 1
    fi
done

# 创建输出目录
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# ============================================
# 显示配置信息
# ============================================

echo ""
echo "============================================"
echo "Q&A Generation with Agent & Skill System"
echo "============================================"
echo ""
echo "Configuration:"
echo "  Backend:       ${BACKEND}"
echo "  Task:          ${TASK}"
echo "  Agent:         ${AGENT_NAME} (from ${AGENTS_DIR})"
echo "  Skills:        ${SKILLS} (from ${SKILLS_DIR})"
echo "  CLI Command:   ${CLI_CMD}"
echo "  CLI Model:     ${CLI_MODEL}"
echo "  CLI Timeout:   ${CLI_TIMEOUT}s"
echo "  Workers:       ${WORKERS}"
echo "  Max Retries:   ${MAX_RETRIES}"
echo ""
echo "Input/Output:"
echo "  Input:         ${INPUT_FILE}"
echo "  Output:        ${OUTPUT_FILE}"
echo "  Progress:      ${PROGRESS_THRESHOLD}%"
echo "  Split Lines:   ${SPLIT_MAX_LINES}"
echo ""

# 统计输入文件行数
if command -v wc &> /dev/null; then
    total_lines=$(wc -l < "$INPUT_FILE" 2>/dev/null || echo "unknown")
    echo "  Input Lines:   ${total_lines}"
    echo ""
fi

echo "============================================"
echo ""

# ============================================
# 确认是否继续
# ============================================

if [ -f "$OUTPUT_FILE" ]; then
    echo "Notice: Output file already exists: $OUTPUT_FILE"
    echo "        The pipeline will automatically resume from where it left off."
    echo ""
fi

# 如果是交互式终端，询问是否继续
if [ -t 0 ]; then
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    echo ""
fi

# ============================================
# 运行蒸馏任务
# ============================================

echo "Starting Q&A generation..."
echo ""

# 构建命令
CMD="python3 -u run.py \
    --task $TASK \
    --backend $BACKEND \
    --agent-name $AGENT_NAME \
    --agents-dir $AGENTS_DIR \
    --skills $SKILLS \
    --skills-dir $SKILLS_DIR \
    --cli-cmd $CLI_CMD \
    --cli-model $CLI_MODEL \
    --cli-timeout $CLI_TIMEOUT \
    -i $INPUT_FILE \
    -o $OUTPUT_FILE \
    -w $WORKERS \
    --max-retries $MAX_RETRIES \
    --split-max-lines $SPLIT_MAX_LINES \
    --progress-threshold $PROGRESS_THRESHOLD"

# 可选参数
if [ -n "$MAX_TEXT_LENGTH" ]; then
    CMD="$CMD --max-text-length $MAX_TEXT_LENGTH"
fi

# 运行
eval $CMD

EXIT_CODE=$?

echo ""
echo "============================================"

if [ $EXIT_CODE -eq 0 ]; then
    echo "✓ Q&A Generation Completed Successfully!"
    echo ""
    echo "Output file: ${OUTPUT_FILE}"

    # 统计输出文件
    if [ -f "$OUTPUT_FILE" ] && command -v wc &> /dev/null; then
        output_lines=$(wc -l < "$OUTPUT_FILE" 2>/dev/null || echo "unknown")
        echo "Output lines: ${output_lines}"
    fi

    # 检查分片文件
    OUTPUT_BASE="${OUTPUT_FILE%.jsonl}"
    PART_FILES=$(ls -1 "${OUTPUT_BASE}.part"*.jsonl 2>/dev/null | wc -l)
    if [ "$PART_FILES" -gt 0 ]; then
        echo "Part files:   ${PART_FILES}"
        echo ""
        echo "To merge all parts into a single file:"
        echo "  cat ${OUTPUT_BASE}.part*.jsonl > ${OUTPUT_FILE}.merged"
    fi
else
    echo "✗ Q&A Generation Failed (exit code: ${EXIT_CODE})"
    echo ""
    echo "Check the logs above for error details."
fi

echo "============================================"
echo ""

exit $EXIT_CODE
