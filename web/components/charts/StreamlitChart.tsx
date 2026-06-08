"use client";

/**
 * StreamlitChart - Embed Streamlit charts in Next.js
 *
 * This component provides a secure iframe wrapper for Streamlit charts,
 * handling authentication and responsive resizing.
 */

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";

interface StreamlitChartProps {
  /** Chart type to display */
  chartType: string;
  /** Additional URL parameters */
  params?: Record<string, string>;
  /** Height of the chart container */
  height?: string | number;
  /** CSS class name */
  className?: string;
  /** Authentication token */
  token?: string;
  /** Loading state callback */
  onLoad?: () => void;
  /** Error callback */
  onError?: (error: Error) => void;
}

interface ChartMessage {
  type: "chartReady" | "chartResize";
  chartId: string;
  height: number;
}

export function StreamlitChart({
  chartType,
  params = {},
  height = "600px",
  className = "",
  token,
  onLoad,
  onError,
}: StreamlitChartProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [iframeHeight, setIframeHeight] = useState<number>(600);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const searchParams = useSearchParams();

  // Build Streamlit URL with parameters - use current origin for external access
  const streamlitUrl = (() => {
    // Use current page origin for external access compatibility
    const baseUrl = typeof window !== "undefined"
      ? window.location.origin
      : (process.env.NEXT_PUBLIC_STREAMLIT_URL || "http://localhost:8087");

    // Get token from props or URL params
    const authToken = token || searchParams.get("token") || "";

    const urlParams = new URLSearchParams({
      headless: "true",
      chart: chartType,
      ...(authToken && { token: authToken }),
      ...params,
    });

    return `${baseUrl}?${urlParams.toString()}`;
  })();

  // Get current origin for message validation
  const currentOrigin = typeof window !== "undefined" ? window.location.origin : "";

  // Handle messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent<ChartMessage>) => {
      // Validate origin for security - accept from current origin
      if (event.origin !== currentOrigin) {
        return;
      }

      const { type, height: messageHeight } = event.data;

      switch (type) {
        case "chartReady":
          setIframeHeight(messageHeight);
          setIsLoading(false);
          onLoad?.();
          break;

        case "chartResize":
          setIframeHeight(messageHeight);
          break;
      }
    };

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, [onLoad, currentOrigin]);

  // Handle iframe load events
  const handleIframeLoad = () => {
    // Chart ready message will handle the actual ready state
    // This is just a fallback timeout
    const fallbackTimer = setTimeout(() => {
      if (isLoading) {
        setIsLoading(false);
        onLoad?.();
      }
    }, 5000);

    return () => clearTimeout(fallbackTimer);
  };

  const handleIframeError = () => {
    const error = new Error("Failed to load chart");
    setError(error.message);
    setIsLoading(false);
    onError?.(error);
  };

  return (
    <div className={`streamlit-chart-container ${className}`}>
      {isLoading && (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
        </div>
      )}

      {error && (
        <div className="bg-red-500/10 border border-red-500 text-red-500 p-4 rounded">
          Error loading chart: {error}
        </div>
      )}

      <iframe
        ref={iframeRef}
        src={streamlitUrl}
        className="w-full border-0 rounded-lg"
        style={{
          height: typeof height === "number" ? `${height}px` : height,
          minHeight: `${iframeHeight}px`,
          display: isLoading ? "none" : "block",
        }}
        onLoad={handleIframeLoad}
        onError={handleIframeError}
        title={`${chartType} chart`}
        sandbox="allow-scripts allow-same-origin allow-forms"
        allow="clipboard-write"
      />
    </div>
  );
}

/**
 * Hook to get chart-specific parameters
 */
export function useChartParams() {
  const searchParams = useSearchParams();

  return {
    symbol: searchParams.get("symbol") || "",
    startDate: searchParams.get("start") || "",
    endDate: searchParams.get("end") || "",
    strategyId: searchParams.get("strategy") || "",
  };
}

/**
 * Props for specific chart types
 */
export interface BacktestChartProps extends Omit<StreamlitChartProps, "chartType"> {
  backtestId?: string;
  strategyId?: string;
}

export function BacktestChart({ backtestId, strategyId, ...props }: BacktestChartProps) {
  return (
    <StreamlitChart
      chartType="backtest"
      params={{
        ...(backtestId && { backtest: backtestId }),
        ...(strategyId && { strategy: strategyId }),
      }}
      {...props}
    />
  );
}

export interface HistoryChartProps extends Omit<StreamlitChartProps, "chartType"> {
  symbol: string;
  startDate?: string;
  endDate?: string;
}

export function HistoryChart({ symbol, startDate, endDate, ...props }: HistoryChartProps) {
  return (
    <StreamlitChart
      chartType="history"
      params={{
        symbol,
        ...(startDate && { start: startDate }),
        ...(endDate && { end: endDate }),
      }}
      {...props}
    />
  );
}
