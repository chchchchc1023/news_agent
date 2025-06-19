"""
配置文件
"""
import os
from dotenv import load_dotenv

# 加载环境变量 - 强制加载.env文件
load_dotenv('.env', override=True)

# 数据库配置
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'news_agent'),
    'charset': 'utf8mb4',
    'ssl_disabled': False,  # 启用SSL
    'ssl_verify_cert': False,  # 跳过证书验证
    'ssl_verify_identity': False  # 跳过身份验证
}

# API配置
NEWS_API_URL = "http://volefuture.com/redis/get_latest_news/"

# OpenAI配置 (如果使用OpenAI)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# 调度配置
SCHEDULE_HOURS = 6  # 每6小时执行一次

# 日志配置
LOG_LEVEL = os.getenv('LOG_LEVEL', "DEBUG")  # 临时启用DEBUG
LOG_FILE = "news_agent.log"
