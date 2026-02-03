"""共享工具模块

提供API路由中使用的共享工具函数。
"""
from typing import Optional, AsyncGenerator
import json


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


async def stream_json_response(data: dict) -> AsyncGenerator[bytes, None]:
    """流式JSON响应

    Args:
        data: 要序列化的数据

    Yields:
        JSON数据的字节块
    """
    json_str = json.dumps(data, ensure_ascii=False, default=str)
    chunk_size = 8192
    for i in range(0, len(json_str), chunk_size):
        yield json_str[i:i + chunk_size].encode('utf-8')
