import ast
import operator as op
from typing import Dict, Callable, Union
from dataclasses import dataclass
import pandas as pd

@dataclass
class IndicatorFunction:
    """指标函数描述"""
    name: str
    func: Callable
    params: Dict[str, type]
    description: str

class RuleParser:
    """规则解析引擎核心类"""
    
    OPERATORS = {
        ast.Gt: op.gt, 
        ast.Lt: op.lt,
        ast.Eq: op.eq,
        ast.And: op.and_,
        ast.Or: op.or_,
        ast.Not: op.not_
    }
    
    def __init__(self, data_provider: pd.DataFrame):
        """初始化解析器
        Args:
            data_provider: 提供OHLCV等市场数据的DataFrame
        """
        self.data = data_provider
        self._indicators = self._init_indicators()
        
    def _init_indicators(self) -> Dict[str, IndicatorFunction]:
        """初始化指标函数注册表"""
        return {
            'SMA': IndicatorFunction(
                name='SMA',
                func=self._sma,
                params={'n': int},
                description='简单移动平均线'
            ),
            'RSI': IndicatorFunction(
                name='RSI',
                func=self._rsi,
                params={'n': int},
                description='相对强弱指数'
            ),
            'MACD': IndicatorFunction(
                name='MACD',
                func=self._macd,
                params={},
                description='指数平滑异同平均线'
            ),
            'VOLUME': IndicatorFunction(
                name='VOLUME',
                func=lambda: self.data['volume'],
                params={},
                description='成交量'
            )
        }
    
    def parse(self, rule: str) -> bool:
        """解析规则表达式
        Args:
            rule: 规则表达式字符串，如"(SMA(5) > SMA(20)) & (RSI(14) < 30)"
        Returns:
            规则评估结果(bool)
        Raises:
            SyntaxError: 规则语法错误时抛出
            ValueError: 指标参数错误时抛出
        """
        try:
            tree = ast.parse(rule, mode='eval')
            return self._eval(tree.body)
        except Exception as e:
            raise SyntaxError(f"规则解析失败: {str(e)}") from e
            
    def _eval(self, node) -> Union[bool, float]:
        """递归评估AST节点
        Returns:
            比较运算返回bool，指标计算返回float
        """
        if isinstance(node, ast.Compare):
            left = float(self._eval(node.left))
            right = float(self._eval(node.comparators[0]))
            return bool(self.OPERATORS[type(node.ops[0])](left, right))
        elif isinstance(node, ast.BoolOp):
            return self._eval_bool_op(node)
        elif isinstance(node, ast.Call):
            return self._eval_function_call(node)
        elif isinstance(node, ast.Name):
            return self._eval_variable(node)
        elif isinstance(node, ast.Constant):
            return node.value
        else:
            raise ValueError(f"不支持的AST节点类型: {type(node)}")
    
    def _eval_bool_op(self, node) -> bool:
        """评估逻辑运算符"""
        values = [self._eval(v) for v in node.values]
        return self.OPERATORS[type(node.op)](*values)
    
    def _eval_function_call(self, node) -> float:
        """评估指标函数调用"""
        func_name = node.func.id
        if func_name not in self._indicators:
            raise ValueError(f"不支持的指标函数: {func_name}")
            
        indicator = self._indicators[func_name]
        args = [self._eval(arg) for arg in node.args]
        return indicator.func(*args)
    
    def _eval_variable(self, node) -> float:
        """评估变量(从数据源获取)"""
        if node.id not in self.data.columns:
            raise ValueError(f"数据中不存在列: {node.id}")
        value = self.data[node.id].iloc[-1]
        if pd.isna(value):
            raise ValueError(f"变量 {node.id} 的值为空")
        return float(value)  # 确保返回float类型
    
    # 指标计算函数实现
    def _sma(self, n: int) -> float:
        """计算简单移动平均"""
        value = self.data['close'].rolling(n).mean().iloc[-1]
        return float(value) if not pd.isna(value) else 0.0
        
    def _rsi(self, n: int) -> float:
        """计算相对强弱指数"""
        close_series = self.data['close'].astype(float)
        delta = close_series.diff()
        
        # 确保比较运算在标量值上进行
        gain = delta.apply(lambda x: x if x > 0 else 0.0)
        loss = delta.apply(lambda x: -x if x < 0 else 0.0)
        
        avg_gain = gain.rolling(n).mean().iloc[-1]
        avg_loss = loss.rolling(n).mean().iloc[-1]
        
        if avg_loss == 0:
            return 100.0  # 避免除零
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi) if not pd.isna(rsi) else 50.0
        
    def _macd(self) -> float:
        """计算MACD指标"""
        ema12 = self.data['close'].ewm(span=12).mean()
        ema26 = self.data['close'].ewm(span=26).mean()
        macd = ema12 - ema26
        return float(macd.iloc[-1]) if not pd.isna(macd.iloc[-1]) else 0.0
