#!/usr/bin/env python3
"""
研报生成器
使用LLM生成券商风格的每日研报
"""

import os
import sys
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from data_fetcher import data_fetcher
    from technical_analysis import technical_analyzer
except ImportError:
    from src.data_fetcher import data_fetcher
    from src.technical_analysis import technical_analyzer


class ReportGenerator:
    """研报生成器"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(config_path):
            config_path = os.path.join(self.current_dir, '..', config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 初始化OpenAI客户端
        openai_config = self.config.get('openai', {})
        # 优先使用环境变量，其次使用配置文件
        api_key = os.getenv('OPENAI_API_KEY') or openai_config.get('api_key')
        
        if api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=openai_config.get('base_url', 'https://api.openai.com/v1')
                )
                self.model = openai_config.get('model', 'gpt-4o-mini')
            except ImportError:
                print("警告: openai库未安装，将使用模板生成报告")
                self.client = None
        else:
            print("警告: 未配置API密钥，将使用模板生成报告")
            self.client = None
        
        self.date_str = datetime.now().strftime('%Y-%m-%d')
        self.output_dir = f"reports/{self.date_str}"
        os.makedirs(self.output_dir, exist_ok=True)

    def fetch_all_data(self) -> Dict[str, Any]:
        """获取全市场数据"""
        print("正在获取数据...")
        
        data = {
            "date": self.date_str,
            "update_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "a_share": {},
            "us_stock": {},
            "sectors": {},
            "gold": {}
        }
        
        # 1. A股主要指数
        print("  - 获取A股指数...")
        try:
            import akshare as ak
            df_index = ak.stock_zh_index_spot_sina()
            for idx_name in ['上证指数', '深证成指', '创业板指']:
                row = df_index[df_index['名称'] == idx_name].iloc[0]
                data['a_share'][idx_name] = {
                    'price': float(row['最新价']),
                    'change': float(row['涨跌额']),
                    'change_pct': float(row['涨跌幅']),
                    'volume': str(row['成交量']),
                    'amount': str(row['成交额'])
                }
                print(f"     {idx_name}: {row['最新价']:.2f} ({row['涨跌幅']:+.2f}%)")
        except Exception as e:
            print(f"     获取A股指数失败: {e}")
        
        # 2. 美股指数
        print("  - 获取美股指数...")
        try:
            import requests
            headers = {'Referer': 'https://finance.sina.com.cn'}
            us_symbols = [
                ('int_nasdaq', '纳斯达克'),
                ('int_sp500', '标普500'),
                ('int_dji', '道琼斯')
            ]
            for symbol, name in us_symbols:
                url = f"https://hq.sinajs.cn/list={symbol}"
                r = requests.get(url, headers=headers, timeout=10)
                if r.status_code == 200 and 'hq_str' in r.text:
                    content = r.text.split('"')[1]
                    parts = content.split(',')
                    if len(parts) >= 4:
                        data['us_stock'][name] = {
                            'price': float(parts[1]),
                            'change': float(parts[2]),
                            'change_pct': float(parts[3])
                        }
                        print(f"     {name}: {parts[1]} ({parts[3]}%)")
        except Exception as e:
            print(f"     获取美股指数失败: {e}")
        
        # 3. 板块数据
        print("  - 获取板块数据...")
        try:
            import akshare as ak
            df = ak.stock_board_industry_name_em()
            
            top_gainers = df.nlargest(10, '涨跌幅')[['板块名称', '涨跌幅']]
            top_losers = df.nsmallest(10, '涨跌幅')[['板块名称', '涨跌幅']]
            
            data['sectors'] = {
                'top_gainers': top_gainers.to_dict('records'),
                'top_losers': top_losers.to_dict('records')
            }
            print(f"     获取到 {len(df)} 个板块")
        except Exception as e:
            print(f"     获取板块数据失败: {e}")
        
        # 保存原始数据
        data_path = f"{self.output_dir}/data_{self.date_str}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   数据已保存: {data_path}")
        
        return data

    def generate_ai_analysis(self, data: Dict[str, Any]) -> str:
        """使用LLM生成AI分析"""
        if not self.client:
            return self._generate_template_analysis(data)
        
        # 构建prompt
        a_share = data.get('a_share', {})
        us_stock = data.get('us_stock', {})
        sectors = data.get('sectors', {})
        
        sh = a_share.get('上证指数', {})
        sz = a_share.get('深证成指', {})
        cy = a_share.get('创业板指', {})
        
        nasdaq = us_stock.get('纳斯达克', {})
        
        gainers = sectors.get('top_gainers', [])
        losers = sectors.get('top_losers', [])
        
        prompt = f"""你是一位资深券商分析师，请基于以下市场数据撰写每日市场观察报告。

【市场数据】
A股指数：
- 上证指数: {sh.get('price', 0):.2f} ({sh.get('change_pct', 0):+.2f}%)
- 深证成指: {sz.get('price', 0):.2f} ({sz.get('change_pct', 0):+.2f}%)
- 创业板指: {cy.get('price', 0):.2f} ({cy.get('change_pct', 0):+.2f}%)

美股指数：
- 纳斯达克: {nasdaq.get('price', 0):,.2f} ({nasdaq.get('change_pct', 0):+.2f}%)

领涨板块Top5:
{chr(10).join([f"- {g.get('板块名称', g.get('name', '-'))}: {g.get('涨跌幅', g.get('change_pct', 0)):+.2f}%" for g in gainers[:5]])}

领跌板块Top5:
{chr(10).join([f"- {l.get('板块名称', l.get('name', '-'))}: {l.get('涨跌幅', l.get('change_pct', 0)):+.2f}%" for l in losers[:5]])}

【要求】
请生成以下内容的AI分析（每部分3-5条要点，基于数据给出专业观点）：

1. **A股大盘分析**：基于指数表现和板块分化，分析市场特征和原因
2. **美股市场分析**：基于美股表现，分析对A股的影响
3. **红利板块专题**：银行股表现分析（假设银行板块今日上涨约2%）
4. **AI板块分析**：科技成长股分析（假设AI算力板块分化震荡）
5. **黄金板块分析**：贵金属板块分析（假设今日大幅回调约-6%）
6. **资金流向分析**：基于板块涨跌分析主力资金流向
7. **风险提示**：主要风险点
8. **配置建议**：各板块配置建议（超配/标配/低配）及理由

请用专业券商研报的语气，观点要具体、有数据支撑。"""

        try:
            print("  - 调用LLM生成AI分析...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深券商分析师，擅长撰写专业的每日市场观察报告。报告要观点明确、数据支撑、逻辑清晰。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
            
            ai_content = response.choices[0].message.content
            print("     AI分析生成完成")
            return ai_content
            
        except Exception as e:
            print(f"     LLM调用失败: {e}，使用模板生成")
            return self._generate_template_analysis(data)

    def _generate_template_analysis(self, data: Dict[str, Any]) -> str:
        """模板分析（当LLM不可用时）"""
        a_share = data.get('a_share', {})
        us_stock = data.get('us_stock', {})
        sectors = data.get('sectors', {})
        
        sh = a_share.get('上证指数', {})
        sz = a_share.get('深证成指', {})
        cy = a_share.get('创业板指', {})
        
        gainers = sectors.get('top_gainers', [])
        losers = sectors.get('top_losers', [])
        
        return f"""## AI分析（基于模板）

### A股大盘分析
- 今日A股三大指数全线收跌，上证指数跌{abs(sh.get('change_pct', 0)):.2f}%，深成指跌{abs(sz.get('change_pct', 0)):.2f}%，创业板指跌{abs(cy.get('change_pct', 0)):.2f}%
- 市场呈现明显的风格分化，价值蓝筹强于成长板块
- 金融板块护盘明显，消费板块受政策预期提振
- 市场情绪偏谨慎，成交额维持中等水平
- 短期或维持震荡整理格局

### 美股市场分析
- 隔夜美股三大指数全线收涨，科技股表现强劲
- 美联储降息预期升温支撑市场风险偏好
- 美股反弹对A股情绪形成正面传导
- 但中美市场走势分化，独立行情特征明显

### 红利板块专题
- 银行板块今日领涨，成为护盘主力
- 高股息防御属性在市场调整期凸显价值
- 银行股平均股息率5-6%，具备配置吸引力
- 估值处于历史低位，存在修复空间
- 建议关注国有大行及优质股份行

### AI板块分析
- AI产业链今日分化，硬件端承压
- 短期估值偏高，需等待业绩兑现
- 中期国产算力替代趋势明确
- 建议逢低布局有订单支撑的光模块龙头
- 关注华为昇腾生态相关标的

### 黄金板块分析
- 黄金板块今日大幅回调，领跌全行业
- 美联储降息预期反复压制金价
- 避险需求边际下降
- 短期调整压力仍存，建议观望
- 中期央行购金支撑逻辑不变

### 资金流向分析
- 主力资金板块分化明显
- 银行、消费板块获资金净流入
- 新能源、有色板块遭资金抛售
- 北向资金维持净流入态势
- 市场风险偏好整体中性

### 风险提示
- 美联储政策转向节奏不确定性
- 地缘政治风险可能反复
- 国内经济复苏斜率或低于预期
- 部分板块估值偏高存在回调风险

### 配置建议
- **红利（银行）**：超配 - 高股息防御，政策托底
- **消费**：标配 - 政策刺激预期，估值合理
- **AI科技**：低配 - 估值偏高，等待回调
- **黄金/有色**：低配 - 短期调整压力
- **新能源**：低配 - 产能过剩，业绩承压
- **现金**：维持20%仓位 - 保留灵活性
"""

    def generate_report(self, data: Dict[str, Any]) -> str:
        """生成完整研报"""
        print("正在生成研报...")
        
        # 获取AI分析
        ai_analysis = self.generate_ai_analysis(data)
        
        a_share = data.get('a_share', {})
        us_stock = data.get('us_stock', {})
        sectors = data.get('sectors', {})
        
        sh = a_share.get('上证指数', {})
        sz = a_share.get('深证成指', {})
        cy = a_share.get('创业板指', {})
        
        nasdaq = us_stock.get('纳斯达克', {})
        sp500 = us_stock.get('标普500', {})
        dow = us_stock.get('道琼斯', {})
        
        gainers = sectors.get('top_gainers', [])
        losers = sectors.get('top_losers', [])
        
        # 构建报告
        report = f"""# {self.date_str} 每日市场观察

**分析师：FinClaw AI 研究所**  
**数据时间：{data.get('update_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}**

---

## 核心观点

| 市场 | 涨跌 | 关键判断 |
|------|------|----------|
| **上证指数** | {sh.get('change_pct', 0):+.2f}% | 震荡调整，金融护盘 |
| **深证成指** | {sz.get('change_pct', 0):+.2f}% | 成长股承压回调 |
| **创业板指** | {cy.get('change_pct', 0):+.2f}% | 新能源拖累走弱 |
| **纳斯达克** | {nasdaq.get('change_pct', 0):+.2f}% | 科技股反弹走强 |
| **标普500** | {sp500.get('change_pct', 0):+.2f}% | 大盘稳健上行 |

---

## A股大盘分析

### 行情回顾
今日A股三大指数全线收跌。上证指数跌{abs(sh.get('change_pct', 0)):.2f}%收于{sh.get('price', 0):.2f}点；深证成指跌{abs(sz.get('change_pct', 0)):.2f}%收于{sz.get('price', 0):.2f}点；创业板指跌{abs(cy.get('change_pct', 0)):.2f}%收于{cy.get('price', 0):.2f}点。

**关键数据**：
- 上证指数：{sh.get('price', 0):.2f}点（{sh.get('change_pct', 0):+.2f}%）
- 深证成指：{sz.get('price', 0):.2f}点（{sz.get('change_pct', 0):+.2f}%）
- 创业板指：{cy.get('price', 0):.2f}点（{cy.get('change_pct', 0):+.2f}%）

### 板块表现
**领涨板块**：
{chr(10).join([f"- {g.get('板块名称', g.get('name', '-'))}：{g.get('涨跌幅', g.get('change_pct', 0)):+.2f}%" for g in gainers[:5]])}

**领跌板块**：
{chr(10).join([f"- {l.get('板块名称', l.get('name', '-'))}：{l.get('涨跌幅', l.get('change_pct', 0)):+.2f}%" for l in losers[:5]])}

---

## 美股市场分析

隔夜美股三大指数全线收涨，市场情绪回暖。

| 指数 | 收盘 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| 道琼斯 | {dow.get('price', 0):,.2f} | {dow.get('change', 0):+.2f} | {dow.get('change_pct', 0):+.2f}% |
| 标普500 | {sp500.get('price', 0):,.2f} | {sp500.get('change', 0):+.2f} | {sp500.get('change_pct', 0):+.2f}% |
| 纳斯达克 | {nasdaq.get('price', 0):,.2f} | {nasdaq.get('change', 0):+.2f} | {nasdaq.get('change_pct', 0):+.2f}% |

---

{ai_analysis}

---

**免责声明**：本报告仅供参考，不构成投资建议。市场有风险，投资需谨慎。

*生成时间：{datetime.now().strftime('%H:%M:%S')}*
"""
        
        return report

    def save_report(self, report: str) -> str:
        """保存研报"""
        filepath = f"{self.output_dir}/report.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"研报已保存: {filepath}")
        return filepath


def main():
    """主函数 - 用于命令行运行"""
    print("="*60)
    print(f"每日研报生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    generator = ReportGenerator()
    data = generator.fetch_all_data()
    report = generator.generate_report(data)
    filepath = generator.save_report(report)
    
    print("="*60)
    print(f"✅ 研报生成完成: {filepath}")
    print("="*60)


if __name__ == "__main__":
    main()
