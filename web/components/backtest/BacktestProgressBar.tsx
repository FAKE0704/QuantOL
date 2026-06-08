"use client";

import { Card } from "@/components/ui/card";

interface BacktestProgressBarProps {
  progress: number; // 0-100
  currentTime?: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  error?: string;
}

export function BacktestProgressBar({
  progress,
  currentTime,
  status,
  error,
}: BacktestProgressBarProps) {
  const statusConfig = {
    pending: { color: 'bg-slate-500', text: '等待中...' },
    running: { color: 'bg-sky-500', text: '运行中' },
    completed: { color: 'bg-emerald-500', text: '完成' },
    failed: { color: 'bg-red-500', text: '失败' },
  };

  const config = statusConfig[status];

  return (
    <Card className="p-6 bg-slate-900/50 border-slate-800">
      <div className="space-y-3">
        {/* 进度条容器 */}
        <div className="relative h-4 bg-slate-700 rounded-full overflow-hidden">
          <div
            className={`absolute top-0 left-0 h-full ${config.color} transition-all duration-300 ease-out`}
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* 状态信息 */}
        <div className="flex justify-between text-sm">
          <span className="text-slate-400">
            {config.text} - {progress.toFixed(1)}%
          </span>
          {currentTime && (
            <span className="text-slate-500">
              当前: {new Date(currentTime).toLocaleDateString()}
            </span>
          )}
        </div>

        {/* 错误提示 */}
        {error && (
          <div className="text-red-400 text-sm mt-2 p-2 bg-red-900/20 rounded">
            错误: {error}
          </div>
        )}
      </div>
    </Card>
  );
}
