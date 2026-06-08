# QuantOL 仓库架构实施方案

## 文档版本

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|----------|
| 1.0 | 2025-03-05 | Claude | 初始版本 |

---

## 1. 架构概述

### 1.1 仓库结构

```
┌─────────────────────────────────────────────────────────────────┐
│                        开源生态                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  QuantOL (公开仓库)                                             │
│  ├── src/                    # 后端核心代码                      │
│  │   ├── core/               # 核心业务逻辑                     │
│  │   ├── api/                # API 路由（无认证）                │
│  │   ├── services/           # 服务层                           │
│  │   └── event_bus/          # 事件总线                         │
│  ├── main.py                 # Streamlit 界面                   │
│  ├── docs/                   # 完整文档                         │
│  └── README.md               # 一键启动说明                     │
│                                                                 │
│  开源用户体验：                                                  │
│  git clone https://github.com/FAKE0704/QuantOL.git              │
│  cd QuantOL && uv sync && uv run streamlit run main.py          │
│  → ✅ 完整的量化交易回测系统                                      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        商用生态                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  QuantOL-Pro (私有仓库)                                         │
│  ├── src/                    # 从 QuantOL 同步（未来）          │
│  ├── src-auth/               # 用户认证系统                     │
│  ├── src-subscription/       # 订阅管理系统                     │
│  ├── frontend/               # 完整商用前端                     │
│  │   ├── app/                # Next.js 应用                     │
│  │   │   ├── (app)/backtest/      # 回测功能                   │
│  │   │   ├── (app)/dashboard/     # 仪表盘                     │
│  │   │   ├── (app)/login/          # ✅ 登录                   │
│  │   │   ├── (app)/settings/       # 用户设置                   │
│  │   │   └── (landing)/            # ✅ Landing Page          │
│  │   ├── components/         # React 组件                      │
│  │   │   ├── ui/             # 基础 UI 组件                    │
│  │   │   └── auth/           # ✅ 认证组件                     │
│  │   ├── lib/                # 工具库                          │
│  │   │   ├── api.ts          # API 客户端（带认证）            │
│  │   │   ├── auth.ts         # ✅ 认证逻辑                     │
│  │   │   └── subscription.ts  # ✅ 订阅管理                     │
│  │   └── package.json                                         │
│  ├── deployment/             # 商用部署配置                     │
│  └── README.md               # 商用版说明                       │
│                                                                 │
│  商用用户流程：                                                  │
│  访问 https://quantol.pro → 注册/登录 → 选择订阅 → 使用完整功能  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 核心设计原则

### 2.1 功能边界

| 功能模块 | 开源版 (QuantOL) | 商用版 (QuantOL-Pro) |
|---------|------------------|----------------------|
| 回测引擎 | ✅ 完整 | ✅ 完整 |
| 策略系统 | ✅ 完整 | ✅ 完整 |
| 数据源支持 | ✅ 完整 | ✅ 完整 |
| 前端界面 | ✅ Streamlit | ✅ Next.js 完整版 |
| 用户认证 | ❌ 无 | ✅ 完整 |
| 订阅管理 | ❌ 无 | ✅ 完整 |
| 多账户管理 | ❌ 无 | ✅ 完整 |
| 实盘交易 | ❌ 无 | ✅ 完整 |
| 云端数据存储 | ❌ 本地存储 | ✅ 云端同步 |
| Landing Page | ❌ 无 | ✅ 完整 |
| 技术支持 | 社区支持 | ✅ 优先支持 |

### 2.2 代码隔离策略

```
后端隔离：
├── 开源代码 (src/)
│   └── 纯功能逻辑，零商业依赖
│
└── 商用扩展 (src-auth/, src-subscription/)
    ├── 独立目录
    └── 通过 API 集成

前端隔离：
├── 开源前端 (main.py - Streamlit)
│   └── 本地运行，无需认证
│
└── 商用前端 (frontend/)
    ├── 完整 Next.js 应用
    └── 用户系统和订阅逻辑
```

---

## 3. 实施步骤

### 3.1 阶段 1：开源仓库准备

#### 步骤 1.1：清理开源仓库

```bash
# 1. 删除之前误复制的 landing-page
cd /Users/gaogao/Documents/vscWork/QuantOL
rm -rf landing-page/

# 2. 确认 .gitignore 已更新（移除 landing-page/ 忽略规则）
git status
git add .gitignore
git commit -m "chore: update gitignore for repository split"

# 3. 推送到 GitHub
git push origin main
```

#### 步骤 1.2：确认 Streamlit 界面可用

```bash
# 当前已有 main.py，确认可以正常运行
cd /Users/gaogao/Documents/vscWork/QuantOL
uv sync
uv run streamlit run main.py

# 访问 http://localhost:8501 确认界面正常
```

#### 步骤 1.3：更新开源仓库 README

在 `README.md` 中更新快速开始部分：

```markdown
## 快速开始

### 安装
\`\`\`bash
git clone https://github.com/FAKE0704/QuantOL.git
cd QuantOL
uv sync
\`\`\`

### 启动
\`\`\`bash
# 使用 Streamlit 界面
uv run streamlit run main.py

# 访问 http://localhost:8501
\`\`\`

### 环境要求
- Python 3.12+
- uv (包管理器)
- SQLite 3.0+ (默认) 或 PostgreSQL 13+ (可选)
- Redis 7.0+ (用于状态存储)

## 功能说明

### ✅ 开源版功能
- 完整的回测引擎
- 多种策略支持（规则策略、仓位策略）
- 回测结果分析和可视化
- 多数据源支持（Tushare、Baostock、AkShare）
- 本地配置存储

### ❌ 不包含功能
- 无用户系统（本地运行）
- 无云端数据存储
- 无实盘交易接口
- 无订阅管理

需要完整功能？访问 [QuantOL-Pro](https://quantol.pro) 了解商用版。
```

---

### 3.2 阶段 2：商用仓库设置

#### 步骤 2.1：重命名 QuantOL-frontend 为 QuantOL-Pro

```bash
# 1. 在 GitHub 上重命名仓库
# 访问 https://github.com/FAKE0704/quantol-frontend/settings
# Repository name: QuantOL-Pro
# 确认是 Private

# 2. 更新本地仓库 remote URL
cd /Users/gaogao/Documents/vscWork/QuantOL-frontend
git remote set-url origin git@github.com:FAKE0704/QuantOL-Pro.git

# 3. 可选：重命名本地目录
mv /Users/gaogao/Documents/vscWork/QuantOL-frontend \
   /Users/gaogao/Documents/vscWork/QuantOL-Pro

# 4. 推送更改
cd /Users/gaogao/Documents/vscWork/QuantOL-Pro
git push -u origin main
```

#### 步骤 2.2：创建商用仓库结构

```bash
cd /Users/gaogao/Documents/vscWork/QuantOL-Pro

# 创建后端代码目录（未来从 QuantOL 同步）
mkdir -p src

# 创建商用扩展目录
mkdir -p src-auth/{api,services,models}
mkdir -p src-subscription/{api,services,models}

# 创建部署配置目录
mkdir -p deployment/{docker,kubernetes,nginx}
```

#### 步骤 2.3：更新商用仓库 README

更新 `README.md`：

```markdown
# QuantOL-Pro

商用版量化交易系统（私有仓库）

## 与开源版的关系

- 后端核心代码从 [QuantOL](https://github.com/FAKE0704/QuantOL) 定期同步
- 包含额外的商业功能：用户系统、订阅管理、实盘交易
- 完整的 Next.js 前端界面

## 功能对比

| 功能 | QuantOL (开源) | QuantOL-Pro (商用) |
|------|---------------|-------------------|
| 回测引擎 | ✅ | ✅ |
| 策略系统 | ✅ | ✅ |
| 前端界面 | Streamlit | Next.js 完整版 |
| 用户认证 | ❌ | ✅ |
| 多账户 | ❌ | ✅ |
| 实盘交易 | ❌ | ✅ |
| 云端存储 | ❌ | ✅ |
| 技术支持 | 社区 | 优先 |

## 本地开发

\`\`\`bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 访问 http://localhost:3000
\`\`\`

## 部署

详见 `deployment/` 目录下的部署文档。
```

---

## 4. 开发工作流程

### 4.1 当前状态

```
QuantOL (开源)
├── src/                    ✅ 后端核心代码
├── main.py                 ✅ Streamlit 界面
└── README.md               ⚠️ 需要更新

QuantOL-Pro (商用)
├── frontend/               ✅ 完整前端（原 QuantOL-frontend）
├── src/                    ⏳ 待创建（从 QuantOL 同步）
├── src-auth/               ⏳ 待创建（商用认证）
└── src-subscription/       ⏳ 待创建（订阅管理）
```

### 4.2 开发模式

**开源版开发**：
- 在 `QuantOL` 仓库直接开发
- 核心功能改进直接 push 到 GitHub
- 用户通过 Streamlit 界面使用

**商用版开发**：
- 在 `QuantOL-Pro` 仓库开发商业功能
- 后端核心代码未来可从 QuantOL 同步
- 前端继续使用 Next.js 完整版

### 4.3 版本管理

- 开源版：语义化版本 (1.0.0, 1.1.0...)
- 商用版：带前缀 (pro-1.0.0, pro-1.1.0...)

---

## 5. 检查清单

### 开源仓库 (QuantOL)

- [ ] 删除 landing-page 目录
- [ ] 更新 .gitignore
- [ ] 更新 README.md
- [ ] 确认 Streamlit 界面可用
- [ ] 推送到 GitHub

### 商用仓库 (QuantOL-Pro)

- [ ] 在 GitHub 重命名为 QuantOL-Pro
- [ ] 确认为 Private 状态
- [ ] 更新本地 remote URL
- [ ] 创建目录结构
- [ ] 更新 README.md

### 验证

- [ ] 开源仓库可以独立运行
- [ ] 商用仓库前端可以独立运行
- [ ] 两个仓库功能边界清晰

---

## 6. 注意事项

### 6.1 代码安全

1. **商用代码永远不要推送到开源仓库**
   - 商用仓库保持 Private
   - 严格的 Code Review 流程

2. **敏感信息管理**
   - API Key 使用环境变量
   - 数据库连接字符串加密存储
   - .env 文件加入 .gitignore

### 6.2 依赖管理

```python
# 开源版 pyproject.toml
# 只包含开源依赖
dependencies = [
    "fastapi>=0.104.0",
    "pandas>=2.1.0",
    # ...
]

# 商用版
# 继承开源依赖 + 商用依赖
dependencies = [
    # 开源依赖
    "fastapi>=0.104.0",
    "pandas>=2.1.0",
    # 商用依赖
    "stripe>=7.0.0",      # 支付
    "authlib>=1.2.0",     # 认证
]
```

---

## 7. 后续规划

### 7.1 未来工作（待定）

- [ ] 建立后端代码同步机制
- [ ] 实现商用认证系统
- [ ] 实现订阅管理系统
- [ ] 部署商用版到生产环境

### 7.2 同步策略（未来）

当需要同步后端代码时，可采用以下方式：

1. **手动同步**：定期复制核心代码
2. **脚本同步**：编写自动化同步脚本
3. **Submodule**：使用 Git Submodule 管理共享代码

---

## 8. 常见问题

### Q1: 为什么不使用 Git Submodule？

**A**: 当前阶段不需要频繁同步，手动复制即可满足需求。Submodule 会增加复杂度，等有明确需求时再考虑。

### Q2: 开源用户想要商业功能怎么办？

**A**: 在开源版本中添加友好的引导，提示访问 QuantOL-Pro 了解商用版功能。

### Q3: 如何避免商业代码泄漏？

**A**:
1. 商用仓库保持 Private
2. 严格的 Code Review
3. 定期审计开源仓库代码

---

## 9. 联系方式

如有问题，请联系：
- 开源项目：https://github.com/FAKE0704/QuantOL/issues
- 商用咨询：https://quantol.pro/contact

---

**文档结束**
