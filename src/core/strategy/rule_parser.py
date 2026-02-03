"""RuleParser 模块

重构后的规则解析器 - 向后兼容的导入接口。

原有的 RuleParser 类已重构为模块化结构，本文件保持向后兼容性。
"""
# 从新的包中导入 RuleParser
from .rule_parser.rule_parser import RuleParser

# 导出常用的类和函数
__all__ = ['RuleParser']

# 向后兼容：保留原文件中的常量和工具函数
import ast
import operator as op

# 向后兼容的 OPERATORS 常量
OPERATORS = {
    ast.Gt: op.gt,
    ast.Lt: op.lt,
    ast.Eq: op.eq,
    ast.GtE: op.ge,
    ast.LtE: op.le,
    ast.And: op.and_,
    ast.BitAnd: op.and_,
    ast.Or: op.or_,
    ast.Not: op.not_,
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    ast.Pow: op.pow
}

# 向后兼容：将 OPERATORS 添加到 RuleParser 类
RuleParser.OPERATORS = OPERATORS
