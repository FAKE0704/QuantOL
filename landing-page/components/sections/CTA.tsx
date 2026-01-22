'use client'

import { useTranslations } from 'next-intl'
import { Link } from '@/lib/routing'
import { Play } from 'lucide-react'
import { motion } from 'framer-motion'

export function CTA() {
  const t = useTranslations('cta')

  return (
    <section className="py-24 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          className="relative overflow-hidden rounded-2xl border border-border bg-gradient-to-br from-primary/10 via-accent/10 to-background p-12 md:p-16 text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          {/* Background decoration */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#262626_1px,transparent_1px),linear-gradient(to_bottom,#262626_1px,transparent_1px)] bg-[size:48px_48px] opacity-10" />

          {/* Glowing orbs */}
          <motion.div
            className="absolute top-0 left-1/4 w-64 h-64 bg-primary/20 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut"
            }}
          />
          <motion.div
            className="absolute bottom-0 right-1/4 w-64 h-64 bg-accent/20 rounded-full blur-3xl"
            animate={{
              scale: [1, 1.2, 1],
              opacity: [0.3, 0.5, 0.3],
            }}
            transition={{
              duration: 6,
              repeat: Infinity,
              ease: "easeInOut",
              delay: 3
            }}
          />

          {/* Content */}
          <div className="relative z-10 max-w-2xl mx-auto">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-6">
              {t('title')}
            </h2>
            <p className="text-muted-foreground text-lg mb-8">
              {t('description')}
            </p>
            <div className="flex flex-wrap justify-center gap-4">
              <Link
                href="/backtest"
                className="inline-flex items-center gap-2 px-6 py-3 bg-black dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-gray-800 dark:hover:from-amber-600 dark:hover:to-orange-600 text-white rounded-full text-base font-medium transition-all shadow-md hover:shadow-lg"
              >
                <Play className="w-4 h-4" />
                {t('secondary')}
              </Link>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  )
}
