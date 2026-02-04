#!/usr/bin/env python3
"""
研报生成器
使用LLM生成券商风格的每日研报
"""

import os
import yaml
import json
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI

from data_fetcher import data_fetcher
from technical_analysis import technical_analyzer


class ReportGenerator:
    """研报生成器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化OpenAI客户端
        openai_config = self.config.get('openai', {})
        self.client = OpenAI(
            api_key=openai_config.get('api_key', os.getenv('OPENAI_API_KEY')),
            base_url=openai_config.get('base_url', 'https://api.openai.com/v1')
        )
        self.model = openai_config.get('model', 'gpt-4')
        self.temperature = openai_config.get('temperature', 0.7)
    
    def fetch_all_data(self) -> Dict:
        """获取所有需要的数据"""
        print("正在获取数据...")
        
        data = {
            'date': datetime.now().strftime('%Y年%m月%d日'),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 1. A股数据
        print("  - 获取A股指数...")
        data['a_share_index'] = data_fetcher.get_a_share_index()
        
        # 2. 纳斯达克数据
        print("  - 获取纳斯达克数据...")
        data['nasdaq'] = data_fetcher.get_nasdaq_overview()
        nasdaq_stocks = self.config.get('data_sources', {}).get('nasdaq', {}).get('symbols', [])
        data['nasdaq_stocks'] = data_fetcher.get_nasdaq_data(nasdaq_stocks[:5], period="5d")
        
        # 3. 黄金数据
        print("  - 获取黄金数据...")
        data['gold'] = data_fetcher.get_gold_price()
        
        # 4. AI板块
        print("  - 获取AI板块数据...")
        data['ai_sector'] = data_fetcher.get_ai_sector_a_share()
        data['ai_leaders'] = data_fetcher.get_ai_leaders()
        ai_us = self.config.get('data_sources', {}).get('ai_sector', {}).get('us_stocks', [])
        data['ai_us_stocks'] = data_fetcher.get_ai_us_stocks(ai_us)
        
        # 5. 红利板块
        print("  - 获取红利板块数据...")
        data['dividend_etfs'] = data_fetcher.get_dividend_etfs()
        
        # 6. 资金流向
        print("  - 获取资金流向...")
        data['sector_flow'] = data_fetcher.get_sector_flow()
        
        # 7. 新闻
        print("  - 获取财经新闻...")
        data['news'] = data_fetcher.get_financial_news(10)
        
        return data
    
    def prepare_prompt(self, data: Dict) -> str:
        """准备Prompt"""
        
        # 构建数据摘要
        a_share_summary = ""
        if not data['a_share_index'].empty:
            for _, row in data['a_share_index'].iterrows():
                a_share_summary += f"- {row['name']}({row['code']}): {row['price']:.2f}, 涨跌{row['change_pct']:+.2f}%\n"
        
        nasdaq_summary = ""
        if data['nasdaq']:
            nq = data['nasdaq'].get('nasdaq_index', {})
            nasdaq_summary = f"纳斯达克指数: {nq.get('current', 'N/A'):.2f}, 涨跌{nq.get('change_pct', 0):+.2f}%"
        
        gold_summary = ""
        if data['gold']:
            gc = data['gold'].get('comex_gold', {})
            gold_summary = f"COMEX黄金: ${gc.get('current', 'N/A'):.2f}/盎司, 涨跌{gc.get('change_pct', 0):+.2f}%"
        
        news_summary = "\n".join([f"- {n['title']}" for n in data['news'][:5]])
        
        prompt = f"""你是一位资深证券分析师，请根据以下市场数据，撰写一份专业的每日市场研报。

## 报告日期: {data['date']}

### 一、市场数据概览

**A股主要指数:**
{a_share_summary}

**隔夜美股:**
{nasdaq_summary}

**黄金价格:**
{gold_summary}

**重要财经新闻:**
{news_summary}

### 二、研报格式要求

请按照以下格式撰写研报：

---

# [{data['date']}] 每日市场观察

**分析师：** 策略研究团队  
**报告日期：** {data['date']}  
**投资评级：** 震荡/看好/谨慎（根据市场情况判断）

---

## 【核心观点】
（3-5条核心观点，每条观点简洁有力，包含明确的投资建议）

---

## 【市场行情回顾】

### 1. A股市场
- 大盘走势分析
- 主要指数表现
- 成交量和资金流向

### 2. 隔夜美股
- 纳斯达克指数表现
- 科技股走势
- 对A股的影响预判

---

## 【板块专题分析】

### 3. 红利板块
- 红利ETF表现
- 高分红股票动态
- 配置价值分析

### 4. 人工智能板块
- A股AI概念股表现
- 美股AI龙头动态（英伟达、AMD等）
- 行业催化剂和风险

### 5. 黄金板块
- 国际金价走势
- 国内黄金ETF表现
- 避险需求分析

---

## 【技术面分析】
- 关键支撑位和阻力位
- 技术指标解读（RSI、MACD等）
- 趋势判断

---

## 【资金流向】
- 北向资金流向（如有数据）
- 主力资金偏好
- 板块资金净流入排名

---

## 【风险提示】
（列出3-5条主要投资风险）

---

## 【配置建议】
- 仓位建议（如：维持中性仓位60-70%）
- 行业配置方向
- 重点关注标的类型

---

**免责声明：** 本报告仅供参考，不构成投资建议。投资者应独立判断并承担投资风险。

---

请使用专业、客观的券商研报语言风格，数据准确，逻辑清晰，观点明确。
"""
        return prompt
    
    def generate_report(self, data: Optional[Dict] = None) -> str:
        """生成研报"""
        if data is None:
            data = self.fetch_all_data()
        
        prompt = self.prepare_prompt(data)
        
        print("正在生成研报...")
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位经验丰富的证券分析师，擅长撰写专业、客观的市场研究报告。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=4000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"生成研报失败: {e}")
            return self._generate_fallback_report(data)
    
    def _generate_fallback_report(self, data: Dict) -> str:
        """生成简化版研报（当LLM调用失败时）"""
        date_str = data['date']
        
        report = f"""# [{date_str}] 每日市场观察

**分析师：** 策略研究团队  
**报告日期：** {date_str}  
**投资评级：** 震荡

---

## 【核心观点】
1. 市场处于震荡整理阶段，建议控制仓位
2. 关注政策面和资金面变化
3. 结构性机会仍存，关注业绩确定性标的

---

## 【市场行情回顾】

### A股市场
"""
        if not data['a_share_index'].empty:
            for _, row in data['a_share_index'].iterrows():
                report += f"- {row['name']}: {row['change_pct']:+.2f}%\n"
        
        report += "\n### 隔夜美股\n"
        if data['nasdaq']:
            nq = data['nasdaq'].get('nasdaq_index', {})
            report += f"- 纳斯达克指数: {nq.get('change_pct', 0):+.2f}%\n"
        
        report += f"""

### 黄金价格
"""
        if data['gold']:
            gc = data['gold'].get('comex_gold', {})
            report += f"- COMEX黄金: ${gc.get('current', 'N/A'):.2f}/盎司\n"
        
        report += f"""

---

## 【风险提示】
1. 市场波动风险
2. 政策不确定性
3. 外部环境变化

---

**免责声明：** 本报告仅供参考，不构成投资建议。

---

*注：由于技术原因，本报告为简化版本。完整版研报请稍后查看。*
"""
        return report
    
    def save_report(self, report: str, output_dir: str = None) -> str:
        """保存研报到文件"""
        if output_dir is None:
            output_dir = self.config.get('report', {}).get('output_dir', './reports')
        
        os.makedirs(output_dir, exist_ok=True)
        
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"daily_report_{date_str}.md"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"研报已保存至: {filepath}")
        return filepath


def main():
    """主函数"""
    generator = ReportGenerator()
    data = generator.fetch_all_data()
    report = generator.generate_report(data)
    filepath = generator.save_report(report)
    print(f"\n研报生成完成: {filepath}")
    return report


if __name__ == "__main__":
    main()
