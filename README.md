# 新闻代理系统 (News Agent System)

基于 LangChain + LangGraph 的智能新闻分析系统，自动获取、分析、总结重要新闻并存储到数据库。

## 功能特性

- 🤖 **智能分析**: 使用AI模型分析新闻重要性
- 📰 **自动获取**: 从指定API自动获取最新新闻
- 📝 **智能总结**: AI生成新闻摘要和每日总结
- 💾 **数据存储**: 自动存储重要新闻到MySQL数据库
- ⏰ **定时任务**: 每6小时自动执行一次
- 🔧 **模块化设计**: 基于LangGraph的工作流设计

## 系统架构

```
新闻获取 → AI分析 → 生成总结 → 存储数据库
    ↓         ↓         ↓         ↓
news_fetcher → ai_summarizer → news_agent → database
```

## 安装配置

### 1. 环境要求

- Python 3.10+
- MySQL 5.7+
- conda环境: news_agent

### 2. 安装依赖

```bash
# 激活conda环境
conda activate news_agent

# 安装依赖包
uv pip install -r requirements.txt
```

### 3. 数据库配置

创建MySQL数据库和表：

```sql
-- 创建数据库
CREATE DATABASE news_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE news_agent;

-- 创建新闻表
CREATE TABLE news (
    id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(255) NOT NULL COMMENT '文章标题',
    summary TEXT COMMENT '文章摘要',
    importance ENUM('低', '中', '高') DEFAULT '低' COMMENT '新闻重要性等级',
    content MEDIUMTEXT NOT NULL COMMENT '文章正文',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);
```

### 4. 环境变量配置

复制并编辑环境变量文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入你的配置：

```env
# 数据库配置
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password  # 填入你的MySQL密码
DB_NAME=news_agent

# OpenAI API Key (如果使用OpenAI模型)
OPENAI_API_KEY=your_openai_api_key_here  # 填入你的OpenAI API Key

# 其他可选配置
LOG_LEVEL=INFO
```

## 使用方法

### 1. 测试系统组件

首次使用前，建议先测试所有组件：

```bash
python main.py --test
```

### 2. 执行单次任务

测试单次执行：

```bash
python main.py --run-once
```

### 3. 启动定时调度器

启动定时调度器（每6小时执行一次）：

```bash
# 启动调度器
python main.py --start

# 启动调度器并立即执行一次
python main.py --start-now
```

### 4. 查看系统信息

```bash
python main.py --info
```

## 项目结构

```
news_agent/
├── main.py              # 主程序入口
├── config.py            # 配置文件
├── database.py          # 数据库操作模块
├── news_fetcher.py      # 新闻获取模块
├── ai_summarizer.py     # AI总结模块
├── news_agent.py        # LangGraph代理核心
├── scheduler.py         # 定时任务调度模块
├── requirements.txt     # 依赖包列表
├── .env.example         # 环境变量模板
├── .env                 # 环境变量配置（需要自己创建）
└── README.md           # 说明文档
```

## 工作流程

1. **新闻获取**: 从新闻端口获取最新新闻
2. **AI分析**: 使用OpenAI模型分析新闻重要性（高/中/低）
3. **筛选过滤**: 只保留重要性为"中"或"高"的新闻
4. **生成总结**: 为重要新闻生成摘要和每日总结
5. **存储数据**: 将重要新闻和总结存储到MySQL数据库

## 配置说明

### 主要配置项

- `SCHEDULE_HOURS`: 定时任务间隔（默认6小时）
- `NEWS_API_URL`: 新闻API地址
- `DB_CONFIG`: 数据库连接配置
- `OPENAI_API_KEY`: OpenAI API密钥

### 日志配置

- 控制台输出：彩色格式，实时显示
- 文件输出：保存到 `news_agent.log`，自动轮转
- 日志级别：可通过 `LOG_LEVEL` 配置

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 确认数据库用户名密码正确
   - 确认数据库 `news_agent` 已创建

2. **新闻获取失败**
   - 检查网络连接
   - 确认API地址可访问

3. **AI分析失败**
   - 检查OpenAI API Key是否正确
   - 确认API配额是否充足

### 调试模式

启用详细日志：

```bash
# 修改 .env 文件
LOG_LEVEL=DEBUG
```

## 开发说明

### 扩展功能

- 添加新的新闻源：修改 `news_fetcher.py`
- 修改AI分析逻辑：修改 `ai_summarizer.py`
- 调整工作流程：修改 `news_agent.py`
- 更改调度策略：修改 `scheduler.py`

### 测试

每个模块都包含独立的测试函数，可以单独测试：

```bash
python database.py      # 测试数据库连接
python news_fetcher.py  # 测试新闻获取
python ai_summarizer.py # 测试AI总结
python news_agent.py    # 测试完整工作流
```

## 许可证

MIT License

## 更新日志

### v1.0.0
- 初始版本发布
- 支持新闻获取、AI分析、数据存储
- 支持定时任务调度
- 基于LangGraph的工作流设计
