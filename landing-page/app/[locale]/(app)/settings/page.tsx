"use client";

/**
 * Settings Page
 *
 * User settings including data source selection.
 */

import { useState } from "react";
import { useTranslations } from "next-intl";
import { useRequireAuth } from "@/lib/store";
import { UserAccountMenu } from "@/components/layout/UserAccountMenu";
import { ThemeSwitcher } from "@/components/layout/ThemeSwitcher";
import { CoffeeModal } from "@/components/layout/CoffeeModal";
import { Link } from "@/lib/routing";
import { Settings as SettingsIcon, Database, Check, Loader2 } from "lucide-react";

// Available data sources
const DATA_SOURCES = [
  { id: "tushare", name: "Tushare", description: "Professional financial data provider" },
  { id: "baostock", name: "Baostock", description: "Free securities data" },
  { id: "akshare", name: "AkShare", description: "Chinese economic data" },
  { id: "yahoo", name: "Yahoo Finance", description: "Global market data" },
];

export default function SettingsPage() {
  const t = useTranslations('settings');
  const { user, isLoading, token } = useRequireAuth();
  const { logout } = useRequireAuth();

  // Data source selection state
  const [selectedSource, setSelectedSource] = useState<string>("tushare");
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSaveDataSource = async () => {
    setIsSaving(true);
    setSaveSuccess(false);

    // Simulate API call - replace with actual API call
    await new Promise(resolve => setTimeout(resolve, 1000));

    // TODO: Call API to save data source preference
    // await api.saveDataSourcePreference(selectedSource);

    setIsSaving(false);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 2000);
  };

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sky-500" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-6">
            <Link href="/dashboard" className="text-2xl font-bold text-sky-500">
              QuantOL
            </Link>
            <nav className="hidden md:flex items-center gap-4">
              <Link
                href="/dashboard"
                className="text-slate-400 hover:text-sky-400 transition-colors"
              >
                {t('dashboard')}
              </Link>
              <Link
                href="/backtest"
                className="text-slate-400 hover:text-sky-400 transition-colors"
              >
                {t('backtesting')}
              </Link>
              <Link
                href="/trading"
                className="text-slate-400 hover:text-sky-400 transition-colors"
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
          <p className="text-slate-400">
            {t('description')}
          </p>
        </div>

        {/* Settings Sections */}
        <div className="space-y-6">
          {/* Data Source Selection */}
          <section className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
            <div className="p-6 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <Database className="h-5 w-5 text-sky-500" />
                <h2 className="text-xl font-semibold">{t('dataSource.title')}</h2>
              </div>
              <p className="text-sm text-slate-400 mt-1">{t('dataSource.description')}</p>
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
                        : 'border-slate-700 bg-slate-800/50 hover:border-slate-600'
                      }
                    `}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`
                        flex items-center justify-center w-5 h-5 rounded-full border-2
                        ${selectedSource === source.id ? 'border-sky-500 bg-sky-500' : 'border-slate-500'}
                      `}>
                        {selectedSource === source.id && (
                          <Check className="h-3 w-3 text-white" />
                        )}
                      </div>
                      <div>
                        <h3 className="font-medium text-white">{source.name}</h3>
                        <p className="text-sm text-slate-400">{source.description}</p>
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

              <div className="mt-6 flex items-center justify-between">
                <p className="text-sm text-slate-400">
                  {t('dataSource.note')}
                </p>
                <button
                  onClick={handleSaveDataSource}
                  disabled={isSaving}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all
                    ${isSaving
                      ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                      : 'bg-sky-500 hover:bg-sky-600 text-white'
                    }
                  `}
                >
                  {isSaving ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      {t('saving')}
                    </>
                  ) : saveSuccess ? (
                    <>
                      <Check className="h-4 w-4" />
                      {t('saved')}
                    </>
                  ) : (
                    t('save')
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
