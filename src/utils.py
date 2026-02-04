#!/usr/bin/env python3
"""
工具函数模块
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional


def format_number(num: float, decimal: int = 2) -> str:
    """格式化数字"""
    if num is None:
        return "N/A"
    return f"{num:,.{decimal}f}"


def format_percent(num: float) -> str:
    """格式化百分比"""
    if num is None:
        return "N/A"
    return f"{num:+.2f}%"


def get_market_status() -> str:
    """获取市场状态"""
    now = datetime.now()
    hour = now.hour
    minute = now.minute
    weekday = now.weekday()
    
    # 周末休市
    if weekday >= 5:
        return "休市"
    
    # 开盘时间 9:30-11:30, 13:00-15:00
    time_val = hour * 100 + minute
    if 930 <= time_val <= 1130 or 1300 <= time_val <= 1500:
        return "交易中"
    else:
        return "休市"


def get_trading_sessions() -> List[Dict]:
    """获取全球主要市场交易时间"""
    return [
        {
            'name': 'A股',
            'timezone': 'Asia/Shanghai',
            'sessions': ['09:30-11:30', '13:00-15:00']
        },
        {
            'name': '港股',
            'timezone': 'Asia/Hong_Kong',
            'sessions': ['09:30-12:00', '13:00-16:00']
        },
        {
            'name': '美股',
            'timezone': 'America/New_York',
            'sessions': ['09:30-16:00']
        },
        {
            'name': '伦敦',
            'timezone': 'Europe/London',
            'sessions': ['08:00-16:30']
        }
    ]


def calculate_change_pct(current: float, previous: float) -> float:
    """计算涨跌幅"""
    if previous and previous != 0:
        return ((current / previous) - 1) * 100
    return 0


def save_json(data: Dict, filepath: str):
    """保存JSON文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filepath: str) -> Optional[Dict]:
    """加载JSON文件"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_date_range(days: int = 30) -> tuple:
    """获取日期范围"""
    end = datetime.now()
    start = end - timedelta(days=days)
    return start.strftime('%Y%m%d'), end.strftime('%Y%m%d')


def validate_symbol(symbol: str) -> bool:
    """验证股票代码格式"""
    if not symbol:
        return False
    # A股代码: 6位数字
    if symbol.isdigit() and len(symbol) == 6:
        return True
    # 美股代码
    if symbol.isalpha() or (symbol.isalnum() and len(symbol) <= 5):
        return True
    return False


def get_sector_name(sector_code: str) -> str:
    """获取板块名称"""
    sector_map = {
        'ai': '人工智能',
        'semiconductor': '半导体',
        'new_energy': '新能源',
        'finance': '金融',
        'healthcare': '医药',
        'consumer': '消费',
        'dividend': '红利',
        'gold': '黄金'
    }
    return sector_map.get(sector_code, sector_code)


class ColorFormatter:
    """终端颜色格式化"""
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'
    
    @classmethod
    def red(cls, text: str) -> str:
        return f"{cls.RED}{text}{cls.END}"
    
    @classmethod
    def green(cls, text: str) -> str:
        return f"{cls.GREEN}{text}{cls.END}"
    
    @classmethod
    def yellow(cls, text: str) -> str:
        return f"{cls.YELLOW}{text}{cls.END}"
    
    @classmethod
    def bold(cls, text: str) -> str:
        return f"{cls.BOLD}{text}{cls.END}"
