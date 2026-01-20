"""
回测专用调试日志记录器

为每次回测创建独立的日志文件，包含：
- 信号生成记录
- 仓位计算详情
- 订单创建记录
- 交易执行记录
- 汇总统计

日志文件命名格式: {backtest_id}_{策略名称}_{时间戳}_debug.log
示例: bt_20260116123456_双均线策略_20260116_143022_debug.log
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class BacktestDebugLogger:
    """回测专用调试日志记录器"""

    def __init__(self, backtest_id: str, strategy_name: str, config: Optional[Dict[str, Any]] = None):
        """
        初始化回测调试日志

        Args:
            backtest_id: 回测唯一标识
            strategy_name: 策略名称
            config: 回测配置（可选）
        """
        self.backtest_id = backtest_id
        self.strategy_name = strategy_name
        self.config = config or {}

        # 统计计数器
        self.signal_count = 0
        self.order_created_count = 0
        self.trade_executed_count = 0
        self.position_zero_count = 0

        # 创建日志目录
        self.log_dir = Path(__file__).parent.parent.parent / "logs" / "backtests"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # 创建日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # 清理策略名称，移除特殊字符
        safe_strategy_name = self._sanitize_filename(strategy_name)
        filename = f"{backtest_id}_{safe_strategy_name}_{timestamp}_debug.log"
        self.log_path = self.log_dir / filename

        # 初始化logger
        self.logger = logging.getLogger(f"backtest_debug_{backtest_id}")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False  # 不传播到父logger

        # 清除已有的handlers
        self.logger.handlers.clear()

        # 创建文件handler
        file_handler = logging.FileHandler(self.log_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 设置格式：简化的格式，便于阅读
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # 写入回测开始信息
        self._write_header()

    def _sanitize_filename(self, name: str) -> str:
        """清理文件名，移除特殊字符"""
        # 移除或替换特殊字符
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        # 限制长度
        return name[:50] if len(name) > 50 else name

    def _write_header(self):
        """写入日志头部信息"""
        separator = "=" * 80
        self.logger.info(separator)
        self.logger.info(f"回测调试日志: {self.backtest_id}")
        self.logger.info(f"策略名称: {self.strategy_name}")
        self.logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("")

        # 写入配置信息
        if self.config:
            self.logger.info("【回测配置】")
            for key, value in self.config.items():
                if key not in ['custom_rules', 'default_custom_rules', 'strategy_mapping']:
                    self.logger.info(f"  {key}: {value}")
            self.logger.info("")

        self.logger.info(separator)
        self.logger.info("")

    def log_signal(self, index: int, signal_type: str, symbol: str,
                   price: float, rule_name: str = "", extra: str = ""):
        """
        记录信号生成

        Args:
            index: 数据索引
            signal_type: 信号类型 (OPEN, CLOSE, BUY, SELL)
            symbol: 标的代码
            price: 价格
            rule_name: 触发的规则名称
            extra: 额外信息
        """
        self.signal_count += 1
        rule_info = f" | 规则: {rule_name}" if rule_name else ""
        extra_info = f" | {extra}" if extra else ""
        self.logger.info(f"[信号生成 #{self.signal_count:04d}] 索引={index} | {signal_type} | {symbol} @ {price:.2f}{rule_info}{extra_info}")

    def log_position_calculation(self, index: int, signal_type: str,
                                 available_cash: float, total_equity: float,
                                 current_position: int, calculated_quantity: int,
                                 reason: str = ""):
        """
        记录仓位计算结果

        Args:
            index: 数据索引
            signal_type: 信号类型
            available_cash: 可用资金
            total_equity: 总权益
            current_position: 当前持仓
            calculated_quantity: 计算结果
            reason: 数量为0的原因
        """
        if calculated_quantity == 0:
            self.position_zero_count += 1

        zero_mark = " ⚠️ 数量为0" if calculated_quantity == 0 else ""
        reason_info = f" | 原因: {reason}" if reason else ""

        self.logger.info(
            f"[仓位计算] 索引={index} | {signal_type} | "
            f"可用资金={available_cash:.2f} | 总权益={total_equity:.2f} | "
            f"当前持仓={current_position} | "
            f"计算结果={calculated_quantity}{zero_mark}{reason_info}"
        )

    def log_order_created(self, index: int, direction: str, symbol: str,
                         quantity: int, price: float):
        """
        记录订单创建

        Args:
            index: 数据索引
            direction: 方向 (BUY/SELL)
            symbol: 标的代码
            quantity: 数量
            price: 价格
        """
        self.order_created_count += 1
        self.logger.info(f"[订单创建 #{self.order_created_count:04d}] 索引={index} | {direction} {quantity}股 {symbol} @ {price:.2f}")

    def log_order_skipped(self, index: int, signal_type: str, reason: str):
        """
        记录订单被跳过

        Args:
            index: 数据索引
            signal_type: 信号类型
            reason: 跳过原因
        """
        self.logger.warning(f"[订单跳过] 索引={index} | {signal_type} | 原因: {reason}")

    def log_trade_executed(self, index: int, direction: str, symbol: str,
                          quantity: int, price: float, commission: float):
        """
        记录交易执行

        Args:
            index: 数据索引
            direction: 方向
            symbol: 标的代码
            quantity: 数量
            price: 价格
            commission: 手续费
        """
        self.trade_executed_count += 1
        total_cost = quantity * price + commission if direction == 'BUY' else quantity * price - commission
        self.logger.info(
            f"[交易执行 #{self.trade_executed_count:04d}] 索引={index} | "
            f"{direction} {quantity}股 {symbol} @ {price:.2f} | "
            f"手续费={commission:.2f} | 总金额={total_cost:.2f}"
        )

    def log_warning(self, message: str):
        """记录警告"""
        self.logger.warning(f"[警告] {message}")

    def log_error(self, message: str):
        """记录错误"""
        self.logger.error(f"[错误] {message}")

    def log_info(self, message: str):
        """记录普通信息"""
        self.logger.info(f"[信息] {message}")

    def log_extra(self, message: str):
        """记录额外调试信息"""
        self.logger.info(f"{message}")

    def write_summary(self, total_data_points: int):
        """
        写入回测汇总统计

        Args:
            total_data_points: 总数据点数
        """
        separator = "=" * 80
        self.logger.info("")
        self.logger.info(separator)
        self.logger.info("【回测汇总统计】")
        self.logger.info(f"  回测ID: {self.backtest_id}")
        self.logger.info(f"  策略名称: {self.strategy_name}")
        self.logger.info(f"  结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info("")
        self.logger.info("【统计数据】")
        self.logger.info(f"  总数据点数: {total_data_points}")
        self.logger.info(f"  信号生成总数: {self.signal_count}")
        self.logger.info(f"  订单创建总数: {self.order_created_count}")
        self.logger.info(f"  交易执行总数: {self.trade_executed_count}")
        self.logger.info(f"  仓位计算为0次数: {self.position_zero_count}")

        # 计算转换率
        if self.signal_count > 0:
            order_rate = (self.order_created_count / self.signal_count) * 100
            self.logger.info(f"  信号→订单转换率: {order_rate:.1f}% ({self.order_created_count}/{self.signal_count})")

        if self.order_created_count > 0:
            trade_rate = (self.trade_executed_count / self.order_created_count) * 100
            self.logger.info(f"  订单→交易转换率: {trade_rate:.1f}% ({self.trade_executed_count}/{self.order_created_count})")

        # 问题诊断
        self.logger.info("")
        self.logger.info("【问题诊断】")
        if self.signal_count > 0 and self.order_created_count == 0:
            self.logger.warning("  ⚠️ 所有信号都未生成订单！请检查:")
            self.logger.warning("      - 资金是否充足")
            self.logger.warning("      - 仓位策略配置是否正确")
            self.logger.warning("      - 最小手数限制是否过高")
        elif self.signal_count > self.order_created_count:
            skipped = self.signal_count - self.order_created_count
            self.logger.warning(f"  ⚠️ {skipped}个信号未生成订单 (仓位计算返回0)")

        self.logger.info("")
        self.logger.info(f"日志文件: {self.log_path}")
        self.logger.info(separator)

    def get_log_path(self) -> str:
        """获取日志文件路径"""
        return str(self.log_path)

    def close(self):
        """关闭日志"""
        for handler in self.logger.handlers:
            handler.close()
        self.logger.handlers.clear()
