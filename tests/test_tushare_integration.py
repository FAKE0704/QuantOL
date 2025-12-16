#!/usr/bin/env python3
"""
测试tushare数据源集成
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, '.')

def test_imports():
    """测试各个组件导入"""
    print("测试组件导入...")

    try:
        # 测试基础组件导入
        from src.core.data.data_factory import DataFactory
        print("✅ DataFactory导入成功")

        # 测试baostock导入
        from src.core.data.baostock_source import BaostockDataSource
        print("✅ BaostockDataSource导入成功")

        # 测试新的tushare组件导入
        from src.core.data.adapters.tushare_adapter import TushareAdapter
        print("✅ TushareAdapter导入成功")

        from src.core.data.transformers.data_transformer import DataTransformer
        print("✅ DataTransformer导入成功")

        from src.core.data.cache.cache_manager import CacheManager
        print("✅ CacheManager导入成功")

        from src.core.data.config.tushare_config import TushareConfig
        print("✅ TushareConfig导入成功")

        from src.services.data.tushare_market_service import TushareMarketService
        print("✅ TushareMarketService导入成功")

        from src.core.data.adapters.tushare_service_adapter import TushareServiceAdapter
        print("✅ TushareServiceAdapter导入成功")

        return True

    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_registration():
    """测试数据源注册"""
    print("\n测试数据源注册...")

    try:
        from src.core.data.register_tushare import register_tushare_source

        # 注册tushare数据源
        register_tushare_source()

        from src.core.data.data_factory import DataFactory
        registered_sources = list(DataFactory._registered_sources.keys())

        print(f"已注册的数据源: {registered_sources}")

        if "tushare" in registered_sources:
            print("✅ Tushare数据源注册成功")
            return True
        else:
            print("❌ Tushare数据源注册失败")
            return False

    except Exception as e:
        print(f"❌ 注册失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_source_creation():
    """测试数据源创建"""
    print("\n测试数据源创建...")

    try:
        from src.core.data.register_tushare import get_tushare_source

        # 创建tushare数据源实例（使用示例token）
        tushare_source = get_tushare_source(token="test_token")

        if tushare_source is not None:
            print("✅ Tushare数据源创建成功")
            print(f"数据源类型: {type(tushare_source)}")
            return True
        else:
            print("❌ Tushare数据源创建失败")
            return False

    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config():
    """测试配置管理"""
    print("\n测试配置管理...")

    try:
        from src.core.data.config.tushare_config import TushareConfig

        # 测试配置创建
        config = TushareConfig(token="test_token")
        print("✅ 配置创建成功")

        # 测试配置验证
        is_valid = config.validate()
        print(f"✅ 配置验证: {is_valid}")

        # 测试配置字典转换
        config_dict = config.to_dict()
        print(f"✅ 配置转换: {len(config_dict)} 个配置项")

        return True

    except Exception as e:
        print(f"❌ 配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("Tushare数据源集成测试")
    print("=" * 50)

    results = []

    # 运行各项测试
    results.append(("组件导入", test_imports()))
    results.append(("数据源注册", test_registration()))
    results.append(("数据源创建", test_source_creation()))
    results.append(("配置管理", test_config()))

    # 汇总结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1

    print(f"\n总计: {passed}/{total} 项测试通过")

    if passed == total:
        print("🎉 所有测试通过！Tushare数据源集成成功！")
        return True
    else:
        print("⚠️  部分测试失败，请检查错误信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)