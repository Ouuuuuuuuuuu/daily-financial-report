# 快速开始指南

## 5分钟快速启动

### 1. 安装依赖 (1分钟)

```bash
cd financial-report-system
pip install -r requirements.txt
```

### 2. 配置API密钥 (1分钟)

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的OpenAI API密钥
nano .env  # 或使用任何文本编辑器
```

```
OPENAI_API_KEY=sk-your-api-key-here
```

### 3. 测试数据获取 (1分钟)

```bash
python -c "from src.data_fetcher import data_fetcher; print(data_fetcher.get_a_share_index())"
```

### 4. 生成第一份研报 (2分钟)

```bash
python src/report_generator.py
```

生成的研报将保存在 `reports/daily_report_YYYYMMDD.md`

### 5. 启动Web界面 (可选)

```bash
streamlit run app.py
```

浏览器打开 http://localhost:8501

---

## 目录结构速览

```
.
├── src/                    # 核心代码
├── reports/                # 生成的研报
├── app.py                  # Web界面
├── cron_job.py            # 定时任务
└── config.yaml            # 配置文件
```

---

## 常用命令

```bash
# 生成研报
python src/report_generator.py

# 启动Web界面
streamlit run app.py

# 运行定时任务（测试）
python cron_job.py --run-once

# 强制运行（非交易日）
python cron_job.py --run-once --force

# Docker启动
docker-compose up -d
```

---

## 配置定时任务

### Linux/Mac

```bash
# 编辑crontab
crontab -e

# 添加以下行（每个工作日12:00运行）
0 12 * * 1-5 cd /path/to/financial-report-system && python cron_job.py >> logs/cron.log 2>&1
```

### Windows

使用任务计划程序，创建每日12:00运行的任务。

---

## 数据源说明

| 市场 | 数据源 | 免费额度 |
|------|--------|----------|
| A股 | akshare | 免费 |
| 美股 | yfinance | 免费 |
| 黄金 | yfinance | 免费 |
| 研报生成 | OpenAI | 按量付费 |

---

## 故障排查

| 问题 | 解决 |
|------|------|
| API错误 | 检查 `.env` 中的API密钥 |
| 数据为空 | 检查网络连接，确认是非交易时间 |
| 端口冲突 | 修改 `app.py` 端口或使用 `streamlit run app.py --server.port 8502` |

---

## 下一步

- 阅读 [SKILL.md](skills/financial-report/SKILL.md) 了解完整功能
- 查看 [DEPLOYMENT.md](docs/DEPLOYMENT.md) 了解部署方案
- 自定义 `config.yaml` 调整参数
