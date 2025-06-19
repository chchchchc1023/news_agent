#!/usr/bin/env python3
"""
新闻代理系统主程序
"""
import argparse
import sys
from datetime import datetime
from loguru import logger

# 导入所有模块
from config import DB_CONFIG, NEWS_API_URL, SCHEDULE_HOURS, LOG_LEVEL, LOG_FILE
from database import test_database_connection, db_manager
from news_fetcher import test_news_fetcher
from ai_summarizer import test_ai_summarizer
from news_agent import test_news_agent
from scheduler import news_scheduler


def setup_logging():
    """设置日志配置"""
    # 移除默认处理器
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 添加文件输出
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="30 days",
        compression="zip"
    )


def print_banner():
    """打印启动横幅"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                    新闻代理系统 v1.0                          ║
║                News Agent System v1.0                       ║
║                                                              ║
║  🤖 基于 LangChain + LangGraph 的智能新闻分析系统              ║
║  📰 自动获取、分析、总结重要新闻并存储到数据库                   ║
║  ⏰ 支持定时任务，每6小时自动执行                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def show_system_info():
    """显示系统信息"""
    logger.info("📋 系统配置信息:")
    logger.info(f"   - 数据库: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    logger.info(f"   - 新闻API: {NEWS_API_URL}")
    logger.info(f"   - 执行间隔: 每 {SCHEDULE_HOURS} 小时")
    logger.info(f"   - 日志级别: {LOG_LEVEL}")
    logger.info(f"   - 日志文件: {LOG_FILE}")
    logger.info(f"   - 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


def test_all_components():
    """测试所有组件"""
    logger.info("🔧 开始系统组件测试...")
    
    tests = [
        ("数据库连接", test_database_connection),
        ("新闻获取", test_news_fetcher),
        ("AI总结", test_ai_summarizer),
        ("新闻代理", test_news_agent)
    ]
    
    results = {}
    for test_name, test_func in tests:
        logger.info(f"测试 {test_name}...")
        try:
            result = test_func()
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name} 测试通过")
            else:
                logger.error(f"❌ {test_name} 测试失败")
        except Exception as e:
            logger.error(f"❌ {test_name} 测试异常: {e}")
            results[test_name] = False
    
    # 显示测试结果
    logger.info("📊 测试结果汇总:")
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"   - {test_name}: {status}")
    
    all_passed = all(results.values())
    if all_passed:
        logger.info("🎉 所有组件测试通过!")
    else:
        logger.warning("⚠️ 部分组件测试失败，请检查配置")
    
    return all_passed


def run_once():
    """执行一次新闻代理任务"""
    logger.info("🚀 执行单次新闻代理任务...")
    news_scheduler.run_once()


def start_scheduler(run_immediately=False):
    """启动定时调度器"""
    logger.info("⏰ 启动定时调度器...")
    news_scheduler.run_forever(run_immediately=run_immediately)


def start_web_server():
    """启动Web服务器模式（用于Render部署）"""
    import os
    import threading
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import json

    # 启动后台调度器
    def run_scheduler():
        try:
            logger.info("启动后台新闻调度器...")
            news_scheduler.run_forever(run_immediately=True)
        except Exception as e:
            logger.error(f"调度器错误: {e}")

    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()

    # 简单的HTTP处理器
    class SimpleHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == '/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "status": "healthy",
                    "service": "News Agent System",
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
            elif self.path == '/':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {
                    "service": "News Agent System",
                    "status": "running",
                    "description": "基于LangChain + LangGraph的智能新闻分析系统",
                    "timestamp": datetime.now().isoformat()
                }
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_response(404)
                self.end_headers()

        def log_message(self, format, *args):
            # 禁用默认日志，使用我们的logger
            logger.info(f"HTTP {format % args}")

    # 启动HTTP服务器
    port = int(os.environ.get('PORT', 8000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    logger.info(f"🌐 Web服务器启动在端口 {port}")
    logger.info("📡 健康检查端点: /health")
    logger.info("🏠 主页端点: /")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("👋 Web服务器关闭")
        server.shutdown()


def main():
    """主函数"""
    # 设置日志
    setup_logging()
    
    # 打印横幅
    print_banner()
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="新闻代理系统")
    parser.add_argument("--test", action="store_true", help="测试所有组件")
    parser.add_argument("--run-once", action="store_true", help="执行一次任务")
    parser.add_argument("--start", action="store_true", help="启动定时调度器")
    parser.add_argument("--start-now", action="store_true", help="启动定时调度器并立即执行一次")
    parser.add_argument("--info", action="store_true", help="显示系统信息")
    parser.add_argument("--web", action="store_true", help="启动Web服务器模式（用于Render部署）")
    
    args = parser.parse_args()
    
    # 显示系统信息
    show_system_info()
    
    try:
        if args.test:
            # 测试模式
            logger.info("🔧 进入测试模式...")
            success = test_all_components()
            sys.exit(0 if success else 1)
            
        elif args.run_once:
            # 单次执行模式
            logger.info("🏃 进入单次执行模式...")
            run_once()
            
        elif args.start:
            # 启动调度器模式
            logger.info("⏰ 进入调度器模式...")
            start_scheduler(run_immediately=False)
            
        elif args.start_now:
            # 启动调度器并立即执行
            logger.info("🚀 进入调度器模式（立即执行）...")
            start_scheduler(run_immediately=True)
            
        elif args.info:
            # 仅显示信息
            logger.info("ℹ️ 系统信息显示完成")

        elif args.web:
            # Web服务器模式
            logger.info("🌐 启动Web服务器模式...")
            start_web_server()
            
        else:
            # 默认行为：显示帮助
            logger.info("💡 使用说明:")
            logger.info("   python main.py --test        # 测试所有组件")
            logger.info("   python main.py --run-once    # 执行一次任务")
            logger.info("   python main.py --start       # 启动定时调度器")
            logger.info("   python main.py --start-now   # 启动调度器并立即执行")
            logger.info("   python main.py --info        # 显示系统信息")
            logger.info("   python main.py --web         # 启动Web服务器（Render部署用）")
            logger.info("")
            logger.info("🔧 首次使用建议:")
            logger.info("   1. 先运行 --test 测试所有组件")
            logger.info("   2. 再运行 --run-once 执行一次任务")
            logger.info("   3. 最后运行 --start-now 启动定时调度")
            
    except KeyboardInterrupt:
        logger.info("👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ 程序运行异常: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
