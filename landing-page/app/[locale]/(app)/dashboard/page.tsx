"use client";

/**
 * Dashboard Page
 *
 * Main dashboard page showing embedded Streamlit charts.
 */

import { useEffect, useState } from "react";
import { useTranslations } from "next-intl";
import { useRequireAuth } from "@/lib/store";
import { useApi } from "@/lib/api";
import { StreamlitChart } from "@/components/charts/StreamlitChart";
import { Button } from "@/components/ui/button";
import { Link } from "@/lib/routing";
import { ThemeSwitcher } from "@/components/layout/ThemeSwitcher";
import { UserAccountMenu } from "@/components/layout/UserAccountMenu";

export default function DashboardPage() {
  const t = useTranslations('dashboard')
  const { user, isLoading, token, logout } = useRequireAuth();
  const { getDashboardStats } = useApi();

  const [stats, setStats] = useState({
    total_strategies: 0,
    active_backtests: 0,
  });
  const [isLoadingStats, setIsLoadingStats] = useState(true);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await getDashboardStats();
        if (response.success && response.data) {
          setStats(response.data);
        }
      } catch (error) {
        console.error('Failed to load dashboard stats:', error);
      } finally {
        setIsLoadingStats(false);
      }
    };

    loadStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!user) {
    return null; // Will redirect
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/" className="text-2xl font-bold text-sky-500">
              QuantOL
            </Link>
            <nav className="hidden md:flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-foreground hover:text-primary transition-colors"
              >
                {t('dashboard')}
              </Link>
              <Link
                href="/backtest"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('backtesting')}
              </Link>
              <Link
                href="/trading"
                className="text-muted-foreground hover:text-primary transition-colors"
              >
                {t('trading')}
              </Link>
            </nav>
          </div>

          <div className="flex items-center gap-4">
            <ThemeSwitcher />
            <UserAccountMenu
              username={user.username}
              onLogout={async () => {
                await logout();
                window.location.href = "/login";
              }}
            />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">{t('title')}</h1>
          <p className="text-muted-foreground">
            {t('description', { name: user.username })}
          </p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <StatCard
            title={t('totalStrategies')}
            value={stats.total_strategies}
            change={t('availableStrategies')}
            isLoading={isLoadingStats}
          />
          <StatCard
            title={t('activeBacktests')}
            value={stats.active_backtests}
            change={t('runningNow')}
            isLoading={isLoadingStats}
          />
          <StatCard
            title={t('totalReturn')}
            value="N/A"
            change={t('comingSoon')}
            isLoading={isLoadingStats}
            tooltip={t('realtimeTradingInDev')}
          />
          <StatCard
            title={t('winRate')}
            value="N/A"
            change={t('comingSoon')}
            isLoading={isLoadingStats}
            tooltip={t('realtimeTradingInDev')}
          />
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Performance Chart */}
          <ChartCard
            title={t('portfolioPerformance')}
            description={t('portfolioPerformanceDesc')}
          >
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              {t('comingSoon')}
            </div>
          </ChartCard>

          {/* Returns Distribution */}
          <ChartCard
            title={t('returnsDistribution')}
            description={t('returnsDistributionDesc')}
          >
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              {t('comingSoon')}
            </div>
          </ChartCard>

          {/* Drawdown Chart */}
          <ChartCard
            title={t('drawdownAnalysis')}
            description={t('drawdownAnalysisDesc')}
          >
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              {t('comingSoon')}
            </div>
          </ChartCard>

          {/* Trade History */}
          <ChartCard
            title={t('recentTrades')}
            description={t('recentTradesDesc')}
          >
            <div className="h-[400px] flex items-center justify-center text-muted-foreground">
              {t('comingSoon')}
            </div>
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
  isLoading = false,
  tooltip,
}: {
  title: string;
  value: string | number;
  change: string;
  isLoading?: boolean;
  tooltip?: string;
}) {
  return (
    <div className="bg-card/50 border border-border rounded-lg p-6">
      <p className="text-sm text-muted-foreground mb-1">{title}</p>
      {isLoading ? (
        <div className="animate-pulse">
          <div className="h-8 bg-muted rounded w-16 mb-2"></div>
          <div className="h-4 bg-muted rounded w-24"></div>
        </div>
      ) : (
        <>
          <p
            className="text-2xl font-bold text-foreground mb-1"
            title={tooltip}
          >
            {value}
          </p>
          <p className="text-xs text-sky-500">{change}</p>
        </>
      )}
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
    <div className="bg-card/30 border border-border rounded-lg overflow-hidden">
      <div className="p-4 border-b border-border">
        <h3 className="text-lg font-semibold text-foreground">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
