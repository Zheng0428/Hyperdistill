# Tests

测试脚本目录。

## 测试文件

### test_agent_skill_system.py
测试 Agent 和 Skill 系统的加载、注册和集成功能。

**运行方式**：
```bash
# 从项目根目录运行
python tests/test_agent_skill_system.py
```

**测试内容**：
- Agent 加载（单个和批量）
- Skill 加载（单个和批量）
- 注册表操作
- CLI Backend 集成

### test_providers.py
Provider 端到端测试，验证所有 API Provider 的正确性。

**运行方式**：
```bash
# 测试所有 providers
python tests/test_providers.py

# 测试指定 provider
python tests/test_providers.py --provider kimi minimax

# 指定配置目录
python tests/test_providers.py --config-dir configs/

# 限制每个 provider 测试的端点数量
python tests/test_providers.py --max-endpoints 1
```

**测试内容**：
- Provider 注册和匹配
- API 配置加载
- 请求参数构建
- 响应解析（content + thinking）
- 端到端推理调用

## 运行所有测试

```bash
# 从项目根目录
python tests/test_agent_skill_system.py
python tests/test_providers.py
```

## 添加新测试

在此目录下创建 `test_*.py` 文件，确保：
1. 添加正确的路径设置：
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
   ```
2. 从 `hyperdistill` 包导入模块
3. 使用清晰的测试函数名和文档字符串
