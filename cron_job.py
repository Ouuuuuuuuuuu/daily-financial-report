#!/usr/bin/env python3
"""
定时任务脚本
用于cron或其他定时调度器调用
"""

import os
import sys
import logging
from datetime import datetime
from dateutil import tz
from croniter import croniter

# 设置日志
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/cron_job.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.report_generator import ReportGenerator


def is_trading_day(date: datetime = None) -> bool:
    """
    判断是否为交易日
    周末和非工作日返回False
    """
    if date is None:
        date = datetime.now()
    
    # 周六、周日
    if date.weekday() >= 5:
        return False
    
    # TODO: 可以增加节假日判断
    # 可以通过akshare获取交易日历
    try:
        import akshare as ak
        # 获取交易日历
        tool_trade_date_hist_sina = ak.tool_trade_date_hist_sina()
        date_str = date.strftime('%Y-%m-%d')
        return date_str in tool_trade_date_hist_sina['trade_date'].values
    except:
        # 如果无法获取，默认周一到周五为交易日
        return date.weekday() < 5


def run_daily_report():
    """运行每日研报生成任务"""
    logger.info("="*50)
    logger.info("开始执行每日研报生成任务")
    logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # 检查是否为交易日
        if not is_trading_day():
            logger.info("今天不是交易日，跳过研报生成")
            return
        
        # 生成研报
        generator = ReportGenerator()
        data = generator.fetch_all_data()
        report = generator.generate_report(data)
        filepath = generator.save_report(report)
        
        logger.info(f"研报生成成功: {filepath}")
        
        # 可以在这里添加通知功能
        # send_notification(f"研报已生成: {filepath}")
        
    except Exception as e:
        logger.error(f"研报生成失败: {e}", exc_info=True)
        raise


def run_with_cron(cron_string: str = "0 12 * * 1-5"):
    """
    使用cron表达式运行任务
    默认每个工作日12:00运行
    """
    iter = croniter(cron_string, datetime.now())
    
    while True:
        next_run = iter.get_next(datetime)
        wait_seconds = (next_run - datetime.now()).total_seconds()
        
        logger.info(f"下次运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"等待 {wait_seconds/60:.1f} 分钟...")
        
        import time
        time.sleep(wait_seconds)
        
        run_daily_report()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='每日研报定时任务')
    parser.add_argument('--run-once', action='store_true', help='立即运行一次')
    parser.add_argument('--cron', type=str, default='0 12 * * 1-5', help='cron表达式')
    parser.add_argument('--force', action='store_true', help='强制运行（无视交易日检查）')
    
    args = parser.parse_args()
    
    if args.run_once:
        if args.force:
            # 强制运行，不检查交易日
            generator = ReportGenerator()
            data = generator.fetch_all_data()
            report = generator.generate_report(data)
            generator.save_report(report)
        else:
            run_daily_report()
    else:
        run_with_cron(args.cron)
