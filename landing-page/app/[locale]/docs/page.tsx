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

      <div className="grid gap-6 md:grid-cols-2">
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
