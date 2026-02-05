#!/usr/bin/env python3
"""
研报生成器 - SiliconFlow API版本
使用Kimi-K2-Thinking模型，流式输出
"""

import os
import sys
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any, Optional, Generator

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def get_api_key():
    """获取API Key"""
    # 环境变量
    env_key = os.getenv("SILICONFLOW_API_KEY")
    if env_key:
        return env_key
    
    # 配置文件
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
        
        # 获取API Key
        self.api_key = get_api_key()
        if not self.api_key:
            raise ValueError("未找到有效的API Key。请设置 SILICONFLOW_API_KEY 环境变量或在config.yaml中配置。")
        
        # 初始化OpenAI客户端
        try:
            from openai import OpenAI
            openai_config = self.config.get('openai', {})
            base_url = openai_config.get('base_url', self.DEFAULT_BASE_URL)
            self.model = openai_config.get('model', self.DEFAULT_MODEL)
            
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=base_url
            )
        except ImportError:
            raise ImportError("openai库未安装")
        
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
            "dividend_index": {},  # 红利低波50
            "gold": {}  # AU9999和XAU
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
            print(f"     失败: {e}")
        
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
            print(f"     失败: {e}")
        
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
            print(f"     失败: {e}")
        
        # 4. 红利低波50指数成分股
        print("  - 获取红利低波50成分股...")
        try:
            import akshare as ak
            # 中证红利低波50指数 H30269
            df = ak.index_stock_cons_weight_csindex(symbol="H30269")
            # 只保留前20大权重
            top_weights = df.nlargest(20, '权重')[['成分券代码', '成分券名称', '权重']]
            data['dividend_index'] = {
                'name': '中证红利低波50 (H30269)',
                'top_components': top_weights.to_dict('records')
            }
            print(f"     获取到 {len(top_weights)} 只成分股")
        except Exception as e:
            print(f"     失败: {e}")
        
        # 5. 黄金价格 (AU9999和XAU)
        print("  - 获取黄金价格...")
        try:
            import requests
            headers = {'Referer': 'https://finance.sina.com.cn'}
            
            # AU9999 (上海黄金交易所)
            url_au = "https://hq.sinajs.cn/list=au0"
            r_au = requests.get(url_au, headers=headers, timeout=10)
            if r_au.status_code == 200:
                content = r_au.text.split('"')[1]
                parts = content.split(',')
                if len(parts) >= 3:
                    data['gold']['AU9999'] = {
                        'price': float(parts[2]),
                        'name': 'AU9999'
                    }
                    print(f"     AU9999: {parts[2]}")
            
            # XAU (国际现货黄金)
            url_xau = "https://hq.sinajs.cn/list=hf_GC"
            r_xau = requests.get(url_xau, headers=headers, timeout=10)
            if r_xau.status_code == 200:
                content = r_xau.text.split('"')[1]
                parts = content.split(',')
                if len(parts) >= 3:
                    data['gold']['XAU'] = {
                        'price': float(parts[2]),
                        'name': 'XAU/USD'
                    }
                    print(f"     XAU: {parts[2]}")
        except Exception as e:
            print(f"     失败: {e}")
        
        # 保存数据
        data_path = f"{self.output_dir}/data_{self.date_str}.json"
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   数据已保存: {data_path}")
        
        return data

    def build_prompt(self, data: Dict[str, Any]) -> str:
        """构建提示词 - 只包含数据和框架，不引导AI"""
        a_share = data.get('a_share', {})
        us_stock = data.get('us_stock', {})
        sectors = data.get('sectors', {})
        dividend = data.get('dividend_index', {})
        gold = data.get('gold', {})
        
        sh = a_share.get('上证指数', {})
        sz = a_share.get('深证成指', {})
        cy = a_share.get('创业板指', {})
        
        nasdaq = us_stock.get('纳斯达克', {})
        sp500 = us_stock.get('标普500', {})
        dow = us_stock.get('道琼斯', {})
        
        gainers = sectors.get('top_gainers', [])
        losers = sectors.get('top_losers', [])
        
        dividend_components = dividend.get('top_components', [])
        
        prompt = f"""今日市场数据：

A股指数：
上证指数: {sh.get('price', 0):.2f} ({sh.get('change_pct', 0):+.2f}%)
深证成指: {sz.get('price', 0):.2f} ({sz.get('change_pct', 0):+.2f}%)
创业板指: {cy.get('price', 0):.2f} ({cy.get('change_pct', 0):+.2f}%)

美股指数：
道琼斯: {dow.get('price', 0):,.2f} ({dow.get('change_pct', 0):+.2f}%)
标普500: {sp500.get('price', 0):,.2f} ({sp500.get('change_pct', 0):+.2f}%)
纳斯达克: {nasdaq.get('price', 0):,.2f} ({nasdaq.get('change_pct', 0):+.2f}%)

行业板块涨跌前5：
领涨: {', '.join([f"{g.get('板块名称', '-')}({g.get('涨跌幅', 0):+.2f}%)" for g in (gainers[:5] if gainers else [])])}
领跌: {', '.join([f"{l.get('板块名称', '-')}({l.get('涨跌幅', 0):+.2f}%)" for l in (losers[:5] if losers else [])])}

红利低波50指数成分股（前10大权重）：
{chr(10).join([f"{c.get('成分券代码', '-')} {c.get('成分券名称', '-')} 权重{c.get('权重', 0):.2f}%" for c in (dividend_components[:10] if dividend_components else [])])}

黄金：
AU9999: {gold.get('AU9999', {}).get('price', '-')}元/克
XAU: {gold.get('XAU', {}).get('price', '-')}美元/盎司

请基于以上数据撰写每日市场观察报告，包含：
1. A股大盘分析
2. 美股市场分析  
3. 行业板块分析
4. 红利低波50指数分析（关注其走势和成分股表现）
5. AI板块分析
6. 黄金分析（AU9999和XAU）
7. 资金流向分析
8. 风险提示
9. 配置建议

要求：基于数据给出观点，不要泛泛而谈。"""
        
        return prompt

    def generate_ai_analysis_stream(self, data: Dict[str, Any]) -> Generator[str, None, None]:
        """流式生成AI分析"""
        prompt = self.build_prompt(data)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一位资深券商分析师。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"\n\n[错误: {e}]"

    def save_report(self, content: str) -> str:
        """保存研报"""
        filepath = f"{self.output_dir}/report.md"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath


def main():
    """主函数"""
    print("="*60)
    print(f"每日研报生成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        generator = ReportGenerator()
        data = generator.fetch_all_data()
        
        print("\n生成AI分析（流式输出）...")
        print("-"*60)
        
        ai_content = ""
        for chunk in generator.generate_ai_analysis_stream(data):
            print(chunk, end='', flush=True)
            ai_content += chunk
        
        print("\n" + "-"*60)
        
        # 构建完整报告
        report = f"""# {generator.date_str} 每日市场观察

**数据时间：{data.get('update_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}**

---

## 市场数据

### A股指数
| 指数 | 价格 | 涨跌 |
|------|------|------|
| 上证指数 | {data.get('a_share', {}).get('上证指数', {}).get('price', 0):.2f} | {data.get('a_share', {}).get('上证指数', {}).get('change_pct', 0):+.2f}% |
| 深证成指 | {data.get('a_share', {}).get('深证成指', {}).get('price', 0):.2f} | {data.get('a_share', {}).get('深证成指', {}).get('change_pct', 0):+.2f}% |
| 创业板指 | {data.get('a_share', {}).get('创业板指', {}).get('price', 0):.2f} | {data.get('a_share', {}).get('创业板指', {}).get('change_pct', 0):+.2f}% |

### 美股指数
| 指数 | 价格 | 涨跌 |
|------|------|------|
| 道琼斯 | {data.get('us_stock', {}).get('道琼斯', {}).get('price', 0):,.2f} | {data.get('us_stock', {}).get('道琼斯', {}).get('change_pct', 0):+.2f}% |
| 标普500 | {data.get('us_stock', {}).get('标普500', {}).get('price', 0):,.2f} | {data.get('us_stock', {}).get('标普500', {}).get('change_pct', 0):+.2f}% |
| 纳斯达克 | {data.get('us_stock', {}).get('纳斯达克', {}).get('price', 0):,.2f} | {data.get('us_stock', {}).get('纳斯达克', {}).get('change_pct', 0):+.2f}% |

### 黄金
| 品种 | 价格 |
|------|------|
| AU9999 | {data.get('gold', {}).get('AU9999', {}).get('price', '-')}元/克 |
| XAU | {data.get('gold', {}).get('XAU', {}).get('price', '-')}美元/盎司 |

---

## AI分析

{ai_content}

---

**免责声明**：本报告仅供参考，不构成投资建议。

*生成时间：{datetime.now().strftime('%H:%M:%S')}*
"""
        
        filepath = generator.save_report(report)
        
        print("\n" + "="*60)
        print(f"✅ 研报生成完成: {filepath}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ 失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
