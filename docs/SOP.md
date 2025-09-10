# 启动应用
.\venvWin\Scripts\activate
source 

cd .\src\
streamlit run main.py


# 创建任务
@/docs/system-design/文件结构.md 我正在开发一个量化交易系统，由于数据模块(core/data)涉及多个外部api数据接口，是否建议使用工厂(factory)的设计，我原本的打算是一个api接口建立一个类，如baostock_source.py就对应baostock数据源

# git prompt
请参考模板 /Users/gaogao/Documents/vsc_work/awesome-Qsys/.github/ISSUE_TEMPLATE/开发任务管理.md 写开发任务并调用github mcp server 发布到ISSUE




# 安装依赖
pip install xxx -i https://mirrors.aliyun.com/pypi/simple/



# 重新部署单个容器
docker-compose stop **web** && docker-compose rm -f **web** && docker-compose up -d --force-recreate --build **web**

docker-compose down && docker-compose up --build  -d

# 
```mermaid
flowchart TD
    A([开始]) --> B[阅读文件结构]
    B --> C[阅读类与方法]
    C --> D[开发具体问题]
    D --> E{涉及结构调整？}
    E -- 是 --> F[更新文件结构]
    E -- 否 --> G{涉及代码变更？}
    F --> G
    G -- 是 --> H[更新类与方法]
    G -- 否 --> I([结束])
    H --> I
    H --> B
    F --> C

%% 样式优化
    style A fill:#1d9fe4,stroke:#333,stroke-width:2px,color:#fff
    style B fill:#9f9,stroke:#333
    style C fill:#9f9,stroke:#333
    style D fill:#f90,stroke:#333
    style F fill:#ff9,stroke:#333
    style H fill:#ff9,stroke:#333
    style I fill:#e84133,stroke:#333,color:#fff
    style E fill:#f9f,stroke:#333,stroke-dasharray:5 5
    style G fill:#f9f,stroke:#333,stroke-dasharray:5 5
```
