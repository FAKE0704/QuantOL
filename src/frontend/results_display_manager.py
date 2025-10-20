import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, List, Optional
from src.core.strategy.backtesting import BacktestConfig

class ResultsDisplayManager:
    """回测结果展示管理器，负责结果的可视化和分析"""

    def __init__(self, session_state):
        self.session_state = session_state

    def display_backtest_summary(self, results: Dict[str, Any], backtest_config: BacktestConfig):
        """显示回测摘要"""
        st.subheader("📊 回测摘要")

        if "combined_equity" in results:
            self._display_multi_symbol_summary(results, backtest_config)
        else:
            self._display_single_symbol_summary(results)

    def _display_multi_symbol_summary(self, results: Dict[str, Any], backtest_config: BacktestConfig):
        """显示多符号回测摘要"""
        st.info(f"组合回测 - {len(backtest_config.get_symbols())} 只股票")

        combined_equity = results["combined_equity"]
        initial_capital = backtest_config.initial_capital
        final_capital = combined_equity['total_value'].iloc[-1] if not combined_equity.empty else initial_capital
        profit = final_capital - initial_capital
        profit_pct = (profit / initial_capital) * 100

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("初始资金", f"¥{initial_capital:,.2f}")
            st.metric("最终资金", f"¥{final_capital:,.2f}")
            st.metric("总收益", f"¥{profit:,.2f}", f"{profit_pct:.2f}%")

        with col2:
            total_trades = len(results["trades"])
            st.metric("总交易次数", total_trades)

            # 计算组合胜率
            win_rate = 0.0
            win_rate_count = 0
            for symbol_result in results["individual"].values():
                if 'summary' in symbol_result and 'win_rate' in symbol_result['summary']:
                    win_rate += symbol_result['summary']['win_rate']
                    win_rate_count += 1

            if win_rate_count > 0:
                avg_win_rate = (win_rate / win_rate_count) * 100
                st.metric("胜率", f"{avg_win_rate:.2f}%")
            else:
                st.metric("胜率", "N/A")

            # 计算组合最大回撤
            if not combined_equity.empty and 'total_value' in combined_equity.columns:
                equity_values = combined_equity['total_value'].values
                max_drawdown = self._calculate_max_drawdown(equity_values)
                st.metric("最大回撤", f"{max_drawdown:.2f}%")
            else:
                st.metric("最大回撤", "N/A")

        with col3:
            # 计算年化收益率
            if len(combined_equity) > 1:
                days = (combined_equity['timestamp'].iloc[-1] - combined_equity['timestamp'].iloc[0]).days
                if days > 0:
                    annual_return = (profit_pct / days) * 365
                    st.metric("年化收益率", f"{annual_return:.2f}%")
                else:
                    st.metric("年化收益率", "N/A")
            else:
                st.metric("年化收益率", "N/A")

        # 显示各股票表现
        st.subheader("各股票表现")
        for symbol, symbol_results in results["individual"].items():
            symbol_summary = symbol_results["summary"]
            symbol_capital = backtest_config.get_symbol_capital(symbol)
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{symbol} 分配资金", f"¥{symbol_capital:,.2f}")
            with col2:
                st.metric(f"{symbol} 最终资金", f"¥{symbol_summary['final_capital']:,.2f}")
            with col3:
                symbol_profit = symbol_summary['final_capital'] - symbol_capital
                symbol_profit_pct = (symbol_profit / symbol_capital) * 100
                st.metric(f"{symbol} 收益", f"¥{symbol_profit:,.2f}", f"{symbol_profit_pct:.2f}%")

    def _display_single_symbol_summary(self, results: Dict[str, Any]):
        """显示单符号回测摘要"""
        summary = results["summary"]
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("初始资金", f"¥{summary['initial_capital']:,.2f}")
            st.metric("最终资金", f"¥{summary['final_capital']:,.2f}")
            profit = summary['final_capital'] - summary['initial_capital']
            profit_pct = (profit / summary['initial_capital']) * 100
            st.metric("总收益", f"¥{profit:,.2f}", f"{profit_pct:.2f}%")

        with col2:
            st.metric("总交易次数", summary['total_trades'])
            win_rate_pct = summary['win_rate'] * 100
            st.metric("胜率", f"{win_rate_pct:.2f}%")
            st.metric("最大回撤", f"{summary['max_drawdown'] * 100:.2f}%")

        with col3:
            # 计算年化收益率（简化计算）
            equity_data = pd.DataFrame(results["equity_records"])
            if len(equity_data) > 1:
                days = (equity_data['timestamp'].iloc[-1] - equity_data['timestamp'].iloc[0]).days
                if days > 0:
                    annual_return = (profit_pct / days) * 365
                    st.metric("年化收益率", f"{annual_return:.2f}%")
                else:
                    st.metric("年化收益率", "N/A")
            else:
                st.metric("年化收益率", "N/A")

    def display_trade_records(self, results: Dict[str, Any]):
        """显示交易记录"""
        st.subheader("💱 交易记录")
        if results["trades"]:
            trades_df = pd.DataFrame(results["trades"])
            # 格式化时间显示
            if 'timestamp' in trades_df.columns:
                trades_df['timestamp'] = pd.to_datetime(trades_df['timestamp'])

            st.dataframe(trades_df, use_container_width=True)

            # 交易统计
            if not trades_df.empty:
                st.subheader("交易统计")
                buy_trades = trades_df[trades_df['direction'] == 'BUY']
                sell_trades = trades_df[trades_df['direction'] == 'SELL']

                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("买入交易", len(buy_trades))
                with col2:
                    st.metric("卖出交易", len(sell_trades))
                with col3:
                    total_commission = trades_df['commission'].sum()
                    st.metric("总手续费", f"¥{total_commission:,.2f}")
                with col4:
                    # 显示当前现金和持仓状态
                    portfolio_manager = results.get('portfolio_manager')
                    if portfolio_manager:
                        current_cash = portfolio_manager.get_cash_balance()
                        current_positions = portfolio_manager.get_portfolio_value() - current_cash
                        st.metric("当前现金/持仓", f"¥{current_cash:,.0f}/¥{current_positions:,.0f}")
        else:
            st.info("暂无交易记录")

    def display_position_details(self, results: Dict[str, Any]):
        """显示仓位明细"""
        st.subheader("📈 仓位明细")

        # 获取当前持仓信息
        portfolio_manager = results.get('portfolio_manager')
        if portfolio_manager:
            all_positions = portfolio_manager.get_all_positions()

            if all_positions:
                # 创建持仓信息表格
                position_data = []
                for symbol, position in all_positions.items():
                    position_data.append({
                        '标的代码': symbol,
                        '持仓数量': position.quantity,
                        '平均成本': position.avg_cost,
                        '当前价值': position.current_value,
                        '当前价格': position.stock.last_price if hasattr(position.stock, 'last_price') else 0
                    })

                positions_df = pd.DataFrame(position_data)

                # 计算持仓权重
                total_value = portfolio_manager.get_portfolio_value()
                if total_value > 0:
                    positions_df['持仓权重'] = (positions_df['当前价值'] / total_value) * 100

                st.dataframe(positions_df, use_container_width=True)

                # 仓位统计
                st.subheader("仓位统计")
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_position_value = positions_df['当前价值'].sum()
                    st.metric("持仓总价值", f"¥{total_position_value:,.2f}")
                with col2:
                    cash_balance = portfolio_manager.get_cash_balance()
                    st.metric("现金余额", f"¥{cash_balance:,.2f}")
                with col3:
                    portfolio_value = portfolio_manager.get_portfolio_value()
                    st.metric("组合总价值", f"¥{portfolio_value:,.2f}")

                # 持仓分布饼图
                if not positions_df.empty and total_value > 0:
                    st.subheader("持仓分布")
                    fig = px.pie(positions_df, values='当前价值', names='标的代码',
                                title='持仓价值分布')
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("暂无持仓记录")

                # 显示现金信息
                cash_balance = portfolio_manager.get_cash_balance()
                portfolio_value = portfolio_manager.get_portfolio_value()

                col1, col2 = st.columns(2)
                with col1:
                    st.metric("现金余额", f"¥{cash_balance:,.2f}")
                with col2:
                    st.metric("组合总价值", f"¥{portfolio_value:,.2f}")

    def _calculate_max_drawdown(self, equity_values: np.ndarray) -> float:
        """计算最大回撤"""
        peak = equity_values[0]
        max_drawdown = 0.0

        for value in equity_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def display_performance_metrics(self, equity_data: pd.DataFrame, trades_df: pd.DataFrame = None):
        """显示性能指标面板"""
        metrics = calculate_performance_metrics(equity_data, trades_df)
        if metrics:
            st.subheader("📊 综合性能指标")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("夏普比率", f"{metrics.get('sharpe_ratio', 0):.2f}" if metrics.get('sharpe_ratio') else "N/A")
                st.metric("索提诺比率", f"{metrics.get('sortino_ratio', 0):.2f}" if metrics.get('sortino_ratio') and metrics.get('sortino_ratio') != float('inf') else "N/A")

            with col2:
                st.metric("卡玛比率", f"{metrics.get('calmar_ratio', 0):.2f}" if metrics.get('calmar_ratio') and metrics.get('calmar_ratio') != float('inf') else "N/A")
                st.metric("年化波动率", f"{metrics.get('annual_volatility', 0)*100:.2f}%" if metrics.get('annual_volatility') else "N/A")

            with col3:
                if 'return_stats' in metrics:
                    st.metric("正收益天数", f"{metrics['return_stats']['positive_days']}")
                    st.metric("负收益天数", f"{metrics['return_stats']['negative_days']}")

            with col4:
                if 'trade_stats' in metrics:
                    st.metric("胜率", f"{metrics['trade_stats']['win_rate']*100:.1f}%")
                    st.metric("盈亏比", f"{metrics['trade_stats'].get('win_loss_ratio', 0):.2f}" if metrics['trade_stats'].get('win_loss_ratio') != float('inf') else "N/A")

            # 显示回撤信息
            if 'max_drawdown_period' in metrics:
                st.info(f"最大回撤期间: 第{metrics['max_drawdown_period']['start']}天到第{metrics['max_drawdown_period']['end']}天, 持续{metrics['max_drawdown_period']['duration']}天")


def calculate_performance_metrics(equity_data, trades_df=None, risk_free_rate=0.03):
    """计算全面的性能指标"""
    metrics = {}

    if equity_data is None or equity_data.empty:
        return metrics

    # 确保净值数据按时间排序
    if 'timestamp' in equity_data.columns:
        equity_data = equity_data.sort_values('timestamp')

    equity_values = equity_data['total_value'].values if 'total_value' in equity_data.columns else equity_data.values

    if len(equity_values) < 2:
        return metrics

    # 计算基本指标
    initial_value = equity_values[0]
    final_value = equity_values[-1]
    total_return = (final_value - initial_value) / initial_value

    # 计算年化收益率（更精确的计算）
    if 'timestamp' in equity_data.columns:
        days = (equity_data['timestamp'].iloc[-1] - equity_data['timestamp'].iloc[0]).days
        if days > 0:
            annual_return = (1 + total_return) ** (365 / days) - 1
        else:
            annual_return = 0
    else:
        # 简化计算
        days = len(equity_values)
        annual_return = (1 + total_return) ** (365 / max(days, 1)) - 1 if days > 0 else 0

    # 计算最大回撤和回撤期间
    peak = equity_values[0]
    max_drawdown = 0.0
    drawdown_start = None
    drawdown_end = None
    current_drawdown_start = None

    for i, value in enumerate(equity_values):
        if value > peak:
            peak = value
            current_drawdown_start = None

        drawdown = (peak - value) / peak

        if drawdown > max_drawdown:
            max_drawdown = drawdown
            if current_drawdown_start is not None:
                drawdown_start = current_drawdown_start
                drawdown_end = i

        if current_drawdown_start is None and drawdown > 0:
            current_drawdown_start = i

    metrics['annual_return'] = annual_return
    metrics['total_return'] = total_return
    metrics['max_drawdown'] = max_drawdown

    # 计算回撤期间信息
    if drawdown_start is not None and drawdown_end is not None:
        metrics['max_drawdown_period'] = {
            'start': drawdown_start,
            'end': drawdown_end,
            'duration': drawdown_end - drawdown_start + 1
        }

    # 计算日收益率序列
    returns = np.diff(equity_values) / equity_values[:-1]
    if len(returns) > 0:
        # 计算夏普比率
        excess_returns = returns - risk_free_rate/252
        sharpe_ratio = (excess_returns.mean() / returns.std()) * np.sqrt(252) if returns.std() > 0 else 0
        metrics['sharpe_ratio'] = sharpe_ratio

        # 计算索提诺比率
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            sortino_ratio = (returns.mean() / downside_returns.std()) * np.sqrt(252) if downside_returns.std() > 0 else 0
            metrics['sortino_ratio'] = sortino_ratio
        else:
            metrics['sortino_ratio'] = float('inf')

        # 计算卡玛比率
        if max_drawdown > 0:
            metrics['calmar_ratio'] = annual_return / max_drawdown
        else:
            metrics['calmar_ratio'] = float('inf')

        # 计算年化波动率
        metrics['annual_volatility'] = returns.std() * np.sqrt(252)

        # 计算收益分布统计
        metrics['return_stats'] = {
            'mean': returns.mean(),
            'std': returns.std(),
            'skew': pd.Series(returns).skew(),
            'kurtosis': pd.Series(returns).kurtosis(),
            'positive_days': len(returns[returns > 0]),
            'negative_days': len(returns[returns < 0]),
            'zero_days': len(returns[returns == 0])
        }

    # 计算交易相关指标
    if trades_df is not None:
        if isinstance(trades_df, list):
            trades_df = pd.DataFrame(trades_df)

        if not trades_df.empty and 'profit' in trades_df.columns:
            winning_trades = trades_df[trades_df['profit'] > 0]
            losing_trades = trades_df[trades_df['profit'] < 0]
            breakeven_trades = trades_df[trades_df['profit'] == 0]

            total_trades = len(trades_df)
            metrics['trade_stats'] = {
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'breakeven_trades': len(breakeven_trades),
                'win_rate': len(winning_trades) / total_trades if total_trades > 0 else 0
            }

            if len(losing_trades) > 0:
                avg_win = winning_trades['profit'].mean() if len(winning_trades) > 0 else 0
                avg_loss = abs(losing_trades['profit'].mean())
                metrics['trade_stats']['win_loss_ratio'] = avg_win / avg_loss if avg_loss > 0 else float('inf')
                metrics['trade_stats']['profit_factor'] = winning_trades['profit'].sum() / abs(losing_trades['profit'].sum()) if losing_trades['profit'].sum() < 0 else float('inf')

            # 计算平均持仓时间（如果有timestamp信息）
            if 'timestamp' in trades_df.columns and 'direction' in trades_df.columns:
                buy_trades = trades_df[trades_df['direction'] == 'BUY']
                if len(buy_trades) > 1:
                    buy_times = pd.to_datetime(buy_trades['timestamp'])
                    hold_times = (buy_times.shift(-1) - buy_times).dt.total_seconds() / 86400  # 转换为天数
                    metrics['trade_stats']['avg_holding_days'] = hold_times.mean()

    return metrics