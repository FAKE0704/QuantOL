"use client";

/**
 * CandlestickChart - K线图组件
 *
 * 使用 lightweight-charts (TradingView) 渲染专业的K线图
 * 支持买卖点标记显示
 */

import { useEffect, useRef, useState } from "react";
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
  const [isReady, setIsReady] = useState(false);

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
        height: height,
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
        if (chartContainerRef.current && chart) {
          chart.applyOptions({
            width: chartContainerRef.current.clientWidth,
          });
        }
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
  }, [height]);

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

  // 添加买卖点标记 - 暂时禁用以测试K线图本身
  useEffect(() => {
    console.log("Markers useEffect: isReady =", isReady, ", trades.length =", trades?.length);

    if (!isReady || !seriesRef.current || !trades.length) {
      console.log("Skipping markers");
      return;
    }

    console.log("Markers disabled temporarily for testing");

    // 暂时禁用标记功能
    /*
    // v5 需要 import createSeriesMarkers 并创建插件
    import("lightweight-charts").then((module) => {
      const { createSeriesMarkers } = module;

      const markers = trades
        .filter((trade) => trade.timestamp)
        .map((trade) => {
          const dateObj = new Date(trade.timestamp);

          // 使用与K线相同的 BusinessDay 格式
          const time = {
            year: dateObj.getFullYear(),
            month: dateObj.getMonth() + 1,
            day: dateObj.getDate(),
          };

          const isBuy = trade.direction === "BUY" || trade.direction === "OPEN";

          return {
            time,
            position: (isBuy ? "belowBar" : "aboveBar") as const,
            color: isBuy ? "#22c55e" : "#ef4444",
            shape: (isBuy ? "arrowUp" : "arrowDown") as const,
            text: isBuy ? "买入" : "卖出",
          };
        });

      console.log("Setting markers:", markers.length, "markers");
      console.log("Sample marker:", markers[0]);

      try {
        // 创建标记插件
        const seriesMarkers = createSeriesMarkers(seriesRef.current, markers);
        console.log("Markers created successfully");
      } catch (error) {
        console.error("Error creating markers:", error);
      }
    });
    */
  }, [trades, isReady]);

  return (
    <div className="w-full rounded-lg border border-slate-700 overflow-hidden bg-slate-900/50">
      <div ref={chartContainerRef} />
    </div>
  );
}
