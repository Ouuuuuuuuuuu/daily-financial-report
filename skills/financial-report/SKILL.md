# 每日研报系统技能文档

## 技能名称

金融研报自动化生成

## 技能描述

使用Python构建自动化系统，每个交易日中午12点生成一份包含A股、纳斯达克、红利板块、AI板块和黄金板块分析的专业券商风格研报。

---

## 一、数据源配置

### 1.1 免费数据源

#### A股实时行情 - akshare
```python
import akshare as ak

# 主要指数
stock_zh_index_spot_em()  # 东方财富指数行情

# 个股历史数据
stock_zh_a_hist(symbol="000001", period="daily")

# 板块资金流向
stock_sector_fund_flow_rank(indicator="今日")

# 财经新闻
stock_news_em()
```

#### 纳斯达克数据 - yfinance
```python
import yfinance as yf

# 纳斯达克指数
^IXIC  # 纳斯达克综合指数
NQ=F   # 纳斯达克100期货
QQQ    # 纳斯达克100 ETF

# 科技龙头股
NVDA, AMD, AVGO, CRM, PLTR, SMCI
```

#### 黄金价格
```python
# COMEX黄金期货
GC=F

# 国内黄金ETF
518880.SS  # 黄金ETF
```

### 1.2 可选付费数据源

| 数据源 | 用途 | 费用 | 注册链接 |
|--------|------|------|----------|
| Tushare | A股高级数据 | 积分制 | tushare.pro |
| Alpha Vantage | 全球股票 | 免费500次/天 | alphavantage.co |
| OpenAI API | LLM生成研报 | 按量付费 | openai.com |

### 1.3 API密钥配置

编辑 `config.yaml`:
```yaml
openai:
  api_key: "your-api-key"
  base_url: "https://api.openai.com/v1"
  model: "gpt-4"

data_sources:
  a_share:
    source: "akshare"
    tushare_token: ""  # 可选
```

---

## 二、数据获取脚本

### 2.1 完整数据获取代码

```python
from data_fetcher import data_fetcher
from technical_analysis import technical_analyzer
import pandas as pd

# 获取A股指数
a_share_index = data_fetcher.get_a_share_index()

# 获取纳斯达克
nasdaq = data_fetcher.get_nasdaq_overview()

# 获取黄金价格
gold = data_fetcher.get_gold_price()

# 获取AI板块
ai_sector = data_fetcher.get_ai_sector_a_share()
ai_leaders = data_fetcher.get_ai_leaders()

# 获取红利板块
dividend_etfs = data_fetcher.get_dividend_etfs()

# 获取资金流向
sector_flow = data_fetcher.get_sector_flow()

# 获取新闻
news = data_fetcher.get_financial_news(10)
```

### 2.2 技术指标计算

```python
# 获取个股数据
df = data_fetcher.get_a_share_daily("000001", days=60)

# 计算所有技术指标
df = technical_analyzer.calculate_all_indicators(df)

# 获取最新信号
signals = technical_analyzer.get_latest_signals(df)
# 返回: {'RSI': '超买', 'MACD': '多头', 'KDJ': '震荡区', ...}

# 计算支撑位/阻力位
support, resistance = technical_analyzer.calculate_support_resistance(df)

# 判断趋势强度
trend = technical_analyzer.calculate_trend_strength(df)
```

### 2.3 支持的指标

| 指标 | 函数 | 说明 |
|------|------|------|
| MA | calculate_ma() | 移动平均线 (5/10/20/60日) |
| EMA | calculate_ema() | 指数移动平均线 |
| RSI | calculate_rsi() | 相对强弱指数 |
| MACD | calculate_macd() | 异同移动平均线 |
| BOLL | calculate_bollinger() | 布林带 |
| KDJ | calculate_kdj() | 随机指标 |
| ATR | calculate_atr() | 平均真实波幅 |
| OBV | calculate_obv() | 能量潮 |

---

## 三、研报生成Prompt模板

### 3.1 基础Prompt结构

```
你是一位资深证券分析师，请根据以下市场数据，撰写一份专业的每日市场研报。

## 报告日期: {date}

### 一、市场数据概览

**A股主要指数:**
{index_data}

**隔夜美股:**
{nasdaq_data}

**黄金价格:**
{gold_data}

**重要财经新闻:**
{news_summary}

### 二、研报格式要求

请按照以下格式撰写研报：
...
```

### 3.2 券商研报标准格式

```markdown
# [{日期}] 每日市场观察

**分析师：** 策略研究团队  
**报告日期：** {日期}  
**投资评级：** 震荡/看好/谨慎

---

## 【核心观点】
- 观点1
- 观点2
- 观点3

---

## 【市场行情回顾】
### 1. A股市场
### 2. 隔夜美股

---

## 【板块专题分析】
### 3. 红利板块
### 4. 人工智能板块
### 5. 黄金板块

---

## 【技术面分析】

---

## 【资金流向】

---

## 【风险提示】

---

## 【配置建议】

---

**免责声明：** 本报告仅供参考，不构成投资建议。
```

### 3.3 LLM调用代码

```python
from openai import OpenAI

client = OpenAI(api_key="your-key")

response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "你是一位经验丰富的证券分析师..."},
        {"role": "user", "content": prompt}
    ],
    temperature=0.7,
    max_tokens=4000
)

report = response.choices[0].message.content
```

---

## 四、部署指南

### 4.1 本地部署

```bash
# 1. 克隆仓库
git clone <your-repo>
cd financial-report-system

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置API密钥
# 编辑 config.yaml 文件

# 5. 测试运行
python src/report_generator.py

# 6. 启动Streamlit
streamlit run app.py
```

### 4.2 Streamlit部署

**Streamlit Cloud (免费)**

1. 将代码推送到GitHub
2. 访问 share.streamlit.io
3. 连接GitHub仓库
4. 设置Secrets (API密钥):
   ```
   OPENAI_API_KEY = "your-key"
   ```
5. 部署完成

**Requirements:**
```
streamlit
akshare
yfinance
pandas
numpy
plotly
openai
pyyaml
```

### 4.3 Cron定时任务配置

**Linux/Mac:**

```bash
# 编辑crontab
crontab -e

# 每个工作日12:00运行
0 12 * * 1-5 cd /path/to/financial-report-system && python cron_job.py >> logs/cron.log 2>&1

# 或使用更灵活的Python调度
0 12 * * 1-5 cd /path/to/financial-report-system && python -c "from cron_job import run_daily_report; run_daily_report()" >> logs/cron.log 2>&1
```

**Windows (任务计划程序):**

```powershell
# 创建任务
schtasks /create /tn "DailyReport" /tr "python C:\path\to\cron_job.py" /sc weekly /d MON,TUE,WED,THU,FRI /st 12:00
```

### 4.4 Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

```bash
# 构建镜像
docker build -t financial-report .

# 运行容器
docker run -p 8501:8501 -e OPENAI_API_KEY=your-key financial-report
```

---

## 五、项目结构

```
financial-report-system/
├── src/                          # 源代码
│   ├── __init__.py
│   ├── data_fetcher.py           # 数据获取
│   ├── technical_analysis.py     # 技术指标
│   ├── report_generator.py       # 研报生成
│   └── utils.py                  # 工具函数
├── data/                         # 数据存储
├── reports/                      # 生成报告
├── logs/                         # 日志文件
├── app.py                        # Streamlit应用
├── cron_job.py                   # 定时任务
├── config.yaml                   # 配置文件
├── requirements.txt              # 依赖
└── README.md                     # 说明文档
```

---

## 六、常见问题

### Q: 数据获取失败怎么办？

检查网络连接和API限制：
```python
# 测试akshare
import akshare as ak
print(ak.stock_zh_index_spot_em())

# 测试yfinance
import yfinance as yf
print(yf.Ticker("^IXIC").info)
```

### Q: LLM API调用失败？

检查API密钥和余额：
```bash
export OPENAI_API_KEY="your-key"
python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

### Q: 如何添加新的数据源？

在 `data_fetcher.py` 中添加新方法，保持返回格式一致。

---

## 七、参考资源

- [akshare文档](https://www.akshare.xyz/)
- [yfinance文档](https://pypi.org/project/yfinance/)
- [Streamlit文档](https://docs.streamlit.io/)
- [OpenAI API](https://platform.openai.com/)

---

## 八、更新日志

**v1.0.0** (2025-02-04)
- 初始版本
- 支持A股、纳斯达克、黄金、AI板块、红利板块
- Streamlit前端展示
- Cron定时任务支持
