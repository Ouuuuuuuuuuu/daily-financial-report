#!/usr/bin/env python3
"""
技术指标计算模块
支持RSI、MACD、均线、布林带等常用技术指标
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


class TechnicalAnalyzer:
    """技术分析器"""
    
    @staticmethod
    def calculate_ma(data: pd.DataFrame, periods: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """计算移动平均线"""
        df = data.copy()
        for period in periods:
            df[f'MA{period}'] = df['close'].rolling(window=period).mean()
        return df
    
    @staticmethod
    def calculate_ema(data: pd.DataFrame, periods: List[int] = [5, 12, 26]) -> pd.DataFrame:
        """计算指数移动平均线"""
        df = data.copy()
        for period in periods:
            df[f'EMA{period}'] = df['close'].ewm(span=period, adjust=False).mean()
        return df
    
    @staticmethod
    def calculate_rsi(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算RSI指标"""
        df = data.copy()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        return df
    
    @staticmethod
    def calculate_macd(data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
        """计算MACD指标"""
        df = data.copy()
        exp1 = df['close'].ewm(span=fast, adjust=False).mean()
        exp2 = df['close'].ewm(span=slow, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=signal, adjust=False).mean()
        df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
        return df
    
    @staticmethod
    def calculate_bollinger(data: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> pd.DataFrame:
        """计算布林带"""
        df = data.copy()
        df['BOLL_MID'] = df['close'].rolling(window=period).mean()
        df['BOLL_STD'] = df['close'].rolling(window=period).std()
        df['BOLL_UPPER'] = df['BOLL_MID'] + (df['BOLL_STD'] * std_dev)
        df['BOLL_LOWER'] = df['BOLL_MID'] - (df['BOLL_STD'] * std_dev)
        df['BOLL_WIDTH'] = (df['BOLL_UPPER'] - df['BOLL_LOWER']) / df['BOLL_MID']
        return df
    
    @staticmethod
    def calculate_kdj(data: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> pd.DataFrame:
        """计算KDJ指标"""
        df = data.copy()
        low_list = df['low'].rolling(window=n, min_periods=n).min()
        high_list = df['high'].rolling(window=n, min_periods=n).max()
        rsv = (df['close'] - low_list) / (high_list - low_list) * 100
        df['K'] = rsv.ewm(alpha=1/m1, adjust=False).mean()
        df['D'] = df['K'].ewm(alpha=1/m2, adjust=False).mean()
        df['J'] = 3 * df['K'] - 2 * df['D']
        return df
    
    @staticmethod
    def calculate_volume_ma(data: pd.DataFrame, periods: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """计算成交量均线"""
        df = data.copy()
        for period in periods:
            df[f'VOL_MA{period}'] = df['volume'].rolling(window=period).mean()
        return df
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.DataFrame:
        """计算ATR指标"""
        df = data.copy()
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        df['ATR'] = true_range.rolling(period).mean()
        return df
    
    @staticmethod
    def calculate_obv(data: pd.DataFrame) -> pd.DataFrame:
        """计算OBV指标"""
        df = data.copy()
        df['OBV'] = np.where(df['close'] > df['close'].shift(1), 
                             df['volume'], 
                             np.where(df['close'] < df['close'].shift(1), 
                                     -df['volume'], 0)).cumsum()
        return df
    
    @staticmethod
    def calculate_all_indicators(data: pd.DataFrame) -> pd.DataFrame:
        """计算所有技术指标"""
        df = data.copy()
        
        # 确保有必要的列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"缺少必要列: {col}")
        
        # 计算各类指标
        df = TechnicalAnalyzer.calculate_ma(df)
        df = TechnicalAnalyzer.calculate_ema(df)
        df = TechnicalAnalyzer.calculate_rsi(df)
        df = TechnicalAnalyzer.calculate_macd(df)
        df = TechnicalAnalyzer.calculate_bollinger(df)
        df = TechnicalAnalyzer.calculate_kdj(df)
        df = TechnicalAnalyzer.calculate_volume_ma(df)
        df = TechnicalAnalyzer.calculate_atr(df)
        df = TechnicalAnalyzer.calculate_obv(df)
        
        return df
    
    @staticmethod
    def get_latest_signals(data: pd.DataFrame) -> Dict:
        """获取最新技术信号"""
        if data.empty:
            return {}
        
        latest = data.iloc[-1]
        signals = {}
        
        # RSI信号
        if 'RSI' in latest:
            rsi = latest['RSI']
            if rsi > 70:
                signals['RSI'] = '超买'
            elif rsi < 30:
                signals['RSI'] = '超卖'
            else:
                signals['RSI'] = '中性'
            signals['RSI_VALUE'] = round(rsi, 2)
        
        # MACD信号
        if 'MACD' in latest and 'MACD_Signal' in latest:
            macd = latest['MACD']
            signal = latest['MACD_Signal']
            if macd > signal:
                signals['MACD'] = '多头'
            else:
                signals['MACD'] = '空头'
            signals['MACD_VALUE'] = round(macd, 4)
            signals['MACD_SIGNAL'] = round(signal, 4)
        
        # 均线排列
        ma_cols = [col for col in data.columns if col.startswith('MA')]
        if len(ma_cols) >= 3:
            ma_values = [latest[col] for col in sorted(ma_cols)[:3]]
            if ma_values[0] > ma_values[1] > ma_values[2]:
                signals['MA_TREND'] = '多头排列'
            elif ma_values[0] < ma_values[1] < ma_values[2]:
                signals['MA_TREND'] = '空头排列'
            else:
                signals['MA_TREND'] = '震荡整理'
        
        # 布林带位置
        if 'BOLL_UPPER' in latest and 'BOLL_LOWER' in latest:
            close = latest['close']
            upper = latest['BOLL_UPPER']
            lower = latest['BOLL_LOWER']
            if close > upper:
                signals['BOLLINGER'] = '突破上轨'
            elif close < lower:
                signals['BOLLINGER'] = '跌破下轨'
            else:
                boll_pct = (close - lower) / (upper - lower)
                if boll_pct > 0.8:
                    signals['BOLLINGER'] = '接近上轨'
                elif boll_pct < 0.2:
                    signals['BOLLINGER'] = '接近下轨'
                else:
                    signals['BOLLINGER'] = '中轨附近'
        
        # KDJ信号
        if 'J' in latest:
            j = latest['J']
            if j > 100:
                signals['KDJ'] = '超买区'
            elif j < 0:
                signals['KDJ'] = '超卖区'
            else:
                signals['KDJ'] = '震荡区'
            signals['KDJ_J'] = round(j, 2)
        
        return signals
    
    @staticmethod
    def calculate_support_resistance(data: pd.DataFrame, window: int = 20) -> Tuple[float, float]:
        """计算支撑位和阻力位"""
        recent = data.tail(window)
        resistance = recent['high'].max()
        support = recent['low'].min()
        return support, resistance
    
    @staticmethod
    def calculate_trend_strength(data: pd.DataFrame) -> str:
        """计算趋势强度"""
        if len(data) < 20:
            return "数据不足"
        
        # 使用价格和均线关系判断趋势
        recent = data.tail(20)
        ma20 = recent['close'].mean()
        latest = data.iloc[-1]['close']
        
        # 计算近期斜率
        x = np.arange(len(recent))
        y = recent['close'].values
        slope = np.polyfit(x, y, 1)[0]
        
        if slope > 0 and latest > ma20:
            return "强势上涨"
        elif slope > 0:
            return "温和上涨"
        elif slope < 0 and latest < ma20:
            return "强势下跌"
        elif slope < 0:
            return "温和下跌"
        else:
            return "横盘整理"


technical_analyzer = TechnicalAnalyzer()


if __name__ == "__main__":
    # 测试
    import sys
    sys.path.append('.')
    from data_fetcher import data_fetcher
    
    # 获取上证指数数据
    df = data_fetcher.get_a_share_daily("000001", days=60)
    if not df.empty:
        df = TechnicalAnalyzer.calculate_all_indicators(df)
        signals = TechnicalAnalyzer.get_latest_signals(df)
        print("技术指标信号:")
        for k, v in signals.items():
            print(f"  {k}: {v}")
