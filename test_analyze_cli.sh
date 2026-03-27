#!/bin/bash
# Test analyze_trajectory task with CLI backend
# This task REQUIRES CLI backend because it uses tools (Glob, Read, etc.)

set -e

# Configuration
TEST_INSTANCE="/volume/pt-coder/users/tuney/posttrain_data/tb-traj-reorganized-v2/adaptive-rejection-sampler"
TEST_INPUT="/tmp/test_analyze_cli_input.jsonl"
TEST_OUTPUT="/tmp/test_analyze_cli_output.jsonl"

echo "=== Testing analyze_trajectory with CLI Backend ==="
echo ""
echo "Test instance: $TEST_INSTANCE"
echo "Test input: $TEST_INPUT"
echo "Test output: $TEST_OUTPUT"
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

# Run analysis with CLI backend
echo "Starting analysis with CLI backend (claude)..."
cd /volume/pt-coder/users/tuney/Script/HyperDistill

python run.py \
  --task analyze_trajectory \
  --backend cli \
  --cli-model sonnet \
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
    fi

    if grep -q "analysis_content" "$OUTPUT_FOUND"; then
        echo "✓ analysis_content field present"
        CONTENT_LENGTH=$(cat "$OUTPUT_FOUND" | jq -r '.analysis_content | length')
        echo "  Content length: $CONTENT_LENGTH characters"
    fi

    if grep -q "analysis_thinking" "$OUTPUT_FOUND"; then
        echo "✓ analysis_thinking field present"
        THINKING_LENGTH=$(cat "$OUTPUT_FOUND" | jq -r '.analysis_thinking | length')
        echo "  Thinking length: $THINKING_LENGTH characters"
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
        echo ""
        echo "Markdown file preview (first 20 lines):"
        head -20 "$MARKDOWN_FILE"
    else
        echo "✗ Expected markdown file not found: $MARKDOWN_FILE"
    fi
else
    echo "✗ No output files created"
    exit 1
fi

echo ""
echo "Test completed successfully!"
