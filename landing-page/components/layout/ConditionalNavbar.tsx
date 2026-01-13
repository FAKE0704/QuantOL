'use client'

import { usePathname } from 'next/navigation'
import { Navbar } from './Navbar'

// 不显示 Navbar 的路径
const HIDE_NAVBAR_PATHS = ['/dashboard', '/backtest', '/login', '/register']

export function ConditionalNavbar() {
  const pathname = usePathname()

  // 如果当前路径在不显示 Navbar 的列表中，返回 null
  if (HIDE_NAVBAR_PATHS.some(path => pathname?.startsWith(path))) {
    return null
  }

  return <Navbar />
}
