"""AST节点处理模块

提供无状态的纯函数工具类，用于AST节点操作和表达式转换。
"""
import ast
import operator as op
from typing import Dict, Any
import astunparse


class ASTNodeHandler:
    """AST节点操作工具（无状态纯函数）

    提供AST节点到表达式字符串的转换功能，用于生成列名和调试信息。
    """

    # 运算符映射
    OPERATORS: Dict[type, Any] = {
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

    # 运算符优先级
    OPERATOR_PRECEDENCE: Dict[type, int] = {
        ast.Pow: 4,
        ast.Mult: 3, ast.Div: 3, ast.FloorDiv: 3, ast.Mod: 3,
        ast.Add: 2, ast.Sub: 2,
        ast.Gt: 1, ast.Lt: 1, ast.Eq: 1, ast.GtE: 1, ast.LtE: 1
    }

    @staticmethod
    def node_to_expr(node: ast.AST) -> str:
        """将AST节点转换为表达式字符串

        生成更简洁的列名，用于DataFrame列名创建。

        Args:
            node: AST节点

        Returns:
            表达式字符串
        """
        if isinstance(node, ast.Compare):
            # 对于比较运算，生成更简洁的表达式
            left = ASTNodeHandler._node_to_expr_simple(node.left)
            right = ASTNodeHandler._node_to_expr_simple(node.comparators[0])
            op_sym = ASTNodeHandler._get_operator_symbol(node.ops[0])
            return f"{left} {op_sym} {right}"
        elif isinstance(node, ast.BinOp):
            # 对于二元运算，生成更简洁的表达式
            left = ASTNodeHandler._node_to_expr_simple(node.left)
            right = ASTNodeHandler._node_to_expr_simple(node.right)
            op_sym = ASTNodeHandler._get_operator_symbol(node.op)
            return f"{left} {op_sym} {right}"
        elif isinstance(node, ast.UnaryOp):
            # 对于一元运算
            operand = ASTNodeHandler._node_to_expr_simple(node.operand)
            op_sym = ASTNodeHandler._get_operator_symbol(node.op)
            return f"{op_sym}{operand}"
        else:
            # 其他情况使用原始方法
            expr = astunparse.unparse(node).strip()
            # 处理函数调用参数间的多余空格
            if isinstance(node, ast.Call):
                expr = expr.replace(', ', ',')
            return expr

    @staticmethod
    def _node_to_expr_simple(node: ast.AST) -> str:
        """生成更简洁的表达式字符串，用于内部运算

        Args:
            node: AST节点

        Returns:
            简化的表达式字符串
        """
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = ASTNodeHandler._node_to_expr_simple(node.left)
            right = ASTNodeHandler._node_to_expr_simple(node.right)
            op = ASTNodeHandler._get_operator_symbol(node.op)

            # 简化括号逻辑 - 只在真正必要时添加括号
            left_needs_parens = ASTNodeHandler._needs_parentheses(
                node.left, node.op, is_left=True
            )
            right_needs_parens = ASTNodeHandler._needs_parentheses(
                node.right, node.op, is_left=False
            )

            if left_needs_parens:
                left = f"({left})"
            if right_needs_parens:
                right = f"({right})"

            return f"{left}{op}{right}"
        elif isinstance(node, ast.UnaryOp):
            operand = ASTNodeHandler._node_to_expr_simple(node.operand)
            op = ASTNodeHandler._get_operator_symbol(node.op)
            return f"{op}{operand}"
        elif isinstance(node, ast.Call):
            # 函数调用保持原样
            func_name = node.func.id
            args = [
                ASTNodeHandler._node_to_expr_simple(arg)
                for arg in node.args
            ]
            return f"{func_name}({','.join(args)})"
        else:
            return astunparse.unparse(node).strip()

    @staticmethod
    def _needs_parentheses(child_node: ast.AST, parent_op: Any, is_left: bool = True) -> bool:
        """判断子节点是否需要括号

        Args:
            child_node: 子AST节点
            parent_op: 父节点的操作符
            is_left: 是否为左操作数

        Returns:
            是否需要添加括号
        """
        if not isinstance(child_node, ast.BinOp):
            return False

        # 获取操作符优先级
        child_op_precedence = ASTNodeHandler.OPERATOR_PRECEDENCE.get(
            type(child_node.op), 0
        )
        parent_op_precedence = ASTNodeHandler.OPERATOR_PRECEDENCE.get(
            type(parent_op), 0
        )

        # 如果子操作符优先级更低，需要括号
        if child_op_precedence < parent_op_precedence:
            return True

        # 对于相同优先级的操作符，需要处理结合性
        if child_op_precedence == parent_op_precedence:
            # 对于左结合的运算符，右操作数需要括号
            if not is_left and parent_op_precedence in [2, 3]:  # +-*/等
                return True
            # 对于幂运算，左操作数需要括号
            if is_left and isinstance(parent_op, ast.Pow):
                return True

        return False

    @staticmethod
    def _get_operator_symbol(op_node: Any) -> str:
        """获取运算符的符号表示

        Args:
            op_node: AST运算符节点

        Returns:
            运算符符号字符串
        """
        if isinstance(op_node, ast.Add):
            return "+"
        elif isinstance(op_node, ast.Sub):
            return "-"
        elif isinstance(op_node, ast.Mult):
            return "*"
        elif isinstance(op_node, ast.Div):
            return "/"
        elif isinstance(op_node, ast.FloorDiv):
            return "//"
        elif isinstance(op_node, ast.Mod):
            return "%"
        elif isinstance(op_node, ast.Pow):
            return "**"
        elif isinstance(op_node, ast.Gt):
            return ">"
        elif isinstance(op_node, ast.Lt):
            return "<"
        elif isinstance(op_node, ast.Eq):
            return "=="
        elif isinstance(op_node, ast.GtE):
            return ">="
        elif isinstance(op_node, ast.LtE):
            return "<="
        elif isinstance(op_node, ast.USub):
            return "-"
        elif isinstance(op_node, ast.UAdd):
            return "+"
        elif isinstance(op_node, ast.Not):
            return "not "
        else:
            return str(op_node)

    @staticmethod
    def get_operator_func(op_type: type) -> Any:
        """获取运算符对应的函数

        Args:
            op_type: AST运算符类型

        Returns:
            对应的运算符函数
        """
        if op_type not in ASTNodeHandler.OPERATORS:
            raise ValueError(f"不支持的运算符类型: {op_type}")
        return ASTNodeHandler.OPERATORS[op_type]
