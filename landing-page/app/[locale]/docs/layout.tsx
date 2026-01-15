'use client'

import { useState } from 'react'
import { useTranslations } from 'next-intl'
import { Link } from '@/lib/routing'
import { Menu, X, FileText, ChevronRight } from 'lucide-react'
import { docsNavigation } from '@/lib/data'

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const t = useTranslations('docs')
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="fixed top-16 left-0 right-0 z-40 bg-background/80 backdrop-blur-lg border-b border-border shadow-md">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <button
              className="lg:hidden p-2 hover:bg-accent rounded-md"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            >
              {isSidebarOpen ? (
                <X className="w-5 h-5" />
              ) : (
                <Menu className="w-5 h-5" />
              )}
            </button>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <FileText className="w-4 h-4" />
              <span>QuantOL {t('categories.gettingStarted')}</span>
            </div>
          </div>
        </div>
      </header>

      <div className="pt-[120px]">
        <div className="container mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex">
            {/* Sidebar */}
            <aside
              className={`fixed lg:sticky top-[120px] left-0 z-30 w-64 h-[calc(100vh-120px)] bg-background border-r border-border overflow-y-auto transform transition-transform lg:translate-x-0 ${
                isSidebarOpen ? 'translate-x-0' : '-translate-x-full'
              }`}
            >
              <nav className="p-4 space-y-6">
                {docsNavigation.map((section) => {
                  const categoryKey = section.category === '入门指南' ? 'gettingStarted' :
                                    section.category === '核心功能' ? 'core' :
                                    section.category === '交易策略规则' ? 'tradingRules' : 'api'
                  return (
                    <div key={section.category}>
                      <h3 className="mb-2 text-sm font-semibold text-foreground">
                        {t(`categories.${categoryKey}`)}
                      </h3>
                      <ul className="space-y-1">
                        {section.items.map((item) => (
                          <li key={item.slug}>
                            <Link
                              href={`/docs/${item.slug}`}
                              className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-accent rounded-md transition-colors"
                              onClick={() => setIsSidebarOpen(false)}
                            >
                              <ChevronRight className="w-4 h-4" />
                              {t(item.slug as any) || item.title}
                            </Link>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )
                })}
              </nav>
            </aside>

            {/* Overlay for mobile */}
            {isSidebarOpen && (
              <div
                className="fixed inset-0 z-20 bg-black/50 lg:hidden"
                onClick={() => setIsSidebarOpen(false)}
              />
            )}

            {/* Main content */}
            <main className="flex-1 min-w-0 lg:ml-0 p-4 lg:p-8">
              <div className="max-w-4xl mx-auto">{children}</div>
            </main>
          </div>
        </div>
      </div>
    </div>
  )
}
