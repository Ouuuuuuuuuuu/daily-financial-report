# 项目结构

```
financial-report-system/
├── src/                          # 核心源代码
│   ├── __init__.py              # 包初始化
│   ├── data_fetcher.py          # 数据获取模块 (akshare, yfinance)
│   ├── technical_analysis.py    # 技术指标计算模块
│   ├── report_generator.py      # LLM研报生成器
│   └── utils.py                 # 工具函数
│
├── skills/financial-report/     # 技能文件
│   └── SKILL.md                 # 技能文档
│
├── docs/                        # 文档
│   └── DEPLOYMENT.md            # 部署指南
│
├── data/                        # 数据存储目录
├── reports/                     # 生成报告目录
├── logs/                        # 日志目录
│
├── app.py                       # Streamlit主应用
├── cron_job.py                  # 定时任务脚本
│
├── config.yaml                  # 配置文件
├── requirements.txt             # Python依赖
├── Dockerfile                   # Docker镜像配置
├── docker-compose.yml           # Docker Compose配置
│
├── .env.example                 # 环境变量示例
├── .gitignore                   # Git忽略规则
└── README.md                    # 项目说明
```

## 文件说明

### 核心模块

| 文件 | 功能 | 关键类/函数 |
|------|------|-------------|
| `data_fetcher.py` | 金融数据获取 | `DataFetcher` - A股/美股/黄金/AI/红利数据 |
| `technical_analysis.py` | 技术指标计算 | `TechnicalAnalyzer` - RSI/MACD/均线/KDJ等 |
| `report_generator.py` | 研报生成 | `ReportGenerator` - LLM生成券商风格研报 |
| `utils.py` | 工具函数 | 格式化、验证、颜色输出等 |

### 应用入口

| 文件 | 用途 |
|------|------|
| `app.py` | Streamlit Web界面 |
| `cron_job.py` | 定时任务脚本 |

### 配置

| 文件 | 说明 |
|------|------|
| `config.yaml` | 数据源、API密钥、技术指标参数配置 |
| `requirements.txt` | Python包依赖 |
| `.env.example` | 环境变量模板 |

### 部署

| 文件 | 说明 |
|------|------|
| `Dockerfile` | Docker镜像构建 |
| `docker-compose.yml` | 容器编排配置 |
| `docs/DEPLOYMENT.md` | 详细部署指南 |

## 数据流

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Data Sources│────▶│  DataFetcher │────▶│  Technical   │
│  akshare     │     │              │     │  Analysis    │
│  yfinance    │     │  A股/美股/   │     │              │
│  新浪财经     │     │  黄金/AI等   │     │  RSI/MACD    │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                                                ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Report.md   │◀────│ Save Report  │◀────│ LLM Generate │
└─────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                                          ┌─────┴─────┐
                                          │  OpenAI   │
                                          │  API      │
                                          └───────────┘
```

## 使用流程

1. **数据获取** → `data_fetcher.py`
2. **指标计算** → `technical_analysis.py`
3. **研报生成** → `report_generator.py` (调用LLM)
4. **结果保存** → `reports/YYYYMMMDD.md`
5. **Web展示** → `app.py` (Streamlit)

## 扩展指南

添加新数据源:
1. 在 `data_fetcher.py` 添加新方法
2. 在 `config.yaml` 配置参数
3. 在 `report_generator.py` 集成数据

添加新指标:
1. 在 `technical_analysis.py` 添加计算方法
2. 在 `calculate_all_indicators()` 中调用
3. 更新 `get_latest_signals()` 输出信号
