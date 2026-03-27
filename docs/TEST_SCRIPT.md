# Test Script Documentation

## Overview

`test_single.sh` 是一个通用的单条数据测试脚本，用于快速验证任务配置是否正确。

## 使用方式

### 1. 交互模式（推荐用于首次测试）

```bash
bash test_single.sh
```

脚本会逐步提示你输入：
- 任务名称
- Backend 类型（API 或 CLI）
- 相关配置参数
- 测试数据

### 2. 命令行模式（快速测试）

#### 测试 analyze_trajectory 任务

```bash
bash test_single.sh \
  --task analyze_trajectory \
  --backend cli \
  --skills trajectory-analysis \
  --instance /volume/pt-coder/users/tuney/posttrain_data/tb-traj-reorganized-v2/adaptive-rejection-sampler
```

#### 测试 query_response 任务（API backend）

```bash
bash test_single.sh \
  --task query_response \
  --backend api \
  --provider minimax \
  --config configs/config_minimax.json \
  --input '{"id": "test_1", "query": "What is Python?"}'
```

#### 测试 stackoverflow 任务（CLI backend）

```bash
bash test_single.sh \
  --task stackoverflow \
  --backend cli \
  --cli-model sonnet \
  --agent-name stackoverflow-enhancer \
  --skills enhanced-response-generation \
  --input '{"id": "test_1", "Post_Title": "How to sort a list?", "Post_Body": "I need to sort a Python list", "Answers": []}'
```

## 参数说明

### 通用参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--task` | 任务名称 | `analyze_trajectory` |
| `--backend` | 后端类型 | `api` 或 `cli` |
| `--input` | 自定义 JSON 输入 | `'{"id": "1", "query": "..."}'` |
| `-h, --help` | 显示帮助信息 | - |

### API Backend 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--provider` | Provider 名称 | `minimax`, `glm`, `kimi` |
| `--config` | 配置文件路径 | `configs/config_minimax.json` |

### CLI Backend 参数

| 参数 | 说明 | 示例 |
|------|------|------|
| `--cli-model` | 模型名称 | `sonnet` (默认) |
| `--skills` | Skill 名称（逗号分隔） | `trajectory-analysis` |
| `--agent-name` | Agent 名称（可选） | `stackoverflow-enhancer` |
| `--timeout` | 超时时间（秒） | `600` (默认) |

### 任务特定参数

| 参数 | 适用任务 | 说明 |
|------|----------|------|
| `--instance` | `analyze_trajectory` | Instance 目录路径 |

## 输出说明

### 成功时

脚本会显示：
- ✅ 执行时间
- 📄 输出 JSON（格式化显示）
- 📁 生成的文件（如 markdown）
- 📊 测试摘要

### 失败时

脚本会显示：
- ❌ 错误信息
- 📂 保留临时文件路径（用于调试）
- ⏱️ 执行时间

## 示例场景

### 场景 1: 快速测试 trajectory 分析配置

```bash
# 使用第一个 instance 进行测试
FIRST_INSTANCE=$(ls -d /volume/pt-coder/users/tuney/posttrain_data/tb-traj-reorganized-v2/*/ | head -1 | sed 's|/$||')

bash test_single.sh \
  --task analyze_trajectory \
  --backend cli \
  --skills trajectory-analysis \
  --instance "$FIRST_INSTANCE"
```

### 场景 2: 测试新的 task 实现

```bash
# 假设你刚实现了 my_new_task
bash test_single.sh \
  --task my_new_task \
  --backend cli \
  --input '{"id": "test", "data": "sample"}'
```

### 场景 3: 调试 API provider 配置

```bash
bash test_single.sh \
  --task query_response \
  --backend api \
  --provider glm \
  --config configs/config_glm.json \
  --input '{"id": "1", "query": "Hello"}'
```

## 高级用法

### 自定义输入文件

```bash
# 创建自定义输入
echo '{"instance_path": "/path/to/custom/instance"}' > my_test.jsonl

# 使用自定义输入
INPUT=$(cat my_test.jsonl)
bash test_single.sh \
  --task analyze_trajectory \
  --backend cli \
  --skills trajectory-analysis \
  --input "$INPUT"
```

### 保留临时文件用于调试

运行后选择保留临时文件（回答 'y'），然后：

```bash
# 查看输入
cat /tmp/tmp.xxxxx/test_input.jsonl

# 查看输出
cat /tmp/tmp.xxxxx/test_output.jsonl

# 重新运行相同配置
python run.py --task ... -i /tmp/tmp.xxxxx/test_input.jsonl -o /tmp/tmp.xxxxx/test_output.jsonl
```

## 故障排查

### 问题：任务失败但没有错误信息

**解决**: 检查临时文件目录，查看详细日志：
```bash
ls -la /tmp/tmp.*/
```

### 问题：CLI backend 超时

**解决**: 增加超时时间：
```bash
bash test_single.sh --task ... --timeout 1200
```

### 问题：找不到 skill 或 agent

**解决**: 确保文件存在：
```bash
find .claude/skills -mindepth 1 -maxdepth 1 -type d
ls .claude/agents/
```

## 最佳实践

1. **首次使用交互模式**: 熟悉参数后再用命令行模式
2. **从简单任务开始**: 先测试 `query_response`，再测试复杂任务
3. **保存成功的命令**: 把有效的命令保存到脚本中
4. **逐步增加复杂度**: 先测基础功能，再加 `.claude/skills` / `.claude/agents`
5. **查看生成的文件**: 不只看 JSON 输出，也要检查生成的 markdown 等文件

## 集成到开发流程

```bash
# 1. 实现新 task
vim hyperdistill/tasks/my_task.py

# 2. 测试单条数据
bash test_single.sh --task my_task --backend cli --input '...'

# 3. 确认输出符合预期

# 4. 批量运行
python run.py --task my_task -i input.jsonl -o output.jsonl -w 8
```

## 与其他工具对比

| 工具 | 用途 | 何时使用 |
|------|------|----------|
| `test_single.sh` | 单条测试 | 开发、调试、快速验证 |
| `run.py` | 批量运行 | 生产环境、大规模处理 |
| `run_trajectory_analysis.sh` | 特定任务的批量脚本 | 固定配置的重复执行 |

## 总结

`test_single.sh` 是开发和调试的最佳工具：
- ✅ 快速验证配置
- ✅ 单条测试，秒级反馈
- ✅ 支持所有 task 和 backend
- ✅ 交互式引导 + 命令行灵活性
- ✅ 自动清理临时文件
- ✅ 详细的输出和验证
