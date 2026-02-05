#!/usr/bin/env python3
"""
研报生成器
使用LLM生成券商风格的每日研报 - SiliconFlow API版本
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


def get_api_key():
    """
    获取API Key，优先级：
    1. Streamlit secrets (如果在Streamlit环境中)
    2. 环境变量 SILICONFLOW_API_KEY
    3. 配置文件中的api_key
    """
    # 1. 尝试Streamlit secrets
    try:
        import streamlit as st
        # 在Streamlit环境中运行
        try:
            return st.secrets["api_keys"]["silicon_flow"]
        except (KeyError, FileNotFoundError):
            pass
        
        # 尝试sidebar输入（仅在交互模式下）
        if hasattr(st, 'sidebar'):
            try:
                api_key = st.sidebar.text_input(
                    "SiliconFlow API Key", 
                    type="password", 
                    key="global_api_key_input"
                )
                if api_key:
                    return api_key
            except:
                pass
    except ImportError:
        pass
    
    # 2. 环境变量
    env_key = os.getenv("SILICONFLOW_API_KEY")
    if env_key:
        return env_key
    
    # 3. 配置文件
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'config.yaml')
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        openai_config = config.get('openai', {})
        api_key = openai_config.get('api_key')
        if api_key and api_key != 'your-api-key-here':
            return api_key
    
    return None


class ReportGenerator:
    """研报生成器"""
    
    DEFAULT_MODEL = "moonshotai/Kimi-K2-Thinking"
    DEFAULT_BASE_URL = "https://api.siliconflow.cn/v1"
    
    def __init__(self, config_path: str = "config.yaml"):
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        if not os.path.exists(config_path):
            config_path = os.path.join(self.current_dir, '..', config_path)
        
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 获取API Key - 必须存在，否则报错
        self.api_key = get_api_key()
        if not self.api_key:
            raise ValueError(
                "未找到有效的API Key。请通过以下方式之一配置：\n"
                "1. 创建 .streamlit/secrets.toml 文件，包含 [api_keys] silicon_flow = 'your-key'\n"
                "2. 设置环境变量 SILICONFLOW_API_KEY\n"
                "3. 修改 config.yaml 中的 openai.api_key"
            )
        
        # 初始化OpenAI客户端
        try:
            from openai import OpenAI
            
            # 优先使用配置文件中的设置，否则使用默认值
            openai_config = self.config.get('openai', {})
            base_url = openai_config.get('base_url', self.DEFAULT_BASE_URL)
            self.model = openai_config.get('model', self.DEFAULT_MODEL)
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
            print(f"✅ API客户端初始化成功")
            print(f"   模型: {self.model}")
            print(f"   API端点: {base_url}")
            
        except ImportError:
            raise ImportError("openai库未安装，请运行: pip install openai")
        
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
        
        # 3. 板块数据 - 使用新浪接口
        print("  - 获取板块数据...")
        try:
            import requests
            from bs4 import BeautifulSoup
            
            # 使用新浪财经板块数据
            url = "https://vip.stock.finance.sina.com.cn/q/view/newSinaHy.php"
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            if r.status_code == 200:
                # 解析JS格式数据
                content = r.text
                if 'var S_Finance_bankuai_sinaindustry' in content:
                    # 提取JSON数据
                    json_start = content.find('{')
                    json_end = content.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        data_str = content[json_start:json_end]
                        # 简化为手动解析主要板块
                        sectors_list = []
                        for line in data_str.split(','):
                            if 'new_' in line and ':' in line:
                                parts = line.split(':')
                                if len(parts) >= 2:
                                    sector_info = parts[1].split(',')
                                    if len(sector_info) >= 5:
                                        try:
                                            change = float(sector_info[3])
                                            sectors_list.append({
                                                '板块名称': sector_info[1],
                                                '涨跌幅': change
                                            })
                                        except:
                                            pass
                        
                        # 排序获取领涨领跌
                        sectors_list.sort(key=lambda x: x['涨跌幅'], reverse=True)
                        data['sectors'] = {
                            'top_gainers': sectors_list[:10],
                            'top_losers': sectors_list[-10:][::-1]
                        }
                        print(f"     获取到 {len(sectors_list)} 个板块")
        except Exception as e:
            print(f"     获取板块数据失败: {e}")
        
        # 保存原始数据
        data_path = f"{self.output_dir}/data_{self.date_str}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   数据已保存: {data_path}")
        
        return data

    def generate_ai_analysis(self, data: Dict[str, Any]) -> str:
        """使用SiliconFlow LLM生成AI分析"""
        print("  - 调用SiliconFlow LLM生成AI分析...")
        
        a_share = data.get('a_share', {})
        us_stock = data.get('us_stock', {})
        sectors = data.get('sectors', {})
        
        sh = a_share.get('上证指数', {})
        sz = a_share.get('深证成指', {})
        cy = a_share.get('创业板指', {})
        
        nasdaq = us_stock.get('纳斯达克', {})
        
        gainers = sectors.get('top_gainers', [])
        losers = sectors.get('top_losers', [])
        
        gainer_text = "\n".join([f"- {g.get('板块名称', g.get('name', '-'))}: {g.get('涨跌幅', g.get('change_pct', 0)):+.2f}%" for g in gainers[:5]]) if gainers else "暂无数据"
        loser_text = "\n".join([f"- {l.get('板块名称', l.get('name', '-'))}: {l.get('涨跌幅', l.get('change_pct', 0)):+.2f}%" for l in losers[:5]]) if losers else "暂无数据"
        
        prompt = f"""你是一位资深券商分析师，请基于以下市场数据撰写每日市场观察报告。

【市场数据】
A股指数：
- 上证指数: {sh.get('price', 0):.2f} ({sh.get('change_pct', 0):+.2f}%)
- 深证成指: {sz.get('price', 0):.2f} ({sz.get('change_pct', 0):+.2f}%)
- 创业板指: {cy.get('price', 0):.2f} ({cy.get('change_pct', 0):+.2f}%)

美股指数：
- 纳斯达克: {nasdaq.get('price', 0):,.2f} ({nasdaq.get('change_pct', 0):+.2f}%)

领涨板块Top5:
{gainer_text}

领跌板块Top5:
{loser_text}

【要求】
请生成以下内容的AI分析（每部分3-5条要点，基于数据给出专业观点）：

1. **A股大盘分析**：基于指数表现和板块分化，分析市场特征和原因
2. **美股市场分析**：基于美股表现，分析对A股的影响
3. **红利板块专题**：银行股表现分析
4. **AI板块分析**：科技成长股分析
5. **黄金板块分析**：贵金属板块分析
6. **资金流向分析**：基于板块涨跌分析主力资金流向
7. **风险提示**：主要风险点
8. **配置建议**：各板块配置建议（超配/标配/低配）及理由

请用专业券商研报的语气，观点要具体、有数据支撑。"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深券商分析师，擅长撰写专业的每日市场观察报告。报告要观点明确、数据支撑、逻辑清晰。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000
            )
            
            ai_content = response.choices[0].message.content
            print("     ✅ AI分析生成完成")
            return ai_content
            
        except Exception as e:
            raise RuntimeError(f"LLM调用失败: {e}")

    def generate_report(self, data: Dict[str, Any]) -> str:
        """生成完整研报"""
        print("正在生成研报...")
        
        # 获取AI分析（必须有API key）
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
{chr(10).join([f"- {g.get('板块名称', g.get('name', '-'))}：{g.get('涨跌幅', g.get('change_pct', 0)):+.2f}%" for g in (gainers[:5] if gainers else [])]) if gainers else '- 暂无数据'}

**领跌板块**：
{chr(10).join([f"- {l.get('板块名称', l.get('name', '-'))}：{l.get('涨跌幅', l.get('change_pct', 0)):+.2f}%" for l in (losers[:5] if losers else [])]) if losers else '- 暂无数据'}

---

## 美股市场分析

隔夜美股三大指数全线收涨，市场情绪回暖。

| 指数 | 收盘 | 涨跌 | 涨跌幅 |
|------|------|------|--------|
| 道琼斯 | {dow.get('price', 0):,.2f} | {dow.get('change', 0):+.2f} | {dow.get('change_pct', 0):+.2f}% |
| 标普500 | {sp500.get('price', 0):,.2f} | {sp500.get('change', 0):+.2f} | {sp500.get('change_pct', 0):+.2f}% |
| 纳斯达克 | {nasdaq.get('price', 0):,.2f} | {nasdaq.get('change', 0):+.2f} | {nasdaq.get('change_pct', 0):+.2f}% |

---

## AI深度分析

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
    
    try:
        generator = ReportGenerator()
        data = generator.fetch_all_data()
        report = generator.generate_report(data)
        filepath = generator.save_report(report)
        
        print("="*60)
        print(f"✅ 研报生成完成: {filepath}")
        print("="*60)
    except ValueError as e:
        print("="*60)
        print(f"❌ 配置错误: {e}")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print("="*60)
        print(f"❌ 生成失败: {e}")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
