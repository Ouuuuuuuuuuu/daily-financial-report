#!/usr/bin/env python3
"""
金融数据获取模块
支持A股、纳斯达克、黄金、AI板块、红利板块数据获取
"""

import akshare as ak
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
import json


class DataFetcher:
    """金融数据获取器"""
    
    def __init__(self):
        self.cache = {}
        
    # ==================== A股数据 ====================
    
    def get_a_share_index(self) -> pd.DataFrame:
        """获取A股主要指数行情"""
        try:
            # 上证指数、深证成指、创业板指
            indices = {
                "000001": "上证指数",
                "399001": "深证成指", 
                "399006": "创业板指",
                "000300": "沪深300",
                "000905": "中证500",
                "000016": "上证50"
            }
            
            data = []
            for code, name in indices.items():
                df = ak.stock_zh_index_spot_em()
                row = df[df['代码'] == code]
                if not row.empty:
                    data.append({
                        'code': code,
                        'name': name,
                        'price': float(row['最新价'].values[0]),
                        'change': float(row['涨跌额'].values[0]),
                        'change_pct': float(row['涨跌幅'].values[0]),
                        'volume': float(row['成交量'].values[0]),
                        'amount': float(row['成交额'].values[0])
                    })
            return pd.DataFrame(data)
        except Exception as e:
            print(f"获取A股指数失败: {e}")
            return pd.DataFrame()
    
    def get_a_share_daily(self, symbol: str, days: int = 60) -> pd.DataFrame:
        """获取A股个股历史数据"""
        try:
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", 
                                    start_date=(datetime.now() - timedelta(days=days)).strftime("%Y%m%d"),
                                    end_date=datetime.now().strftime("%Y%m%d"),
                                    adjust="qfq")
            df.columns = ['date', 'open', 'close', 'high', 'low', 'volume', 'amount', 
                         'amplitude', 'change_pct', 'change', 'turnover']
            return df
        except Exception as e:
            print(f"获取A股数据失败 {symbol}: {e}")
            return pd.DataFrame()
    
    def get_sector_flow(self, sector: str = "行业板块") -> pd.DataFrame:
        """获取板块资金流向"""
        try:
            if sector == "行业板块":
                df = ak.stock_sector_fund_flow_rank(indicator="今日")
            else:
                df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type=sector)
            return df.head(20)
        except Exception as e:
            print(f"获取板块资金流向失败: {e}")
            return pd.DataFrame()
    
    # ==================== 纳斯达克数据 ====================
    
    def get_nasdaq_data(self, symbols: List[str], period: str = "1mo") -> Dict[str, pd.DataFrame]:
        """获取纳斯达克相关数据"""
        data = {}
        for symbol in symbols:
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period=period)
                if not hist.empty:
                    data[symbol] = hist
            except Exception as e:
                print(f"获取{symbol}失败: {e}")
        return data
    
    def get_nasdaq_overview(self) -> Dict:
        """获取纳斯达克整体概览"""
        try:
            # 纳斯达克指数
            ixic = yf.Ticker("^IXIC")
            ixic_info = ixic.info
            ixic_hist = ixic.history(period="5d")
            
            # 纳斯达克100期货
            nq_futures = yf.Ticker("NQ=F")
            nq_hist = nq_futures.history(period="2d")
            
            return {
                'nasdaq_index': {
                    'current': ixic_hist['Close'].iloc[-1] if not ixic_hist.empty else None,
                    'previous': ixic_hist['Close'].iloc[-2] if len(ixic_hist) > 1 else None,
                    'change_pct': ((ixic_hist['Close'].iloc[-1] / ixic_hist['Close'].iloc[-2]) - 1) * 100 
                                  if len(ixic_hist) > 1 else 0
                },
                'nasdaq_100_futures': {
                    'current': nq_hist['Close'].iloc[-1] if not nq_hist.empty else None,
                    'previous': nq_hist['Close'].iloc[-2] if len(nq_hist) > 1 else None,
                },
                'volume': ixic_info.get('volume'),
                'market_status': ixic_info.get('marketState', 'unknown')
            }
        except Exception as e:
            print(f"获取纳斯达克概览失败: {e}")
            return {}
    
    # ==================== 黄金数据 ====================
    
    def get_gold_price(self) -> Dict:
        """获取黄金价格数据"""
        try:
            # COMEX黄金期货
            gc = yf.Ticker("GC=F")
            gc_hist = gc.history(period="1mo")
            gc_info = gc.info
            
            # 国内黄金ETF
            try:
                gold_etf = ak.fund_etf_hist_em(symbol="518880", period="daily",
                                               start_date=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d"),
                                               end_date=datetime.now().strftime("%Y%m%d"),
                                               adjust="qfq")
            except:
                gold_etf = pd.DataFrame()
            
            return {
                'comex_gold': {
                    'current': gc_hist['Close'].iloc[-1] if not gc_hist.empty else None,
                    'open': gc_hist['Open'].iloc[-1] if not gc_hist.empty else None,
                    'high': gc_hist['High'].iloc[-1] if not gc_hist.empty else None,
                    'low': gc_hist['Low'].iloc[-1] if not gc_hist.empty else None,
                    'change_pct': ((gc_hist['Close'].iloc[-1] / gc_hist['Close'].iloc[-2]) - 1) * 100 
                                  if len(gc_hist) > 1 else 0,
                    'history': gc_hist
                },
                'domestic_etf': gold_etf,
                'unit': 'USD/oz'
            }
        except Exception as e:
            print(f"获取黄金数据失败: {e}")
            return {}
    
    # ==================== AI板块数据 ====================
    
    def get_ai_sector_a_share(self) -> pd.DataFrame:
        """获取A股AI板块数据"""
        try:
            # 获取人工智能概念板块
            df = ak.stock_board_concept_hist_em(symbol="人工智能", period="daily")
            return df
        except Exception as e:
            print(f"获取AI板块失败: {e}")
            return pd.DataFrame()
    
    def get_ai_leaders(self) -> pd.DataFrame:
        """获取AI板块龙头股"""
        try:
            # 获取AI相关股票排行
            df = ak.stock_board_concept_cons_em(symbol="人工智能")
            df = df.sort_values('涨跌幅', ascending=False)
            return df.head(10)
        except Exception as e:
            print(f"获取AI龙头股失败: {e}")
            return pd.DataFrame()
    
    def get_ai_us_stocks(self, symbols: List[str] = None) -> Dict[str, pd.DataFrame]:
        """获取美股AI概念股"""
        if symbols is None:
            symbols = ["NVDA", "AMD", "AVGO", "CRM", "PLTR", "SMCI"]
        return self.get_nasdaq_data(symbols, period="1mo")
    
    # ==================== 红利板块数据 ====================
    
    def get_dividend_etfs(self) -> Dict[str, pd.DataFrame]:
        """获取红利ETF数据"""
        etfs = {
            "510880": "红利ETF",
            "515180": "红利低波ETF",
            "512590": "中证红利ETF"
        }
        data = {}
        for code, name in etfs.items():
            try:
                df = ak.fund_etf_hist_em(symbol=code, period="daily",
                                         start_date=(datetime.now() - timedelta(days=60)).strftime("%Y%m%d"),
                                         end_date=datetime.now().strftime("%Y%m%d"),
                                         adjust="qfq")
                data[name] = df
            except Exception as e:
                print(f"获取ETF {code} 失败: {e}")
        return data
    
    def get_dividend_stocks(self) -> pd.DataFrame:
        """获取高分红股票排行"""
        try:
            # 获取A股分红数据
            df = ak.stock_dividents_cninfo()
            df = df.sort_values('每股派息(元)', ascending=False)
            return df.head(20)
        except Exception as e:
            print(f"获取分红数据失败: {e}")
            return pd.DataFrame()
    
    # ==================== 新闻数据 ====================
    
    def get_financial_news(self, limit: int = 20) -> List[Dict]:
        """获取财经新闻"""
        try:
            # 新浪财经新闻
            df = ak.stock_news_em()
            news = []
            for _, row in df.head(limit).iterrows():
                news.append({
                    'title': row['标题'],
                    'content': row['内容'],
                    'time': row['时间'],
                    'source': '新浪财经'
                })
            return news
        except Exception as e:
            print(f"获取新闻失败: {e}")
            return []
    
    def get_sector_news(self, sector: str) -> List[Dict]:
        """获取板块相关新闻"""
        try:
            df = ak.stock_news_em()
            # 过滤相关新闻
            filtered = df[df['内容'].str.contains(sector, na=False) | 
                         df['标题'].str.contains(sector, na=False)]
            news = []
            for _, row in filtered.head(10).iterrows():
                news.append({
                    'title': row['标题'],
                    'content': row['内容'],
                    'time': row['时间']
                })
            return news
        except Exception as e:
            print(f"获取板块新闻失败: {e}")
            return []


# 单例模式
data_fetcher = DataFetcher()


if __name__ == "__main__":
    # 测试数据获取
    fetcher = DataFetcher()
    
    print("=== 获取A股指数 ===")
    a_share = fetcher.get_a_share_index()
    print(a_share)
    
    print("\n=== 获取纳斯达克概览 ===")
    nasdaq = fetcher.get_nasdaq_overview()
    print(nasdaq)
    
    print("\n=== 获取黄金价格 ===")
    gold = fetcher.get_gold_price()
    print(gold)
