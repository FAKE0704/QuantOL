# 测试指引文档

本文档目录提供编写测试的指引，分为通用规范和特定场景规范。

## 文档目录

### 通用规范（适用于所有测试）

#### [测试文件组织规范](./TEST_STRUCTURE.md)
- 测试目录结构
- 文件命名规则
- 新增测试流程
- 运行测试的方法

**适用范围**：所有类型测试（指标函数、策略、组件等）

---

### 指标规则测试规范

以下文档专门针对**技术指标函数**的测试编写：

#### [指标函数测试编写指南](./TEST_WRITING_GUIDE.md)
- 测试用例应覆盖的场景（基本功能、边界条件、参数验证、组合使用）
- 测试数据创建规范
- 断言编写规范
- 运算符优先级注意事项

**适用范围**：技术指标函数（如 SMA、RSI、Q 等）

#### [指标函数测试模板](./TEST_TEMPLATES.md)
- 指标函数测试完整模板
- 使用模板的步骤
- 实际示例参考

**适用范围**：新增技术指标函数时

---

## 快速开始

### 新增指标函数测试

```bash
# 1. 创建测试文件
touch tests/core/strategy/test_indicator_<函数名>.py

# 2. 参考 TEST_TEMPLATES.md 编写测试

# 3. 运行测试
uv run pytest tests/core/strategy/test_indicator_<函数名>.py -v
```

### 其他类型测试

对于策略测试、组件测试等，参考 TEST_STRUCTURE.md 中的文件组织规范，测试编写方式根据具体场景自行设计。

## 测试文件命名

| 类型 | 命名格式 | 示例 | 指引文档 |
|------|----------|------|----------|
| 指标函数 | `test_indicator_<name>.py` | `test_indicator_q.py` | TEST_WRITING_GUIDE.md + TEST_TEMPLATES.md |
| 策略 | `test_<name>_strategy.py` | `test_martingale_position_strategy.py` | 通用规范 |
| 组件 | `test_<name>.py` | `test_rule_parser.py` | 通用规范 |

## 指标规则测试最佳实践

1. **一个指标一个文件** - 每个技术指标函数应有独立的测试文件
2. **覆盖关键场景** - 基本功能、边界条件、参数验证、组合使用
3. **使用完整条件表达式** - 测试应该是 `close > XXX(close, ...)` 而不是单独的 `XXX(close, ...)`
4. **明确运算符优先级** - 使用括号避免歧义：`(A) & (B)`
5. **描述性断言消息** - `assert result == True, "具体说明"`

## 常见问题

### Q: 为什么指标测试要使用条件表达式？
A: `evaluate_at` 方法会将返回值转换为布尔值。直接测试函数调用会丢失原始数值，而条件表达式能正确验证函数在策略中的实际使用方式。

### Q: 如何处理 mock 服务？
A: 使用 `create_mock_indicator_service()` 函数创建模拟服务，避免依赖实际的指标计算逻辑。

### Q: 测试数据应该多大？
A: 通常 5-10 行数据足够。数据应覆盖测试场景所需的最小窗口大小。

## 相关资源

- [pytest 官方文档](https://docs.pytest.org/)
- 项目主目录：`tests/`
- 指标测试示例：`tests/core/strategy/test_indicator_q.py`
