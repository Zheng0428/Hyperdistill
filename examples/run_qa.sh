#!/bin/bash

# 多轮对话蒸馏 - 所有轮次版本
# 基于 distill_pipeline 框架

INPUT_FILE=/volume/pt-coder/users/tuney/pretrain_data/stackoverflow/rewrite_qa/extracted_questions_parsed_10000.jsonl
OUTPUT_FILE=/volume/pt-coder/users/tuney/pretrain_data/stackoverflow/rewrite_qa/extracted_questions_parsed_10000.distilled.jsonl
CONFIG_FILE=/volume/pt-coder/users/tuney/Script/distill_pipeline/configs/config_glm.json

# 最大轮次限制（可选，不设置则处理所有轮次）
MAX_TURNS=${MAX_TURNS:-}

# 创建输出目录
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

echo "============================================"
echo "QA Distillation"
echo "============================================"
echo "INPUT_FILE: ${INPUT_FILE}"
echo "OUTPUT_FILE: ${OUTPUT_FILE}"
echo "CONFIG: ${CONFIG_FILE}"
echo "============================================"
echo ""

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "✗ Error: Input file does not exist: $INPUT_FILE"
    exit 1
fi

# 统计输入文件行数
total_lines=$(wc -l < "$INPUT_FILE")
echo "[INFO] Input file: ${INPUT_FILE}"
echo "[INFO] Total lines: ${total_lines}"
echo ""

# 运行蒸馏
cd /volume/pt-coder/users/tuney/Script/distill_pipeline

python run.py \
    --task query_response \
    --backend api \
    --provider glm \
    --config "$CONFIG_FILE" \
    -i "$INPUT_FILE" \
    -o "$OUTPUT_FILE"

echo ""
echo "[DONE] Finished QA distillation"
echo "============================================"
echo "Output file: ${OUTPUT_FILE}"
echo "============================================"
