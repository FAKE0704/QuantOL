# 仓位明细Tab设计文档

## 功能描述
仓位明细tab用于显示回测结束后的持仓情况，包括当前持有的股票、数量、成本价、当前价值等信息。

## 修复前问题
- 交易记录tab正常显示交易历史
- 仓位明细tab显示为空，无法看到当前持仓情况
- 即使有交易记录，也无法知道最终的持仓状态

## 问题根本原因
在 `BacktestEngine.get_results()` 方法中，只返回了交易记录（`trades`），但没有返回 `portfolio_manager` 实例，导致前端无法获取当前持仓信息。

## 修复方案

### 1. 后端修复
在 `src/core/strategy/backtesting.py` 的 `get_results()` 方法中添加 `portfolio_manager`：

```python
return {
    # ... 其他字段
    "portfolio_manager": self.portfolio_manager  # 添加组合管理器以获取持仓信息
}
```

### 2. 前端显示逻辑
仓位明细显示位于 `src/frontend/results_display_manager.py` 的 `display_position_details()` 方法：

```python
def display_position_details(self, results: Dict[str, Any]):
    """显示仓位明细"""
    st.subheader("📈 仓位明细")

    # 获取当前持仓信息
    portfolio_manager = results.get('portfolio_manager')
    if portfolio_manager:
        all_positions = portfolio_manager.get_all_positions()
        # ... 显示逻辑
```

## 功能特性

### 1. 持仓信息展示
- **标的代码**: 持仓股票代码
- **持仓数量**: 当前持有的股票数量
- **平均成本**: 持仓的平均成本价
- **当前价值**: 按当前价格计算的持仓价值
- **当前价格**: 股票的最新价格
- **持仓权重**: 占总投资组合的百分比

### 2. 仓位统计
- **持仓总价值**: 所有持仓的总价值
- **现金余额**: 可用现金金额
- **组合总价值**: 持仓总价值 + 现金余额

### 3. 持仓分布图表
- 饼图显示各持仓股票的价值占比
- 直观展示投资组合分散度

## 界面布局

```
📈 仓位明细
├── 持仓信息表格
│   ├── 标的代码 | 持仓数量 | 平均成本 | 当前价值 | 当前价格 | 持仓权重
│   └── 数据表格展示
├── 仓位统计
│   ├── 持仓总价值 | 现金余额 | 组合总价值
│   └── 三个metric卡片
└── 持仓分布
    └── 饼图（持仓价值分布）
```

## 数据来源

### PortfolioManager接口
- `get_all_positions()`: 获取所有持仓信息
- `get_portfolio_value()`: 获取投资组合总价值
- `get_cash_balance()`: 获取现金余额

### Position对象属性
- `quantity`: 持仓数量
- `avg_cost`: 平均成本
- `current_value`: 当前价值
- `stock.last_price`: 当前价格

## 边界情况处理

1. **无持仓情况**: 显示"暂无持仓记录"提示
2. **数据异常**: 处理None值和异常数据
3. **多符号模式**: 正确处理多只股票的持仓

## 修复验证

修复后，仓位明细tab应该能够：
1. 显示回测结束时的最终持仓状态
2. 提供详细的持仓统计信息
3. 通过图表直观展示持仓分布
4. 与交易记录tab保持数据一致性

## 相关文件
- `src/core/strategy/backtesting.py`: BacktestEngine.get_results()方法
- `src/frontend/results_display_manager.py`: display_position_details()方法
- `src/frontend/results_display_ui.py`: render_positions_tab()方法