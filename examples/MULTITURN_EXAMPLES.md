# 多轮对话蒸馏示例

本文档展示了如何使用 `expand_items()` 机制实现"一条数据生成多条输入"的功能。

## 概述

框架提供了两个多轮对话蒸馏任务作为示例：

1. **`multiturn_distill`** - 只处理最后一轮（原始行为）
2. **`multiturn_all_distill`** - 处理所有轮次（新增，展示 expand_items 用法）

## 核心机制：`expand_items()`

### 默认行为（不扩展）

```python
class BaseTask(ABC):
    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """默认实现：不扩展，返回单个 item"""
        return [item]
```

### 自定义扩展（多轮对话示例）

```python
class MultiTurnAllDistillTask(BaseTask):
    def expand_items(self, item: Dict[str, Any]) -> List[Dict[str, Any]]:
        """将一条对话扩展为多条（每轮一条）"""
        messages = item["messages"]
        turn_count = sum(1 for m in messages if m['role'] == 'user')

        # 创建 N 个扩展 item（N = 轮次数）
        expanded = []
        for turn_idx in range(1, turn_count + 1):
            turn_item = dict(item)  # 浅拷贝
            turn_item["turn_idx"] = turn_idx  # 添加轮次标识
            expanded.append(turn_item)

        return expanded

    def get_id(self, item: Dict[str, Any]) -> str:
        """每个扩展 item 必须有唯一 ID"""
        return f"{item['md5']}:{item['turn_idx']}"
```

## 工作流程

```
输入数据流:
1 条对话（3 轮）
    ↓
expand_items()
    ↓
3 个独立 item（turn_idx=1, 2, 3）
    ↓
validate_item() × 3
    ↓
get_id() → md5:1, md5:2, md5:3（去重检查）
    ↓
build_messages() × 3
    ↓
API 调用 × 3
    ↓
process_result() × 3
    ↓
输出 3 条记录
```

## 使用示例

### 示例 1：只处理最后一轮

```bash
python run.py \
    --task multiturn_distill \
    --backend api \
    --provider glm \
    --config configs/config_glm.json \
    -i input.jsonl \
    -o output.jsonl \
    -w 10
```

**输入：** 1 条对话（3 轮）
**输出：** 1 条记录（第 3 轮）

### 示例 2：处理所有轮次

```bash
python run.py \
    --task multiturn_all_distill \
    --backend api \
    --provider glm \
    --config configs/config_glm.json \
    -i input.jsonl \
    -o output.jsonl \
    -w 10
```

**输入：** 1 条对话（3 轮）
**输出：** 3 条记录（第 1, 2, 3 轮各一条）

### 示例 3：限制最大轮次

```bash
# 通过修改 task 代码设置 max_turns
# 或在 run.py 中添加 --max-turns 参数支持
```

## 输入数据格式

```json
{
  "md5": "abc123",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "回答1"},
    {"role": "user", "content": "问题2"},
    {"role": "assistant", "content": "回答2"},
    {"role": "user", "content": "问题3"},
    {"role": "assistant", "content": "回答3"}
  ],
  "model": "...",
  "create_time": "..."
}
```

## 输出数据格式

### multiturn_distill（只有最后一轮）

```json
{
  "md5": "abc123",
  "turn_idx": 3,
  "messages": [
    {"role": "system", "content": "IQuest-Coder prompt..."},
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "回答1"},
    {"role": "user", "content": "问题2"},
    {"role": "assistant", "content": "回答2"},
    {"role": "user", "content": "问题3"},
    {"role": "assistant", "content": "蒸馏后的回答3"}
  ],
  "thinking": "...",
  "model": "...",
  "create_time": "..."
}
```

### multiturn_all_distill（所有轮次）

```json
// 第 1 轮
{
  "md5": "abc123",
  "turn_idx": 1,
  "messages": [
    {"role": "system", "content": "IQuest-Coder prompt..."},
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "蒸馏后的回答1"}
  ],
  "thinking": "...",
  ...
}

// 第 2 轮
{
  "md5": "abc123",
  "turn_idx": 2,
  "messages": [
    {"role": "system", "content": "IQuest-Coder prompt..."},
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "蒸馏后的回答1"},
    {"role": "user", "content": "问题2"},
    {"role": "assistant", "content": "蒸馏后的回答2"}
  ],
  "thinking": "...",
  ...
}

// 第 3 轮
{
  "md5": "abc123",
  "turn_idx": 3,
  "messages": [
    {"role": "system", "content": "IQuest-Coder prompt..."},
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "蒸馏后的回答1"},
    {"role": "user", "content": "问题2"},
    {"role": "assistant", "content": "蒸馏后的回答2"},
    {"role": "user", "content": "问题3"},
    {"role": "assistant", "content": "蒸馏后的回答3"}
  ],
  "thinking": "...",
  ...
}
```

## 断点续跑

两个任务都支持断点续跑：

- **multiturn_distill**: 基于 `md5` 去重，处理过的对话会被跳过
- **multiturn_all_distill**: 基于 `md5:turn_idx` 去重，已处理的轮次会被跳过

示例：
```bash
# 第一次运行（处理了 100 条对话的所有轮次）
python run.py --task multiturn_all_distill ... -i input.jsonl -o output.jsonl

# 中断后重新运行（自动跳过已处理的 md5:turn_idx）
python run.py --task multiturn_all_distill ... -i input.jsonl -o output.jsonl
```

## 其他扩展场景示例

### 场景 1：数据增强（多个变体）

```python
class QueryVariationTask(BaseTask):
    """为每个 query 生成 3 个变体"""

    def expand_items(self, item):
        variations = []
        for i in range(3):
            var_item = dict(item)
            var_item["variation_id"] = i
            variations.append(var_item)
        return variations

    def get_id(self, item):
        return f"{item['id']}:var{item['variation_id']}"
```

### 场景 2：多语言翻译

```python
class MultiLangTranslateTask(BaseTask):
    """将一条文本翻译为多种语言"""

    def expand_items(self, item):
        langs = ["en", "ja", "ko", "de", "fr"]
        items = []
        for lang in langs:
            lang_item = dict(item)
            lang_item["target_lang"] = lang
            items.append(lang_item)
        return items

    def get_id(self, item):
        return f"{item['id']}:{item['target_lang']}"
```

### 场景 3：难度分级生成

```python
class DifficultyLevelTask(BaseTask):
    """为同一个主题生成简单/中等/困难三个版本"""

    def expand_items(self, item):
        levels = ["easy", "medium", "hard"]
        items = []
        for level in levels:
            level_item = dict(item)
            level_item["difficulty"] = level
            items.append(level_item)
        return items

    def get_id(self, item):
        return f"{item['topic_id']}:{item['difficulty']}"
```

## 注意事项

1. **唯一 ID 必须保证唯一性**：每个扩展后的 item 通过 `get_id()` 返回的 ID 必须全局唯一
2. **扩展在流式处理中进行**：不会占用额外内存，适合大数据集
3. **去重/断点续跑自动支持**：框架会自动基于 ID 进行去重和断点续跑
4. **验证在扩展后进行**：`validate_item()` 对每个扩展后的 item 单独验证
5. **向后兼容**：不实现 `expand_items()` 的 task 保持原有行为（返回 `[item]`）

## 性能影响

- **内存**: 扩展在流式处理中进行，每次只处理一个原始 item 的扩展结果
- **并发**: 扩展后的 item 独立并发处理，不影响并发效率
- **去重**: 每个扩展 item 的 ID 都会被检查，已处理的会被跳过

## 完整示例脚本

参见：`examples/run_multiturn_all.sh`
