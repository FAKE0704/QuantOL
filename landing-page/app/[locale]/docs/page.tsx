import { useTranslations } from 'next-intl'
import { Link } from '@/lib/routing'
import { BookOpen, Code, Cpu, Zap } from 'lucide-react'

export default function DocsPage() {
  const t = useTranslations('docs')

  const quickLinks = [
    {
      icon: BookOpen,
      title: t('gettingStarted'),
      slug: 'getting-started',
      description: '快速了解 QuantOL 的基本概念和安装步骤',
    },
    {
      icon: Code,
      title: t('strategies'),
      slug: 'strategies',
      description: '学习如何开发和配置量化交易策略',
    },
    {
      icon: Cpu,
      title: t('backtesting'),
      slug: 'backtesting',
      description: '使用回测引擎验证您的交易策略',
    },
    {
      icon: Zap,
      title: t('apiEvents'),
      slug: 'api-events',
      description: '深入了解事件系统和技术接口',
    },
  ]

  const indicatorLinks = [
    { title: 'SMA - 简单移动平均', slug: 'rules-sma', desc: 'SMA(close, period)' },
    { title: 'RSI - 相对强弱指数', slug: 'rules-rsi', desc: 'RSI(close, period)' },
    { title: 'REF - 引用历史数据', slug: 'rules-ref', desc: 'REF(expr, period)' },
    { title: 'VWAP - 成交量加权平均价', slug: 'rules-vwap', desc: 'VWAP(period)' },
    { title: 'C_P - 典型价格', slug: 'rules-cp', desc: 'C_P(period)' },
    { title: 'Q - 分位数计算', slug: 'rules-q', desc: 'Q(series, q, period)' },
    { title: 'SQRT - 开方', slug: 'rules-sqrt', desc: 'SQRT(x, n)' },
  ]

  return (
    <div className="py-8">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
          QuantOL 文档
        </h1>
        <p className="text-lg text-slate-400">
          专业级事件驱动量化交易平台的完整文档
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 mb-12">
        {quickLinks.map((link) => {
          const Icon = link.icon
          return (
            <Link
              key={link.slug}
              href={`/docs/${link.slug}`}
              className="group p-6 rounded-lg border border-border hover:border-primary/50 bg-card hover:bg-card/80 transition-all"
            >
              <div className="flex items-start gap-4">
                <div className="p-3 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors">
                  <Icon className="w-6 h-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold mb-2 group-hover:text-primary transition-colors">
                    {link.title}
                  </h3>
                  <p className="text-sm text-slate-400">{link.description}</p>
                </div>
              </div>
            </Link>
          )
        })}
      </div>

      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-4">交易策略规则</h2>
        <p className="text-slate-400 mb-6">配置交易条件时可用的函数（点击查看详情）</p>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-3">
          {indicatorLinks.map((link) => (
            <Link
              key={link.slug}
              href={`/docs/${link.slug}`}
              className="group p-4 rounded-lg border border-border hover:border-primary/50 bg-card hover:bg-card/80 transition-all"
            >
              <h3 className="text-base font-semibold mb-1 group-hover:text-primary transition-colors">
                {link.title}
              </h3>
              <code className="text-sm text-sky-400">{link.desc}</code>
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-12 p-6 rounded-lg bg-gradient-to-r from-primary/10 to-accent/10 border border-border">
        <h3 className="text-xl font-semibold mb-2">开始使用</h3>
        <p className="text-slate-400 mb-4">
          准备好开始您的量化交易之旅了吗？
        </p>
        <Link
          href="/login"
          className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-white rounded-md transition-colors"
        >
          立即开始
        </Link>
      </div>
    </div>
  )
}
