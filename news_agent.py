"""
新闻代理核心 - 使用LangGraph
"""
from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from loguru import logger
import json
from datetime import datetime

# 导入自定义模块
from news_fetcher import news_fetcher
from ai_summarizer import ai_summarizer
from database import db_manager


class NewsAgentState(TypedDict):
    """新闻代理状态"""
    messages: Annotated[list, add_messages]
    raw_news: List[Dict[str, str]]
    important_news: List[Dict[str, Any]]
    final_summary: str
    saved_count: int
    error: str


class NewsAgent:
    """新闻代理系统"""
    
    def __init__(self):
        self.graph = self._create_graph()
    
    def _create_graph(self) -> StateGraph:
        """创建LangGraph工作流"""
        
        # 定义节点函数
        def fetch_news_node(state: NewsAgentState) -> NewsAgentState:
            """获取新闻节点"""
            logger.info("🔄 开始获取新闻...")
            
            try:
                raw_news = news_fetcher.get_processed_news()
                if raw_news:
                    logger.info(f"✅ 成功获取 {len(raw_news)} 条新闻")
                    state["raw_news"] = raw_news
                    state["messages"].append({"role": "system", "content": f"成功获取 {len(raw_news)} 条新闻"})
                else:
                    logger.warning("⚠️ 未获取到新闻数据")
                    state["error"] = "未获取到新闻数据"
                    state["messages"].append({"role": "system", "content": "未获取到新闻数据"})
                    
            except Exception as e:
                logger.error(f"❌ 获取新闻失败: {e}")
                state["error"] = f"获取新闻失败: {e}"
                state["messages"].append({"role": "system", "content": f"获取新闻失败: {e}"})
            
            return state
        
        def analyze_news_node(state: NewsAgentState) -> NewsAgentState:
            """分析新闻重要性节点"""
            logger.info("🤖 开始AI分析新闻重要性...")
            
            try:
                if not state.get("raw_news"):
                    state["error"] = "没有新闻数据可供分析"
                    return state
                
                important_news = ai_summarizer.filter_important_news(state["raw_news"])
                state["important_news"] = important_news
                
                if important_news:
                    logger.info(f"✅ 发现 {len(important_news)} 条重要新闻")
                    state["messages"].append({"role": "system", "content": f"AI分析完成，发现 {len(important_news)} 条重要新闻"})
                else:
                    logger.info("ℹ️ 未发现重要新闻")
                    state["messages"].append({"role": "system", "content": "AI分析完成，未发现重要新闻"})
                    
            except Exception as e:
                logger.error(f"❌ AI分析失败: {e}")
                state["error"] = f"AI分析失败: {e}"
                state["messages"].append({"role": "system", "content": f"AI分析失败: {e}"})
            
            return state
        
        def create_summary_node(state: NewsAgentState) -> NewsAgentState:
            """创建总结节点"""
            logger.info("📝 开始创建新闻总结...")
            
            try:
                important_news = state.get("important_news", [])
                final_summary = ai_summarizer.create_final_summary(important_news)
                state["final_summary"] = final_summary
                
                logger.info("✅ 新闻总结创建完成")
                state["messages"].append({"role": "system", "content": "新闻总结创建完成"})
                
            except Exception as e:
                logger.error(f"❌ 创建总结失败: {e}")
                state["error"] = f"创建总结失败: {e}"
                state["final_summary"] = "总结创建失败"
                state["messages"].append({"role": "system", "content": f"创建总结失败: {e}"})
            
            return state
        
        def save_to_database_node(state: NewsAgentState) -> NewsAgentState:
            """保存到数据库节点"""
            logger.info("💾 开始保存重要新闻到数据库...")
            
            saved_count = 0
            try:
                important_news = state.get("important_news", [])
                final_summary = state.get("final_summary", "")
                
                # 保存重要新闻
                for news in important_news:
                    title = news.get("original_title", "")
                    summary = news.get("summary", "")
                    content = news.get("original_content", "")
                    importance = news.get("importance", "低")

                    # 检查是否已存在
                    if not db_manager.check_news_exists(title):
                        if db_manager.insert_news(title, summary, content, importance):
                            saved_count += 1
                    else:
                        logger.info(f"新闻已存在，跳过: {title[:50]}...")
                
                # 如果有总结，也保存总结
                if final_summary and final_summary != "今日暂无重要新闻。":
                    summary_title = f"每日新闻总结 - {datetime.now().strftime('%Y-%m-%d')}"
                    if not db_manager.check_news_exists(summary_title):
                        if db_manager.insert_news(summary_title, "AI生成的每日新闻总结", final_summary, "高"):
                            saved_count += 1
                
                state["saved_count"] = saved_count
                logger.info(f"✅ 成功保存 {saved_count} 条记录到数据库")
                state["messages"].append({"role": "system", "content": f"成功保存 {saved_count} 条记录到数据库"})
                
            except Exception as e:
                logger.error(f"❌ 保存到数据库失败: {e}")
                state["error"] = f"保存到数据库失败: {e}"
                state["saved_count"] = saved_count
                state["messages"].append({"role": "system", "content": f"保存到数据库失败: {e}"})
            
            return state
        
        def should_continue(state: NewsAgentState) -> str:
            """决定是否继续执行"""
            if state.get("error"):
                return "end"
            if not state.get("raw_news"):
                return "end"
            return "continue"
        
        # 创建状态图
        workflow = StateGraph(NewsAgentState)
        
        # 添加节点
        workflow.add_node("fetch_news", fetch_news_node)
        workflow.add_node("analyze_news", analyze_news_node)
        workflow.add_node("create_summary", create_summary_node)
        workflow.add_node("save_to_database", save_to_database_node)
        
        # 设置入口点
        workflow.set_entry_point("fetch_news")
        
        # 添加条件边
        workflow.add_conditional_edges(
            "fetch_news",
            should_continue,
            {
                "continue": "analyze_news",
                "end": END
            }
        )
        
        # 添加边
        workflow.add_edge("analyze_news", "create_summary")
        workflow.add_edge("create_summary", "save_to_database")
        workflow.add_edge("save_to_database", END)
        
        return workflow.compile()
    
    def run(self) -> Dict[str, Any]:
        """运行新闻代理"""
        logger.info("🚀 启动新闻代理系统...")
        
        # 初始状态
        initial_state = NewsAgentState(
            messages=[{"role": "system", "content": "新闻代理系统启动"}],
            raw_news=[],
            important_news=[],
            final_summary="",
            saved_count=0,
            error=""
        )
        
        try:
            # 运行工作流
            final_state = self.graph.invoke(initial_state)
            
            # 生成运行报告
            report = self._generate_report(final_state)
            logger.info("✅ 新闻代理系统运行完成")
            
            return report
            
        except Exception as e:
            logger.error(f"❌ 新闻代理系统运行失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _generate_report(self, final_state: NewsAgentState) -> Dict[str, Any]:
        """生成运行报告"""
        return {
            "success": not bool(final_state.get("error")),
            "timestamp": datetime.now().isoformat(),
            "raw_news_count": len(final_state.get("raw_news", [])),
            "important_news_count": len(final_state.get("important_news", [])),
            "saved_count": final_state.get("saved_count", 0),
            "final_summary": final_state.get("final_summary", ""),
            "error": final_state.get("error", ""),
            "messages": final_state.get("messages", [])
        }


# 全局新闻代理实例
news_agent = NewsAgent()


def test_news_agent():
    """测试新闻代理系统"""
    logger.info("开始测试新闻代理系统...")
    
    try:
        report = news_agent.run()
        
        if report["success"]:
            logger.info("✅ 新闻代理系统测试成功!")
            logger.info(f"处理了 {report['raw_news_count']} 条原始新闻")
            logger.info(f"发现 {report['important_news_count']} 条重要新闻")
            logger.info(f"保存了 {report['saved_count']} 条记录")
            if report['final_summary']:
                logger.info(f"生成总结: {report['final_summary'][:100]}...")
        else:
            logger.error(f"❌ 新闻代理系统测试失败: {report['error']}")
        
        return report["success"]
        
    except Exception as e:
        logger.error(f"❌ 测试新闻代理系统失败: {e}")
        return False


if __name__ == "__main__":
    # 测试新闻代理系统
    test_news_agent()
