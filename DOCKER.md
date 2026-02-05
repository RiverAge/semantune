# Docker 单容器部署指南

## 概述

本方案使用单个Python容器同时托管后端API和前端静态文件，所有数据集中在一个目录。

## 快速开始

### 方式一：使用本地目录（推荐）

```bash
# 1. 构建镜像
docker build -t semantune .

# 2. 运行容器（只需挂载一个目录！）
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  semantune

# 3. 访问应用
# 前端: http://localhost:8000/
# API文档: http://localhost:8000/docs
```

Windows PowerShell：

```powershell
docker build -t semantune .
docker run -d --name semantune -p 8000:8000 `
  -v "${PWD}/semantune-data:/app/data" `
  semantune
```

### 方式二：使用 Docker 卷

```bash
# 1. 构建镜像
docker build -t semantune .

# 2. 运行容器（Docker 自动管理数据卷）
docker run -d --name semantune -p 8000:8000 \
  -v semantune-data:/app/data \
  semantune
```

### 方式三：使用绝对路径

```bash
docker run -d --name semantune -p 8000:8000 \
  -v /home/user/semantune-data:/app/data \
  semantune
```

## 数据目录结构

容器内的 `/app/data` 目录结构：

```
/app/data/
├── .env                # API Key 等配置（前端设置后自动生成）
├── navidrome.db        # Navidrome 数据库
├── semantic.db         # 语义数据库
├── config/             # YAML 配置文件
│   ├── recommend_config.yaml
│   └── tagging_config.yaml
├── logs/               # 日志文件
│   ├── api.log
│   ├── tagging.log
│   └── ...
└── exports/            # 导出的数据
    └── export_*/
```

**所有数据都这一个目录里！**

## 常用命令

### 查看日志

```bash
# 查看容器日志
docker logs semantune

# 实时跟踪
docker logs -f semantune

# 查看数据目录中的日志
cat semantune-data/logs/api.log
```

### 停止/重启

```bash
# 停止
docker stop semantune

# 重启
docker restart semantune

# 删除容器（数据保留）
docker stop semantune && docker rm semantune
```

### 重新构建

```bash
# 停止并删除容器
docker stop semantune && docker rm semantune

# 重新构建镜像
docker build -t semantune .

# 运行新容器
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  semantune
```

### 进入容器

```bash
docker exec -it semantune bash
```

### 备份数据

```bash
# 备份整个数据目录
tar -czf semantune-backup-$(date +%Y%m%d).tar.gz semantune-data/

# 或者使用 Docker 卷备份
docker run --rm -v semantune-data:/data alpine tar -czf - /data > backup.tar.gz
```

### 恢复数据

```bash
# 解压备份
tar -xzf semantune-backup-20240205.tar.gz

# 重启容器
docker restart semantune
```

## API Key 配置

**不需要在启动时提供 API Key！**

访问 http://localhost:8000/ 后，在前端设置页面输入 API Key 即可。

- API Key 保存在 `/app/data/.env`
- 自动重载，无需重启容器

## 故障排查

### 容器无法启动

```bash
# 查看详细日志
docker logs semantune

# 检查容器状态
docker ps -a

# 进入容器调试
docker exec -it semantune bash
```

### 权限问题

```bash
# 修复数据目录权限
sudo chown -R $USER:$USER semantune-data/
```

### 端口被占用

```bash
# 更改映射端口
docker run -d --name semantune -p 8080:8000 \
  -v $(pwd)/semantune-data:/app/data \
  semantune
```

## 生产环境部署

### 1. 使用绝对路径

```bash
docker run -d --name semantune -p 8000:8000 \
  -v /opt/semantune/data:/app/data \
  --restart unless-stopped \
  semantune
```

### 2. 配置 HTTPS

使用 Nginx 反向代理：

```bash
docker run -d \
  --name nginx-proxy \
  -p 80:80 -p 443:443 \
  -v $(pwd)/nginx.conf:/etc/nginx/nginx.conf:ro \
  -v /etc/letsencrypt:/etc/nginx/certs:ro \
  nginx:alpine
```

### 3. 限制资源

```bash
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  --cpus="2.0" \
  --memory="2g" \
  --restart unless-stopped \
  semantune
```

### 4. 数据迁移

在服务器之间迁移：

```bash
# 备份
tar -czf semantune-data.tar.gz semantune-data/

# 传输到新服务器
scp semantune-data.tar.gz user@new-server:/opt/

# 在新服务器解压
cd /opt/
tar -xzf semantune-data.tar.gz

# 启动容器
docker run -d --name semantune -p 8000:8000 \
  -v /opt/semantune-data:/app/data \
  semantune
```

## 数据管理

### 查看数据

```bash
# 查看数据目录结构
tree semantune-data/

# 或使用 ls
ls -la semantune-data/
```

### 访问日志

```bash
# 所有日志在 semantune-data/logs/
cat semantune-data/logs/api.log
tail -f semantune-data/logs/tagging.log
```

### 查看导出文件

```bash
ls semantune-data/exports/
```

### 修改配置

```python
# 配置文件位置
semantune-data/config/recommend_config.yaml
semantune-data/config/tagging_config.yaml

# 或通过前端设置页面修改
```

## 更新应用

```bash
# 1. 停止容器
docker stop semantune && docker rm semantune

# 2. 拉取最新代码
git pull

# 3. 重新构建
docker build -t semantune .

# 4. 运行（数据保留）
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  semantune
```

## 安全建议

1. **保护数据目录**
   ```bash
   chmod 700 semantune-data/
   ```

2. **使用非 root 用户运行**（需要 Dockerfile 支持）

3. **定期备份数据**
   ```bash
   # 添加到 crontab
   0 2 * * * tar -czf /backup/semantune-$(date +\%Y\%m\%d).tar.gz /path/to/semantune-data/
   ```

4. **使用 HTTPS**（生产环境必需）

## 对比不同方案

| 方案 | 命令 | 优点 | 缺点 |
|------|------|------|------|
| 本地目录 | `-v $(pwd)/data:/app/data` | 数据可见，易备份 | 需要手动创建目录 |
| Docker 卷 | `-v semantune-data:/app/data` | 自动管理，跨平台 | 数据在容器外不可见 |
| 绝对路径 | `-v /opt/data:/app/data` | 生产环境标准 | 路径固定 |

**推荐：个人开发用本地目录，生产环境用绝对路径。**

## 常见问题

### 数据目录在哪里？

- 本地目录：运行命令的 `semantune-data/` 文件夹
- Docker 卷：`docker volume inspect semantune-data`

### 如何查看数据库？

```bash
# 使用 sqlite3
sqlite3 semantune-data/navidrome.db "SELECT * FROM song LIMIT 10"

# 或进入容器
docker exec -it semantune sqlite3 /app/data/navidrome.db
```

### 如何迁移到其他机器？

```bash
# 备份
tar -czf backup.tar.gz semantune-data/

# 传输
scp backup.tar.gz user@server:/opt/

# 恢复
cd /opt && tar -xzf backup.tar.gz
docker run -d --name semantune -p 8000:8000 -v /opt/semantune-data:/app/data semantune
```

### 可以同时运行多个实例吗？

可以，使用不同的名称和数据目录：

```bash
docker run -d --name semantune-test -p 8001:8000 \
  -v $(pwd)/semantune-test-data:/app/data \
  semantune
```

## 完整启动脚本

```bash
#!/bin/bash
set -e

IMAGE_NAME="semantune"
CONTAINER_NAME="semantune"
DATA_DIR="${1:-./semantune-data}"

# 创建数据目录
mkdir -p "$DATA_DIR"

# 构建镜像
echo "🏗️  构建镜像..."
docker build -t "$IMAGE_NAME" .

# 停止旧容器
if [ "$(docker ps -q -f name=$CONTAINER_NAME)" ]; then
    echo "⏹️  停止旧容器..."
    docker stop "$CONTAINER_NAME"
    docker rm "$CONTAINER_NAME"
fi

# 运行容器
echo "🚀 启动容器..."
docker run -d \
  --name "$CONTAINER_NAME" \
  -p 8000:8000 \
  -v "$(pwd)/$DATA_DIR:/app/data" \
  --restart unless-stopped \
  "$IMAGE_NAME"

echo "✅ 容器启动成功！"
echo "📝 访问地址: http://localhost:8000/"
echo "💾 数据目录: $(pwd)/$DATA_DIR"
```

使用：

```bash
chmod +x start.sh
./start.sh
```

## 对比：改进前后

【改进前】复杂 ✗
```bash
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/config:/app/config \
  -e SEMANTUNE_API_KEY=your-api-key \
  semantune
```

【改进后】简单 ✓
```bash
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  semantune
```

**一个 `-v` 参数，搞定一切！**
