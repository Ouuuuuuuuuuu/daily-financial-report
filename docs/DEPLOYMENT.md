# Streamlit 部署指南

## 方案一: Streamlit Cloud (推荐，免费)

### 步骤 1: 准备GitHub仓库

```bash
# 初始化Git仓库
cd financial-report-system
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: Daily financial report system"

# 创建GitHub仓库并推送
git remote add origin https://github.com/yourusername/financial-report.git
git push -u origin main
```

### 步骤 2: 部署到 Streamlit Cloud

1. 访问 [share.streamlit.io](https://share.streamlit.io)
2. 使用GitHub账号登录
3. 点击 "New app"
4. 选择你的仓库和分支
5. 主文件路径填写: `app.py`
6. 点击 "Deploy"

### 步骤 3: 配置 Secrets

1. 在App页面点击 "⋮" → "Settings"
2. 选择 "Secrets" 标签
3. 添加以下配置:

```toml
[openai]
api_key = "your-openai-api-key"

[general]
timezone = "Asia/Shanghai"
```

### 步骤 4: 更新代码读取 Secrets

创建 `.streamlit/secrets.toml` (本地):
```toml
[openai]
api_key = "your-openai-api-key"
```

在 `app.py` 中添加:
```python
import streamlit as st

# 从Secrets读取API密钥
openai_api_key = st.secrets.get("openai", {}).get("api_key")
if openai_api_key:
    os.environ['OPENAI_API_KEY'] = openai_api_key
```

---

## 方案二: 自有服务器部署

### Docker 部署

```bash
# 构建镜像
docker build -t financial-report:latest .

# 运行容器
docker run -d \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your-api-key \
  -v $(pwd)/reports:/app/reports \
  -v $(pwd)/logs:/app/logs \
  --name financial-report \
  --restart unless-stopped \
  financial-report:latest
```

### Docker Compose

创建 `docker-compose.yml`:

```yaml
version: '3.8'

services:
  financial-report:
    build: .
    ports:
      - "8501:8501"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./reports:/app/reports
      - ./logs:/app/logs
      - ./data:/app/data
    restart: unless-stopped
    
  # 可选：使用Ofelia定时任务
  scheduler:
    image: mcuadros/ofelia:latest
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      ofelia.job-run.report.schedule: "0 12 * * 1-5"
      ofelia.job-run.report.container: "financial-report"
      ofelia.job-run.report.command: "python cron_job.py --run-once"
```

运行:
```bash
docker-compose up -d
```

---

## 方案三: 云平台部署

### 阿里云 ECS

```bash
# 1. 购买ECS实例 (推荐2核4G)
# 2. 安装Docker
curl -fsSL https://get.docker.com | bash

# 3. 克隆项目
git clone https://github.com/yourusername/financial-report.git
cd financial-report

# 4. 创建环境变量文件
echo "OPENAI_API_KEY=your-key" > .env

# 5. 启动
docker-compose up -d

# 6. 配置安全组，开放8501端口
```

### 腾讯云 CloudBase

1. 登录 [CloudBase控制台](https://console.cloud.tencent.com/tcb)
2. 创建新环境
3. 选择 "Web应用"
4. 上传代码或连接Git仓库
5. 配置环境变量

### Vercel (Serverless)

创建 `vercel.json`:
```json
{
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

---

## 方案四: 内网穿透 (开发测试)

### 使用 ngrok

```bash
# 1. 安装 ngrok
# https://ngrok.com/download

# 2. 注册并获取authtoken
ngrok authtoken your-token

# 3. 启动Streamlit
streamlit run app.py &

# 4. 启动ngrok
ngrok http 8501

# 5. 获取公网URL
# Forwarding  https://xxxx.ngrok-free.app -> http://localhost:8501
```

### 使用 Cloudflare Tunnel

```bash
# 1. 安装 cloudflared
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/

# 2. 登录
cloudflared tunnel login

# 3. 创建隧道
cloudflared tunnel create financial-report

# 4. 运行
cloudflared tunnel run financial-report
```

---

## 定时任务配置

### 服务器Cron

```bash
# 编辑crontab
crontab -e

# 添加行（工作日12:00）
0 12 * * 1-5 cd /path/to/financial-report && docker-compose exec -T financial-report python cron_job.py --run-once >> logs/cron.log 2>&1
```

### 使用Systemd Timer

创建 `/etc/systemd/system/financial-report.service`:
```ini
[Unit]
Description=Generate Daily Financial Report

[Service]
Type=oneshot
WorkingDirectory=/path/to/financial-report
ExecStart=/usr/bin/docker-compose exec -T financial-report python cron_job.py --run-once
```

创建 `/etc/systemd/system/financial-report.timer`:
```ini
[Unit]
Description=Run Financial Report Generator at 12:00 on weekdays

[Timer]
OnCalendar=Mon..Fri 12:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

启用:
```bash
sudo systemctl daemon-reload
sudo systemctl enable financial-report.timer
sudo systemctl start financial-report.timer
```

---

## 域名和HTTPS

### 使用Nginx反向代理

```nginx
server {
    listen 80;
    server_name report.yourdomain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Let's Encrypt SSL

```bash
# 安装certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d report.yourdomain.com
```

---

## 监控和日志

### 查看日志

```bash
# Docker日志
docker logs -f financial-report

# 定时任务日志
tail -f logs/cron.log

# 系统日志
journalctl -u financial-report.timer -f
```

### 健康检查

添加 `healthcheck.py`:
```python
import requests
import sys

response = requests.get("http://localhost:8501/healthz")
if response.status_code == 200:
    print("✓ Service is healthy")
    sys.exit(0)
else:
    print("✗ Service is unhealthy")
    sys.exit(1)
```

---

## 备份策略

```bash
# 备份报告
0 0 * * * tar -czf backups/reports-$(date +\%Y\%m\%d).tar.gz reports/

# 备份数据
0 0 * * * tar -czf backups/data-$(date +\%Y\%m\%d).tar.gz data/

# 保留30天
0 0 * * * find backups/ -name "*.tar.gz" -mtime +30 -delete
```

---

## 故障排查

| 问题 | 解决方案 |
|------|----------|
| 端口被占用 | `lsof -i :8501` 查看并关闭 |
| 内存不足 | 增加swap或升级服务器配置 |
| API配额用完 | 检查API使用量，考虑升级套餐 |
| 数据获取失败 | 检查网络，查看 `logs/cron.log` |
| 容器无法启动 | `docker logs financial-report` 查看错误 |

---

## 参考

- [Streamlit Deployment Guide](https://docs.streamlit.io/streamlit-community-cloud/deploy-your-app)
- [Docker Documentation](https://docs.docker.com/)
- [Systemd Timers](https://wiki.archlinux.org/title/Systemd/Timers)
