'use client'

import { Card, CardContent } from '@/components/ui/card'
import { performanceMetrics, backtestChartData, architectureSteps } from '@/lib/data'
import { motion } from 'framer-motion'
import {
  TrendingUp, BarChart3, AlertCircle, Target,
  Scale, Calendar, LucideIcon
} from 'lucide-react'
import {
  LineChart,
  Line,
  ResponsiveContainer,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts'

const iconMap: Record<string, LucideIcon> = {
  TrendingUp,
  BarChart3,
  AlertCircle,
  Target,
  Scale,
  Calendar,
}

export function Performance() {
  return (
    <section id="performance" className="py-24 relative">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-background via-background to-primary/5" />

      <div className="container mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        {/* Section header */}
        <motion.div
          className="text-center mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            性能指标与回测结果
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
            基于真实历史数据的回测结果展示，助您了解策略的实际表现
          </p>
        </motion.div>

        {/* Metrics grid */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {performanceMetrics.map((metric, index) => {
            const Icon = iconMap[metric.icon]
            return (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className="border-border bg-card/50 hover:bg-card/80 transition-all duration-300">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className={`p-3 rounded-lg bg-background ${metric.color}`}>
                        <Icon className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-sm text-muted-foreground">{metric.label}</div>
                        <div className="text-2xl font-bold">{metric.value}</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )
          })}
        </div>

        {/* Backtest chart */}
        <motion.div
          className="mb-16"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Card className="border-border bg-card/50">
            <CardContent className="p-6">
              <h3 className="text-xl font-semibold mb-6">回测收益曲线</h3>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={backtestChartData.datasets[0].data.map((val, i) => ({
                  month: backtestChartData.labels[i],
                  策略收益: val,
                  基准收益: backtestChartData.datasets[1].data[i],
                }))}>
                  <XAxis
                    dataKey="month"
                    stroke="#737373"
                    fontSize={12}
                  />
                  <YAxis
                    stroke="#737373"
                    fontSize={12}
                    tickFormatter={(value) => `¥${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#141414',
                      border: '1px solid #262626',
                      borderRadius: '8px',
                    }}
                    formatter={(value) => [`¥${(value || 0).toLocaleString()}`, '']}
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="策略收益"
                    stroke={backtestChartData.datasets[0].color}
                    strokeWidth={2}
                    dot={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="基准收益"
                    stroke={backtestChartData.datasets[1].color}
                    strokeWidth={2}
                    dot={false}
                    strokeDasharray="5 5"
                  />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </motion.div>

        {/* Architecture flow */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
        >
          <Card className="border-border bg-card/50">
            <CardContent className="p-8">
              <h3 className="text-xl font-semibold mb-8 text-center">系统架构流程</h3>
              <div className="flex flex-col md:flex-row items-center justify-between gap-4">
                {architectureSteps.map((step, index) => (
                  <div key={step.title} className="flex items-center gap-4">
                    <motion.div
                      className="flex flex-col items-center gap-2"
                      whileHover={{ scale: 1.05 }}
                      transition={{ duration: 0.2 }}
                    >
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30">
                        {(() => {
                          const IconComponent = iconMap[step.icon as keyof typeof iconMap] || AlertCircle;
                          return <IconComponent className="w-7 h-7 text-primary" />;
                        })()}
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-sm">{step.title}</div>
                        <div className="text-xs text-muted-foreground">{step.description}</div>
                      </div>
                    </motion.div>
                    {index < architectureSteps.length - 1 && (
                      <div className="hidden md:block w-12 h-0.5 bg-gradient-to-r from-primary to-accent" />
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </section>
  )
}
