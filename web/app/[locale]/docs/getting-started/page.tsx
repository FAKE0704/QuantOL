import { useTranslations } from 'next-intl'

export default function GettingStartedPage() {
  const t = useTranslations('docs')

  return (
    <div className="py-8">
      <h1 className="text-3xl font-bold mb-6">{t('gettingStarted')}</h1>

      <div className="prose prose-invert max-w-none">
        <h2 className="text-2xl font-semibold mb-4">系统要求</h2>
        <ul className="list-disc list-inside text-muted-foreground space-y-2 mb-6">
          <li>Python 3.10+</li>
          <li>Node.js 18+</li>
          <li>SQLite 或 PostgreSQL</li>
          <li>4GB+ 内存推荐</li>
        </ul>

        <h2 className="text-2xl font-semibold mb-4">快速安装</h2>
        <div className="bg-slate-900 rounded-lg p-4 mb-6">
          <pre className="text-sm text-slate-300">
{`# 克隆仓库
git clone https://github.com/FAKE0704/QuantOL.git
cd QuantOL

# 安装 Python 依赖
uv pip install -e .

# 启动后端服务
python -m uvicorn src.main:app --reload`}
          </pre>
        </div>

        <h2 className="text-2xl font-semibold mb-4">配置数据源</h2>
        <p className="text-muted-foreground mb-4">
          QuantOL 支持多种数据源，您可以在配置文件中选择使用：
        </p>
        <ul className="list-disc list-inside text-muted-foreground space-y-2">
          <li>Tushare - 需要申请 API Token</li>
          <li>Baostock - 免费注册使用</li>
          <li>AkShare - 开源免费数据接口</li>
        </ul>
      </div>
    </div>
  )
}
