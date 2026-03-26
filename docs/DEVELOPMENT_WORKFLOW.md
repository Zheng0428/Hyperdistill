# Development Workflow Checklist

新功能开发标准流程的快速检查清单。

## 📋 Complete Checklist

### Phase 1: Planning
- [ ] 明确功能需求和设计
- [ ] 确定影响的模块
- [ ] 检查是否需要破坏性更改
- [ ] 规划文档和测试策略

### Phase 2: Implementation
- [ ] 编写代码（遵循现有模式）
- [ ] 添加完整的 docstrings
- [ ] 添加内联注释
- [ ] 遵循 Registry/ABC 等模式
- [ ] 处理异常和边界情况

### Phase 3: Documentation (MANDATORY ⚠️)

#### ⭐ CRITICAL: README.md (Root)
- [ ] 更新功能列表/特性说明
- [ ] 更新 CLI 参数表
- [ ] 添加使用示例
- [ ] 更新项目结构图（如有变化）
- [ ] 更新快速开始部分（如相关）

#### docs/ Directory
- [ ] 创建详细文档 `docs/NEW_FEATURE.md`
  - [ ] 功能描述
  - [ ] 使用方法
  - [ ] 参数说明
  - [ ] 示例代码
  - [ ] 最佳实践
  - [ ] 故障排查
- [ ] 更新 `docs/README.md` 索引
- [ ] 如有架构变更，更新 `.claude/CLAUDE.md`

#### examples/ Directory
- [ ] 创建可运行的示例脚本
- [ ] 添加示例数据（如需要）
- [ ] 更新 `examples/README.md` 或创建专用 README

### Phase 4: Testing (MANDATORY ⚠️)
- [ ] 编写单元测试 `tests/test_*.py`
- [ ] 测试正常路径
- [ ] 测试边界情况
- [ ] 测试错误处理
- [ ] 更新 `tests/README.md`
- [ ] 运行所有现有测试确保无破坏
- [ ] 使用真实数据测试

### Phase 5: Configuration
- [ ] 更新 `requirements.txt`（如有新依赖）
- [ ] 更新 `.gitignore`（如有新文件类型）
- [ ] 更新 `run.py` CLI 参数（如需要）
- [ ] 更新配置文件示例（如需要）

### Phase 6: Verification
- [ ] 所有测试通过
- [ ] 文档完整且准确
- [ ] 示例可运行
- [ ] 向后兼容（或已记录破坏性变更）
- [ ] 代码审查（自审）

### Phase 7: Finalization
- [ ] 清理调试代码
- [ ] 格式化代码
- [ ] 最终检查文档链接
- [ ] Commit with clear message
- [ ] Tag version（如是重要功能）

---

## 🎯 Minimum Documentation Requirements

**即使时间紧张，以下文档也必须完成：**

### 1. README.md (Root) - ⭐ MANDATORY
必须更新的部分：
- [ ] 功能列表中添加新功能
- [ ] 如果是 CLI 功能，更新参数表
- [ ] 添加至少一个使用示例

### 2. Code Docstrings - ⭐ MANDATORY
每个新函数/类必须有：
```python
def new_function(param1: str, param2: int) -> dict:
    """
    简短描述（一句话）

    详细描述（如需要）

    Args:
        param1: 参数1的说明
        param2: 参数2的说明

    Returns:
        返回值说明

    Raises:
        ExceptionType: 异常情况说明

    Example:
        >>> result = new_function("test", 42)
    """
```

### 3. Test File - ⭐ MANDATORY
至少包含：
- [ ] 功能测试
- [ ] 边界情况测试
- [ ] 文件级 docstring 说明测试内容

---

## 🚫 Common Mistakes to Avoid

1. ❌ **忘记更新 README.md**
   - ✅ README 是用户第一个看的文件，必须保持最新

2. ❌ **只在代码中写 docstring，不写独立文档**
   - ✅ docs/ 目录需要独立的完整文档

3. ❌ **不写测试**
   - ✅ 所有新功能必须有测试

4. ❌ **在根目录添加新的文档文件**
   - ✅ 所有文档都应该在 docs/ 目录

5. ❌ **示例代码无法运行**
   - ✅ 所有示例都应该是可运行的

6. ❌ **忘记更新 docs/README.md 索引**
   - ✅ 新文档必须被索引

7. ❌ **破坏现有功能但未测试**
   - ✅ 必须运行所有现有测试

---

## 📝 Quick Templates

### New Task Template
```python
# hyperdistill/tasks/my_task.py
from .base import BaseTask
from .registry import TaskRegistry

@TaskRegistry.register
class MyTask(BaseTask):
    """
    Brief description

    Input format:
        {"field1": "value1", ...}

    Output format:
        {"field1": "value1", "output": "generated", ...}
    """

    name = "my-task"

    def get_id(self, item):
        return str(item["id"])

    def build_messages(self, item):
        return [{"role": "user", "content": item["query"]}]

    def process_result(self, item, content, thinking):
        item["response"] = content
        if thinking:
            item["thinking"] = thinking
        return item

    def validate_item(self, item):
        return "id" in item and "query" in item
```

### New Test Template
```python
# tests/test_my_task.py
"""
Tests for MyTask
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hyperdistill.tasks import get_task

def test_my_task_basic():
    """Test basic functionality"""
    task = get_task("my-task")

    item = {"id": "1", "query": "test query"}
    messages = task.build_messages(item)

    assert len(messages) > 0
    assert messages[0]["role"] == "user"
    print("✓ Basic test passed")

def test_my_task_validation():
    """Test input validation"""
    task = get_task("my-task")

    valid_item = {"id": "1", "query": "test"}
    assert task.validate_item(valid_item) == True

    invalid_item = {"query": "test"}  # missing id
    assert task.validate_item(invalid_item) == False
    print("✓ Validation test passed")

if __name__ == "__main__":
    test_my_task_basic()
    test_my_task_validation()
    print("\n✅ All tests passed!")
```

### New Doc Template
```markdown
# docs/MY_FEATURE.md

# My Feature

Brief description of what this feature does.

## Overview

Detailed description...

## Usage

### Basic Usage

\`\`\`bash
# Example command
python run.py --my-option value
\`\`\`

### Advanced Usage

...

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `--param1` | str | None | ... |

## Examples

### Example 1: Basic

\`\`\`bash
# Full example with input/output
\`\`\`

### Example 2: Advanced

...

## Best Practices

1. ...
2. ...

## Troubleshooting

### Issue 1

**Problem**: ...
**Solution**: ...

## See Also

- [Related Doc 1](./RELATED1.md)
- [Main README](../README.md)
```

---

## 🔍 Self-Review Questions

Before committing, ask yourself:

1. ✅ README.md 是否已更新？
2. ✅ 新功能是否有完整文档在 docs/？
3. ✅ 是否有测试覆盖？
4. ✅ 所有测试是否通过？
5. ✅ 示例代码是否可运行？
6. ✅ 是否向后兼容？
7. ✅ 主目录是否保持整洁？
8. ✅ 文档是否准确无误？
9. ✅ 是否有 docstrings？
10. ✅ .gitignore 是否需要更新？

**如果任何一项回答 "否"，请在提交前完成！**

---

保存此文件并在每次开发新功能时参考。
