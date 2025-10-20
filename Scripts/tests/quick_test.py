#!/usr/bin/env python3
"""
快速测试脚本

此脚本提供简化的测试执行方式，适合快速验证
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def run_quick_test():
    """快速运行所有测试"""
    print("🚀 快速测试开始...\n")

    test_files = [
        "tests/core/strategy/test_rule_parser.py",
        "tests/archive/test_martingale.py",
        "tests/archive/test_simple.py",
        "tests/core/data/test_market_data_source.py"
    ]

    results = []

    for test_file in test_files:
        full_path = project_root / test_file

        if not full_path.exists():
            print(f"❌ 跳过: {test_file} (文件不存在)")
            results.append((test_file, "skipped"))
            continue

        print(f"📋 运行: {test_file}")

        try:
            # 设置Python路径
            env = os.environ.copy()
            env['PYTHONPATH'] = str(project_root) + os.pathsep + env.get('PYTHONPATH', '')

            result = subprocess.run(
                [sys.executable, "-m", "pytest", str(full_path), "-q"],
                cwd=project_root,
                capture_output=True,
                text=True,
                timeout=120,  # 2分钟超时
                env=env
            )

            if result.returncode == 0:
                print(f"   ✅ 通过")
                results.append((test_file, "passed"))
            else:
                print(f"   ❌ 失败")
                results.append((test_file, "failed"))

        except subprocess.TimeoutExpired:
            print(f"   ⏰ 超时")
            results.append((test_file, "timeout"))
        except Exception as e:
            print(f"   💥 错误: {e}")
            results.append((test_file, "error"))

    # 输出总结
    print("\n📊 测试总结:")
    print("-" * 40)

    passed = sum(1 for _, status in results if status == "passed")
    total = len(results)

    for test_file, status in results:
        status_symbol = {
            "passed": "✅",
            "failed": "❌",
            "timeout": "⏰",
            "error": "💥",
            "skipped": "⏭️"
        }.get(status, "❓")
        print(f"{status_symbol} {test_file}")

    print("-" * 40)
    print(f"总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")

    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败")

    return passed == total

def run_single_test(test_file):
    """运行单个测试文件"""
    full_path = project_root / test_file

    if not full_path.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False

    print(f"🔍 运行单个测试: {test_file}")

    try:
        # 设置Python路径
        env = os.environ.copy()
        env['PYTHONPATH'] = str(project_root) + os.pathsep + env.get('PYTHONPATH', '')

        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(full_path), "-v"],
            cwd=project_root,
            capture_output=False,
            timeout=300,
            env=env
        )

        return result.returncode == 0

    except Exception as e:
        print(f"💥 执行错误: {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 运行指定测试
        test_file = sys.argv[1]
        success = run_single_test(test_file)
    else:
        # 运行所有测试
        success = run_quick_test()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()