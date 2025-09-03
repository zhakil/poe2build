# 部署指南

## 📖 概述

本指南涵盖PoE2智能构筑生成器的部署策略，包括本地部署、容器化部署、云端部署和生产环境运维。

## 🏠 本地部署

### 开发环境部署

```bash
# 1. 系统要求
# - Python 3.8+
# - 4GB+ RAM
# - 1GB+ 可用磁盘空间
# - 稳定的网络连接

# 2. 克隆项目
git clone https://github.com/zhakil/poe2build.git
cd poe2build

# 3. 创建虚拟环境
python -m venv poe2_env

# Windows
poe2_env\Scripts\activate

# Linux/Mac
source poe2_env/bin/activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 验证安装
python -c "from poe2_real_data_sources import PoE2RealDataOrchestrator; print('部署成功')"

# 6. 运行测试
python poe2_real_data_sources.py
```

### 生产环境配置

```python
# production_config.py
POE2_PRODUCTION_CONFIG = {
    'debug': False,
    'log_level': 'INFO',
    'cache_settings': {
        'default_ttl': 3600,  # 1小时
        'max_cache_size': 1000
    },
    'data_sources': {
        'poe2_scout': {
            'timeout': 15,
            'retry_count': 3,
            'retry_delay': 1
        },
        'poe2db': {
            'timeout': 20,
            'retry_count': 2,
            'retry_delay': 2
        },
        'poe2_ninja': {
            'timeout': 10,
            'retry_count': 3,
            'retry_delay': 1
        }
    },
    'rate_limiting': {
        'requests_per_minute': 60,
        'burst_limit': 10
    }
}
```

### 环境变量配置

```bash
# .env 文件
POE2_ENV=production
POE2_LOG_LEVEL=INFO
POE2_CACHE_TTL=3600
POE2_MAX_WORKERS=4

# 可选的API密钥
POE2_SCOUT_API_KEY=your_api_key_here
POE2_CUSTOM_SOURCE_URL=https://your-custom-api.com

# 监控配置
POE2_METRICS_ENABLED=true
POE2_METRICS_PORT=9090
```

## 🐳 容器化部署

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制需求文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN adduser --disabled-password --gecos '' poe2user
USER poe2user

# 暴露端口（如果需要）
EXPOSE 8080

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from poe2_real_data_sources import PoE2RealDataOrchestrator; PoE2RealDataOrchestrator()" || exit 1

# 启动命令
CMD ["python", "poe2_real_data_sources.py"]
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  poe2-build-generator:
    build: .
    container_name: poe2-build-gen
    ports:
      - "8080:8080"
    environment:
      - POE2_ENV=production
      - POE2_LOG_LEVEL=INFO
      - POE2_CACHE_TTL=3600
    volumes:
      - ./logs:/app/logs
      - ./cache:/app/cache
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "from poe2_real_data_sources import PoE2RealDataOrchestrator; PoE2RealDataOrchestrator()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # 可选：Redis缓存
  redis:
    image: redis:7-alpine
    container_name: poe2-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # 可选：监控
  prometheus:
    image: prom/prometheus:latest
    container_name: poe2-prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    restart: unless-stopped

volumes:
  redis_data:
```

### 构建和运行

```bash
# 构建镜像
docker build -t poe2-build-generator .

# 运行容器
docker run -d \
    --name poe2-build-gen \
    -p 8080:8080 \
    -e POE2_ENV=production \
    poe2-build-generator

# 使用Docker Compose
docker-compose up -d

# 查看日志
docker-compose logs -f poe2-build-generator

# 停止服务
docker-compose down
```

## ☁️ 云端部署

### AWS部署

#### 1. AWS EC2部署

```bash
# 1. 创建EC2实例
aws ec2 run-instances \
    --image-id ami-0abcdef1234567890 \
    --count 1 \
    --instance-type t3.medium \
    --key-name your-key-pair \
    --security-group-ids sg-12345678 \
    --subnet-id subnet-12345678 \
    --user-data file://user-data.sh

# user-data.sh
#!/bin/bash
yum update -y
yum install -y docker git

# 启动Docker
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# 部署应用
git clone https://github.com/zhakil/poe2build.git
cd poe2build
docker build -t poe2-build-generator .
docker run -d -p 80:8080 --name poe2-app poe2-build-generator
```

#### 2. AWS ECS部署

```json
# task-definition.json
{
    "family": "poe2-build-generator",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "512",
    "memory": "1024",
    "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
    "containerDefinitions": [
        {
            "name": "poe2-container",
            "image": "your-account.dkr.ecr.region.amazonaws.com/poe2-build-generator:latest",
            "portMappings": [
                {
                    "containerPort": 8080,
                    "protocol": "tcp"
                }
            ],
            "environment": [
                {
                    "name": "POE2_ENV",
                    "value": "production"
                }
            ],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/poe2-build-generator",
                    "awslogs-region": "us-west-2",
                    "awslogs-stream-prefix": "ecs"
                }
            }
        }
    ]
}
```

#### 3. AWS Lambda部署 (Serverless)

```python
# lambda_handler.py
import json
import boto3
from poe2_real_data_sources import PoE2RealDataOrchestrator

def lambda_handler(event, context):
    """AWS Lambda处理函数"""
    try:
        # 解析请求
        body = json.loads(event.get('body', '{}'))
        
        # 初始化PoE2系统
        orchestrator = PoE2RealDataOrchestrator()
        
        # 生成推荐
        result = orchestrator.create_poe2_build_recommendation(body)
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(result)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'error': str(e),
                'message': '构筑推荐生成失败'
            })
        }

# requirements.txt for Lambda
requests==2.31.0
beautifulsoup4==4.12.0
```

### Azure部署

```yaml
# azure-pipelines.yml
trigger:
- main

pool:
  vmImage: 'ubuntu-latest'

variables:
  containerRegistry: 'youracr.azurecr.io'
  imageRepository: 'poe2-build-generator'
  dockerfilePath: '$(Build.SourcesDirectory)/Dockerfile'
  tag: '$(Build.BuildId)'

stages:
- stage: Build
  displayName: Build and push stage
  jobs:
  - job: Build
    displayName: Build
    steps:
    - task: Docker@2
      displayName: Build and push image
      inputs:
        command: buildAndPush
        repository: $(imageRepository)
        dockerfile: $(dockerfilePath)
        containerRegistry: $(containerRegistry)
        tags: |
          $(tag)
          latest

- stage: Deploy
  displayName: Deploy stage
  dependsOn: Build
  jobs:
  - deployment: Deploy
    displayName: Deploy to Azure Container Instances
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - task: AzureContainerInstances@0
            displayName: 'Create or update container instance'
            inputs:
              azureSubscription: 'your-subscription'
              resourceGroupName: 'poe2-rg'
              location: 'East US'
              containerInstanceName: 'poe2-build-generator'
              imageSource: 'Container Registry'
              azureContainerRegistry: '$(containerRegistry)'
              imageName: '$(imageRepository):$(tag)'
              containerPorts: '8080'
              dnsNameLabel: 'poe2-build-gen-$(Build.BuildId)'
```

### Google Cloud Platform部署

```yaml
# cloudbuild.yaml
steps:
- name: 'gcr.io/cloud-builders/docker'
  args: ['build', '-t', 'gcr.io/PROJECT_ID/poe2-build-generator', '.']

- name: 'gcr.io/cloud-builders/docker'
  args: ['push', 'gcr.io/PROJECT_ID/poe2-build-generator']

- name: 'gcr.io/cloud-builders/gcloud'
  args: ['run', 'deploy', 'poe2-build-generator', 
         '--image', 'gcr.io/PROJECT_ID/poe2-build-generator',
         '--platform', 'managed',
         '--region', 'us-central1',
         '--allow-unauthenticated']
```

## 🔧 生产环境配置

### 负载均衡配置

```nginx
# nginx.conf
upstream poe2_backend {
    server 127.0.0.1:8080;
    server 127.0.0.1:8081;
    server 127.0.0.1:8082;
}

server {
    listen 80;
    server_name poe2build.example.com;
    
    # 重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name poe2build.example.com;
    
    # SSL配置
    ssl_certificate /path/to/ssl/cert.pem;
    ssl_certificate_key /path/to/ssl/private.key;
    
    # 安全头
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # 缓存静态资源
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # 代理API请求
    location /api/ {
        proxy_pass http://poe2_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 30s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # 健康检查
    location /health {
        proxy_pass http://poe2_backend/health;
        access_log off;
    }
}
```

### 进程管理 (Supervisor)

```ini
# /etc/supervisor/conf.d/poe2.conf
[group:poe2]
programs=poe2-worker-1,poe2-worker-2,poe2-worker-3

[program:poe2-worker-1]
command=/path/to/venv/bin/python poe2_real_data_sources.py --port=8080
directory=/path/to/poe2build
user=poe2user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poe2/worker-1.log
environment=POE2_ENV=production,POE2_WORKER_ID=1

[program:poe2-worker-2]
command=/path/to/venv/bin/python poe2_real_data_sources.py --port=8081
directory=/path/to/poe2build
user=poe2user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poe2/worker-2.log
environment=POE2_ENV=production,POE2_WORKER_ID=2

[program:poe2-worker-3]
command=/path/to/venv/bin/python poe2_real_data_sources.py --port=8082
directory=/path/to/poe2build
user=poe2user
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/poe2/worker-3.log
environment=POE2_ENV=production,POE2_WORKER_ID=3
```

### 系统服务 (systemd)

```ini
# /etc/systemd/system/poe2-build-generator.service
[Unit]
Description=PoE2 Build Generator Service
After=network.target
Wants=network.target

[Service]
Type=forking
User=poe2user
Group=poe2user
WorkingDirectory=/opt/poe2build
Environment=POE2_ENV=production
Environment=PYTHONPATH=/opt/poe2build
ExecStart=/opt/poe2build/venv/bin/python poe2_real_data_sources.py --daemon
ExecReload=/bin/kill -HUP $MAINPID
KillMode=mixed
TimeoutStopSec=30
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/poe2build/logs /opt/poe2build/cache

[Install]
WantedBy=multi-user.target
```

## 📊 监控和日志

### 应用监控

```python
# monitoring.py
import psutil
import time
from typing import Dict
from dataclasses import dataclass

@dataclass
class PoE2SystemMetrics:
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: Dict[str, int]
    active_requests: int
    cache_hit_rate: float
    error_rate: float

class PoE2Monitor:
    """PoE2系统监控"""
    
    def __init__(self):
        self.metrics_history = []
        self.start_time = time.time()
    
    def collect_system_metrics(self) -> PoE2SystemMetrics:
        """收集系统指标"""
        # CPU使用率
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # 内存使用率
        memory = psutil.virtual_memory()
        memory_usage = memory.percent
        
        # 磁盘使用率
        disk = psutil.disk_usage('/')
        disk_usage = disk.percent
        
        # 网络IO
        network = psutil.net_io_counters()
        network_io = {
            'bytes_sent': network.bytes_sent,
            'bytes_recv': network.bytes_recv
        }
        
        return PoE2SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            network_io=network_io,
            active_requests=0,  # 从应用获取
            cache_hit_rate=0.0,  # 从缓存系统获取
            error_rate=0.0  # 从日志分析获取
        )
    
    def export_prometheus_metrics(self) -> str:
        """导出Prometheus格式的指标"""
        metrics = self.collect_system_metrics()
        
        prometheus_format = f"""
# HELP poe2_cpu_usage CPU usage percentage
# TYPE poe2_cpu_usage gauge
poe2_cpu_usage {metrics.cpu_usage}

# HELP poe2_memory_usage Memory usage percentage
# TYPE poe2_memory_usage gauge
poe2_memory_usage {metrics.memory_usage}

# HELP poe2_disk_usage Disk usage percentage
# TYPE poe2_disk_usage gauge
poe2_disk_usage {metrics.disk_usage}

# HELP poe2_uptime_seconds Application uptime in seconds
# TYPE poe2_uptime_seconds counter
poe2_uptime_seconds {time.time() - self.start_time}
"""
        return prometheus_format.strip()
```

### 日志聚合

```python
# logging_config.py
import logging
import logging.handlers
import json
from datetime import datetime

class PoE2JSONFormatter(logging.Formatter):
    """JSON格式的日志格式化器"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_entry['exception'] = self.formatException(record.exc_info)
        
        # 添加自定义字段
        if hasattr(record, 'request_id'):
            log_entry['request_id'] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        
        return json.dumps(log_entry)

def setup_production_logging():
    """设置生产环境日志"""
    
    # 根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # JSON格式化器
    json_formatter = PoE2JSONFormatter()
    
    # 文件处理器 - 应用日志
    app_handler = logging.handlers.RotatingFileHandler(
        'logs/poe2_app.log',
        maxBytes=100*1024*1024,  # 100MB
        backupCount=10
    )
    app_handler.setLevel(logging.INFO)
    app_handler.setFormatter(json_formatter)
    
    # 文件处理器 - 错误日志
    error_handler = logging.handlers.RotatingFileHandler(
        'logs/poe2_error.log',
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(json_formatter)
    
    # 系统日志处理器 (Linux/Mac)
    try:
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        syslog_handler.setLevel(logging.WARNING)
        syslog_formatter = logging.Formatter(
            'poe2-build-generator: %(levelname)s %(message)s'
        )
        syslog_handler.setFormatter(syslog_formatter)
        root_logger.addHandler(syslog_handler)
    except:
        pass  # Windows或其他系统不支持syslog
    
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
```

### Prometheus监控配置

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "poe2_rules.yml"

scrape_configs:
  - job_name: 'poe2-build-generator'
    static_configs:
      - targets: ['localhost:9090']
    metrics_path: '/metrics'
    scrape_interval: 30s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - localhost:9093

# poe2_rules.yml
groups:
  - name: poe2-alerts
    rules:
      - alert: PoE2HighCPUUsage
        expr: poe2_cpu_usage > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "PoE2服务CPU使用率过高"
          description: "CPU使用率超过80% 持续5分钟"
      
      - alert: PoE2HighMemoryUsage
        expr: poe2_memory_usage > 90
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "PoE2服务内存使用率过高"
          description: "内存使用率超过90% 持续2分钟"
      
      - alert: PoE2ServiceDown
        expr: up{job="poe2-build-generator"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "PoE2服务不可用"
          description: "PoE2构筑生成服务已停止响应"
```

## 🔒 安全配置

### 网络安全

```python
# security_middleware.py
import hashlib
import hmac
import time
from flask import Flask, request, abort
from functools import wraps

class PoE2SecurityMiddleware:
    """PoE2安全中间件"""
    
    def __init__(self, app: Flask, secret_key: str):
        self.app = app
        self.secret_key = secret_key
        self.rate_limits = {}
        
    def rate_limit(self, max_requests: int = 60, window: int = 60):
        """速率限制装饰器"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                client_ip = request.remote_addr
                current_time = time.time()
                
                # 清理过期记录
                if client_ip in self.rate_limits:
                    self.rate_limits[client_ip] = [
                        timestamp for timestamp in self.rate_limits[client_ip]
                        if current_time - timestamp < window
                    ]
                else:
                    self.rate_limits[client_ip] = []
                
                # 检查速率限制
                if len(self.rate_limits[client_ip]) >= max_requests:
                    abort(429)  # Too Many Requests
                
                # 记录请求
                self.rate_limits[client_ip].append(current_time)
                
                return f(*args, **kwargs)
            return wrapper
        return decorator
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """验证请求签名"""
        expected_signature = hmac.new(
            self.secret_key.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
```

### HTTPS配置

```bash
# 使用Let's Encrypt获取SSL证书
# 安装certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d poe2build.example.com

# 自动续期
sudo crontab -e
# 添加: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🚀 性能优化

### 缓存层配置

```python
# redis_cache.py
import redis
import json
import time
from typing import Optional, Dict, Any

class PoE2RedisCache:
    """Redis缓存实现"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.stats = {'hits': 0, 'misses': 0}
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                self.stats['hits'] += 1
                return json.loads(cached_data)
            else:
                self.stats['misses'] += 1
                return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, data: Dict[str, Any], ttl: int = 3600):
        """设置缓存数据"""
        try:
            self.redis_client.setex(
                key,
                ttl,
                json.dumps(data, default=str)
            )
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def delete(self, key: str):
        """删除缓存"""
        try:
            self.redis_client.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = self.stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': hit_rate,
            'redis_info': self.redis_client.info()
        }
```

### CDN配置

```javascript
// cdn_config.js - CloudFlare配置示例
const CDN_CONFIG = {
  // 缓存规则
  cacheRules: [
    {
      pattern: '/api/static/*',
      ttl: 86400, // 24小时
      browserTtl: 3600 // 1小时
    },
    {
      pattern: '/api/builds/*',
      ttl: 1800, // 30分钟
      browserTtl: 300 // 5分钟
    }
  ],
  
  // 压缩设置
  compression: {
    enabled: true,
    types: ['text/html', 'application/json', 'text/css', 'application/javascript']
  },
  
  // 安全设置
  security: {
    ddosProtection: true,
    wafEnabled: true,
    botManagement: true
  }
};
```

## 🔄 备份和恢复

### 自动备份脚本

```bash
#!/bin/bash
# backup_poe2.sh

# 配置
BACKUP_DIR="/var/backups/poe2"
APP_DIR="/opt/poe2build"
S3_BUCKET="poe2-backups"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR/$DATE

# 备份应用代码
tar -czf $BACKUP_DIR/$DATE/poe2_app.tar.gz -C $APP_DIR .

# 备份配置文件
cp -r $APP_DIR/config $BACKUP_DIR/$DATE/

# 备份日志 (最近7天)
find $APP_DIR/logs -name "*.log" -mtime -7 | tar -czf $BACKUP_DIR/$DATE/poe2_logs.tar.gz -T -

# 备份缓存数据 (如果使用Redis)
redis-cli --rdb $BACKUP_DIR/$DATE/dump.rdb

# 上传到云存储
aws s3 sync $BACKUP_DIR/$DATE s3://$S3_BUCKET/$DATE/

# 清理本地旧备份 (保留30天)
find $BACKUP_DIR -type d -mtime +30 -exec rm -rf {} \;

echo "备份完成: $DATE"
```

### 灾难恢复计划

```python
# disaster_recovery.py
import os
import subprocess
import logging
from typing import Dict, List

class PoE2DisasterRecovery:
    """PoE2灾难恢复系统"""
    
    def __init__(self, backup_location: str):
        self.backup_location = backup_location
        self.logger = logging.getLogger(__name__)
    
    def restore_from_backup(self, backup_date: str) -> bool:
        """从备份恢复系统"""
        try:
            backup_path = f"{self.backup_location}/{backup_date}"
            
            # 1. 停止服务
            self.logger.info("停止PoE2服务...")
            subprocess.run(["sudo", "systemctl", "stop", "poe2-build-generator"])
            
            # 2. 恢复应用代码
            self.logger.info("恢复应用代码...")
            subprocess.run([
                "tar", "-xzf", f"{backup_path}/poe2_app.tar.gz",
                "-C", "/opt/poe2build"
            ])
            
            # 3. 恢复配置
            self.logger.info("恢复配置文件...")
            subprocess.run([
                "cp", "-r", f"{backup_path}/config/*",
                "/opt/poe2build/config/"
            ])
            
            # 4. 恢复缓存数据 (如果需要)
            if os.path.exists(f"{backup_path}/dump.rdb"):
                self.logger.info("恢复Redis缓存...")
                subprocess.run([
                    "cp", f"{backup_path}/dump.rdb",
                    "/var/lib/redis/dump.rdb"
                ])
                subprocess.run(["sudo", "systemctl", "restart", "redis"])
            
            # 5. 重启服务
            self.logger.info("重启PoE2服务...")
            subprocess.run(["sudo", "systemctl", "start", "poe2-build-generator"])
            
            # 6. 验证服务状态
            result = subprocess.run([
                "sudo", "systemctl", "is-active", "poe2-build-generator"
            ], capture_output=True, text=True)
            
            if result.stdout.strip() == "active":
                self.logger.info("系统恢复成功")
                return True
            else:
                self.logger.error("系统恢复失败")
                return False
                
        except Exception as e:
            self.logger.error(f"恢复过程出错: {e}")
            return False
    
    def health_check(self) -> Dict[str, str]:
        """系统健康检查"""
        health_status = {}
        
        # 检查服务状态
        services = ["poe2-build-generator", "nginx", "redis"]
        for service in services:
            result = subprocess.run([
                "sudo", "systemctl", "is-active", service
            ], capture_output=True, text=True)
            health_status[service] = result.stdout.strip()
        
        # 检查磁盘空间
        result = subprocess.run(["df", "-h", "/"], capture_output=True, text=True)
        health_status["disk_space"] = result.stdout.split('\n')[1]
        
        return health_status
```

---

**总结**: 这个部署指南涵盖了从简单本地部署到复杂云端生产环境的完整部署策略。通过合适的部署方式和运维配置，可以确保PoE2构筑生成器的高可用性、高性能和安全性。