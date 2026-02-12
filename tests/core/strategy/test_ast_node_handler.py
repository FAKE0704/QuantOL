"""测试 AST 节点处理模块

测试列名生成、括号处理、运算符转换等功能
"""

import os
import sys
import ast
import pytest

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.core.strategy.rule_parser.ast_node_handler import ASTNodeHandler


class TestASTNodeHandler:
    """测试 ASTNodeHandler 类"""

    def test_simple_name(self):
        """测试简单变量名"""
        code = "close"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "close"

    def test_simple_constant(self):
        """测试常量"""
        code = "5"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "5"

    def test_binary_subtraction(self):
        """测试二元减法运算"""
        code = "close - low"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 紧凑格式，无空格
        assert result == "close-low"

    def test_binary_multiplication(self):
        """测试二元乘法运算"""
        code = "close * open"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "close*open"

    def test_binary_division(self):
        """测试二元除法运算"""
        code = "close / open"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "close/open"

    def test_binary_power(self):
        """测试幂运算 - 应使用 ^ 而不是 **"""
        code = "close ** 5"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 幂运算使用 ^ 符号
        assert result == "close^5"

    def test_nested_binary_with_parentheses(self):
        """测试嵌套二元运算 - 应该添加括号避免歧义"""
        code = "(close - low) * open"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 子表达式应该有括号
        assert result == "(close-low)*open"

    def test_complex_nested_expression(self):
        """测试复杂嵌套表达式"""
        code = "((close - low) * open) / ((close - high) * close)"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 所有二元运算子表达式都应该有括号
        assert result == "((close-low)*open)/((close-high)*close)"

    def test_comparison_with_spaces(self):
        """测试比较运算 - 应该保留空格以增强可读性"""
        code = "close > SMA(close, 5)"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 比较运算应该有空格
        assert " > " in result
        assert result == "close > SMA(close,5)"

    def test_comparison_less_than(self):
        """测试小于比较"""
        code = "close < SMA(close, 5)"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert " < " in result

    def test_function_call_no_spaces_in_args(self):
        """测试函数调用 - 参数间无空格"""
        code = "SMA(close, 5)"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 参数间无空格
        assert result == "SMA(close,5)"

    def test_complex_function_call(self):
        """测试复杂函数调用"""
        # Python 中幂运算使用 **，但输出应该使用 ^
        code = "Z_SCORE(((close-low)*open**5)/((close-high)*close**5),60)"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 幂运算使用 ^ (不是 **)
        assert "^5" in result
        # 函数参数间无空格
        assert ",60)" in result
        assert result == "Z_SCORE(((close-low)*open^5)/((close-high)*close^5),60)"

    def test_comparison_with_complex_expression(self):
        """测试复杂表达式的比较"""
        code = "((close-low)*open)/((close-high)*close) > 2"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        # 比较运算符两侧应该有空格，且子表达式有括号
        assert " > " in result
        assert "(close-low)" in result
        assert "(close-high)" in result

    def test_unary_minus(self):
        """测试一元负号"""
        code = "-close"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "-close"

    def test_addition(self):
        """测试加法"""
        code = "close + open"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "close+open"

    def test_modulo(self):
        """测试取模运算"""
        code = "close % 5"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "close%5"

    def test_floor_division(self):
        """测试整除运算"""
        code = "close // 5"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert result == "close//5"

    def test_comparison_greater_equal(self):
        """测试大于等于"""
        code = "close >= 100"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert " >= " in result

    def test_comparison_less_equal(self):
        """测试小于等于"""
        code = "close <= 100"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert " <= " in result

    def test_comparison_equal(self):
        """测试等于"""
        code = "close == 100"
        tree = ast.parse(code, mode='eval')
        result = ASTNodeHandler.node_to_expr(tree.body)
        assert " == " in result


if __name__ == "__main__":
    # 直接运行测试
    test = TestASTNodeHandler()

    print("运行 ASTNodeHandler 测试...\n")

    tests = [
        ("简单变量名", test.test_simple_name),
        ("简单常量", test.test_simple_constant),
        ("二元减法运算", test.test_binary_subtraction),
        ("二元乘法运算", test.test_binary_multiplication),
        ("二元除法运算", test.test_binary_division),
        ("幂运算 (^)", test.test_binary_power),
        ("嵌套二元运算(括号)", test.test_nested_binary_with_parentheses),
        ("复杂嵌套表达式", test.test_complex_nested_expression),
        ("比较运算(空格)", test.test_comparison_with_spaces),
        ("小于比较", test.test_comparison_less_than),
        ("函数调用参数", test.test_function_call_no_spaces_in_args),
        ("复杂函数调用", test.test_complex_function_call),
        ("复杂表达式比较", test.test_comparison_with_complex_expression),
        ("一元负号", test.test_unary_minus),
        ("加法运算", test.test_addition),
        ("取模运算", test.test_modulo),
        ("整除运算", test.test_floor_division),
        ("大于等于", test.test_comparison_greater_equal),
        ("小于等于", test.test_comparison_less_equal),
        ("等于比较", test.test_comparison_equal),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            print(f"✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"✗ {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {name}: 意外错误 - {e}")
            failed += 1

    print(f"\n总计: {passed} 通过, {failed} 失败")

    if failed == 0:
        print("所有测试通过！")
        sys.exit(0)
    else:
        sys.exit(1)
