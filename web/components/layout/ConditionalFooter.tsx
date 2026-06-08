'use client'

import { usePathname } from '@/lib/routing'
import { Footer } from './Footer'

// 不显示 Footer 的路径（不含 locale 前缀）
const HIDE_FOOTER_PATHS = ['/login', '/register']

export function ConditionalFooter() {
  const pathname = usePathname()

  // usePathname from routing 会自动移除 locale 前缀
  // 所以可以直接检查
  if (HIDE_FOOTER_PATHS.some(path => pathname?.startsWith(path))) {
    return null
  }

  return <Footer />
}
