---
name: trajectory-analysis
description: Comparative trajectory analysis capabilities for cross-model evaluation
allowed-tools: [Glob, Read, Write]
---

# Trajectory Comparative Analysis Skill

This skill provides structured capabilities for comparative analysis of TerminalBench trajectory data across multiple models. It includes utilities and patterns for identifying performance differences, strategic variations, and model capability insights.

## CRITICAL: File Save Requirement

**YOU MUST save your analysis as a markdown file** in the instance directory:
- **Filename**: `analysis_{task_name}.md` (e.g., `analysis_adaptive-rejection-sampler.md`)
- **Location**: Same directory as the instance path you're analyzing
- **Tool**: Use the `Write` tool to save the file
- **Format**: Complete markdown report with all sections

Example:
```bash
# If analyzing: /path/to/adaptive-rejection-sampler/
# Save to: /path/to/adaptive-rejection-sampler/analysis_adaptive-rejection-sampler.md
Write(file_path="/path/to/adaptive-rejection-sampler/analysis_adaptive-rejection-sampler.md", content="your markdown report")
```

**This is mandatory** - the analysis must be saved for future reference.

## Core Capabilities

### 1. Multi-Model Data Aggregation

Collect and structure data from multiple model trajectories:
- Use `Glob` to find all trajectory directories: `{instance_path}/*/agent/trajectory.json`
- Use `Read` to load JSON files from each model
- Extract comparable metrics (time, tokens, steps, rewards)
- Build unified timeline for comparison
- Identify common checkpoints across executions

### 2. Performance Comparison

Quantitative model comparison:
- **Success rate**: Which models completed the task?
- **Reward scores**: How well did they perform?
- **Efficiency metrics**: Token/time/step consumption
- **Quality assessment**: For successful models, compare solution quality

### 3. Strategic Pattern Recognition

Identify and categorize strategic approaches:
- **Systematic explorers**: Read docs → plan → implement
- **Trial-and-error iterators**: Try → fail → adjust → retry
- **Direct implementers**: Minimal exploration → immediate action
- **Hybrid approaches**: Mixed strategies

### 4. Differential Analysis

Identify what distinguishes models:
- **Success factors**: What do successful models have in common?
- **Failure patterns**: What causes failures?
- **Efficiency drivers**: What makes some models faster?
- **Quality indicators**: What produces better solutions?

### 5. Capability Profiling

Build model capability profiles:
- **Strengths**: What each model excels at
- **Weaknesses**: Where each model struggles
- **Task-fit**: Which models suit which task types
- **Relative positioning**: How models compare to each other

## Analysis Templates

### Quick Comparison Template

```markdown
# {task_name} - Model Comparison

## Results Summary
- ✅ Succeeded: {model1}, {model2} (rewards: X.X, Y.Y)
- ❌ Failed: {model3}, {model4} (reasons: timeout, error)

## Key Differentiator
{The main factor that separated success from failure}

## Recommendation
Best model for this task: {model} - {reason}
```

### Detailed Comparative Template

```markdown
# Cross-Model Analysis: {task_name}

## Performance Table
| Model | Status | Reward | Time | Steps | Tokens | Strategy |
|-------|--------|--------|------|-------|--------|----------|
| ... | ... | ... | ... | ... | ... | ... |

## Strategic Comparison
- **Successful models**: {common approach}
- **Failed models**: {common mistakes}

## Efficiency Ranking
1. {model}: {metric}
2. {model}: {metric}

## Recommendations
- **Best overall**: {model} - {reason}
- **Best for speed**: {model} - {reason}
- **Avoid**: {model} - {reason}
```

## Comparison Dimensions

### Performance Dimensions
1. **Success/failure**: Binary outcome
2. **Reward score**: Quantitative quality (0-1 scale typically)
3. **Execution time**: Wall-clock duration
4. **Token consumption**: Total input + output tokens
5. **Step count**: Number of conversation turns
6. **Completion rate**: Percentage of requirements met

### Strategic Dimensions
1. **Initial approach**: How did the model start?
2. **Problem decomposition**: How was task broken down?
3. **Tool selection**: Which tools were prioritized?
4. **Error recovery**: How were failures handled?
5. **Adaptation**: Did strategy evolve during execution?
6. **Verification**: How was success validated?

### Efficiency Dimensions
1. **Token efficiency**: Reward per token
2. **Time efficiency**: Reward per second
3. **Step efficiency**: Reward per conversation turn
4. **Redundancy rate**: Percentage of repeated/wasted actions
5. **Tool diversity**: Unique tools / total tool calls

## Common Patterns Library

### Success Patterns

#### Pattern: Systematic Documentation-First
```
Read(requirements) → Read(docs) → Plan → Implement → Test → Verify
```
**Models exhibiting**: {list}
**Success rate**: High
**Efficiency**: Medium (thorough but slower)

#### Pattern: Iterative Refinement
```
Quick implementation → Test → Fix errors → Retest → Refine
```
**Models exhibiting**: {list}
**Success rate**: Medium-high
**Efficiency**: High (fast iterations)

#### Pattern: Exploration-Heavy
```
Extensive file reading → Pattern analysis → Careful implementation
```
**Models exhibiting**: {list}
**Success rate**: High
**Efficiency**: Low (many exploratory steps)

### Failure Patterns

#### Pattern: Premature Implementation
```
Skip docs → Implement based on assumptions → Fail → Confused recovery
```
**Models exhibiting**: {list}
**Failure reason**: Misunderstood requirements
**Preventable**: Yes

#### Pattern: Inefficient Looping
```
Try action → Fail → Retry same action → Fail → Repeat until timeout
```
**Models exhibiting**: {list}
**Failure reason**: Not learning from errors
**Preventable**: Yes

#### Pattern: Tool Misuse
```
Use wrong tool → Get unhelpful result → Continue with wrong tool
```
**Models exhibiting**: {list}
**Failure reason**: Poor tool selection
**Preventable**: Yes

#### Pattern: Scope Creep
```
Start task → Get distracted by tangent → Lose focus → Timeout
```
**Models exhibiting**: {list}
**Failure reason**: Poor focus management
**Preventable**: Yes

## Comparison Metrics Reference

### Efficiency Metrics

**Token Efficiency** = Reward / Total Tokens
- Higher is better
- Measures solution quality per unit cost
- Best for cost-sensitive deployments

**Time Efficiency** = Reward / Duration (seconds)
- Higher is better
- Measures solution quality per unit time
- Best for latency-sensitive applications

**Step Efficiency** = Reward / Total Steps
- Higher is better
- Measures solution quality per interaction
- Correlates with conceptual efficiency

### Quality Metrics (for successful models)

**Completeness Score** = Requirements Met / Total Requirements
- 0-1 scale
- Measures thoroughness
- Distinguishes partial from complete solutions

**Code Quality Score** = Subjective 1-5 rating
- Based on: readability, correctness, maintainability
- Requires manual code inspection
- Separates working from elegant solutions

**Robustness Score** = Edge Cases Handled / Total Edge Cases
- 0-1 scale
- Measures solution generality
- Important for production deployments

### Reliability Metrics (across multiple tasks)

**Success Rate** = Successful Attempts / Total Attempts
- 0-1 scale
- Measures consistency
- Best indicator of general capability

**Mean Time To Success** = Average duration for successful attempts
- Lower is better
- Measures reliable speed
- Excludes failed attempts

**Consistency Score** = 1 - (StdDev of rewards across attempts)
- 0-1 scale (higher is better)
- Measures predictability
- Important for production reliability

## Analysis Heuristics

### Identifying Success Factors

**If all successful models share X, but no failed models have X**:
→ X is likely a critical success factor

**If successful models are diverse in approach**:
→ Multiple viable strategies exist for this task

**If one model succeeds while similar models fail**:
→ Look for subtle differences in execution, not just strategy

### Identifying Failure Factors

**If all failed models share Y, but no successful models have Y**:
→ Y is likely a failure-inducing pattern

**If failures happen at similar steps across models**:
→ Task has a critical difficulty spike at that point

**If failures are diverse in type**:
→ Task is broadly challenging, not just in one dimension

### Assessing Task Quality

**If success rate < 30%**:
→ Task may be too difficult or poorly specified

**If success rate > 90%**:
→ Task may be too easy or not discriminative enough

**If all models timeout**:
→ Task time limit may be too restrictive

**If all models fail on same subtask**:
→ Subtask may be ambiguous or impossible

## Comparative Workflow

### 1. Data Collection Phase
- Use `Glob("{instance_path}/*/agent/trajectory.json")` to find all trajectories
- Use `Read()` to load trajectory.json, config.json, result.json for each model
- Extract metrics for each (time, tokens, steps, reward)
- Parse execution flows and timelines
- Identify outcomes (success/fail/timeout/error)

### 2. Categorization Phase
- Group models by outcome
- Group models by strategy type
- Group models by efficiency tier
- Identify outliers (surprising results)

### 3. Comparison Phase
- Compare successful models: what's common?
- Compare failed models: what went wrong?
- Compare success vs failure: what's the difference?
- Compare efficient vs inefficient: what drives efficiency?

### 4. Pattern Recognition Phase
- Identify strategic patterns
- Identify failure modes
- Identify efficiency patterns
- Identify quality patterns

### 5. Insight Synthesis Phase
- What do results reveal about model capabilities?
- Which models are best suited for this task type?
- What factors most influence success?
- What recommendations follow?

### 6. Report Writing Phase
- Generate complete markdown report
- Include all comparison sections
- Add performance tables and visualizations

### 7. **File Save Phase (MANDATORY)**
- Determine task name from instance path
- Create filename: `analysis_{task_name}.md`
- Use `Write` tool to save the markdown report to the instance directory
- Verify file was saved successfully

**Example save command**:
```python
Write(
    file_path="{instance_path}/analysis_{task_name}.md",
    content="# Cross-Model Trajectory Analysis: {task_name}\n\n..."
)
```

## Comparison Visualizations (Text-Based)

### Performance Distribution
```
Reward Distribution:
[model1] ████████████████████ 1.0
[model2] ██████████░░░░░░░░░░ 0.5
[model3] ░░░░░░░░░░░░░░░░░░░░ 0.0 (failed)
[model4] ░░░░░░░░░░░░░░░░░░░░ 0.0 (timeout)
```

### Time Efficiency Ranking
```
1. model1:  1.0 reward / 120s = 0.0083 reward/sec
2. model2:  1.0 reward / 245s = 0.0041 reward/sec
3. model3:  0.5 reward / 180s = 0.0028 reward/sec
4. model4:  0.0 reward / 900s = 0.0000 reward/sec
```

### Strategy Matrix
```
                Systematic | Iterative | Direct
Successful         2            1          0
Failed             0            1          2
```

## Integration Notes

This skill works with:
- **trajectory_analyzer agent**: Provides comparative analysis framework
- **analyze_trajectory task**: Passes instance paths to the agent
- **All CLI tools**: Use Glob, Read, Write, Bash, etc. to explore and save data

**Workflow**:
1. Task provides instance path
2. Agent uses this skill to guide analysis
3. Agent uses `Glob` and `Read` to load trajectory files
4. Agent performs comparative analysis
5. **Agent uses `Write` to save markdown report** (mandatory!)
6. Agent returns markdown content to task

When using this skill, you have access to:
- All trajectory files via `Read` tool
- File discovery via `Glob` tool
- File system operations via `Bash` tool
- **File writing via `Write` tool** (use this to save your report!)
- All standard Claude Code tools

## Best Practices

### Do's
- ✓ **Always save your markdown report using the Write tool**
- ✓ Save to: `{instance_path}/analysis_{task_name}.md`
- ✓ Always compare on same metrics across all models
- ✓ Support claims with specific examples and numbers
- ✓ Quote representative message exchanges
- ✓ Consider task difficulty when evaluating performance
- ✓ Balance quantitative metrics with qualitative insights
- ✓ Provide actionable model selection guidance

### Don'ts
- ✗ Cherry-pick data to favor certain models
- ✗ Make vague comparisons without specifics
- ✗ Focus only on winners or only on losers
- ✗ Ignore context and constraints
- ✗ Over-generalize from single instance
- ✗ Neglect efficiency considerations

## Example Insights

### Good Comparative Insight
> "Model A and B both succeeded, but A used 12K tokens in 180s while B used 28K tokens in 450s. A's efficiency advantage came from reading documentation first (steps 1-8) rather than trial-and-error. B's iterative approach required 3 failed attempts before succeeding."

### Bad Comparative Insight
> "Model A was better than Model B."

### Good Recommendation
> "For tasks requiring file manipulation and testing, we recommend Model A (success rate: 85%, avg time: 240s) over Model C (success rate: 45%, avg time: 780s). Model A's systematic documentation-first approach is well-suited to tasks with clear requirements."

### Bad Recommendation
> "Use Model A."

## Remember

The goal of comparative analysis is to:
1. **Quantify differences** between models on objective metrics
2. **Explain differences** by identifying strategic and execution patterns
3. **Predict performance** on similar tasks based on observed patterns
4. **Guide selection** by matching model strengths to task requirements

Every comparison should reveal something actionable about when and why to choose one model over another.
