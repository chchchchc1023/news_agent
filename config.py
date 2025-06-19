"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'news_agent'),
    'charset': 'utf8mb4'
}

# API配置
NEWS_API_URL = "http://volefuture.com/redis/get_latest_news/"

# OpenAI配置 (如果使用OpenAI)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 调度配置
SCHEDULE_HOURS = 6  # 每6小时执行一次

# 日志配置
LOG_LEVEL = "INFO"
LOG_FILE = "news_agent.log"
