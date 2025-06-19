#!/usr/bin/env python3
"""
Render部署专用Web服务器
最小化修改，保持原有逻辑不变
"""
import os
import threading
import time
from flask import Flask, jsonify, request
from datetime import datetime
from loguru import logger

# 导入原有模块
from main import setup_logging, test_all_components
from scheduler import news_scheduler

app = Flask(__name__)

# 全局变量
scheduler_thread = None
scheduler_running = False
last_activity = datetime.now()

def update_activity():
    """更新最后活动时间"""
    global last_activity
    last_activity = datetime.now()

@app.before_request
def before_request():
    """每次请求前更新活动时间"""
    update_activity()

@app.route('/')
def home():
    """首页 - 提供基本信息"""
    return jsonify({
        "service": "News Agent System",
        "status": "running",
        "scheduler_status": "running" if scheduler_running else "stopped",
        "last_activity": last_activity.isoformat(),
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "test": "/test", 
            "run": "/run-once",
            "status": "/status"
        }
    })

@app.route('/health')
def health():
    """健康检查 - 用于UptimeKuma监控"""
    return jsonify({
        "status": "healthy",
        "scheduler_running": scheduler_running,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/status')
def status():
    """状态检查"""
    return jsonify({
        "scheduler_running": scheduler_running,
        "last_activity": last_activity.isoformat(),
        "uptime": str(datetime.now() - last_activity),
        "timestamp": datetime.now().isoformat()
    })

@app.route('/test')
def test():
    """测试所有组件"""
    try:
        logger.info("开始组件测试...")
        result = test_all_components()
        return jsonify({
            "test_result": "passed" if result else "failed",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"测试失败: {e}")
        return jsonify({
            "test_result": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/run-once')
def run_once():
    """手动执行一次新闻处理"""
    try:
        logger.info("手动执行新闻处理...")
        news_scheduler.run_once()
        return jsonify({
            "status": "completed",
            "message": "News processing completed successfully",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"执行失败: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def keep_alive():
    """保活函数 - 定期自我请求防止休眠"""
    while True:
        try:
            time.sleep(25 * 60)  # 每25分钟执行一次
            # 这里可以添加自我ping逻辑，但由于你使用UptimeKuma，所以不需要
            logger.info("Keep alive check")
        except Exception as e:
            logger.error(f"Keep alive error: {e}")

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
        
        # 启动保活线程
        keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        keep_alive_thread.start()
        
        logger.info("后台调度器和保活线程已启动")

if __name__ == '__main__':
    # 设置日志
    setup_logging()
    logger.info("启动Render Web服务器...")
    
    # 启动后台调度器
    start_background_scheduler()
    
    # 启动Web服务器
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Web服务器启动在端口 {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
