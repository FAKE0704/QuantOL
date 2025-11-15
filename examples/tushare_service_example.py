#!/usr/bin/env python3
"""
Tushare服务使用示例
演示如何使用新的细粒度tushare数据服务
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.data.tushare_market_service import TushareMarketService
from src.core.data.config.tushare_config import TushareConfig
from src.core.data.register_tushare import get_tushare_source


async def example_basic_usage():
    """基本使用示例"""
    print("=== Tushare服务基本使用示例 ===")

    # 从环境变量加载配置
    try:
        config = TushareConfig.from_env()
        print(f"配置加载成功，缓存: {'启用' if config.cache_enabled else '禁用'}")
    except ValueError as e:
        print(f"环境变量配置失败: {e}")
        # 使用示例配置（需要设置实际的token）
        config = TushareConfig(
            token="your_token_here",  # 请替换为实际的token
            cache_enabled=True,
            cache_ttl=3600
        )

    # 创建服务实例
    service = TushareMarketService(config)

    # 测试连接
    print("\n1. 测试连接...")
    connection_result = await service.test_connection()
    if connection_result['success']:
        print("✅ 连接成功")
    else:
        print(f"❌ 连接失败: {connection_result}")
        return

    # 获取股票列表（示例：只获取前10条）
    print("\n2. 获取股票列表...")
    try:
        stock_list = await service.get_stock_list()
        print(f"✅ 成功获取 {len(stock_list)} 条股票信息")
        print("前5条股票:")
        print(stock_list.head()[['symbol_code', 'name', 'industry']].to_string())
    except Exception as e:
        print(f"❌ 获取股票列表失败: {e}")

    # 获取市场数据
    print("\n3. 获取市场数据...")
    try:
        # 获取平安银行的最近30天数据
        market_data = await service.get_market_data(
            symbol_code="000001.SZ",
            start_date="20241101",
            end_date="20241130"
        )
        print(f"✅ 成功获取 {len(market_data)} 条市场数据")
        if not market_data.empty:
            print("最近5条数据:")
            print(market_data.tail()[['date', 'open', 'high', 'low', 'close']].to_string())
    except Exception as e:
        print(f"❌ 获取市场数据失败: {e}")

    # 获取服务统计
    print("\n4. 服务统计...")
    stats = await service.get_service_stats()
    print(f"总请求次数: {stats['service_stats']['total_requests']}")
    print(f"成功次数: {stats['service_stats']['successful_requests']}")
    print(f"缓存命中: {stats['service_stats'].get('cache_hits', 0)}")


async def example_data_factory_usage():
    """DataFactory集成使用示例"""
    print("\n\n=== DataFactory集成使用示例 ===")

    try:
        # 通过DataFactory获取tushare数据源
        tushare_source = get_tushare_source()
        print("✅ 成功通过DataFactory获取tushare数据源")

        # 获取股票列表
        stock_list = await tushare_source.get_stock_list()
        print(f"✅ 成功获取 {len(stock_list)} 条股票信息")

        # 同步获取数据（兼容旧接口）
        print("\n同步获取数据示例...")
        data = tushare_source.get_data(
            symbol="000001.SZ",
            fields=['date', 'open', 'high', 'low', 'close'],
            start_date="20241101",
            end_date="20241105"
        )
        print(f"✅ 同步获取 {len(data)} 条数据")

        # 测试连接
        connection_result = await tushare_source.test_connection()
        print(f"连接状态: {'✅ 成功' if connection_result['success'] else '❌ 失败'}")

    except Exception as e:
        print(f"❌ DataFactory使用失败: {e}")


async def example_batch_operations():
    """批量操作示例"""
    print("\n\n=== 批量操作示例 ===")

    try:
        config = TushareConfig.from_env()
        service = TushareMarketService(config)

        # 批量获取多个股票的数据
        symbols = ["000001.SZ", "000002.SZ", "600000.SH"]
        print(f"批量获取 {len(symbols)} 个股票的数据...")

        batch_data = await service.batch_get_market_data(
            symbol_codes=symbols,
            start_date="20241101",
            end_date="20241105",
            max_concurrent=2
        )

        for symbol, data in batch_data.items():
            print(f"  {symbol}: {len(data)} 条数据")

        print("✅ 批量获取完成")

    except Exception as e:
        print(f"❌ 批量操作失败: {e}")


async def example_cache_operations():
    """缓存操作示例"""
    print("\n\n=== 缓存操作示例 ===")

    try:
        config = TushareConfig.from_env()
        if not config.cache_enabled:
            print("❌ 缓存未启用，跳过缓存示例")
            return

        service = TushareMarketService(config)

        # 第一次获取（会缓存）
        print("第一次获取股票列表（会缓存）...")
        await service.get_stock_list()

        # 第二次获取（从缓存）
        print("第二次获取股票列表（从缓存）...")
        await service.get_stock_list()

        # 查看缓存统计
        stats = await service.get_service_stats()
        if 'cache_stats' in stats:
            cache_stats = stats['cache_stats']
            print(f"缓存命中率: {cache_stats.get('hit_rate', 0):.1f}%")
            print(f"总缓存项: {cache_stats.get('total_keys', 0)}")

        # 清理缓存
        print("清理缓存...")
        clear_result = await service.clear_cache()
        print(f"清理结果: {clear_result}")

    except Exception as e:
        print(f"❌ 缓存操作失败: {e}")


def main():
    """主函数"""
    print("Tushare细粒度服务示例")
    print("=" * 50)

    # 检查环境变量
    if not os.getenv('TUSHARE_TOKEN'):
        print("⚠️  警告: 未设置 TUSHARE_TOKEN 环境变量")
        print("请设置环境变量或在代码中提供token:")
        print("export TUSHARE_TOKEN='your_token_here'")
        print()

    # 运行示例
    asyncio.run(example_basic_usage())
    asyncio.run(example_data_factory_usage())
    asyncio.run(example_batch_operations())
    asyncio.run(example_cache_operations())

    print("\n" + "=" * 50)
    print("示例运行完成!")


if __name__ == "__main__":
    main()