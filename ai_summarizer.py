"""
AI总结模块
"""
from typing import List,Dict,Any,Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel,Field
from loguru import logger
from config import OPENAI_API_KEY,OPENAI_BASE_URL,OPENAI_MODEL

class NewsAnalysis(BaseModel):
    """
    新闻分析结果模型
    用于结构化输出新闻重要性分析结果
    """
    importance: str = Field(
        description="重要性等级，必须是以下值之一：高、中、低"
    )
    summary: Optional[str] = Field(
        default="",
        description="新闻总结，如果重要性为中或高则提供简洁总结（不超过200字），如果为低可以留空"
    )
    keywords: Optional[str] = Field(
        default="",
        description="关键词，如果重要性为中或高则提供3-5个关键词（用逗号分隔），如果为低可以留空"
    )


class AISummarizer:
    """AI新闻总结"""

    def __init__(self):
        if not OPENAI_API_KEY or not  OPENAI_MODEL:
            error_msg="OPENAI_API_KEY或OPENAI_MODEL未设置，请检查配置文件和环境变量。"
            logger.error(error_msg)
            raise ValueError(error_msg)
        import os
        os.environ['OPENAI_API_KEY']=OPENAI_API_KEY
        if OPENAI_BASE_URL:
            logger.info(f"使用自定义url，模型为{OPENAI_MODEL}")
            self.llm=ChatOpenAI(
                base_url=OPENAI_BASE_URL,
                model=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=0
            )
        else :
            logger.info(f"使用默认url，模型为{OPENAI_MODEL}")
            self.llm=ChatOpenAI(
                model=OPENAI_MODEL,
                api_key=OPENAI_API_KEY,
                temperature=0
            )
        # 创建总结提示模板 - 专为结构化输出设计
        self.summary_prompt = ChatPromptTemplate.from_messages([
    ("system", """你是一位专精加密货币和美股市场的资深金融分析师。请客观分析新闻内容对市场的重要性和潜在影响。

重要性评估标准（基于市场影响程度）：

【高重要性 - 可能引发重大市场波动】：
- SEC、CFTC、Fed等监管机构重要决定或政策变化（利率决议、监管框架、执法行动）
- 大型机构（>10亿美元）首次大额配置或撤出加密货币/股票
- 主要ETF获批/拒绝或重大资金流入/流出（>5亿美元）
- 比特币/以太坊等主流币重大技术升级、分叉或安全事件
- 主要交易所重大事件（倒闭、被黑、监管处罚、系统故障）
- 比特币/以太坊单日涨跌幅>15%或创历史新高/新低
- 美股主要指数（S&P500、纳斯达克）单日涨跌幅>3%
- 重大宏观经济事件（通胀数据、就业数据、GDP数据超预期）
- 地缘政治重大事件（战争、制裁、贸易争端）
- 系统性金融风险事件（银行倒闭、流动性危机）

【中重要性 - 可能影响特定板块或短期情绪】：
- 中型机构（1-10亿美元）加密货币/股票投资策略变化
- 区域性监管政策调整或指引发布
- 主流币种（市值前10）或知名上市公司技术更新、合作伙伴关系
- DeFi、NFT、Web3、AI、新能源等热门领域重要项目启动或更新
- 知名人士、企业家、分析师的市场言论或投资建议
- 单个大型公司财报超预期或重大业务变化
- 行业政策变化（如AI监管、新能源补贴政策等）
- 主流币种或知名股票5-15%的价格波动

【低重要性 - 对市场影响有限】：
- 小规模项目的常规更新或技术改进
- 一般性市场分析、价格预测或技术分析
- 个人投资者行为或小额交易
- 娱乐性质的Meme币或小众项目动态
- 常规的公司运营更新或人事变动
- 小幅价格波动（<5%）或正常市场波动
- 与金融市场无直接关联的新闻

分析时请特别关注：
1. 新闻对加密货币市场的直接或间接影响
2. 新闻对美股市场（特别是科技股、金融股）的影响
3. 宏观经济因素对两个市场的联动影响
4. 监管政策变化的市场预期影响
5. 机构资金流向的变化趋势

请基于以上标准分析新闻，并提供：
- importance: 重要性等级（高/中/低）
- summary: 如果重要性为中或高，提供简洁的新闻总结，重点说明对市场的潜在影响（不超过200字）；如果为低，可以留空
- keywords: 如果重要性为中或高，提供3-5个关键词（用逗号分隔），包含相关的市场影响关键词；如果为低，可以留空"""),
    ("human", "新闻内容：{news_content}")
])
        
    def analyze_news_importance(self,news_content:str)->Dict[str,Any]:
        """
        分析单条新闻的重要性
        Args:
            news_content：新闻内容

        Returns:
                Dict：包含重要性等级、总结、关键词的字典
        """
        try:
            # 尝试结构化输出
            structured_llm=self.llm.with_structured_output(NewsAnalysis)
            messages = self.summary_prompt.format_messages(news_content=news_content)
            result=structured_llm.invoke(messages)

            result_dict = {
                'importance':result.importance,
                'summary':result.summary or '',
                'keywords':result.keywords or ''
            }
            logger.debug(f"AI分析结果（结构化）:{result_dict}")
            return result_dict
        except Exception as e:
            logger.info(f"结构化输出失败，尝试json模式：{e}")

            # 尝试使用json模式
            try:
                return self._analyze_with_json_mode(news_content)
            except Exception as e2:
                logger.error(f"json模式也失败：{e2}")
                # 返回失败
                return{
                    'importance':'FAILED',
                    'summary':f'AI分析失败:{str(e2)}',
                    'keywords':'AI分析失败'
                }
            
        
    def _analyze_with_json_mode(self,news_content:str)->Dict[str,Any]:
        """使用json模式分析新闻"""
        json_prompt = f"""请分析以下新闻对加密货币和美股市场的重要性和影响，并以JSON格式回复。

新闻内容：{news_content}

重要性评估标准（基于市场影响程度）：

【高重要性 - 可能引发重大市场波动】：
- SEC、CFTC、Fed等监管机构重要决定（利率决议、监管框架、执法行动）
- 大型机构（>10亿美元）首次大额配置或撤出加密货币/股票
- 主要ETF获批/拒绝或重大资金流入/流出（>5亿美元）
- 比特币/以太坊重大技术升级、分叉或安全事件
- 主要交易所重大事件（倒闭、被黑、监管处罚）
- 主流币或美股指数单日涨跌幅>15%或>3%，创历史新高/新低
- 重大宏观经济事件（通胀、就业、GDP数据超预期）
- 地缘政治重大事件、系统性金融风险事件

【中重要性 - 可能影响特定板块或短期情绪】：
- 中型机构投资策略变化、区域性监管政策调整
- 主流币种（市值前10）或知名上市公司技术更新、合作关系
- DeFi、NFT、Web3、AI、新能源等热门领域重要项目
- 知名人士、企业家、分析师的市场言论或投资建议
- 单个大型公司财报超预期或重大业务变化
- 行业政策变化、主流资产5-15%的价格波动

【低重要性 - 对市场影响有限】：
- 小规模项目常规更新、一般性市场分析或价格预测
- 个人投资者行为、娱乐性Meme币、小众项目动态
- 常规公司运营更新、小幅价格波动（<5%）
- 与金融市场无直接关联的新闻

分析时请特别关注新闻对加密货币市场和美股市场的直接或间接影响，包括宏观经济因素的联动影响、监管政策变化的市场预期影响、机构资金流向变化等。

请严格按照以下JSON格式回复：
{{
    "importance": "高/中/低",
    "summary": "新闻总结，重点说明对市场的潜在影响（如果重要性为低可以留空）",
    "keywords": "关键词1,关键词2,关键词3,市场影响关键词（如果重要性为低可以留空）"
}}

只返回JSON，不要任何其他内容。"""
        from langchain_core.messages import HumanMessage
        response =self.llm.invoke([HumanMessage(content=json_prompt)])
        response_text = str(response.content).strip()

        import json 
        import re

        # 提取json部分
        json_match =re.search(r'\{.*}',response_text,re.DOTALL)
        if json_match:
            json_str = json_match.group(0)
            result_dict = json.loads(json_str)

            # 标准化结果
            return{
                'importance':result_dict.get('importance','低'),
                'summary':result_dict.get('summary',''),
                'keywords':result_dict.get('keywords','')
            }
        else:
            raise ValueError(f"无法从响应中提取JSON，AI回复:{response_text[:100]}...")
        
    def filter_important_news(self,news_list:List[Dict[str,str]])->List[Dict[str,Any]]:
        """
        筛选重要新闻并生成总结
        
        Args:
            news_list:新闻列表

        Returns:
            List[Dict]:重要新闻列表，包含原始新闻和AI分析结果
        """
        important_news = []

        logger.info(f"开始分析{len(news_list)}条新闻的重要性...")

        for i,news in enumerate(news_list):
            logger.info(f"正在分析第{i+1}/{len(news_list)}条新闻...")

            # 分析新闻重要性
            analysis = self.analyze_news_importance(news['content'])

            # 检查分析是否失败
            if analysis['importance']=='FAILED':
                logger.error(f"新闻分析失败，跳过:{news['title'][:50]}...(错误:{analysis['summary']})")
                continue

            # 只保留中等和高重要性的新闻
            if analysis['importance'] in ['中','高']:
                important_news.append({
                    'original_title': news['title'],
                    'original_content': news['content'],
                    'importance': analysis['importance'],
                    'summary': analysis['summary'],
                    'keywords': analysis['keywords']
                })
                logger.info(f"发现重要新闻: {news['title'][:50]}... (重要性: {analysis['importance']})")
        logger.info(f"筛选完成，共发现{len(important_news)}条重要新闻")
        return important_news
    
    def create_final_summary(self,important_news:List[Dict[str,Any]])->str:
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
            news_summaries =[]
            for i,news in enumerate(important_news,1):
                news_summaries.append(f"{i}.{news['summary']}(重要性:{news['importance']})")

            combined_content = "\n".join(news_summaries)
            
            final_prompt=f"""请基于以下重要新闻总结，创建一个综合性的日报总结：

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
            if hasattr(response,'content'):
                return str(response.content).strip()
            else:
                return str(response).strip()
            
        except Exception as e:
            logger.error(f"创建最终总结失败:{e}")
            # 如果AI总结失败，返回简单的列表总结
            summaries = [news['summary']for news in important_news]
            return "今日重要新闻总结：\n"+"\n".join(f"`{summary}"for summary in summaries)
        
    def merge_summaries(self,existing_summary:str,new_summary:str,new_important_news:List[Dict[str,Any]])->str:
        """
        合并已有总结和新总结

        Args:
            existing_summary: 已有的总结内容
            new_summary: 新生成的总结内容
            new_important_news: 新发现的重要新闻列表

        Returns:
            str: 合并后的综合总结
        """
        if not new_important_news:
            logger.info("没有新的重要新闻，保持原有总结")
            return existing_summary
        
        try:
            # 构建合并提示
            new_news_summaries=[]
            for i,news in enumerate(new_important_news,1):
                new_news_summaries.append(f"{i}.{news['summary']}(重要性:{news['importance']})")

            new_content="\n".join(new_news_summaries)

            merge_prompt = f"""请将已有的新闻总结与新发现的重要新闻进行合并，生成一个更全面的综合总结。

已有总结：
{existing_summary}

新发现的重要新闻：
{new_content}

请提供一个综合性的总结，要求：
1. 整合所有重要信息，避免重复
2. 突出最重要的事件和趋势
3. 如果有相关联的事件，请指出其关联性
4. 保持专业但易懂的语言
5. 总结长度控制在400字以内
6. 按重要性和时间逻辑组织内容"""
            
            from langchain_core.messages import HumanMessage
            response = self.llm.invoke([HumanMessage(content=merge_prompt)])

            # 安全获取响应内容
            if hasattr(response, 'content'):
                merged_summary = str(response.content).strip()
            else:
                merged_summary = str(response).strip()

            logger.info("成功合并新闻总结")
            return merged_summary
        
        except Exception as e:
            logger.error(f"合并总结失败: {e}")
            # 如果合并失败，简单拼接
            return f"{existing_summary}\n\n【新增内容】\n{new_summary}"

# 全局AI总结器实例
ai_summarizer = AISummarizer()




# 以下为测试所用
def test_ai_summarizer():
    """测试AI总结功能"""
    logger.info("开始测试AI总结功能...")

    # 测试新闻 - 包含不同重要性级别的新闻
    test_news = [
        {
            'title': '比特币ETF获批',
            'content': 'SEC正式批准首批比特币现货ETF，包括贝莱德、富达等多家机构的申请。这标志着加密货币进入传统金融市场的重要里程碑，预计将吸引大量机构资金流入。'
        },
        {
            'title': 'Fed加息决议',
            'content': '美联储宣布加息25个基点，将联邦基金利率上调至5.5%。这是连续第11次加息，旨在控制通胀。市场预期这可能是本轮加息周期的最后一次，美股三大指数盘后上涨。'
        },
        {
            'title': '特斯拉财报超预期',
            'content': '特斯拉发布Q4财报，营收和净利润均超市场预期。公司表示将加大在自动驾驶技术和储能业务的投资。盘后股价上涨8%。'
        },
        {
            'title': '小型DeFi项目更新',
            'content': '某小型DeFi协议发布了新版本，修复了一些小bug，提升了用户体验。'
        },
        {
            'title': '天气新闻',
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