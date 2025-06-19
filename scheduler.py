"""
定时任务调度模块
"""
import schedule
import time
import threading
from datetime import datetime, timedelta
from loguru import logger
from typing import Optional
import signal
import sys

from news_agent import news_agent
from config import SCHEDULE_HOURS


class NewsScheduler:
    """新闻代理调度器"""
    
    def __init__(self):
        self.is_running = False
        self.scheduler_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        # 设置信号处理器，用于优雅关闭
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，准备关闭调度器...")
        self.stop()
        sys.exit(0)
    
    def run_news_agent_job(self):
        """执行新闻代理任务"""
        logger.info("⏰ 定时任务触发，开始执行新闻代理...")
        
        try:
            start_time = datetime.now()
            report = news_agent.run()
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if report["success"]:
                logger.info(f"✅ 定时任务执行成功，耗时 {duration:.2f} 秒")
                logger.info(f"📊 任务报告: 原始新闻 {report['raw_news_count']} 条，"
                          f"重要新闻 {report['important_news_count']} 条，"
                          f"保存记录 {report['saved_count']} 条")
                
                # 记录执行日志
                self._log_execution_result(report, duration)
            else:
                logger.error(f"❌ 定时任务执行失败: {report['error']}")
                
        except Exception as e:
            logger.error(f"❌ 定时任务执行异常: {e}")
    
    def _log_execution_result(self, report: dict, duration: float):
        """记录执行结果到日志"""
        log_entry = {
            "timestamp": report["timestamp"],
            "duration_seconds": duration,
            "raw_news_count": report["raw_news_count"],
            "important_news_count": report["important_news_count"],
            "saved_count": report["saved_count"],
            "success": report["success"]
        }
        
        logger.info(f"📝 执行记录: {log_entry}")
    
    def setup_schedule(self):
        """设置定时任务"""
        # 清除现有任务
        schedule.clear()
        
        # 设置每6小时执行一次
        schedule.every(SCHEDULE_HOURS).hours.do(self.run_news_agent_job)
        
        logger.info(f"⏱️ 定时任务已设置: 每 {SCHEDULE_HOURS} 小时执行一次")
        
        # 计算下次执行时间
        next_run = datetime.now() + timedelta(hours=SCHEDULE_HOURS)
        logger.info(f"📅 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run_once(self):
        """立即执行一次任务"""
        logger.info("🚀 立即执行新闻代理任务...")
        self.run_news_agent_job()
    
    def start(self, run_immediately: bool = False):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        logger.info("🎯 启动新闻代理调度器...")
        
        # 设置定时任务
        self.setup_schedule()
        
        # 如果需要立即执行一次
        if run_immediately:
            logger.info("🏃 立即执行首次任务...")
            self.run_news_agent_job()
        
        # 启动调度器线程
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("✅ 调度器启动成功，正在后台运行...")
    
    def _run_scheduler(self):
        """运行调度器的内部方法"""
        while self.is_running and not self.stop_event.is_set():
            try:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                logger.error(f"调度器运行异常: {e}")
                time.sleep(60)
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            logger.info("调度器未在运行")
            return
        
        logger.info("🛑 正在停止调度器...")
        
        self.is_running = False
        self.stop_event.set()
        
        # 等待线程结束
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        # 清除定时任务
        schedule.clear()
        
        logger.info("✅ 调度器已停止")
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        next_jobs = schedule.jobs
        next_run_time = None
        
        if next_jobs:
            next_job = next_jobs[0]
            next_run_time = next_job.next_run.strftime('%Y-%m-%d %H:%M:%S') if next_job.next_run else None
        
        return {
            "is_running": self.is_running,
            "schedule_hours": SCHEDULE_HOURS,
            "next_run_time": next_run_time,
            "jobs_count": len(next_jobs)
        }
    
    def run_forever(self, run_immediately: bool = False):
        """持续运行调度器（阻塞模式）"""
        self.start(run_immediately)
        
        try:
            logger.info("🔄 调度器进入持续运行模式，按 Ctrl+C 停止...")
            while self.is_running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止...")
        finally:
            self.stop()


# 全局调度器实例
news_scheduler = NewsScheduler()


def main():
    """主函数 - 用于直接运行调度器"""
    logger.info("🎬 新闻代理调度器启动...")
    
    try:
        # 显示状态信息
        logger.info(f"⚙️ 配置信息:")
        logger.info(f"   - 执行间隔: 每 {SCHEDULE_HOURS} 小时")
        logger.info(f"   - 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 询问是否立即执行一次
        logger.info("是否立即执行一次任务？(y/n)")
        # 在实际部署时，可以通过命令行参数控制
        run_immediately = True  # 默认立即执行一次
        
        # 启动调度器
        news_scheduler.run_forever(run_immediately=run_immediately)
        
    except Exception as e:
        logger.error(f"❌ 调度器启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
