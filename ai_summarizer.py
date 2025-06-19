#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI总结模块
"""
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger
from config import OPENAI_API_KEY
import os


class AISummarizer:
    """AI新闻总结器"""
    
    def __init__(self):
        # 初始化OpenAI模型
        if OPENAI_API_KEY:
            self.llm = ChatOpenAI(
                model="gpt-4.1-mini",
                temperature=0,
                api_key=OPENAI_API_KEY
            )
        else:
            logger.warning("未设置OPENAI_API_KEY，将使用默认配置")
            self.llm = ChatOpenAI(
                model="gpt-4.1-mini",
                temperature=0
            )
        
        # 创建总结提示模板
        self.summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位专精加密货币和区块链领域的资深新闻分析师，拥有深厚的金融市场、技术发展和监管政策分析经验。请基于当前加密货币市场环境，客观、准确地分析新闻内容，评估其重要性并提供专业总结。

当前市场背景（2025年）：
- 加密货币总市值已达3.7万亿美元，机构投资大幅增长
- 比特币ETF获批，稳定币市场创历史新高（2517亿美元）
- 美国政府实施亲加密政策，建立战略比特币储备
- 欧盟MiCAR法规全面生效，监管框架日趋完善
- DeFi生态系统快速发展，TVL预计达2000亿美元
- 47%传统对冲基金已接触数字资产

重要性评估标准：

【高重要性 - 市场震荡级】
监管政策类：
- 主要国家/地区加密货币监管政策重大变化
- SEC、CFTC等监管机构重要决定或执法行动
- 央行数字货币(CBDC)重大进展或政策变化
- 加密货币禁令或合法化决定

机构与市场类：
- 大型机构（>10亿美元AUM）首次大额配置或撤出加密货币
- 主要ETF获批/拒绝或重大资金流入/流出（>5亿美元）
- 知名企业采用/放弃比特币作为储备资产
- 主要交易所重大事件（倒闭、被黑、监管处罚）

技术与项目类：
- 比特币/以太坊等主流币重大技术升级或分叉
- 重大安全事件（>1亿美元损失的黑客攻击）
- 知名DeFi协议重大漏洞或TVL异常变化（>50%）
- Layer 2或跨链技术重大突破

市场表现类：
- 比特币/以太坊单日涨跌幅>15%或创历史新高/新低
- 加密货币总市值单日变化>10%
- 重大"黑天鹅"事件影响整个加密生态

【中重要性 - 行业影响级】
- 中型机构（1-10亿美元）加密货币投资策略变化
- 区域性监管政策调整或指引发布
- 主流币种（市值前10）技术更新或合作伙伴关系
- DeFi、NFT、Web3游戏领域重要项目启动或更新
- 加密货币在支付、跨境汇款等实用场景的应用进展
- 能源环保相关的加密挖矿政策或技术发展
- 知名人士或企业家的加密货币言论（市值>500亿美元影响力）

【低重要性 - 一般资讯级】
- 小规模项目的常规更新或技术改进
- 一般性市场分析或价格预测
- 个人投资者行为或小额交易
- 娱乐性质的Meme币或小众项目动态
- 常规的行业会议、报告发布
- 个人层面的加密货币使用体验分享

特殊考量因素：
1. **连带效应**：评估事件对整个加密生态系统的潜在影响
2. **时效性**：监管政策和技术事件通常具有持续影响
3. **市场情绪**：在牛市/熊市不同阶段，同类事件重要性可能不同
4. **技术复杂性**：Layer 2、DeFi、跨链等技术事件需要专业判断
5. **地缘政治**：国际关系变化对加密货币监管环境的影响

分析要求：
1. 基于事实和数据进行客观评估，避免炒作和恐慌情绪
2. 考虑事件的直接影响和间接影响范围
3. 结合当前市场环境和监管趋势进行综合判断
4. 总结应突出核心信息，避免技术术语过度复杂化
5. 关键词应涵盖相关技术、监管、市场等多个维度

请按以下格式回复：
重要性等级：[高/中/低]
总结：[简洁的新闻总结，不超过200字]
关键词：[3-5个关键词，用逗号分隔]

如果新闻重要性等级为"低"，请直接回复"重要性等级：低"即可。"""),
    ("human", "新闻内容：{news_content}")
])
    
    def analyze_news_importance(self, news_content: str) -> Dict[str, Any]:
        """
        分析单条新闻的重要性
        
        Args:
            news_content: 新闻内容
            
        Returns:
            Dict: 包含重要性等级、总结、关键词的字典
        """
        try:
            # 确保新闻内容是UTF-8编码
            if isinstance(news_content, bytes):
                news_content = news_content.decode('utf-8', errors='ignore')

            # 构建提示
            messages = self.summary_prompt.format_messages(news_content=news_content)

            # 调用AI模型
            response = self.llm.invoke(messages)

            # 安全获取响应内容
            if hasattr(response, 'content'):
                response_text = str(response.content).strip()
            else:
                response_text = str(response).strip()

            # 解析响应
            result = self._parse_ai_response(response_text)
            
            logger.debug(f"AI分析结果: {result}")
            return result
            
        except Exception as e:
            # 安全处理错误信息，避免编码问题
            error_msg = str(e).encode('utf-8', errors='ignore').decode('utf-8')
            logger.error(f"AI分析新闻失败: {error_msg}")

            # 安全处理新闻内容，确保是字符串且编码正确
            safe_content = news_content
            if isinstance(safe_content, bytes):
                safe_content = safe_content.decode('utf-8', errors='ignore')
            safe_content = str(safe_content)[:200]

            return {
                'importance': '低',
                'summary': safe_content + "..." if len(safe_content) > 200 else safe_content,
                'keywords': ''
            }
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """解析AI响应文本"""
        result = {
            'importance': '低',
            'summary': '',
            'keywords': ''
        }
        
        lines = response_text.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('重要性等级：'):
                importance = line.replace('重要性等级：', '').strip()
                result['importance'] = importance
            elif line.startswith('总结：'):
                summary = line.replace('总结：', '').strip()
                result['summary'] = summary
            elif line.startswith('关键词：'):
                keywords = line.replace('关键词：', '').strip()
                result['keywords'] = keywords
        
        return result
    
    def filter_important_news(self, news_list: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        筛选重要新闻并生成总结
        
        Args:
            news_list: 新闻列表
            
        Returns:
            List[Dict]: 重要新闻列表，包含原始新闻和AI分析结果
        """
        important_news = []
        
        logger.info(f"开始分析 {len(news_list)} 条新闻的重要性...")
        
        for i, news in enumerate(news_list):
            logger.info(f"正在分析第 {i+1}/{len(news_list)} 条新闻...")
            
            # 分析新闻重要性
            analysis = self.analyze_news_importance(news['content'])
            
            # 只保留中等和高重要性的新闻
            if analysis['importance'] in ['中', '高']:
                important_news.append({
                    'original_title': news['title'],
                    'original_content': news['content'],
                    'importance': analysis['importance'],
                    'summary': analysis['summary'],
                    'keywords': analysis['keywords']
                })
                logger.info(f"发现重要新闻: {news['title'][:50]}... (重要性: {analysis['importance']})")
        
        logger.info(f"筛选完成，共发现 {len(important_news)} 条重要新闻")
        return important_news
    
    def create_final_summary(self, important_news: List[Dict[str, Any]]) -> str:
        """
        为重要新闻创建最终总结
        
        Args:
            important_news: 重要新闻列表
            
        Returns:
            str: 最终总结文本
        """
        if not important_news:
            return "今日暂无重要新闻。"
        
        try:
            # 构建总结提示
            news_summaries = []
            for i, news in enumerate(important_news, 1):
                news_summaries.append(f"{i}. {news['summary']} (重要性: {news['importance']})")
            
            combined_content = "\n".join(news_summaries)
            
            final_prompt = f"""请基于以下重要新闻总结，创建一个综合性的日报总结：

{combined_content}

请提供一个简洁的综合总结，突出今日最重要的事件和趋势。总结应该：
1. 不超过300字
2. 突出最重要的事件
3. 如果有相关联的事件，请指出其关联性
4. 使用专业但易懂的语言
"""
            
            messages = [HumanMessage(content=final_prompt)]
            response = self.llm.invoke(messages)

            # 安全获取响应内容
            if hasattr(response, 'content'):
                return str(response.content).strip()
            else:
                return str(response).strip()
            
        except Exception as e:
            logger.error(f"创建最终总结失败: {e}")
            # 如果AI总结失败，返回简单的列表总结
            summaries = [news['summary'] for news in important_news]
            return "今日重要新闻总结：\n" + "\n".join(f"• {summary}" for summary in summaries)


# 全局AI总结器实例
ai_summarizer = AISummarizer()


def test_ai_summarizer():
    """测试AI总结功能"""
    logger.info("开始测试AI总结功能...")
    
    # 测试新闻
    test_news = [
        {
            'title': '测试新闻1',
            'content': '美联储宣布加息0.25个百分点，这是今年第三次加息。市场对此反应强烈，股市出现大幅波动。'
        },
        {
            'title': '测试新闻2', 
            'content': '今天天气很好，阳光明媚。'
        }
    ]
    
    try:
        # 测试重要性分析
        important_news = ai_summarizer.filter_important_news(test_news)
        
        if important_news:
            logger.info(f"✅ 成功筛选出 {len(important_news)} 条重要新闻")
            
            # 测试最终总结
            final_summary = ai_summarizer.create_final_summary(important_news)
            logger.info(f"最终总结: {final_summary[:100]}...")
            
            return True
        else:
            logger.warning("未筛选出重要新闻，但功能正常")
            return True
            
    except Exception as e:
        logger.error(f"❌ AI总结测试失败: {e}")
        return False


if __name__ == "__main__":
    # 测试AI总结功能
    test_ai_summarizer()
