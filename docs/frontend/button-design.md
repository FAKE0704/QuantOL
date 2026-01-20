# 按钮设计规范

## 咖啡按钮（Coffee Button）

用于"请我喝咖啡"功能的胶囊形按钮设计。

### 设计特点

- **无边框**：无 border 或 border-transparent
- **完全圆角**：`rounded-full` 胶囊形状
- **阴影效果**：`shadow-md` 静态状态，`hover:shadow-lg` 悬停时增强
- **响应式颜色**：
  - Light 模式：纯色 `#FFEFD5`（Moccasin 米色）
  - Dark 模式：渐变 `from-amber-500 to-orange-500`
- **交互反馈**：
  - Hover 背景色加深
  - 平滑过渡 `transition-all`

### 代码实现

```tsx
<button
  onClick={() => setIsOpen(true)}
  className="inline-flex items-center gap-2 px-4 py-2 bg-[#FFEFD5] dark:bg-gradient-to-r dark:from-amber-500 dark:to-orange-500 hover:bg-[#FFE0C0] dark:hover:from-amber-600 dark:hover:to-orange-600 text-foreground dark:text-white rounded-full text-sm font-medium transition-all shadow-md hover:shadow-lg"
>
  <Coffee className="w-4 h-4" />
  请我喝咖啡
</button>
```

### 类名分解

| 类名 | 用途 |
|------|------|
| `inline-flex` | 内联弹性布局 |
| `items-center` | 垂直居中对齐 |
| `gap-2` | 图标与文字间距 0.5rem |
| `px-4 py-2` | 水平 1rem，垂直 0.5rem 内边距 |
| `bg-[#FFEFD5]` | Light 模式背景色（米色） |
| `dark:bg-gradient-to-r` | Dark 模式渐变背景 |
| `dark:from-amber-500 dark:to-orange-500` | 渐变色：琥珀到橙色 |
| `hover:bg-[#FFE0C0]` | Light 模式悬停背景 |
| `dark:hover:from-amber-600 dark:hover:to-orange-600` | Dark 模式悬停渐变加深 |
| `text-foreground` | Light 模式文字色（跟随主题） |
| `dark:text-white` | Dark 模式白色文字 |
| `rounded-full` | 完全圆角（胶囊形） |
| `text-sm` | 小号字体 |
| `font-medium` | 中等字重 |
| `transition-all` | 所有属性平滑过渡 |
| `shadow-md` | 中等阴影 |
| `hover:shadow-lg` | 悬停时大阴影 |

### 颜色值

| 模式 | 背景 | 悬停背景 | 文字 |
|------|------|----------|------|
| Light | `#FFEFD5` | `#FFE0C0` | `foreground` |
| Dark | `amber-500 → orange-500` | `amber-600 → orange-600` | `white` |

### 使用场景

- 赞助/捐赠功能入口
- 需要突出显示的行动按钮
- 友好/轻松的操作入口
