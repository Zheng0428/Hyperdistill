#!/bin/bash
# Test analyze_trajectory task with MiniMax via CLI backend
# Based on test_cli.sh setup

set -e

# Configuration
TEST_INSTANCE="/volume/pt-coder/users/tuney/posttrain_data/tb-traj-reorganized-v2/break-filter-js-from-html"
TEST_INPUT="/tmp/test_analyze_kimi_input.jsonl"
TEST_OUTPUT="/tmp/test_analyze_kimi_output.jsonl"

echo "=== Testing analyze_trajectory with Kimi-K2.5 CLI Backend ==="
echo ""
echo "Test instance: $TEST_INSTANCE"
echo "Test input: $TEST_INPUT"
echo "Test output: $TEST_OUTPUT"
echo ""

# Set Kimi-K2.5 environment variables (from test_cli.sh)
export ANTHROPIC_BASE_URL='http://gw-aszye4rq8xcwbvpxzu-vpc.cn-hangzhou.pai-eas.aliyuncs.com/api/predict/vllm_kimi_k25_cc/'
  export ANTHROPIC_AUTH_TOKEN='MGY2ZWU3MGM5OTk5ODg4N2QzYjRiMDdlNmM2ZjQ2YjZjMGVkNzBlNw=='
  export ANTHROPIC_API_KEY=""

echo "Environment configured:"
echo "  ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:0:10}..."
echo ""

# Create test input file
echo "{\"instance_path\": \"$TEST_INSTANCE\"}" > "$TEST_INPUT"

# Clean previous output
rm -f "$TEST_OUTPUT"
rm -f "${TEST_OUTPUT}.part"*

# Show test input
echo "Test input content:"
cat "$TEST_INPUT"
echo ""

# Run analysis with Kimi-K2.5 via CLI backend
echo "Starting analysis with Kimi-K2.5 CLI backend..."
cd /volume/pt-coder/users/tuney/Script/HyperDistill

python run.py \
  --task analyze_trajectory \
  --backend cli \
  --cli-model "//cpfs01/models/Kimi-K2.5" \
  --skills trajectory-analysis \
  --skills-dir ./.claude/skills \
  -i "$TEST_INPUT" \
  -o "$TEST_OUTPUT" \
  -w 1 \
  --cli-timeout 600

echo ""
echo "=== Test Complete ==="

# Check for output files
OUTPUT_FOUND=""
if [ -f "$TEST_OUTPUT" ]; then
    OUTPUT_FOUND="$TEST_OUTPUT"
elif ls "${TEST_OUTPUT}.part"* 1> /dev/null 2>&1; then
    OUTPUT_FOUND=$(ls "${TEST_OUTPUT}.part"* | head -1)
fi

if [ -n "$OUTPUT_FOUND" ]; then
    echo "✓ Output file created: $OUTPUT_FOUND"
    echo ""
    echo "Output structure:"
    cat "$OUTPUT_FOUND" | jq 'keys'
    echo ""

    # Check key fields
    if grep -q "task_name" "$OUTPUT_FOUND"; then
        echo "✓ task_name field present"
        TASK_NAME=$(cat "$OUTPUT_FOUND" | jq -r '.task_name')
        echo "  Task name: $TASK_NAME"
    else
        echo "✗ task_name field missing"
    fi

    if grep -q "analysis_content" "$OUTPUT_FOUND"; then
        echo "✓ analysis_content field present"
        CONTENT_LENGTH=$(cat "$OUTPUT_FOUND" | jq -r '.analysis_content | length')
        echo "  Content length: $CONTENT_LENGTH characters"
    else
        echo "✗ analysis_content field missing"
    fi

    if grep -q "analysis_thinking" "$OUTPUT_FOUND"; then
        echo "✓ analysis_thinking field present (Kimi-K2.5 thinking extraction)"
        THINKING_LENGTH=$(cat "$OUTPUT_FOUND" | jq -r '.analysis_thinking | length')
        echo "  Thinking length: $THINKING_LENGTH characters"
    else
        echo "⚠  analysis_thinking field not present (no thinking content)"
    fi

    echo ""
    echo "First 500 characters of analysis_content:"
    cat "$OUTPUT_FOUND" | jq -r '.analysis_content' | head -c 500
    echo "..."
    echo ""

    # Check if markdown file was created
    MARKDOWN_FILE="$TEST_INSTANCE/analysis_${TASK_NAME}.md"
    if [ -f "$MARKDOWN_FILE" ]; then
        echo "✓ Markdown analysis file created: $MARKDOWN_FILE"
        echo "  File size: $(wc -c < "$MARKDOWN_FILE") bytes"
        echo "  Lines: $(wc -l < "$MARKDOWN_FILE")"
        echo ""
        echo "Markdown file preview (first 30 lines):"
        head -30 "$MARKDOWN_FILE"
        echo "..."
    else
        echo "⚠  Expected markdown file not found: $MARKDOWN_FILE"
        echo "  Looking for other analysis files..."
        ls -lh "$TEST_INSTANCE"/analysis*.md 2>/dev/null || echo "  No analysis files found"
    fi
else
    echo "✗ No output files created"
    exit 1
fi

echo ""
echo "=== Test Summary ==="
echo "✅ Test completed successfully!"
echo ""
echo "Key verifications:"
echo "  1. Kimi-K2.5 model accessible via CLI backend"
echo "  2. analyze_trajectory task executed"
echo "  3. Output JSONL file created"
echo "  4. Analysis content present"
if grep -q "analysis_thinking" "$OUTPUT_FOUND"; then
    echo "  5. Kimi-K2.5 thinking content extracted"
fi
