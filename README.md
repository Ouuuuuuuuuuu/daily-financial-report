# 每日研报系统

自动化生成每日市场研报系统，包括A股、纳斯达克、红利板块、AI板块和黄金板块分析。

## 功能特性

- 📊 A股大盘实时行情分析
- 📈 纳斯达克期货/隔夜行情分析
- 💰 红利板块表现追踪
- 🤖 人工智能板块热点分析
- 🪙 黄金价格走势分析
- 🤖 LLM自动生成研报内容
- 🌐 Streamlit可视化展示

## 项目结构

```
financial-report-system/
├── src/                    # 源代码
│   ├── data_fetcher.py     # 数据获取模块
│   ├── technical_analysis.py # 技术指标计算
│   ├── report_generator.py # 研报生成器
│   └── utils.py            # 工具函数
├── data/                   # 数据存储
├── reports/                # 生成报告
├── docs/                   # 文档
├── app.py                  # Streamlit主应用
├── requirements.txt        # 依赖
├── config.yaml             # 配置文件
└── cron_job.py            # 定时任务脚本
```

## 安装使用

```bash
# 1. 克隆仓库
git clone <your-repo>
cd financial-report-system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置API密钥
# 编辑 config.yaml 文件

# 4. 运行一次性报告生成
python src/report_generator.py

# 5. 启动Streamlit
streamlit run app.py
```

## 定时任务

使用cron设置每个交易日12:00运行：

```bash
# 编辑crontab
crontab -e

# 添加以下行
0 12 * * 1-5 cd /path/to/financial-report-system && python cron_job.py >> logs/cron.log 2>&1
```

## 配置说明

在 `config.yaml` 中配置：
- OpenAI/DeepSeek API密钥（用于LLM生成研报）
- Tushare Token（可选，用于高级A股数据）
- 其他数据源配置

## License

MIT
