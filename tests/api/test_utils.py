"""
测试 API 工具函数

重点测试 JSON 序列化器处理 NaN/Inf 的行为
"""
import json
import math
import numpy as np
import pytest
import asyncio

import sys
from pathlib import Path
# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.api.utils import _json_serializer, stream_json_response, _clean_special_floats


class TestJsonSerializer:
    """测试 _json_serializer 函数"""

    def test_nan_converts_to_none(self):
        """测试 NaN 转换为 None"""
        result = _json_serializer(float('nan'))
        assert result is None

    def test_numpy_nan_converts_to_none(self):
        """测试 NumPy NaN 转换为 None"""
        result = _json_serializer(np.nan)
        assert result is None

    def test_positive_inf_converts_to_none(self):
        """测试正无穷大转换为 None"""
        result = _json_serializer(float('inf'))
        assert result is None

    def test_negative_inf_converts_to_none(self):
        """测试负无穷大转换为 None"""
        result = _json_serializer(float('-inf'))
        assert result is None

    def test_normal_float_unchanged(self):
        """测试普通浮点数保持不变（通过抛出异常）"""
        with pytest.raises(TypeError, match="not JSON serializable"):
            _json_serializer(1.23)

    def test_non_float_raises_error(self):
        """测试非浮点类型抛出异常"""
        with pytest.raises(TypeError, match="Object of type str is not JSON serializable"):
            _json_serializer("string")


class TestCleanSpecialFloats:
    """测试 _clean_special_floats 函数"""

    def test_nan_converts_to_none(self):
        """测试 NaN 转换为 None"""
        result = _clean_special_floats(float('nan'))
        assert result is None

    def test_numpy_nan_converts_to_none(self):
        """测试 NumPy NaN 转换为 None"""
        result = _clean_special_floats(np.nan)
        assert result is None

    def test_inf_converts_to_none(self):
        """测试 Infinity 转换为 None"""
        result = _clean_special_floats(float('inf'))
        assert result is None

    def test_negative_inf_converts_to_none(self):
        """测试负无穷大转换为 None"""
        result = _clean_special_floats(float('-inf'))
        assert result is None

    def test_normal_float_unchanged(self):
        """测试普通浮点数保持不变"""
        result = _clean_special_floats(1.23)
        assert result == 1.23

    def test_dict_with_nan(self):
        """测试字典中的 NaN 被转换"""
        data = {"value": float('nan'), "normal": 123}
        result = _clean_special_floats(data)
        assert result["value"] is None
        assert result["normal"] == 123

    def test_nested_dict(self):
        """测试嵌套字典中的 NaN 被转换"""
        data = {"level1": {"level2": {"nan": float('nan'), "normal": 42}}}
        result = _clean_special_floats(data)
        assert result["level1"]["level2"]["nan"] is None
        assert result["level1"]["level2"]["normal"] == 42

    def test_list_with_nan(self):
        """测试列表中的 NaN 被转换"""
        data = [1.0, float('nan'), 3.0]
        result = _clean_special_floats(data)
        assert result == [1.0, None, 3.0]

    def test_tuple_with_nan(self):
        """测试元组中的 NaN 被转换，保持类型"""
        data = (1.0, float('nan'), 3.0)
        result = _clean_special_floats(data)
        assert result == (1.0, None, 3.0)
        assert isinstance(result, tuple)

    def test_non_float_unchanged(self):
        """测试非浮点类型保持不变"""
        data = {"str": "test", "int": 42, "bool": True, "none": None}
        result = _clean_special_floats(data)
        assert result == data

    def test_empty_structures(self):
        """测试空结构"""
        assert _clean_special_floats({}) == {}
        assert _clean_special_floats([]) == []
        assert _clean_special_floats(None) is None


class TestJsonDumpsWithCleanedData:
    """测试 json.dumps 使用自定义序列化器"""

    def test_simple_nan_in_dict(self):
        """测试字典中的 NaN 被转换为 null"""
        data = {"value": float('nan')}
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)
        assert result == '{"value": null}'

    def test_numpy_nan_in_dict(self):
        """测试字典中的 NumPy NaN 被转换为 null"""
        data = {"value": np.nan}
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)
        assert result == '{"value": null}'

    def test_nested_nan(self):
        """测试嵌套结构中的 NaN 被转换"""
        data = {
            "level1": {
                "level2": {
                    "nan_value": float('nan'),
                    "normal_value": 42
                }
            }
        }
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)
        assert '"nan_value": null' in result
        assert '"normal_value": 42' in result

    def test_inf_in_dict(self):
        """测试字典中的 Infinity 被转换为 null"""
        data = {"positive_inf": float('inf'), "negative_inf": float('-inf')}
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)
        assert result == '{"positive_inf": null, "negative_inf": null}'

    def test_list_with_nan(self):
        """测试列表中的 NaN 被转换"""
        data = {"values": [1.0, float('nan'), 3.0, np.nan]}
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)
        assert result == '{"values": [1.0, null, 3.0, null]}'

    def test_complex_backtest_data(self):
        """测试复杂的回测数据结构"""
        # 模拟回测结果数据
        data = {
            "summary": {
                "total_return": float('nan'),
                "sharpe_ratio": 1.5,
                "max_drawdown": float('-inf'),
            },
            "trades": [
                {"profit": 100.0, "return_pct": 0.05},
                {"profit": np.nan, "return_pct": float('inf')},
            ],
            "equity_curve": [1000, 1050, float('nan'), 1100]
        }
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)

        # 验证结果
        parsed = json.loads(result)
        assert parsed["summary"]["total_return"] is None
        assert parsed["summary"]["sharpe_ratio"] == 1.5
        assert parsed["summary"]["max_drawdown"] is None
        assert parsed["trades"][1]["profit"] is None
        assert parsed["trades"][1]["return_pct"] is None
        assert parsed["equity_curve"][2] is None

    def test_valid_json_output(self):
        """测试输出是有效的 JSON"""
        data = {"nan": float('nan'), "inf": float('inf'), "normal": 123}
        cleaned = _clean_special_floats(data)
        result = json.dumps(cleaned, ensure_ascii=False)

        # 验证可以重新解析
        parsed = json.loads(result)
        assert parsed["nan"] is None
        assert parsed["inf"] is None
        assert parsed["normal"] == 123


class TestStreamJsonResponse:
    """测试 stream_json_response 异步生成器"""

    @pytest.mark.asyncio
    async def test_simple_data(self):
        """测试简单数据的流式响应"""
        data = {"message": "hello", "value": 42}
        chunks = []
        async for chunk in stream_json_response(data):
            chunks.append(chunk)

        # 组合所有块
        result = b''.join(chunks).decode('utf-8')
        parsed = json.loads(result)
        assert parsed["message"] == "hello"
        assert parsed["value"] == 42

    @pytest.mark.asyncio
    async def test_nan_handling(self):
        """测试流式响应中 NaN 的处理"""
        data = {
            "normal": 123,
            "nan_value": float('nan'),
            "inf_value": float('inf')
        }
        chunks = []
        async for chunk in stream_json_response(data):
            chunks.append(chunk)

        result = b''.join(chunks).decode('utf-8')
        parsed = json.loads(result)
        assert parsed["normal"] == 123
        assert parsed["nan_value"] is None
        assert parsed["inf_value"] is None

    @pytest.mark.asyncio
    async def test_chunking(self):
        """测试数据被正确分块"""
        # 创建足够大的数据以确保分块
        large_data = {"key_" + str(i): i * 1.5 for i in range(1000)}
        chunks = []
        async for chunk in stream_json_response(large_data):
            chunks.append(chunk)

        # 验证至少有多个块
        assert len(chunks) > 1

        # 验证组合后的数据是正确的
        result = b''.join(chunks).decode('utf-8')
        parsed = json.loads(result)
        assert len(parsed) == 1000
        assert parsed["key_0"] == 0
        assert parsed["key_999"] == 999 * 1.5

    @pytest.mark.asyncio
    async def test_unicode(self):
        """测试 Unicode 字符的正确处理"""
        data = {"chinese": "你好", "emoji": "😀", "normal": "test"}
        chunks = []
        async for chunk in stream_json_response(data):
            chunks.append(chunk)

        result = b''.join(chunks).decode('utf-8')
        parsed = json.loads(result)
        assert parsed["chinese"] == "你好"
        assert parsed["emoji"] == "😀"
        assert parsed["normal"] == "test"

    @pytest.mark.asyncio
    async def test_numpy_types(self):
        """测试 NumPy 类型的处理"""
        data = {
            "np_int": np.int64(42),
            "np_float": np.float64(3.14),
            "np_nan": np.nan,
            "np_inf": np.float64('inf')
        }
        chunks = []
        async for chunk in stream_json_response(data):
            chunks.append(chunk)

        result = b''.join(chunks).decode('utf-8')
        parsed = json.loads(result)
        assert parsed["np_int"] == 42
        assert parsed["np_float"] == 3.14
        assert parsed["np_nan"] is None
        assert parsed["np_inf"] is None


class TestEdgeCases:
    """测试边界情况"""

    def test_empty_dict(self):
        """测试空字典"""
        data = {}
        result = json.dumps(_clean_special_floats(data), ensure_ascii=False)
        assert result == '{}'

    def test_deeply_nested_structure(self):
        """测试深层嵌套结构"""
        data = {"a": {"b": {"c": {"d": float('nan')}}}}
        result = json.dumps(_clean_special_floats(data), ensure_ascii=False)
        parsed = json.loads(result)
        assert parsed["a"]["b"]["c"]["d"] is None

    def test_mixed_nan_types(self):
        """测试混合多种 NaN 类型"""
        data = {
            "python_nan": float('nan'),
            "numpy_nan": np.nan,
            "normal": 123
        }
        result = json.dumps(_clean_special_floats(data), ensure_ascii=False)
        parsed = json.loads(result)
        assert parsed["python_nan"] is None
        assert parsed["numpy_nan"] is None
        assert parsed["normal"] == 123

    def test_large_nan_count(self):
        """测试大量 NaN 的处理"""
        data = {f"key_{i}": float('nan') if i % 2 == 0 else i for i in range(1000)}
        result = json.dumps(_clean_special_floats(data), ensure_ascii=False)
        parsed = json.loads(result)

        # 验证偶数键的值都是 None
        for i in range(0, 1000, 2):
            assert parsed[f"key_{i}"] is None
        # 验证奇数键的值正确
        for i in range(1, 1000, 2):
            assert parsed[f"key_{i}"] == i
