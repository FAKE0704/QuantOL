"use client";

import { Link } from "@/lib/routing";

/**
 * Trading Page (Open Source Version)
 *
 * This page is not available in the open source version.
 * Trading features are available in QuantOL-Pro.
 */

export default function TradingPage() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-4">交易功能不可用</h1>
        <p className="text-muted-foreground mb-4">
          交易功能在开源版本中不可用。
        </p>
        <p className="mb-4">
          请使用 <Link href="/backtest" className="text-sky-500 hover:underline">回测功能</Link> 或升级到 QuantOL-Pro 获取完整交易功能。
        </p>
      </div>
    </div>
  );
}
