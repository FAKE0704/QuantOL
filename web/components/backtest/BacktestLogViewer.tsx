"use client";

/**
 * BacktestLogViewer Component
 *
 * Displays backtest log files with filtering and search capabilities.
 */

import { useState, useEffect, useCallback, useRef } from "react";

interface LogLine {
  line_number: number;
  content: string;
  level: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "OTHER";
}

interface BacktestLogViewerProps {
  backtestId: string;
}

export function BacktestLogViewer({ backtestId }: BacktestLogViewerProps) {
  const [logs, setLogs] = useState<LogLine[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lineStart, setLineStart] = useState(0);
  const [lineEnd, setLineEnd] = useState(1000);
  const [totalLines, setTotalLines] = useState(0);
  const [levelFilter, setLevelFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState("");
  const [autoScroll, setAutoScroll] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Parse log level from line
  const parseLogLevel = (line: string): LogLine["level"] => {
    const upper = line.toUpperCase();
    if (upper.includes("ERROR")) return "ERROR";
    if (upper.includes("WARNING") || upper.includes("WARN")) return "WARNING";
    if (upper.includes("INFO")) return "INFO";
    if (upper.includes("DEBUG")) return "DEBUG";
    return "OTHER";
  };

  // Load logs from API
  const loadLogs = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `/api/backtest/${backtestId}/logs?line_start=${lineStart}&line_end=${lineEnd}`,
        {
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();

      if (data.success && data.data) {
        const parsedLogs: LogLine[] = data.data.lines.map((line: string, index: number) => ({
          line_number: data.data.line_start + index,
          content: line,
          level: parseLogLevel(line),
        }));

        setLogs(parsedLogs);
        setTotalLines(data.data.total_lines);
      } else {
        setError(data.message || "Failed to load logs");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setIsLoading(false);
    }
  }, [backtestId, lineStart, lineEnd]);

  useEffect(() => {
    loadLogs();
  }, [loadLogs]);

  // Auto-scroll to bottom when enabled and logs update
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Filter logs by level and search query
  const filteredLogs = logs.filter((log) => {
    if (levelFilter !== "ALL" && log.level !== levelFilter) {
      return false;
    }
    if (searchQuery && !log.content.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    return true;
  });

  // Get line color based on level
  const getLevelColor = (level: LogLine["level"]) => {
    switch (level) {
      case "ERROR":
        return "text-red-400";
      case "WARNING":
        return "text-yellow-400";
      case "INFO":
        return "text-blue-400";
      case "DEBUG":
        return "text-gray-500";
      default:
        return "text-foreground";
    }
  };

  // Handle pagination
  const handlePrevPage = () => {
    setLineStart(Math.max(0, lineStart - 1000));
    setLineEnd(Math.max(1000, lineEnd - 1000));
  };

  const handleNextPage = () => {
    setLineStart(lineEnd);
    setLineEnd(lineEnd + 1000);
  };

  return (
    <div className="bg-card/50 rounded-lg p-4">
      {/* Header with controls */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <select
            value={levelFilter}
            onChange={(e) => setLevelFilter(e.target.value)}
            className="px-3 py-1 bg-input border border-border rounded text-foreground text-sm"
          >
            <option value="ALL">全部级别</option>
            <option value="ERROR">ERROR</option>
            <option value="WARNING">WARNING</option>
            <option value="INFO">INFO</option>
            <option value="DEBUG">DEBUG</option>
          </select>

          <input
            type="text"
            placeholder="搜索日志..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="px-3 py-1 bg-input border border-border rounded text-foreground text-sm w-48"
          />

          <label className="flex items-center gap-2 text-sm text-muted-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              className="w-4 h-4"
            />
            自动滚动
          </label>
        </div>

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <span>
            显示 {lineStart}-{Math.min(lineEnd, totalLines)} / 共 {totalLines} 行
          </span>
          <button
            onClick={loadLogs}
            disabled={isLoading}
            className="px-2 py-1 bg-input hover:bg-input/80 rounded text-foreground disabled:opacity-50"
          >
            {isLoading ? "加载中..." : "刷新"}
          </button>
        </div>
      </div>

      {/* Pagination controls */}
      <div className="flex items-center justify-between mb-4">
        <button
          onClick={handlePrevPage}
          disabled={lineStart === 0}
          className="px-3 py-1 bg-input hover:bg-input/80 rounded text-foreground disabled:opacity-50 text-sm"
        >
          ← 上一页
        </button>
        <div className="text-sm text-muted-foreground">
          {filteredLogs.length !== logs.length && (
            <span>已过滤显示 {filteredLogs.length} / {logs.length} 行</span>
          )}
        </div>
        <button
          onClick={handleNextPage}
          disabled={lineEnd >= totalLines}
          className="px-3 py-1 bg-input hover:bg-input/80 rounded text-foreground disabled:opacity-50 text-sm"
        >
          下一页 →
        </button>
      </div>

      {/* Log content */}
      <div
        ref={logContainerRef}
        className="bg-background rounded border border-border p-3 h-[500px] overflow-y-auto font-mono text-xs"
      >
        {error && (
          <div className="text-red-400 mb-2">
            错误: {error}
          </div>
        )}

        {isLoading && logs.length === 0 ? (
          <div className="text-muted-foreground text-center py-8">加载中...</div>
        ) : filteredLogs.length === 0 ? (
          <div className="text-muted-foreground text-center py-8">没有符合条件的日志</div>
        ) : (
          <div className="space-y-0.5">
            {filteredLogs.map((log) => (
              <div key={log.line_number} className={`flex ${getLevelColor(log.level)}`}>
                <span className="text-muted-foreground select-none mr-3 min-w-[60px]">
                  [{log.line_number}]
                </span>
                <span className="whitespace-pre-wrap break-all">{log.content}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
