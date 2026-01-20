'use client'

import { useState } from 'react'
import { createPortal } from 'react-dom'
import { Coffee, X } from 'lucide-react'

export function CoffeeButton() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 px-4 py-2 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full text-sm font-medium transition-all shadow-md hover:shadow-lg"
      >
        <Coffee className="w-4 h-4" />
        请我喝咖啡
      </button>

      {isOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          {/* 背景遮罩 */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          {/* 模态框 */}
          <div
            className="relative bg-card border border-border rounded-lg shadow-2xl max-w-2xl w-full text-foreground"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 关闭按钮 */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 p-1 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>

            {/* 头部 */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white rounded-t-lg">
              <div className="flex items-center gap-3">
                <Coffee className="w-8 h-8" />
                <div>
                  <h3 className="text-xl font-bold">感谢你的支持！</h3>
                  <p className="text-amber-100 text-sm">如果你觉得这个项目对你有帮助</p>
                </div>
              </div>
            </div>

            {/* 内容 */}
            <div className="p-6 space-y-6 rounded-b-lg">
              {/* 二维码 */}
              <div className="flex justify-center">
                <div className="bg-white p-2 rounded-lg shadow-inner w-[28rem] h-[28rem] overflow-hidden">
                  <img
                    src="/receive.JPG"
                    alt="收款二维码"
                    className="w-[42.5rem] h-[42.5rem] object-contain -translate-y-[4.25rem]"
                  />
                </div>
              </div>

              {/* 感谢文字 */}
              <div className="text-center">
                <p className="text-sm text-slate-800 dark:text-white">
                  你的支持是我持续开发的动力！
                </p>
              </div>

              {/* 资金用途 */}
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                <h4 className="font-semibold text-amber-600 dark:text-amber-400 mb-2 flex items-center gap-2">
                  <Coffee className="w-4 h-4" />
                  资金用途
                </h4>
                <ul className="text-sm text-slate-800 dark:text-white space-y-1">
                  <li>☕ 买杯咖啡，熬夜写代码更有精神</li>
                  <li>🔧 服务器和域名费用</li>
                  <li>📚 购买技术书籍和学习资料</li>
                  <li>🚀 持续改进功能和添加新特性</li>
                </ul>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  )
}

export function CoffeeModal() {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-2 px-4 py-2 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full text-sm font-medium transition-all shadow-md hover:shadow-lg"
      >
        <Coffee className="w-4 h-4" />
        请我喝咖啡
      </button>

      {isOpen && createPortal(
        <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
          {/* 背景遮罩 */}
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setIsOpen(false)}
          />
          {/* 模态框 */}
          <div
            className="relative bg-card border border-border rounded-lg shadow-2xl max-w-2xl w-full text-foreground"
            onClick={(e) => e.stopPropagation()}
          >
            {/* 关闭按钮 */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-4 right-4 p-1 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200 transition-colors z-10"
            >
              <X className="w-5 h-5" />
            </button>

            {/* 头部 */}
            <div className="bg-gradient-to-r from-amber-500 to-orange-500 p-6 text-white rounded-t-lg">
              <div className="flex items-center gap-3">
                <Coffee className="w-8 h-8" />
                <div>
                  <h3 className="text-xl font-bold">感谢你的支持！</h3>
                  <p className="text-amber-100 text-sm">如果你觉得这个项目对你有帮助</p>
                </div>
              </div>
            </div>

            {/* 内容 */}
            <div className="p-6 space-y-6 rounded-b-lg">
              {/* 二维码 */}
              <div className="flex justify-center">
                <div className="bg-white p-2 rounded-lg shadow-inner w-[28rem] h-[28rem] overflow-hidden">
                  <img
                    src="/receive.JPG"
                    alt="收款二维码"
                    className="w-[42.5rem] h-[42.5rem] object-contain -translate-y-[4.25rem]"
                  />
                </div>
              </div>

              {/* 感谢文字 */}
              <div className="text-center">
                <p className="text-sm text-slate-800 dark:text-white">
                  你的支持是我持续开发的动力！
                </p>
              </div>

              {/* 资金用途 */}
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-lg p-4">
                <h4 className="font-semibold text-amber-600 dark:text-amber-400 mb-2 flex items-center gap-2">
                  <Coffee className="w-4 h-4" />
                  资金用途
                </h4>
                <ul className="text-sm text-slate-800 dark:text-white space-y-1">
                  <li>☕ 买杯咖啡，熬夜写代码更有精神</li>
                  <li>🔧 服务器和域名费用</li>
                  <li>📚 购买技术书籍和学习资料</li>
                  <li>🚀 持续改进功能和添加新特性</li>
                </ul>
              </div>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  )
}
