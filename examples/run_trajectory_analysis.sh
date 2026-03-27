#!/bin/bash
# Example script to analyze TerminalBench trajectories with cross-model comparison
# Usage: bash examples/run_trajectory_analysis.sh

set -e

# Configuration
TRAJECTORY_BASE_DIR="/volume/pt-coder/users/tuney/posttrain_data/tb-traj-reorganized-v2"
INPUT_FILE="$TRAJECTORY_BASE_DIR/traj_input.jsonl"
OUTPUT_FILE="$TRAJECTORY_BASE_DIR/traj_output.jsonl"
WORKERS=4
CLI_TIMEOUT=1200  # 20 minutes per instance (multiple models)

echo "=== TerminalBench Cross-Model Trajectory Analysis ==="
echo ""
echo "Input file: $INPUT_FILE"
echo "Output file: $OUTPUT_FILE"
echo "Workers: $WORKERS"
echo "Timeout per instance: ${CLI_TIMEOUT}s"
echo ""

# Check if input file exists
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file not found at $INPUT_FILE"
    echo "Generating input file..."

    ls -d "$TRAJECTORY_BASE_DIR"/*/ | sed 's|/$||' | \
        awk '{print "{\"instance_path\": \"" $0 "\"}"}' > "$INPUT_FILE"

    echo "Generated $INPUT_FILE with $(wc -l < "$INPUT_FILE") instances"
fi

# Show sample
echo "Sample instances:"
head -3 "$INPUT_FILE"
echo "..."
echo ""

# Confirm
TOTAL_INSTANCES=$(wc -l < "$INPUT_FILE")
echo "Total instances to analyze: $TOTAL_INSTANCES"
echo "Estimated time: $((TOTAL_INSTANCES * CLI_TIMEOUT / WORKERS / 60)) minutes"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Run analysis
echo "Starting cross-model trajectory analysis..."
cd /volume/pt-coder/users/tuney/Script/HyperDistill

# Only using skill, no custom agent needed
python run.py \
  --task analyze_trajectory \
  --backend cli \
  --skills trajectory-analysis \
  --skills-dir ./.claude/skills \
  -i "$INPUT_FILE" \
  -o "$OUTPUT_FILE" \
  -w "$WORKERS" \
  --cli-timeout "$CLI_TIMEOUT"

echo ""
echo "=== Analysis Complete ==="
echo "Results written to: $OUTPUT_FILE"
echo "Markdown reports saved to task directories as: analysis_<task_name>.md"
echo ""
echo "Example commands:"
echo "  # View output summary"
echo "  cat $OUTPUT_FILE | jq '.task_name, .analysis_content' | head -20"
echo ""
echo "  # Read a specific analysis"
echo "  cat $TRAJECTORY_BASE_DIR/adaptive-rejection-sampler/analysis_adaptive-rejection-sampler.md"
