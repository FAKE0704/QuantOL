"""
规则验证器模块
用于验证交易规则表达式的语法正确性
"""


class RuleValidator:
    """规则验证器"""

    def validate_rule_syntax(self, rule_expr: str) -> tuple[bool, str]:
        """
        验证规则语法

        Args:
            rule_expr: 规则表达式

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        if not rule_expr.strip():
            return True, "空规则"

        try:
            # 尝试导入规则解析器进行语法验证
            from src.core.strategy.rule_parser import RuleParser

            # 只验证语法，不实际计算
            is_valid, message = RuleParser.validate_syntax(rule_expr)

            if is_valid:
                return True, "语法验证通过"
            else:
                return False, f"语法错误: {message}"

        except ImportError as e:
            # 如果无法导入规则解析器，进行基本的语法检查
            return self._basic_syntax_check(rule_expr)
        except Exception as e:
            return False, f"验证失败: {str(e)}"

    def _basic_syntax_check(self, rule_expr: str) -> tuple[bool, str]:
        """
        基本语法检查（当规则解析器不可用时）

        Args:
            rule_expr: 规则表达式

        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        try:
            # 检查基本的语法元素
            import ast

            # 尝试解析表达式
            tree = ast.parse(rule_expr, mode='eval')

            # 检查是否包含基本的操作符和函数
            valid_names = {'open', 'high', 'low', 'close', 'volume', 'amount',
                          'REF', 'SMA', 'RSI', 'MACD', 'EMA', 'BOLL', 'C_P', 'VWAP', 'SQRT'}

            # 简单的节点检查
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    if node.id not in valid_names:
                        return False, f"未识别的标识符: {node.id}"

            return True, "基本语法检查通过"

        except SyntaxError as e:
            return False, f"语法错误: {str(e)}"
        except Exception as e:
            return False, f"检查失败: {str(e)}"