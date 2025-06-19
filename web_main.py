#!/usr/bin/env python3
"""
Web版本主程序 - 用于Render部署
保持原有逻辑，只添加最小的Web接口
"""
import os
import threading
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from datetime import datetime
from loguru import logger

# 导入原有模块
from main import setup_logging, test_all_components
from scheduler import news_scheduler

# 全局变量
scheduler_thread = None
scheduler_running = False

def start_background_scheduler():
    """启动后台调度器"""
    global scheduler_thread, scheduler_running
    
    if not scheduler_running:
        def run_scheduler():
            global scheduler_running
            scheduler_running = True
            try:
                logger.info("启动后台新闻调度器...")
                news_scheduler.run_forever(run_immediately=True)
            except Exception as e:
                logger.error(f"调度器错误: {e}")
            finally:
                scheduler_running = False
        
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        logger.info("后台调度器已启动")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    setup_logging()
    logger.info("启动Web服务...")
    start_background_scheduler()
    yield
    # 关闭时执行
    logger.info("Web服务关闭")

# 创建FastAPI应用
app = FastAPI(
    title="News Agent System",
    description="基于LangChain + LangGraph的智能新闻分析系统",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    """首页"""
    return {
        "service": "News Agent System",
        "status": "running",
        "scheduler_running": scheduler_running,
        "timestamp": datetime.now().isoformat(),
        "description": "基于LangChain + LangGraph的智能新闻分析系统"
    }

@app.get("/health")
async def health():
    """健康检查 - UptimeKuma用"""
    return {
        "status": "healthy",
        "scheduler_running": scheduler_running,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/test")
async def test():
    """测试所有组件"""
    try:
        logger.info("开始组件测试...")
        result = test_all_components()
        return {
            "test_result": "passed" if result else "failed",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return {
            "test_result": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/run")
async def run_once():
    """手动执行一次新闻处理"""
    try:
        logger.info("手动执行新闻处理...")
        news_scheduler.run_once()
        return {
            "status": "completed",
            "message": "新闻处理完成",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/status")
async def status():
    """状态检查"""
    return {
        "scheduler_running": scheduler_running,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
