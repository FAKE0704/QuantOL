#!/usr/bin/env python3
"""
执行全部测试脚本

此脚本用于运行项目中的所有测试文件，包括：
- tests/core/strategy/test_rule_parser.py
- tests/archive/test_martingale.py
- tests/archive/test_simple.py
- tests/core/data/test_market_data_source.py
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class TestRunner:
    def __init__(self):
        self.project_root = project_root
        self.test_files = [
            "tests/core/strategy/test_rule_parser.py",
            "tests/archive/test_martingale.py",
            "tests/archive/test_simple.py",
            "tests/core/data/test_market_data_source.py"
        ]
        self.results = {}

    def print_header(self, message):
        """打印标题"""
        print("\n" + "="*60)
        print(f" {message}")
        print("="*60)

    def run_test_file(self, test_file_path):
        """运行单个测试文件"""
        full_path = self.project_root / test_file_path

        if not full_path.exists():
            print(f"❌ 测试文件不存在: {test_file_path}")
            return False

        self.print_header(f"运行测试: {test_file_path}")

        try:
            # 使用pytest运行测试，添加src目录到Python路径
            env = os.environ.copy()
            env['PYTHONPATH'] = str(self.project_root) + os.pathsep + env.get('PYTHONPATH', '')

            # 直接运行Python文件而不是使用pytest
            result = subprocess.run(
                [sys.executable, str(full_path)],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                env=env
            )

            # 输出测试结果
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)

            success = result.returncode == 0

            if success:
                print(f"✅ {test_file_path} - 测试通过")
            else:
                print(f"❌ {test_file_path} - 测试失败")

            return success

        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file_path} - 测试超时")
            return False
        except Exception as e:
            print(f"💥 {test_file_path} - 执行错误: {e}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        self.print_header("开始执行全部测试")

        start_time = time.time()
        total_tests = len(self.test_files)
        passed_tests = 0

        for test_file in self.test_files:
            if self.run_test_file(test_file):
                passed_tests += 1

            print()  # 空行分隔

        end_time = time.time()
        duration = end_time - start_time

        # 输出总结
        self.print_header("测试总结")
        print(f"总测试文件数: {total_tests}")
        print(f"通过测试数: {passed_tests}")
        print(f"失败测试数: {total_tests - passed_tests}")
        print(f"测试通过率: {passed_tests/total_tests*100:.1f}%")
        print(f"总耗时: {duration:.2f} 秒")

        if passed_tests == total_tests:
            print("🎉 所有测试通过！")
        else:
            print("⚠️ 部分测试失败，请检查相关代码")

        return passed_tests == total_tests

    def run_specific_test(self, test_file_path):
        """运行指定测试文件"""
        if test_file_path not in self.test_files:
            print(f"❌ 测试文件不在列表中: {test_file_path}")
            print(f"可用测试文件: {', '.join(self.test_files)}")
            return False

        return self.run_test_file(test_file_path)

def main():
    """主函数"""
    runner = TestRunner()

    # 检查命令行参数
    if len(sys.argv) > 1:
        # 运行指定测试
        test_file = sys.argv[1]
        success = runner.run_specific_test(test_file)
        sys.exit(0 if success else 1)
    else:
        # 运行所有测试
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()