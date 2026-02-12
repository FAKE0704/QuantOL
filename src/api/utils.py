"""共享工具模块

提供API路由中使用的共享工具函数。
"""
from typing import Optional, AsyncGenerator, Any
import json
import math


def filter_result_summary(result_summary: Optional[dict]) -> dict:
    """过滤结果摘要（避免大响应）

    Args:
        result_summary: 完整的结果摘要

    Returns:
        过滤后的结果摘要
    """
    if not result_summary or not isinstance(result_summary, dict):
        return {}

    # 检查是否为多标的模式
    if "individual" in result_summary:
        # 多标的模式
        filtered = {
            "individual": {},
            "combined_equity": result_summary.get("combined_equity"),
        }

        # 从每个标的结果中提取摘要
        individual_results = result_summary.get("individual", {})
        if isinstance(individual_results, dict):
            for symbol, symbol_result in individual_results.items():
                if isinstance(symbol_result, dict):
                    filtered["individual"][symbol] = {
                        "summary": symbol_result.get("summary", {}),
                        "performance_metrics": symbol_result.get("performance_metrics", {}),
                    }

        # 添加策略映射
        if "strategy_mapping" in result_summary:
            filtered["strategy_mapping"] = result_summary["strategy_mapping"]
        if "default_strategy" in result_summary:
            filtered["default_strategy"] = result_summary["default_strategy"]

        return filtered

    # 单标的模式
    return {
        "summary": result_summary.get("summary", {}),
        "performance_metrics": result_summary.get("performance_metrics", {}),
    }


def validate_rule_syntax(rule: str) -> tuple[bool, str]:
    """验证规则语法包装器

    Args:
        rule: 规则表达式

    Returns:
        (是否有效, 错误信息)
    """
    from src.core.strategy.rule_parser import RuleParser
    return RuleParser.validate_syntax(rule)


def _clean_special_floats(obj: Any) -> Any:
    """递归清理数据中的 NaN 和 Inf 值

    将所有 NaN 和 Inf 替换为 None，确保 JSON 序列化安全。

    Args:
        obj: 要清理的对象

    Returns:
        清理后的对象
    """
    import numpy as np

    # 处理 NumPy 标量类型
    if isinstance(obj, (np.integer, np.floating)):
        obj = obj.item()  # 转换为 Python 标量类型

    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    elif isinstance(obj, dict):
        return {k: _clean_special_floats(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_clean_special_floats(item) for item in obj)
    else:
        return obj


def _json_serializer(obj):
    """自定义JSON序列化器，处理NaN和Inf等特殊浮点值

    Args:
        obj: 要序列化的对象

    Returns:
        可序列化的值
    """
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None  # 将NaN和Inf转换为null
    raise TypeError(f'Object of type {type(obj).__name__} is not JSON serializable')


async def stream_json_response(data: dict) -> AsyncGenerator[bytes, None]:
    """流式JSON响应

    Args:
        data: 要序列化的数据

    Yields:
        JSON数据的字节块
    """
    # 先清理 NaN/Inf，再序列化
    cleaned_data = _clean_special_floats(data)
    json_str = json.dumps(cleaned_data, ensure_ascii=False)
    chunk_size = 8192
    for i in range(0, len(json_str), chunk_size):
        yield json_str[i:i + chunk_size].encode('utf-8')
