"""
Financial Report System
自动化每日研报生成系统
"""

__version__ = "1.0.0"
__author__ = "Strategy Research Team"

from .data_fetcher import DataFetcher, data_fetcher
from .technical_analysis import TechnicalAnalyzer, technical_analyzer
from .report_generator import ReportGenerator

__all__ = [
    'DataFetcher',
    'data_fetcher',
    'TechnicalAnalyzer',
    'technical_analyzer',
    'ReportGenerator'
]
