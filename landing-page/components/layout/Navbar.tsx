'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/lib/routing'
import { useState, useEffect } from 'react'
import { Menu, X } from 'lucide-react'
import { siteConfig } from '@/lib/data'
import { LanguageSelector } from './LanguageSelector'
import { ThemeSwitcher } from './ThemeSwitcher'

export function Navbar() {
  const t = useTranslations('nav')
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled
          ? 'bg-background/80 backdrop-blur-lg border-b border-border'
          : 'bg-transparent'
      }`}
    >
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-gradient-to-br from-primary to-accent rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">Q</span>
            </div>
            <span className="text-xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              {siteConfig.name}
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              {t('home')}
            </Link>
            <a
              href="#features"
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              {t('features')}
            </a>
            <a
              href="#performance"
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              {t('performance')}
            </a>
            <Link
              href="/docs"
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              {t('docs')}
            </Link>
            <Link
              href={siteConfig.links.app}
              className="text-muted-foreground hover:text-primary transition-colors"
            >
              {t('getStarted')}
            </Link>
            <ThemeSwitcher />
            <LanguageSelector />
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden p-2 text-muted-foreground hover:text-foreground transition-colors"
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        {isMobileMenuOpen && (
          <div className="md:hidden py-4 space-y-4 border-t border-border">
            <Link
              href="/"
              className="block text-muted-foreground hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              {t('home')}
            </Link>
            <a
              href="#features"
              className="block text-muted-foreground hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              {t('features')}
            </a>
            <a
              href="#performance"
              className="block text-muted-foreground hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              {t('performance')}
            </a>
            <Link
              href="/docs"
              className="block text-muted-foreground hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              {t('docs')}
            </Link>
            <Link
              href={siteConfig.links.app}
              className="block text-muted-foreground hover:text-primary transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              {t('getStarted')}
            </Link>
            <div className="pt-2 border-t border-border flex items-center gap-4">
              <ThemeSwitcher />
              <LanguageSelector />
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
