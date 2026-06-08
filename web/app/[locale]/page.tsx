import { redirect } from 'next/navigation'

export default function Home({ params }: { params: { locale: string } }) {
  redirect(`/${params.locale}/backtest`)
}
