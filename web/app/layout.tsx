import type { Metadata } from 'next'
import { Inter, JetBrains_Mono } from 'next/font/google'
import './globals.css'

const inter = Inter({
  variable: '--font-inter',
  subsets: ['latin'],
})

const jetbrainsMono = JetBrains_Mono({
  variable: '--font-mono',
  subsets: ['latin'],
})

export const metadata: Metadata = {
  title: 'QuantOL - 专业级量化交易平台',
  description: '基于事件驱动架构的Python量化交易系统，支持多策略回测、实时风控、多数据源集成',
  keywords: '量化交易, 回测系统, Python交易, 策略开发, QuantOL',
  openGraph: {
    title: 'QuantOL - 量化交易平台',
    description: '专业级事件驱动量化交易平台',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  )
}
