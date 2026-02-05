import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from openai import OpenAI

# --- 关键：解决包内引用问题 ---
try:
    from .data_fetcher import data_fetcher
    from .technical_analysis import technical_analyzer
except (ImportError, ValueError):
    # 兼容本地直接运行 python src/report_generator.py
    import sys
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from data_fetcher import data_fetcher
    from technical_analysis import technical_analyzer


class ReportGenerator:
    def __init__(self):
        self.output_dir = "./reports"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def fetch_all_data(self) -> Dict[str, Any]:
        """获取全市场聚合数据"""
        # 这里调用 data_fetcher 里的方法
        return {
            "timestamp": datetime.now().isoformat(),
            "market_status": "Data fetched successfully"
        }

    def generate_report(self, data: Dict[str, Any]) -> str:
        """调用 LLM (如 OpenAI/DeepSeek) 生成 Markdown 文本"""
        # 实际代码中这里应包含 prompt 和 api 调用
        date_str = datetime.now().strftime('%Y-%m-%d')
        report = f"""# 每日金融市场观察 ({date_str})
        
## 1. 市场核心走势分析
今日市场表现数据点：{data.get('timestamp')}

## 2. 技术面解读
- A股处于关键支撑位
- 纳斯达克表现强劲

## 3. 投资建议
*策略仅供参考，不构成投资建议。*
"""
        return report

    def save_report(self, content: str) -> str:
        """保存为 Markdown 文件"""
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        path = os.path.join(self.output_dir, filename)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path
