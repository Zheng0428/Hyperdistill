#!/bin/bash
# ============================================
# Distill Pipeline - 通用启动脚本
# ============================================
#
# 使用方式:
#   1. 修改下方配置区域的变量
#   2. 运行: bash run.sh
#
# 环境变量覆盖:
#   TASK=code_to_question PROVIDER=default CONFIG_FILE=my_config.json bash run.sh
#
# ============================================

# 切换到脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# ============================================
# 配置区域（可通过环境变量覆盖）
# ============================================

# 任务类型: query_response, code_to_question, text_to_response, 或 YAML 文件路径
TASK=${TASK:-"query_response"}

# API Provider: kimi, dpsk, glm, default
PROVIDER=${PROVIDER:-"default"}

# API 配置文件
CONFIG_FILE=${CONFIG_FILE:-"configs/config.json"}

# 输入输出文件
INPUT_FILE=${INPUT_FILE:-""}
OUTPUT_FILE=${OUTPUT_FILE:-""}

# 生成参数
TEMPERATURE=${TEMPERATURE:-1.0}
TOP_P=${TOP_P:-0.95}
WORKERS=${WORKERS:-""}  # 留空则自动计算

# 进度控制
PROGRESS_THRESHOLD=${PROGRESS_THRESHOLD:-95}
SPLIT_MAX_LINES=${SPLIT_MAX_LINES:-100000}

# 数据过滤
MAX_TEXT_LENGTH=${MAX_TEXT_LENGTH:-""}

# 是否启用定期健康检查（1=启用，0=禁用）
ENABLE_PERIODIC_HEALTH_CHECK=${ENABLE_PERIODIC_HEALTH_CHECK:-0}

# ============================================
# 参数校验
# ============================================

if [ -z "$INPUT_FILE" ]; then
    echo "Error: INPUT_FILE is not set"
    echo "Usage: INPUT_FILE=/path/to/input.jsonl OUTPUT_FILE=/path/to/output.jsonl bash run.sh"
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

if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file does not exist: $CONFIG_FILE"
    exit 1
fi

# 创建输出目录
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# ============================================
# Step 1: 健康检查
# ============================================

echo ""
echo "Step 1: Running health check..."
echo ""

python3 -u run.py --health-check --config "$CONFIG_FILE"

if [ $? -ne 0 ]; then
    echo ""
    echo "Error: Health check failed!"
    exit 1
fi

# 自动生成 active config 路径
CONFIG_STEM="${CONFIG_FILE%.json}"
ACTIVE_CONFIG="${CONFIG_STEM}.active.json"

if [ ! -f "$ACTIVE_CONFIG" ]; then
    echo "Error: Active config not found: $ACTIVE_CONFIG"
    exit 1
fi

# ============================================
# Step 2: 定期健康检查（可选）
# ============================================

HEALTH_CHECK_PID=""

if [ "$ENABLE_PERIODIC_HEALTH_CHECK" = "1" ]; then
    echo ""
    echo "Starting background health check (every 30 minutes)..."
    echo ""

    (
        while true; do
            sleep 1800
            echo ""
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running periodic health check..."
            python3 -u run.py --health-check --config "$CONFIG_FILE"
            if [ $? -eq 0 ]; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Health check OK"
            else
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] Health check FAILED"
            fi
            echo ""
        done
    ) &

    HEALTH_CHECK_PID=$!
    echo "Health check service started (PID: $HEALTH_CHECK_PID)"
else
    echo ""
    echo "Periodic health check: DISABLED"
    echo ""
fi

# 退出时清理
cleanup() {
    if [ -n "$HEALTH_CHECK_PID" ]; then
        echo ""
        echo "Stopping health check service (PID: $HEALTH_CHECK_PID)..."
        kill $HEALTH_CHECK_PID 2>/dev/null
        wait $HEALTH_CHECK_PID 2>/dev/null
        echo "Health check service stopped"
    fi
}

trap cleanup EXIT INT TERM

# ============================================
# Step 3: 运行蒸馏任务
# ============================================

echo ""
echo "============================================"
echo "Step 2: Running distillation task"
echo "============================================"
echo "TASK:     ${TASK}"
echo "PROVIDER: ${PROVIDER}"
echo "CONFIG:   ${ACTIVE_CONFIG}"
echo "INPUT:    ${INPUT_FILE}"
echo "OUTPUT:   ${OUTPUT_FILE}"
echo "TEMP:     ${TEMPERATURE}"
echo "TOP_P:    ${TOP_P}"
echo "PROGRESS: ${PROGRESS_THRESHOLD}%"
echo "============================================"
echo ""

# 统计输入文件行数
total_lines=$(wc -l < "$INPUT_FILE")
echo "[INFO] Input lines: ${total_lines}"
echo ""

# 构建命令
CMD="python3 -u run.py \
    --task $TASK \
    --provider $PROVIDER \
    --config $ACTIVE_CONFIG \
    -i $INPUT_FILE \
    -o $OUTPUT_FILE \
    --temperature $TEMPERATURE \
    --top_p $TOP_P \
    --split-max-lines $SPLIT_MAX_LINES \
    --progress-threshold $PROGRESS_THRESHOLD"

# 可选参数
if [ -n "$WORKERS" ]; then
    CMD="$CMD -w $WORKERS"
fi

if [ -n "$MAX_TEXT_LENGTH" ]; then
    CMD="$CMD --max-text-length $MAX_TEXT_LENGTH"
fi

# 运行
eval $CMD

echo ""
echo "============================================"
echo "Done!"
echo "Output: ${OUTPUT_FILE}"
echo "============================================"
