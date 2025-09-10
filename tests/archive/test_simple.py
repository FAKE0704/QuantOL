#!/usr/bin/env python3
"""简单测试表达式生成"""

import ast
import astunparse

# 测试表达式生成函数
def test_expression_generation():
    # 测试Martingale规则表达式
    rule = "(close - (COST / POSITION)) / (COST / POSITION) * 100 <= -5"
    
    print("原始规则:", rule)
    
    # 解析AST
    tree = ast.parse(rule, mode='eval')
    
    # 模拟 _node_to_expr_simple 函数
    def _get_operator_symbol(op_node):
        if isinstance(op_node, ast.Add):
            return "+"
        elif isinstance(op_node, ast.Sub):
            return "-"
        elif isinstance(op_node, ast.Mult):
            return "*"
        elif isinstance(op_node, ast.Div):
            return "/"
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
        return str(op_node)
    
    def _needs_parentheses(child_node, parent_op, is_left=True):
        """判断子节点是否需要括号"""
        if not isinstance(child_node, ast.BinOp):
            return False
            
        # 获取操作符优先级
        op_precedence = {
            ast.Pow: 4,
            ast.Mult: 3, ast.Div: 3, ast.FloorDiv: 3, ast.Mod: 3,
            ast.Add: 2, ast.Sub: 2,
            ast.Gt: 1, ast.Lt: 1, ast.Eq: 1, ast.GtE: 1, ast.LtE: 1
        }
        
        child_op_precedence = op_precedence.get(type(child_node.op), 0)
        parent_op_precedence = op_precedence.get(type(parent_op), 0)
        
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
    
    def _node_to_expr_simple(node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Constant):
            return str(node.value)
        elif isinstance(node, ast.BinOp):
            left = _node_to_expr_simple(node.left)
            right = _node_to_expr_simple(node.right)
            op = _get_operator_symbol(node.op)
            
            # 只在必要时添加括号
            left_needs_parens = _needs_parentheses(node.left, node.op, is_left=True)
            right_needs_parens = _needs_parentheses(node.right, node.op, is_left=False)
            
            if left_needs_parens:
                left = f"({left})"
            if right_needs_parens:
                right = f"({right})"
                
            return f"{left} {op} {right}"
        elif isinstance(node, ast.UnaryOp):
            operand = _node_to_expr_simple(node.operand)
            op = _get_operator_symbol(node.op)
            return f"{op}{operand}"
        else:
            return astunparse.unparse(node).strip()
    
    def _node_to_expr(node):
        if isinstance(node, ast.Compare):
            left = _node_to_expr_simple(node.left)
            right = _node_to_expr_simple(node.comparators[0])
            op = _get_operator_symbol(node.ops[0])
            return f"{left} {op} {right}"
        elif isinstance(node, ast.BinOp):
            left = _node_to_expr_simple(node.left)
            right = _node_to_expr_simple(node.right)
            op = _get_operator_symbol(node.op)
            return f"{left} {op} {right}"
        else:
            return astunparse.unparse(node).strip()
    
    # 生成表达式
    generated_expr = _node_to_expr(tree.body)
    print("生成的表达式:", generated_expr)
    
    # 检查是否包含不必要的括号
    if "((" in generated_expr or "))" in generated_expr:
        print("警告: 表达式包含不必要的括号")
    else:
        print("表达式格式良好")

if __name__ == "__main__":
    test_expression_generation()