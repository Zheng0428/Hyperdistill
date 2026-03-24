# Documentation

项目文档目录。

## 文档文件

### DEVELOPMENT_WORKFLOW.md ⭐ NEW
**开发流程检查清单** - 新功能开发的标准流程

**必读** - 开发任何新功能前必看！

**内容包括**：
- 完整的开发检查清单
- 文档要求（⚠️ MANDATORY）
- 测试要求（⚠️ MANDATORY）
- 代码模板
- 常见错误及避免方法

### AGENT_SKILL_SYSTEM.md
Agent 和 Skill 系统完整文档。

**内容包括**：
- 系统概述和架构
- Agent/Skill 文件格式
- CLI 使用方法
- 编程接口
- 工作原理详解
- 最佳实践
- 未来增强计划

### DEVELOPMENT.md
开发历史和设计决策文档。

**内容包括**：
- 6 个开发阶段的演进历史
- 重要设计决策和权衡
- 架构变更记录
- 已修复的问题

### IMPLEMENTATION_SUMMARY.md
Agent/Skill 系统实现总结。

**内容包括**：
- 实现概述
- 新增文件清单
- 使用示例
- 工作原理
- 测试验证
- 完成状态

## 相关文档

根目录文档：
- `README.md` - 用户文档和使用指南（⭐ 主入口）
- `.claude/CLAUDE.md` - 项目上下文（供 AI 使用）

示例文档：
- `examples/README_AGENT_QA.md` - Agent Q&A 快速开始
- `examples/AGENT_EXAMPLE_README.md` - Agent Q&A 详细文档
- `examples/MULTITURN_EXAMPLES.md` - 多轮对话示例

测试文档：
- `tests/README.md` - 测试说明

## 文档层级

```
文档体系：
├── README.md (根目录) ⭐                 # 用户入口文档
├── .claude/
│   └── CLAUDE.md                        # AI 上下文
├── docs/                                 # 详细文档
│   ├── README.md (本文件)               # 文档索引
│   ├── DEVELOPMENT_WORKFLOW.md ⭐ NEW   # 开发流程（必读）
│   ├── AGENT_SKILL_SYSTEM.md           # Agent/Skill 系统
│   ├── DEVELOPMENT.md                   # 开发历史
│   └── IMPLEMENTATION_SUMMARY.md        # 实现总结
├── examples/                             # 示例文档
│   ├── README_AGENT_QA.md              # Agent Q&A 快速开始
│   ├── AGENT_EXAMPLE_README.md         # Agent Q&A 详细文档
│   └── MULTITURN_EXAMPLES.md           # 多轮对话示例
└── tests/                                # 测试文档
    └── README.md                        # 测试说明
```

## 阅读顺序建议

### 用户视角
1. **快速开始**：`README.md` (根目录)
2. **Agent 系统**：`docs/AGENT_SKILL_SYSTEM.md`
3. **实际示例**：`examples/README_AGENT_QA.md`
4. **深入理解**：`docs/DEVELOPMENT.md`

### 开发者视角
1. **开发流程**：`docs/DEVELOPMENT_WORKFLOW.md` ⭐ **必读**
2. **代码架构**：`README.md` (根目录) + `.claude/CLAUDE.md`
3. **历史决策**：`docs/DEVELOPMENT.md`
4. **测试规范**：`tests/README.md`
5. **实现细节**：`docs/IMPLEMENTATION_SUMMARY.md`

## 🚀 开发新功能必读

**如果你要开发新功能，请先阅读：**

📖 **`DEVELOPMENT_WORKFLOW.md`** - 开发流程检查清单

这个文档包含：
- ✅ 完整的开发步骤
- ⚠️ 必须更新的文档清单
- ⚠️ 必须编写的测试要求
- 📝 代码和文档模板
- 🚫 常见错误及避免方法

**重点提醒：**
1. **README.md (root) 必须更新** - 用户第一入口
2. **所有新功能必须有文档** - 在 docs/
3. **所有新功能必须有测试** - 在 tests/
4. **保持主目录整洁** - 文档放 docs/，测试放 tests/
