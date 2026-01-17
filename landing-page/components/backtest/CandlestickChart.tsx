"use client";

/**
 * CandlestickChart - K线图组件
 *
 * 使用 lightweight-charts (TradingView) 渲染专业的K线图
 * 支持买卖点标记显示、自定义Tooltip和全屏功能
 */

import { useEffect, useRef, useState, useCallback } from "react";
import { PriceData, Trade } from "@/types/backtest";

interface CandlestickChartProps {
  priceData: PriceData[];
  trades: Trade[];
  height?: number;
}

export function CandlestickChart({ priceData, trades, height = 400 }: CandlestickChartProps) {
  const chartContainerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<any>(null);
  const seriesRef = useRef<any>(null);
  const tooltipRef = useRef<HTMLDivElement>(null);
  const [isReady, setIsReady] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [currentHeight, setCurrentHeight] = useState(height);

  // 格式化时间显示
  const formatTime = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day} ${hours}:${minutes}`;
  };

  // 查找指定时间戳附近的交易
  const findTradesNearTime = useCallback((timestamp: number, windowSeconds = 300): Trade[] => {
    return trades.filter(trade => {
      if (!trade.timestamp) return false;
      const tradeTime = new Date(trade.timestamp).getTime() / 1000;
      return Math.abs(tradeTime - timestamp) <= windowSeconds;
    });
  }, [trades]);

  // 全屏切换
  const toggleFullscreen = () => {
    if (!document.fullscreenElement) {
      chartContainerRef.current?.requestFullscreen();
    } else {
      document.exitFullscreen();
    }
  };

  // 处理图表大小调整
  const handleChartResize = useCallback(() => {
    if (!chartRef.current || !chartContainerRef.current) return;

    const isActuallyFullscreen = !!document.fullscreenElement;
    const newWidth = chartContainerRef.current.clientWidth;
    // 全屏时使用整个窗口高度，否则使用原始高度
    const newHeight = isActuallyFullscreen ? window.innerHeight : height;

    chartRef.current.applyOptions({
      width: newWidth,
      height: newHeight,
    });

    setCurrentHeight(newHeight);
  }, [height]);

  // 监听全屏变化
  useEffect(() => {
    const handleFullscreenChange = () => {
      const isNowFullscreen = !!document.fullscreenElement;
      setIsFullscreen(isNowFullscreen);

      // 全屏状态变化时，调整图表大小
      if (chartRef.current) {
        // 使用 requestAnimationFrame 和 setTimeout 确保全屏转换完成
        const resizeAfterTransition = () => {
          requestAnimationFrame(() => {
            setTimeout(() => {
              handleChartResize();
            }, 50);
          });
        };

        if (isNowFullscreen) {
          // 进入全屏：给更多时间让浏览器完成全屏动画
          setTimeout(resizeAfterTransition, 150);
        } else {
          // 退出全屏：立即调整
          resizeAfterTransition();
        }
      }
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange);
    };
  }, [handleChartResize]);

  // 监听窗口大小变化（全屏模式下）
  useEffect(() => {
    if (!isFullscreen) return;

    const handleWindowResize = () => {
      handleChartResize();
    };

    window.addEventListener('resize', handleWindowResize);
    return () => {
      window.removeEventListener('resize', handleWindowResize);
    };
  }, [isFullscreen, handleChartResize]);

  useEffect(() => {
    console.log("Chart init useEffect: chartContainerRef.current =", chartContainerRef.current);
    if (!chartContainerRef.current) {
      console.log("Chart container is null, skipping init");
      return;
    }

    let mounted = true;
    console.log("Starting lightweight-charts import...");

    // 动态导入 lightweight-charts v5
    import("lightweight-charts").then((module) => {
      if (!mounted || !chartContainerRef.current) return;

      const { createChart, CandlestickSeries } = module;

      console.log("Creating chart with CandlestickSeries...");

      const chart = createChart(chartContainerRef.current, {
        width: chartContainerRef.current.clientWidth,
        height: currentHeight,
        layout: {
          background: { type: "solid", color: "#0f172a" },
          textColor: "#94a3b8",
        },
        grid: {
          vertLines: { color: "#1e293b" },
          horzLines: { color: "#1e293b" },
        },
        crosshair: {
          mode: 1,
        },
        rightPriceScale: {
          borderColor: "#334155",
        },
        timeScale: {
          borderColor: "#334155",
          timeVisible: true,
          secondsVisible: false,
        },
      });

      chartRef.current = chart;

      // v5 新API: 使用 addSeries 而不是 addCandlestickSeries
      try {
        console.log("About to call chart.addSeries...");
        const candlestickSeries = chart.addSeries(CandlestickSeries, {
          upColor: "#22c55e",
          downColor: "#ef4444",
          borderUpColor: "#22c55e",
          borderDownColor: "#ef4444",
          wickUpColor: "#22c55e",
          wickDownColor: "#ef4444",
        });
        console.log("Series created successfully:", candlestickSeries);

        seriesRef.current = candlestickSeries;
        setIsReady(true);
      } catch (error) {
        console.error("Error creating series:", error);
        console.error("Error details:", error instanceof Error ? error.message : error);
      }

      // 响应式调整大小
      const handleResize = () => {
        handleChartResize();
      };

      window.addEventListener("resize", handleResize);

      // 清理函数
      return () => {
        window.removeEventListener("resize", handleResize);
        chart.remove();
      };
    }).catch((err) => {
      console.error("Failed to import lightweight-charts:", err);
    });

    return () => {
      mounted = false;
    };
  }, [currentHeight, handleChartResize]);

  // 更新K线数据 - 只有当图表准备好后才执行
  useEffect(() => {
    if (!isReady || !seriesRef.current || !priceData.length) {
      console.log("Skip setData: isReady =", isReady, ", seriesRef.current =", seriesRef.current, ", priceData.length =", priceData.length);
      return;
    }

    const candlestickData = priceData.map((item, index) => {
      // 使用 Unix 时间戳（秒）以保留精确时间
      const dateObj = new Date(item.time);
      const time = Math.floor(dateObj.getTime() / 1000);

      if (index === 0) {
        console.log("Sample time conversion:", item.time, "->", time, "(", dateObj.toISOString(), ")");
      }

      // 验证数据
      if (!item.open || !item.high || !item.low || !item.close) {
        console.warn("Invalid data at index", index, ":", item);
      }

      return {
        time,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      };
    });

    console.log("Setting candlestick data:", candlestickData.length, "points");
    console.log("First data point:", candlestickData[0]);
    console.log("Last data point:", candlestickData[candlestickData.length - 1]);
    console.log("Checking time order...");
    for (let i = 1; i < Math.min(5, candlestickData.length); i++) {
      console.log(`  [${i}] time=${candlestickData[i].time}, prev=${candlestickData[i-1].time}, ordered=${candlestickData[i].time >= candlestickData[i-1].time}`);
    }

    try {
      seriesRef.current.setData(candlestickData);
      console.log("Data set successfully");

      // 使用 chartRef 调用 timeScale().fitContent()
      if (chartRef.current) {
        chartRef.current.timeScale().fitContent();
        console.log("Called fitContent()");
      }
    } catch (error) {
      console.error("Error setting data:", error);
    }
  }, [priceData, isReady]);

  // 自定义Tooltip
  useEffect(() => {
    if (!isReady || !chartRef.current || !chartContainerRef.current) {
      return;
    }

    // 创建tooltip元素
    const toolTip = document.createElement('div');
    toolTip.className = 'chart-tooltip';
    chartContainerRef.current.appendChild(toolTip);
    tooltipRef.current = toolTip;

    // 订阅crosshair移动事件
    const unsubscribe = chartRef.current.subscribeCrosshairMove((param: any) => {
      if (
        !param.point ||
        !param.time ||
        param.point.x < 0 ||
        param.point.x > chartContainerRef.current!.clientWidth ||
        param.point.y < 0 ||
        param.point.y > chartContainerRef.current!.clientHeight
      ) {
        toolTip.style.display = 'none';
        return;
      }

      toolTip.style.display = 'block';

      // 获取K线数据
      const seriesData = param.seriesData.get(seriesRef.current);
      if (!seriesData) {
        toolTip.style.display = 'none';
        return;
      }

      // 格式化时间
      const timeStr = formatTime(param.time as number);

      // 查找附近的交易
      const nearbyTrades = findTradesNearTime(param.time as number);

      // 构建tooltip内容
      let tooltipContent = `
        <div class="tooltip-time">${timeStr}</div>
        <div class="tooltip-ohlc">
          <span class="ohlc-label">O:</span><span class="ohlc-value">${seriesData.open?.toFixed(2) || '-'}</span>
          <span class="ohlc-label">H:</span><span class="ohlc-value">${seriesData.high?.toFixed(2) || '-'}</span>
          <span class="ohlc-label">L:</span><span class="ohlc-value">${seriesData.low?.toFixed(2) || '-'}</span>
          <span class="ohlc-label">C:</span><span class="ohlc-value close-${seriesData.close >= seriesData.open ? 'up' : 'down'}">${seriesData.close?.toFixed(2) || '-'}</span>
        </div>
      `;

      // 如果有交易，显示交易信息
      if (nearbyTrades.length > 0) {
        tooltipContent += `<div class="tooltip-trades">`;
        nearbyTrades.forEach(trade => {
          const isBuy = trade.direction === "BUY" || trade.direction === "OPEN";
          const letter = isBuy ? 'B' : 'S';
          const colorClass = isBuy ? 'trade-buy' : 'trade-sell';
          tooltipContent += `<div class="tooltip-trade ${colorClass}">${letter}@${trade.price.toFixed(2)},${trade.quantity}</div>`;
        });
        tooltipContent += `</div>`;
      }

      toolTip.innerHTML = tooltipContent;

      // 定位tooltip
      const toolTipWidth = 200;
      const toolTipHeight = 100;
      const toolTipMargin = 10;

      let left = param.point.x + toolTipMargin;
      if (left > chartContainerRef.current!.clientWidth - toolTipWidth) {
        left = param.point.x - toolTipMargin - toolTipWidth;
      }

      let top = param.point.y + toolTipMargin;
      if (top > chartContainerRef.current!.clientHeight - toolTipHeight) {
        top = param.point.y - toolTipHeight - toolTipMargin;
      }

      toolTip.style.left = `${Math.max(0, left)}px`;
      toolTip.style.top = `${Math.max(0, top)}px`;
    });

    return () => {
      unsubscribe?.();
      toolTip?.remove();
    };
  }, [isReady, findTradesNearTime]);

  // 添加买卖点标记 - 启用并优化
  useEffect(() => {
    console.log("Markers useEffect: isReady =", isReady, ", trades.length =", trades?.length);

    if (!isReady || !seriesRef.current || !trades.length) {
      console.log("Skipping markers");
      return;
    }

    // v5 需要 import createSeriesMarkers 并创建插件
    import("lightweight-charts").then((module) => {
      const { createSeriesMarkers } = module;

      // 按时间戳分组交易，处理同一时间有买卖的情况
      const tradesByTime = new Map<number, Trade[]>();
      trades.forEach(trade => {
        if (!trade.timestamp) return;
        const timestamp = Math.floor(new Date(trade.timestamp).getTime() / 1000);
        if (!tradesByTime.has(timestamp)) {
          tradesByTime.set(timestamp, []);
        }
        tradesByTime.get(timestamp)!.push(trade);
      });

      const markers = Array.from(tradesByTime.entries()).map(([timestamp, tradesAtTime]) => {
        const hasBuy = tradesAtTime.some(t => t.direction === "BUY" || t.direction === "OPEN");
        const hasSell = tradesAtTime.some(t => t.direction === "SELL" || t.direction === "CLOSE");

        // 确定标记文字和颜色
        let text = '';
        let color = '';
        let position: 'aboveBar' | 'belowBar' = 'aboveBar';

        if (hasBuy && hasSell) {
          text = 'T';  // 同时买卖
          color = '#f59e0b';  // 橙色
          position = 'aboveBar';
        } else if (hasBuy) {
          text = 'B';  // 买入
          color = '#22c55e';  // 绿色
          position = 'belowBar';
        } else {
          text = 'S';  // 卖出
          color = '#ef4444';  // 红色
          position = 'aboveBar';
        }

        return {
          time: timestamp,
          position: position as const,
          color: color,
          shape: 'circle' as const,
          text: text,
          size: 2,
        };
      });

      console.log("Setting markers:", markers.length, "markers");
      if (markers.length > 0) {
        console.log("Sample marker:", markers[0]);
      }

      try {
        // 创建标记插件
        const seriesMarkers = createSeriesMarkers(seriesRef.current, markers);
        console.log("Markers created successfully");
        return () => {
          seriesMarkers?.();
        };
      } catch (error) {
        console.error("Error creating markers:", error);
      }
    });
  }, [trades, isReady]);

  return (
    <div
      className="w-full rounded-lg border border-slate-700 overflow-hidden bg-slate-900/50 relative"
      style={isFullscreen ? { height: '100vh' } : {}}
    >
      {/* 全屏按钮 */}
      <button
        onClick={toggleFullscreen}
        className="absolute top-2 right-2 z-10 px-3 py-1 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded border border-slate-600 transition-colors"
        title={isFullscreen ? "退出全屏" : "全屏"}
      >
        {isFullscreen ? '退出全屏' : '全屏'}
      </button>

      {/* 图表容器 */}
      <div ref={chartContainerRef} className="w-full" style={{ height: isFullscreen ? '100%' : `${currentHeight}px` }} />

      {/* Tooltip样式 */}
      <style jsx global>{`
        .chart-tooltip {
          position: absolute;
          background: rgba(15, 23, 42, 0.95);
          border: 1px solid #334155;
          border-radius: 6px;
          padding: 8px 12px;
          font-size: 12px;
          color: #e2e8f0;
          pointer-events: none;
          z-index: 1000;
          display: none;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
          min-width: 150px;
        }

        .tooltip-time {
          font-size: 11px;
          color: #94a3b8;
          margin-bottom: 4px;
          font-family: monospace;
        }

        .tooltip-ohlc {
          display: flex;
          gap: 8px;
          margin-bottom: 6px;
        }

        .ohlc-label {
          color: #64748b;
          font-size: 10px;
        }

        .ohlc-value {
          color: #e2e8f0;
          font-size: 11px;
          font-family: monospace;
        }

        .ohlc-value.close-up {
          color: #22c55e;
        }

        .ohlc-value.close-down {
          color: #ef4444;
        }

        .tooltip-trades {
          border-top: 1px solid #334155;
          padding-top: 6px;
          margin-top: 4px;
        }

        .tooltip-trade {
          font-size: 11px;
          font-family: monospace;
          padding: 2px 0;
        }

        .tooltip-trade.trade-buy {
          color: #22c55e;
        }

        .tooltip-trade.trade-sell {
          color: #ef4444;
        }

        /* 全屏模式下的样式调整 */
        :fullscreen .chart-tooltip {
          font-size: 14px;
        }

        :fullscreen .tooltip-time,
        :fullscreen .tooltip-trade {
          font-size: 12px;
        }

        /* 确保全屏时图表容器填充整个视口 */
        :fullscreen {
          height: 100vh;
          width: 100vw;
        }

        :fullscreen > div {
          height: 100vh !important;
          width: 100vw !important;
        }

        :fullscreen .tv-lightweight-charts {
          width: 100% !important;
          height: 100% !important;
        }

        /* 图表canvas元素全屏样式 */
        :fullscreen canvas {
          display: block !important;
        }
      `}</style>
    </div>
  );
}
