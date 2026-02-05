#!/usr/bin/env python3
"""
定时任务脚本 - 每日研报生成
用于cron或其他定时调度器调用
使用方式：
  python cron_job.py --run-once     # 立即运行一次
  python cron_job.py --run-once --force  # 强制运行（无视交易日）
  python cron_job.py                # 持续运行，按cron表达式定时执行
"""

import os
import sys
import logging
from datetime import datetime

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
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))


def is_trading_day(date: datetime = None) -> bool:
    """
    判断是否为交易日
    周末返回False
    """
    if date is None:
        date = datetime.now()
    
    # 周六、周日
    if date.weekday() >= 5:
        return False
    
    # 尝试使用akshare获取交易日历
    try:
        import akshare as ak
        tool_trade_date_hist_sina = ak.tool_trade_date_hist_sina()
        date_str = date.strftime('%Y-%m-%d')
        return date_str in tool_trade_date_hist_sina['trade_date'].values
    except Exception:
        # 如果无法获取，默认周一到周五为交易日
        return date.weekday() < 5


def run_daily_report(force: bool = False):
    """
    运行每日研报生成任务
    
    Args:
        force: 是否强制运行（无视交易日检查）
    """
    logger.info("="*60)
    logger.info("开始执行每日研报生成任务")
    logger.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"强制模式: {force}")
    
    try:
        # 检查是否为交易日
        if not force and not is_trading_day():
            logger.info("今天不是交易日，跳过研报生成")
            return False
        
        # 导入并运行研报生成器
        from src.report_generator import ReportGenerator
        
        logger.info("初始化研报生成器...")
        generator = ReportGenerator()
        
        logger.info("获取市场数据...")
        data = generator.fetch_all_data()
        
        logger.info("生成研报（含AI分析）...")
        report = generator.generate_report(data)
        
        logger.info("保存研报...")
        filepath = generator.save_report(report)
        
        logger.info(f"✅ 研报生成成功: {filepath}")
        
        # 可以在这里添加通知功能
        # send_notification(f"研报已生成: {filepath}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 研报生成失败: {e}", exc_info=True)
        return False


def run_with_schedule():
    """
    持续运行，按定时计划执行
    默认每个工作日12:00运行
    """
    try:
        from croniter import croniter
        
        cron_string = "0 12 * * 1-5"  # 工作日12:00
        logger.info(f"启动定时任务，计划: {cron_string}")
        logger.info("按Ctrl+C停止")
        
        iter = croniter(cron_string, datetime.now())
        
        while True:
            next_run = iter.get_next(datetime)
            wait_seconds = (next_run - datetime.now()).total_seconds()
            
            logger.info(f"下次运行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"等待 {wait_seconds/60:.1f} 分钟...")
            
            import time
            time.sleep(wait_seconds)
            
            run_daily_report()
            
    except ImportError:
        logger.error("croniter库未安装，无法使用定时功能。请运行: pip install croniter")
        return False
    except KeyboardInterrupt:
        logger.info("定时任务已停止")
        return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='每日研报定时任务 - 自动获取市场数据并生成AI分析报告',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python cron_job.py --run-once          # 立即运行一次（自动判断交易日）
  python cron_job.py --run-once --force  # 强制立即运行
  python cron_job.py                     # 持续运行，工作日12:00自动执行
        """
    )
    
    parser.add_argument(
        '--run-once', 
        action='store_true', 
        help='立即运行一次研报生成'
    )
    parser.add_argument(
        '--force', 
        action='store_true', 
        help='强制运行，无视交易日检查'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='测试模式：检查配置但不实际生成'
    )
    
    args = parser.parse_args()
    
    if args.test:
        # 测试模式：检查配置
        print("="*60)
        print("测试模式 - 检查配置")
        print("="*60)
        
        # 检查Python路径
        print(f"Python: {sys.executable}")
        print(f"工作目录: {os.getcwd()}")
        
        # 检查必要的库
        try:
            import akshare
            print(f"✅ akshare: {akshare.__version__}")
        except ImportError:
            print("❌ akshare: 未安装")
        
        try:
            import openai
            print(f"✅ openai: {openai.__version__}")
        except ImportError:
            print("⚠️  openai: 未安装（将使用模板生成报告）")
        
        try:
            import yaml
            print("✅ pyyaml: 已安装")
        except ImportError:
            print("❌ pyyaml: 未安装")
        
        # 检查API密钥
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            print(f"✅ OPENAI_API_KEY: 已设置 ({api_key[:10]}...)")
        else:
            print("⚠️  OPENAI_API_KEY: 未设置（将使用模板生成报告）")
        
        # 检查配置文件
        if os.path.exists('config.yaml'):
            print("✅ config.yaml: 存在")
        else:
            print("⚠️  config.yaml: 不存在")
        
        print("="*60)
        
    elif args.run_once:
        # 立即运行一次
        success = run_daily_report(force=args.force)
        sys.exit(0 if success else 1)
        
    else:
        # 持续定时运行
        run_with_schedule()
