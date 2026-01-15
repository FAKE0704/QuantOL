'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/lib/routing'
import { Github } from 'lucide-react'
import { siteConfig } from '@/lib/data'

export function Footer() {
  const t = useTranslations('footer')

  return (
    <footer className="border-t border-border bg-card/50">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="space-y-4">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-lg">Q</span>
              </div>
              <span className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                {siteConfig.name}
              </span>
            </Link>
            <p className="text-muted-foreground text-sm">
              {siteConfig.description}
            </p>
            <div className="flex space-x-4">
              <a
                href={siteConfig.links.github}
                target="_blank"
                rel="noopener noreferrer"
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <Github className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product Links */}
          <div>
            <h3 className="font-semibold mb-4">{t('product')}</h3>
            <ul className="space-y-2">
              <li>
                <a
                  href="#features"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  {t('features')}
                </a>
              </li>
              <li>
                <a
                  href="#performance"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  {t('performance')}
                </a>
              </li>
              <li>
                <Link
                  href="/docs/architecture"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  {t('features')}
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources Links */}
          <div>
            <h3 className="font-semibold mb-4">{t('resources')}</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/docs/getting-started"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  {t('features')}
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/strategies"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  {t('features')}
                </Link>
              </li>
              <li>
                <Link
                  href="/docs/api"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  API
                </Link>
              </li>
            </ul>
          </div>

          {/* Company Links */}
          <div>
            <h3 className="font-semibold mb-4">{t('company')}</h3>
            <ul className="space-y-2">
              <li>
                <Link
                  href="/about"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  {t('aboutUs')}
                </Link>
              </li>
              <li>
                <a
                  href={siteConfig.links.github}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-muted-foreground hover:text-foreground text-sm transition-colors"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-12 pt-8 border-t border-border text-center text-muted-foreground text-sm">
          <p>&copy; {new Date().getFullYear()} {siteConfig.name}. {t('allRightsReserved')}</p>
        </div>
      </div>
    </footer>
  )
}
