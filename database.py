"""
数据库连接和操作模块
"""
import mysql.connector
from mysql.connector import Error
from typing import Optional, Dict, Any, List
from loguru import logger
from config import DB_CONFIG


class DatabaseManager:
    """MySQL数据库管理器"""
    
    def __init__(self):
        self.connection = None
        self.cursor = None
    
    def connect(self) -> bool:
        """连接到数据库"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            if self.connection.is_connected():
                self.cursor = self.connection.cursor()
                logger.info("成功连接到MySQL数据库")
                return True
        except Error as e:
            logger.error(f"连接数据库失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("数据库连接已关闭")
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            if self.connect():
                # 测试查询
                self.cursor.execute("SELECT 1")
                result = self.cursor.fetchone()
                self.disconnect()
                return result is not None
        except Error as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def insert_news(self, title: str, summary: str, content: str, importance: str = '低') -> bool:
        """插入新闻数据"""
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return False

            query = """
            INSERT INTO news (title, summary, importance, content)
            VALUES (%s, %s, %s, %s)
            """
            values = (title, summary, importance, content)
            
            self.cursor.execute(query, values)
            self.connection.commit()
            
            logger.info(f"成功插入新闻: {title[:50]}...")
            return True
            
        except Error as e:
            logger.error(f"插入新闻失败: {e}")
            if self.connection:
                self.connection.rollback()
            return False
    
    def get_latest_news(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最新的新闻"""
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return []
            
            query = """
            SELECT id, title, summary, importance, content, created_at, updated_at
            FROM news
            ORDER BY created_at DESC
            LIMIT %s
            """

            self.cursor.execute(query, (limit,))
            results = self.cursor.fetchall()

            # 转换为字典格式
            columns = ['id', 'title', 'summary', 'importance', 'content', 'created_at', 'updated_at']
            news_list = []
            for row in results:
                news_dict = dict(zip(columns, row))
                news_list.append(news_dict)
            
            return news_list
            
        except Error as e:
            logger.error(f"获取新闻失败: {e}")
            return []
    
    def check_news_exists(self, title: str) -> bool:
        """检查新闻是否已存在"""
        try:
            if not self.connection or not self.connection.is_connected():
                if not self.connect():
                    return False
            
            query = "SELECT COUNT(*) FROM news WHERE title = %s"
            self.cursor.execute(query, (title,))
            count = self.cursor.fetchone()[0]
            
            return count > 0
            
        except Error as e:
            logger.error(f"检查新闻是否存在失败: {e}")
            return False


# 全局数据库管理器实例
db_manager = DatabaseManager()


def test_database_connection():
    """测试数据库连接的独立函数"""
    logger.info("开始测试数据库连接...")
    
    if db_manager.test_connection():
        logger.info("✅ 数据库连接测试成功!")
        return True
    else:
        logger.error("❌ 数据库连接测试失败!")
        return False


if __name__ == "__main__":
    # 测试数据库连接
    test_database_connection()
