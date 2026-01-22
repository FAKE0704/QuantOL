'use client'

import { usePathname } from '@/lib/routing'
import { Navbar } from './Navbar'

// 不显示 Navbar 的路径（不含 locale 前缀）
const HIDE_NAVBAR_PATHS = ['/dashboard', '/backtest', '/settings', '/register']

export function ConditionalNavbar() {
  const pathname = usePathname()

  // usePathname from routing 会自动移除 locale 前缀
  // 所以可以直接检查
  if (HIDE_NAVBAR_PATHS.some(path => pathname?.startsWith(path))) {
    return null
  }

  return <Navbar />
}
