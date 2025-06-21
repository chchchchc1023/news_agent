"""
新闻获取模块
"""
import requests
from typing import List, Dict, Any, Optional
from loguru import logger
from config import NEWS_API_URL
import json


class NewsFetcher:
    """新闻获取器"""
    
    def __init__(self):
        self.api_url = NEWS_API_URL
    
    def fetch_latest_news(self) -> Optional[List[Dict[str, Any]]]:
        """
        从API获取最新新闻
        
        Returns:
            List[Dict[str, Any]]: 新闻列表，每个新闻包含标题、内容等信息
        """
        try:
            logger.info(f"开始从 {self.api_url} 获取新闻...")

            # 每次请求时创建新的Session
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'close'
            })

            response = session.get(self.api_url, timeout=30)
            response.raise_for_status()  # 如果状态码不是200会抛出异常
            
            # 尝试解析JSON响应
            try:
                news_data = response.json()
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试解析文本
                logger.warning("响应不是JSON格式，尝试解析文本...")
                news_data = response.text
            
            logger.info(f"成功获取新闻数据，响应长度: {len(str(news_data))}")
            
            # 处理不同的响应格式
            if isinstance(news_data, list):
                # 检查是否是包含redis_value的特殊格式
                if len(news_data) > 0 and isinstance(news_data[0], dict) and 'redis_value' in news_data[0]:
                    # 提取redis_value中的新闻列表
                    all_news = []
                    for item in news_data:
                        if 'redis_value' in item and isinstance(item['redis_value'], list):
                            all_news.extend(item['redis_value'])
                    return all_news
                else:
                    return news_data
            elif isinstance(news_data, dict):
                # 如果是字典，尝试提取新闻列表
                if 'redis_value' in news_data:
                    return news_data['redis_value']
                elif 'data' in news_data:
                    return news_data['data']
                elif 'news' in news_data:
                    return news_data['news']
                elif 'items' in news_data:
                    return news_data['items']
                else:
                    # 如果字典中没有明显的新闻列表，将整个字典作为单条新闻
                    return [news_data]
            else:
                # 如果是字符串，尝试解析
                logger.warning(f"收到文本响应: {str(news_data)[:200]}...")
                return [{"title": "API响应", "content": str(news_data)}]
                
        except requests.exceptions.RequestException as e:
            logger.error(f"获取新闻失败 - 网络错误: {e}")
            return None
        except Exception as e:
            logger.error(f"获取新闻失败 - 未知错误: {e}")
            return None
    
    def parse_news_item(self, news_item: Dict[str, Any]) -> Dict[str, str]:
        """
        解析单条新闻项目，标准化字段名称
        
        Args:
            news_item: 原始新闻数据
            
        Returns:
            Dict[str, str]: 标准化的新闻数据，包含title, content字段
        """
        parsed_news = {
            'title': '',
            'content': ''
        }
        
        # 尝试提取标题
        title_fields = ['title', 'headline', 'subject', 'name', 'summary', 'app_msg']
        for field in title_fields:
            if field in news_item and news_item[field]:
                content_text = str(news_item[field]).strip()
                # 如果是app_msg，提取第一行作为标题
                if field == 'app_msg':
                    lines = content_text.split('\n')
                    parsed_news['title'] = lines[0].strip()
                else:
                    parsed_news['title'] = content_text
                break

        # 尝试提取内容
        content_fields = ['content', 'body', 'text', 'description', 'detail', 'article', 'app_msg']
        for field in content_fields:
            if field in news_item and news_item[field]:
                parsed_news['content'] = str(news_item[field]).strip()
                break
        
        # 如果没有找到标题，使用内容的前50个字符作为标题
        if not parsed_news['title'] and parsed_news['content']:
            parsed_news['title'] = parsed_news['content'][:50] + "..."
        
        # 如果没有找到内容，将整个item转为字符串
        if not parsed_news['content']:
            parsed_news['content'] = str(news_item)
        
        return parsed_news
    
    def get_processed_news(self) -> List[Dict[str, str]]:
        """
        获取并处理新闻数据
        
        Returns:
            List[Dict[str, str]]: 处理后的新闻列表
        """
        raw_news = self.fetch_latest_news()
        if not raw_news:
            logger.warning("没有获取到新闻数据")
            return []
        
        processed_news = []
        for item in raw_news:
            if isinstance(item, dict):
                parsed_item = self.parse_news_item(item)
                if parsed_item['title'] and parsed_item['content']:
                    processed_news.append(parsed_item)
            else:
                # 如果不是字典，直接转换
                processed_news.append({
                    'title': str(item)[:100] + "..." if len(str(item)) > 100 else str(item),
                    'content': str(item)
                })
        
        logger.info(f"成功处理 {len(processed_news)} 条新闻")
        return processed_news


# 全局新闻获取器实例
news_fetcher = NewsFetcher()


def test_news_fetcher():
    """测试新闻获取功能"""
    logger.info("开始测试新闻获取功能...")

    # 先测试原始数据获取
    raw_data = news_fetcher.fetch_latest_news()
    if raw_data:
        logger.info(f"原始数据类型: {type(raw_data)}")
        logger.info(f"原始数据内容: {str(raw_data)[:500]}...")

    news_list = news_fetcher.get_processed_news()

    if news_list:
        logger.info(f"✅ 成功获取 {len(news_list)} 条新闻")
        for i, news in enumerate(news_list[:3]):  # 只显示前3条
            logger.info(f"新闻 {i+1}: {news['title'][:50]}...")
        return True
    else:
        logger.error("❌ 新闻获取测试失败!")
        return False


if __name__ == "__main__":
    # 测试新闻获取功能
    test_news_fetcher()
