* this is a Event-Driven Architecture-Based Quantitative System program
* 该项目使用Streamlit框架，数据库是PostgreSQL
* 

# 个人偏好设置
- @~/.claude/my-project-instructions.md
- 使用中文进行沟通

# 代码测试
- 需要先运行`.\venvWin\Scripts\activate`进入虚拟环境

# 系统的所有模块、所有类的members与职责
@docs/system-design/project_components_catalog.md

# 命名一致性
- 管理类：Manager后缀（RiskManager）
- 策略相关：Strategy后缀（PositionStrategy）
- 数据源：Source后缀（DataSource）
- 事件：无后缀（OrderEvent）