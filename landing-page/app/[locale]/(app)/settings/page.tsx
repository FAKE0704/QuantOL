"use client";

/**
 * Settings Page
 *
 * User settings including data source selection.
 */

import { useState, useEffect } from "react";
import { useTranslations } from "next-intl";
import { useRequireAuth } from "@/lib/store";
import { useApi } from "@/lib/api";
import { UserAccountMenu } from "@/components/layout/UserAccountMenu";
import { ThemeSwitcher } from "@/components/layout/ThemeSwitcher";
import { CoffeeModal } from "@/components/layout/CoffeeModal";
import { Link } from "@/lib/routing";
import { Settings as SettingsIcon, Database, Check, Loader2, Key } from "lucide-react";

// Available data sources
const DATA_SOURCES = [
  { id: "tushare", name: "Tushare", description: "Professional financial data provider", requiresToken: true },
  { id: "baostock", name: "Baostock", description: "Free securities data", requiresToken: false },
  { id: "akshare", name: "AkShare", description: "Chinese economic data", requiresToken: false },
  { id: "yahoo", name: "Yahoo Finance", description: "Global market data", requiresToken: false },
];

export default function SettingsPage() {
  const t = useTranslations('settings');
  const { user, isLoading, token, logout } = useRequireAuth();
  const { getDataSourceConfig, updateDataSourceConfig } = useApi();

  // Data source selection state
  const [selectedSource, setSelectedSource] = useState<string>("baostock");
  const [tushareToken, setTushareToken] = useState<string>("");
  const [tokenPreview, setTokenPreview] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [isLoadingConfig, setIsLoadingConfig] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string>("");

  // Load user's data source configuration on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await getDataSourceConfig();
        if (response.success && response.data) {
          setSelectedSource(response.data.data_source);
          setTokenPreview(response.data.token_preview || "");
        }
      } catch (error) {
        console.error("Failed to load data source config:", error);
      } finally {
        setIsLoadingConfig(false);
      }
    };

    if (user) {
      loadConfig();
    }
  }, [user, getDataSourceConfig]);

  const handleSaveDataSource = async () => {
    setIsSaving(true);
    setSaveSuccess(false);
    setErrorMessage("");

    try {
      // Validate Tushare token if Tushare is selected
      if (selectedSource === "tushare" && !tushareToken && !tokenPreview) {
        setErrorMessage("Tushare API token is required");
        setIsSaving(false);
        return;
      }

      const response = await updateDataSourceConfig({
        data_source: selectedSource,
        tushare_token: tushareToken || undefined,
      });

      if (response.success) {
        setSaveSuccess(true);
        setTokenPreview(tushareToken ? `${tushareToken.slice(0, 8)}...` : "");
        setTushareToken("");
        setTimeout(() => setSaveSuccess(false), 2000);
      } else {
        setErrorMessage(response.message || "Failed to save configuration");
      }
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Failed to save configuration");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="text-2xl font-bold text-sky-500">
              QuantOL
            </Link>
            <nav className="hidden md:flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-muted-foreground hover:text-primary transition-colors"
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
            <CoffeeModal />
            <UserAccountMenu username={user.username} onLogout={logout} />
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Page Title */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <SettingsIcon className="h-8 w-8 text-sky-500" />
            <h1 className="text-3xl font-bold">{t('title')}</h1>
          </div>
          <p className="text-muted-foreground">
            {t('description')}
          </p>
        </div>

        {/* Settings Sections */}
        <div className="space-y-6">
          {/* Data Source Selection */}
          <section className="bg-card/50 border border-border rounded-lg overflow-hidden">
            <div className="p-6 border-b border-border">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-sky-500" />
                <h2 className="text-xl font-semibold">{t('dataSource.title')}</h2>
              </div>
              <p className="text-sm text-muted-foreground mt-1">{t('dataSource.description')}</p>
            </div>

            <div className="p-6">
              <div className="space-y-3">
                {DATA_SOURCES.map((source) => (
                  <label
                    key={source.id}
                    className={`
                      flex items-center justify-between p-4 rounded-lg border-2 cursor-pointer transition-all
                      ${selectedSource === source.id
                        ? 'border-sky-500 bg-sky-500/10'
                        : 'border-border bg-muted/50 hover:border-border'
                      }
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`
                        flex items-center justify-center w-5 h-5 rounded-full border-2
                        ${selectedSource === source.id ? 'border-sky-500 bg-sky-500' : 'border-muted'}
                      `}>
                        {selectedSource === source.id && (
                          <Check className="h-3 w-3 text-white" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-medium text-foreground">{source.name}</h3>
                        <p className="text-sm text-muted-foreground">{source.description}</p>
                        {source.requiresToken && (
                          <p className="text-xs text-amber-400 mt-1 flex items-center gap-1">
                            <Key className="h-3 w-3" />
                            Requires API token
                          </p>
                        )}
                      </div>
                    </div>
                    <input
                      type="radio"
                      name="dataSource"
                      value={source.id}
                      checked={selectedSource === source.id}
                      onChange={(e) => setSelectedSource(e.target.value)}
                      className="sr-only"
                    />
                  </label>
                ))}
              </div>

              {/* Tushare Token Input */}
              {selectedSource === "tushare" && (
                <div className="mt-6 p-4 bg-muted/50 rounded-lg border border-border">
                  <label htmlFor="tushare-token" className="block text-sm font-medium text-foreground mb-2">
                    Tushare API Token
                    {tokenPreview && (
                      <span className="ml-2 text-xs text-green-400">
                        (Currently set: {tokenPreview})
                      </span>
                    )}
                  </label>
                  <input
                    id="tushare-token"
                    type="password"
                    value={tushareToken}
                    onChange={(e) => setTushareToken(e.target.value)}
                    placeholder={tokenPreview ? "Leave empty to keep current token" : "Enter your Tushare API token"}
                    className="w-full px-3 py-2 bg-background border border-input rounded-lg text-foreground placeholder-muted-foreground text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent"
                  />
                  <p className="text-xs text-muted-foreground mt-2">
                    Get your token at <a href="https://tushare.pro" target="_blank" rel="noopener noreferrer" className="text-sky-400 hover:underline">tushare.pro</a>
                  </p>
                </div>
              )}

              {/* Error message */}
              {errorMessage && (
                <div className="mt-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg">
                  <p className="text-sm text-destructive">{errorMessage}</p>
                </div>
              )}

              <div className="mt-6 flex items-center justify-between">
                <p className="text-sm text-muted-foreground">
                  {t('dataSource.note')}
                </p>
                <button
                  onClick={handleSaveDataSource}
                  disabled={isSaving || isLoadingConfig}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
                    ${isSaving || isLoadingConfig
                      ? 'bg-muted text-muted-foreground cursor-not-allowed'
                      : 'bg-sky-500 hover:bg-sky-600 text-white'
                    }
                  `}
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t('dataSource.saving')}
                    </>
                  ) : saveSuccess ? (
                    <>
                      <Check className="h-4 w-4" />
                      {t('dataSource.saved')}
                    </>
                  ) : (
                    t('dataSource.save')
                  )}
                </button>
              </div>
            </div>
          </section>

          {/* More settings sections can be added here */}
        </div>
      </main>
    </div>
  );
}
