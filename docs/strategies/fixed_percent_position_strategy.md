# 仓位管理策略 - 固定比例策略设计文档

## 概述
固定比例仓位管理策略（Fixed Percent Strategy）是一种基于初始资金固定比例进行仓位管理的策略。该策略的核心思想是按照预先设定的资金比例进行交易，确保风险控制和资金使用的稳定性。

## 核心原则
- **资金分配**: 基于初始资金或当前可用资金的固定比例
- **信号响应**: 根据交易信号调整仓位
  - 开仓信号：按固定比例开仓（仅当无持仓时）
  - 加仓信号：按固定比例增加仓位
  - 平仓信号：按固定比例部分卖出
  - 清仓信号：完全清仓所有仓位
- **风险控制**: 通过固定比例限制单次交易风险

## 策略参数
```python
{
    "percent": 0.1,          # 仓位比例（10%）
    "use_initial_capital": true,  # 是否基于初始资金计算（true）或当前权益（false）
    "max_position_percent": 0.3,   # 最大总仓位限制（可选）
    "min_lot_size": 100      # 最小交易手数
}
```

## 信号处理逻辑

### 1. 开仓信号（方案C：基于可用资金和持仓状态）
```python
def calculate_open_position_size(self, available_cash, current_price, current_position, percent):
    # 已有持仓时不开新仓，避免重复开仓
    if current_position > 0:
        return 0

    # 基于可用现金计算可买数量
    position_value = available_cash * percent
    quantity = int(position_value / current_price / self.min_lot_size) * self.min_lot_size

    # 检查资金是否足够
    required_cash = quantity * current_price
    if required_cash > available_cash:
        # 资金不足时减少数量
        quantity = int(available_cash / current_price / self.min_lot_size) * self.min_lot_size

    return quantity
```

### 2. 加仓信号
```python
def calculate_add_position_size(self, available_cash, current_price, current_position, percent):
    # 加仓时按固定比例计算
    position_value = available_cash * percent
    additional_quantity = int(position_value / current_price / self.min_lot_size) * self.min_lot_size

    # 检查资金是否足够
    required_cash = additional_quantity * current_price
    if required_cash > available_cash:
        additional_quantity = int(available_cash / current_price / self.min_lot_size) * self.min_lot_size

    return additional_quantity
```

### 3. 平仓信号（修正理解：按固定比例部分卖出）
```python
def calculate_close_position_size(self, current_position, percent, min_lot_size):
    # 平仓信号：按固定比例部分卖出，不是完全平仓
    if current_position <= 0:
        return 0

    # 计算要卖出的数量（按比例）
    sell_quantity = int(current_position * percent / min_lot_size) * self.min_lot_size

    # 确保不超过当前持仓
    sell_quantity = min(sell_quantity, current_position)

    return sell_quantity  # 返回需要卖出的数量
```

### 4. 清仓信号
```python
def calculate_liquidate_position_size(self, current_position):
    # 清仓信号：强制清仓所有持仓
    return current_position if current_position > 0 else 0
```

## 实现细节

### 核心计算逻辑
```python
class FixedPercentStrategy:
    def __init__(self, percent=0.1, use_initial_capital=True, min_lot_size=100):
        self.percent = percent
        self.use_initial_capital = use_initial_capital
        self.min_lot_size = min_lot_size

    def calculate_position_size(self, signal_type, portfolio_data, current_price, current_position=0):
        """
        计算目标仓位大小

        Args:
            signal_type: 信号类型（OPEN, ADD, CLOSE, LIQUIDATE）
            portfolio_data: 投资组合数据
                - initial_capital: 初始资金
                - available_cash: 可用现金
                - total_equity: 总权益
            current_price: 当前价格
            current_position: 当前持仓数量

        Returns:
            int: 目标交易数量（正数买入，负数卖出，0表示无操作）
        """

        if signal_type == SignalType.LIQUIDATE:
            return self.calculate_liquidate_position_size(current_position)

        if signal_type == SignalType.CLOSE:
            return -self.calculate_close_position_size(current_position, self.percent, self.min_lot_size)

        # 计算可用资金
        available_capital = (portfolio_data['initial_capital']
                           if self.use_initial_capital
                           else portfolio_data['available_cash'])

        if signal_type == SignalType.OPEN:
            return self.calculate_open_position_size(
                portfolio_data['available_cash'], current_price, current_position, self.percent
            )

        elif signal_type == SignalType.ADD:
            return self.calculate_add_position_size(
                portfolio_data['available_cash'], current_price, current_position, self.percent
            )

        return 0
```

### 信号处理流程
```python
def handle_signal(self, signal, portfolio_data, current_price, current_position):
    """统一信号处理入口"""
    quantity = self.calculate_position_size(
        signal_type=signal.signal_type,
        portfolio_data=portfolio_data,
        current_price=current_price,
        current_position=current_position
    )

    # 返回交易指令
    if quantity > 0:
        return TradeOrder(symbol=signal.symbol, quantity=quantity, side="BUY")
    elif quantity < 0:
        return TradeOrder(symbol=signal.symbol, quantity=abs(quantity), side="SELL")
    else:
        return None
```

## 使用示例

### 配置示例
```python
# 10%固定比例策略
position_config = {
    "strategy_type": "fixed_percent",
    "percent": 0.1,                    # 10%仓位
    "use_initial_capital": True,       # 基于初始资金
    "min_lot_size": 100               # A股最小交易单位
}

# 30%仓位策略
aggressive_config = {
    "strategy_type": "fixed_percent",
    "percent": 0.3,                    # 30%仓位
    "use_initial_capital": False,      # 基于当前权益
    "min_lot_size": 100
}
```

### 回测集成示例
```python
# 在回测引擎中的使用
position_strategy = FixedPercentStrategy(
    percent=0.1,
    use_initial_capital=True,
    min_lot_size=100
)

# 信号处理
for signal in signals:
    trade_order = position_strategy.handle_signal(
        signal=signal,
        portfolio_data={
            'initial_capital': 1000000,
            'available_cash': 900000,
            'total_equity': 1100000
        },
        current_price=signal.price,
        current_position=current_position
    )

    if trade_order:
        # 执行交易
        engine.create_order(
            timestamp=signal.timestamp,
            symbol=trade_order.symbol,
            quantity=trade_order.quantity,
            side=trade_order.side
        )
```

## 策略优势
1. **简单明确**：逻辑清晰，易于理解和实现
2. **风险可控**：通过固定比例限制单次交易风险
3. **资金稳定**：避免过度集中或过度分散
4. **适应性强**：可适用于不同市场和时间周期

## 策略局限
1. **缺乏弹性**：固定比例可能错过某些机会
2. **频繁交易**：可能在震荡市中产生过多交易
3. **市场适应性**：在极端市场条件下可能需要调整比例

## 关键设计决策

### 1. 开仓资金分配（方案C）
- **决策**：基于可用资金和当前持仓状态
- **优势**：避免重复开仓，确保资金安全
- **实现**：已有持仓时不开新仓，仅基于可用现金计算

### 2. 平仓信号理解（修正）
- **修正前**：平仓 = 完全平仓
- **修正后**：平仓 = 按固定比例部分卖出
- **原因**：更符合仓位管理策略的渐进式调整原则

### 3. 成本价考量
- **决策**：不考虑现有持仓成本价
- **原因**：简化逻辑，避免复杂的成本计算影响策略执行

## 优化方向
1. **动态比例**：根据市场波动率调整仓位比例
2. **分批建仓**：大额资金时分批进入市场
3. **止损机制**：结合技术指标设置止损点
4. **再平衡**：定期调整仓位比例
5. **多标的协调**：多个标的之间的仓位分配策略

---

**核心要点总结**：
1. 开仓：基于可用资金，已有持仓时不开新仓
2. 平仓：按固定比例部分卖出，不是完全平仓
3. 不考虑持仓成本价，简化逻辑
4. 始终满足最小交易手数要求
5. 确保资金充足性检查