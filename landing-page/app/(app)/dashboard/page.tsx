"use client";

/**
 * Dashboard Page
 *
 * Main dashboard page showing embedded Streamlit charts.
 */

import { useRequireAuth } from "@/lib/store";
import { StreamlitChart } from "@/components/charts/StreamlitChart";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function DashboardPage() {
  const { user, isLoading, token } = useRequireAuth();

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-2xl font-bold text-sky-500">
              QuantOL
            </Link>
            <nav className="hidden md:flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-white hover:text-sky-400 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                href="/backtest"
                className="text-slate-400 hover:text-sky-400 transition-colors"
              >
                Backtesting
              </Link>
              <Link
                href="/trading"
                className="text-slate-400 hover:text-sky-400 transition-colors"
              >
                Trading
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <span className="text-sm text-slate-400">{user.username}</span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => window.location.href = "/login"}
              className="border-slate-700 text-slate-300 hover:bg-slate-800"
            >
              Logout
            </Button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-slate-400">
            Welcome back, {user.username}. Here&apos;s your trading overview.
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard title="Total Strategies" value="12" change="+2 this month" />
          <StatCard title="Active Backtests" value="3" change="Running" />
          <StatCard title="Total Return" value="+24.5%" change="+5.2% this month" />
          <StatCard title="Win Rate" value="68%" change="+3% this month" />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Chart */}
          <ChartCard
            title="Portfolio Performance"
            description="Historical performance of your portfolio"
          >
            <StreamlitChart
              chartType="performance"
              token={token || undefined}
              height="400px"
              className="bg-slate-900/50 rounded-lg"
            />
          </ChartCard>

          {/* Returns Distribution */}
          <ChartCard
            title="Returns Distribution"
            description="Monthly returns breakdown"
          >
            <StreamlitChart
              chartType="returns"
              token={token || undefined}
              height="400px"
              className="bg-slate-900/50 rounded-lg"
            />
          </ChartCard>

          {/* Drawdown Chart */}
          <ChartCard
            title="Drawdown Analysis"
            description="Portfolio drawdown over time"
          >
            <StreamlitChart
              chartType="drawdown"
              token={token || undefined}
              height="400px"
              className="bg-slate-900/50 rounded-lg"
            />
          </ChartCard>

          {/* Trade History */}
          <ChartCard
            title="Recent Trades"
            description="Your latest trading activity"
          >
            <StreamlitChart
              chartType="trades"
              token={token || undefined}
              height="400px"
              className="bg-slate-900/50 rounded-lg"
            />
          </ChartCard>
        </div>
      </main>
    </div>
  );
}

// Dashboard Components

function StatCard({
  title,
  value,
  change,
}: {
  title: string;
  value: string | number;
  change: string;
}) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className="text-2xl font-bold text-white mb-1">{value}</p>
      <p className="text-xs text-sky-500">{change}</p>
    </div>
  );
}

function ChartCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-slate-900/30 border border-slate-800 rounded-lg overflow-hidden">
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-lg font-semibold text-white">{title}</h3>
        <p className="text-sm text-slate-400">{description}</p>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
