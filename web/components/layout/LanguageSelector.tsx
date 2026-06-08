'use client'

import { useState } from 'react'
import { useRouter, usePathname } from '@/lib/routing'
import { useLocale } from 'next-intl'
import { localeFlags, localeNames, type Locale } from '@/i18n/config'
import { Button } from '@/components/ui/button'
import { Check, ChevronDown, Globe } from 'lucide-react'

export function LanguageSelector() {
  const router = useRouter()
  const pathname = usePathname()
  const currentLocale = useLocale() as Locale
  const [isOpen, setIsOpen] = useState(false)

  const switchLocale = (locale: Locale) => {
    router.replace(pathname, { locale })
    setIsOpen(false)
  }

  const locales: Locale[] = ['zh', 'en']

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        className="text-muted-foreground hover:text-foreground"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Globe className="w-4 h-4 mr-2" />
        <span>{localeFlags[currentLocale]}</span>
        <ChevronDown className="w-4 h-4 ml-2" />
      </Button>

      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-2 z-50 min-w-[150px] rounded-lg border border-border bg-card p-1 shadow-lg">
            {locales.map((locale) => (
              <button
                key={locale}
                onClick={() => switchLocale(locale)}
                className="flex w-full items-center justify-between px-3 py-2 text-sm rounded-md hover:bg-accent transition-colors"
              >
                <span className="flex items-center gap-2">
                  <span>{localeFlags[locale]}</span>
                  <span>{localeNames[locale]}</span>
                </span>
                {currentLocale === locale && (
                  <Check className="w-4 h-4 text-primary" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}
