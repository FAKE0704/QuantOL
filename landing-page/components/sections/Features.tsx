'use client'

import { useTranslations } from 'next-intl'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { motion } from 'framer-motion'
import {
  Network, LineChart, Shield, Database,
  FunctionSquare, BarChart3, LucideIcon
} from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Circuit: Network,
  ChartLine: LineChart,
  Shield,
  Database,
  FunctionSquare,
  BarChart3,
}

export function Features() {
  const t = useTranslations('features')

  const featureList = [
    { icon: 'Circuit', key: 'eventDriven' },
    { icon: 'ChartLine', key: 'backtesting' },
    { icon: 'Shield', key: 'riskControl' },
    { icon: 'Database', key: 'dataIntegration' },
    { icon: 'FunctionSquare', key: 'indicators' },
    { icon: 'BarChart3', key: 'visualization' },
  ]

  return (
    <section id="features" className="py-24 relative">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            强大的功能特性
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            QuantOL 提供完整的量化交易解决方案，从策略开发到回测执行，一站式满足您的需求
          </p>
        </motion.div>

        {/* Features grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featureList.map((feature, index) => {
            const Icon = iconMap[feature.icon]
            return (
              <motion.div
                key={feature.key}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="h-full border-border bg-card/50 hover:bg-card/80 transition-all duration-300 hover:border-primary/50 hover:shadow-lg hover:shadow-primary/10 group">
                  <CardHeader>
                    <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300">
                      <Icon className="w-6 h-6 text-primary" />
                    </div>
                    <CardTitle className="text-xl">{t(`${feature.key}.title` as any)}</CardTitle>
                    <CardDescription className="text-muted-foreground">
                      {t(`${feature.key}.description` as any)}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      <Badge variant="secondary" className="text-xs bg-muted text-muted-foreground hover:bg-muted/80">
                        Tech
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
