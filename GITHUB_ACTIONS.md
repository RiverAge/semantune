# GitHub Actions 自动部署指南

## 概述

使用 GitHub Actions 实现：
1. 自动构建 Docker 镜像
2. 自动推送到 GitHub Container Registry (GHCR)
3. 自动部署到服务器（可选）

## 快速开始

### 1. 启用 Actions

首次推送代码后：
1. 进入 GitHub 仓库
2. 点击 "Actions" 标签
3. 点击 "I understand my workflows, go ahead and enable them"

### 2. 启用 Container Registry 权限

确保仓库设置允许推送镜像：
1. Settings → Actions → General
2. Workflow permissions
3. 选择 "Read and write permissions"
4. 点击 Save

### 2. 构建并推送镜像

**方式一：通过 Tag 触发**

```bash
# 创建并推送 tag
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions 会自动构建并推送镜像到 GHCR
```

**方式二：手动触发**

1. 进入 GitHub 仓库的 "Actions" 页面
2. 选择 "Build and Push Docker Image"
3. 点击 "Run workflow"

### 3. 拉取镜像

```bash
# 登录 GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# 拉取镜像
docker pull ghcr.io/你的用户名/semantune:latest

# 运行容器
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  ghcr.io/你的用户名/semantune:latest
```

## Workflow 文件说明

### docker.yml（构建和推送）

触发条件：
- 推送新的 tag（如 `v1.0.0`）
- 手动触发

功能：
- 自动构建 Docker 镜像
- 推送到 GitHub Container Registry (GHCR)
- 自动生成多个标签（tag、commit sha、latest）
- 使用 GitHub Actions 缓存加速构建
- 仅对主分支推送时标记为 latest

## 镜像使用说明

### 拉取镜像

```bash
# 拉取最新版本
docker pull ghcr.io/你的用户名/semantune:latest

# 拉取指定版本
docker pull ghcr.io/你的用户名/semantune:v1.0.0
```

### 运行镜像

```bash
# 运行容器
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  ghcr.io/你的用户名/semantune:latest
```

### 查看镜像

访问 GitHub 查看推送的镜像：
https://github.com/你的用户名/semantune/pkgs/container/semantune

## 常见使用场景

### 场景 1：开发新功能

```bash
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
git push origin feature/new-feature

# 合并到主分支后，如果想发布：
git checkout main
git merge feature/new-feature
git tag v1.1.0
git push origin main --tags

# 自动构建并推送镜像
```

### 场景 2：修复 Bug

```bash
# 代码修复后
git commit -m "Fix: 修复 API 响应问题"
git push

# 发布补丁版本
git tag v1.0.1
git push origin v1.0.1

# 自动构建并推送
```

### 场景 3：部署新版本

```bash
# 拉取指定版本的镜像
docker pull ghcr.io/你的用户名/semantune:v1.0.0

# 停止旧容器
docker stop semantune && docker rm semantune

# 运行新容器
docker run -d --name semantune -p 8000:8000 \
  -v $(pwd)/semantune-data:/app/data \
  ghcr.io/你的用户名/semantune:v1.0.0
```

## 镜像标签说明

GitHub Actions 会自动生成以下标签：

| 标签 | 说明 | 示例 |
|------|------|------|
| `latest` | 最新稳定版，来自主分支 | `ghcr.io/user/semantune:latest` |
| `v*` | 版本号，来自 tag | `ghcr.io/user/semantune:v1.0.0` |
| `sha-*` | Commit SHA，每次提交 | `ghcr.io/user/semantune:sha-1a2b3c4` |

### 使用不同标签

```bash
# 使用最新版本
docker pull ghcr.io/user/semantune:latest

# 使用特定版本
docker pull ghcr.io/user/semantune:v1.0.0

# 使用特定提交
docker pull ghcr.io/user/semantune:sha-1a2b3c4
```

## 查看构建状态

```bash
# 方法 1: GitHub 页面
# 仓库主页 → Actions

# 方法 2: GitHub CLI
gh run list

# 方法 3: 查看特定 workflow
gh run view --workflow=docker.yml
```

## 取消构建任务

```bash
# 查看运行中的 workflow
gh run list --status=in_progress

# 取消特定 run
gh run cancel <run-id>
```

## 本地构建 vs GitHub Actions

| 对比项 | 本地构建 | GitHub Actions |
|--------|---------|----------------|
| 速度 | ⚠️ 受本地网络影响 | ✅ GitHub CDN 加速 |
| 免费 | ⚠️ 占用本地资源 | ✅ GitHub 免费提供 |
| 自动化 | ❌ 需要手动 | ✅ 自动触发 |
| 缓存 | ⚠️ 本地缓存 | ✅ GitHub Actions cache |
| 记录 | ❌ 需要自己记录 | ✅ 完整日志 |

## 高级配置

### 多平台构建

修改 `.github/workflows/docker.yml`：

```yaml
- name: Set up QEMU
  uses: docker/setup-qemu-action@v3

- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    platforms: linux/amd64,linux/arm64
    push: true
    tags: ${{ steps.meta.outputs.tags }}
```

### 定时构建

```yaml
on:
  schedule:
    - cron: '0 2 * * *'  # 每天凌晨2点
```

### 环境变量配置

```yaml
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ${{ steps.meta.outputs.tags }}
    build-args: |
      SEMANTUNE_API_KEY=${{ secrets.API_KEY }}
```

## 故障排查

### 构建失败

1. 查看 Actions 日志
2. 检查 Dockerfile 语法
3. 确保依赖安装正常

### 推送失败

1. 检查权限设置：Settings → Actions → General → Workflow permissions
2. 确保 "Read and write permissions" 已勾选
3. 查看 Actions 日志获取详细错误信息

### 镜像太慢

1. GitHub Actions 构建通常需要 2-5 分钟
2. 可以在本地构建测试，确认 Dockerfile 没问题后再推送

## 最佳实践

1. **版本管理**
   - 使用语义化版本（v1.0.0）
   - 主干分支保持稳定
   - 重要变更才打 tag

2. **镜像标签**
   - `latest` - 最新稳定版，来自主分支
   - `v*` - 版本号，如 v1.0.0
   - `sha-*` - 特定提交，用于调试

3. **权限**
   - 确保 "Read and write permissions" 已启用
   - 保护敏感信息在 Secrets 中

4. **监控**
   - 启用 workflow 通知
   - 定期检查构建状态
   - 关注失败原因

## 镜像优化建议

```yaml
# 启用缓存
- name: Build and push Docker image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max

# Dockerfile 优化建议
# 使用更小的基础镜像
# 充分利用层缓存
# 清理不必要的文件
jobs:
  build:
    strategy:
      matrix:
        platform: [linux-amd64, linux-arm64]
```

## 成本说明

GitHub Actions 免费额度（公开仓库）：

| 资源 | 免费额度 |
|------|---------|
| 构建分钟 | 2000 分钟/月 |
| 存储 | 500 MB |
| 带宽 | 无限制 |

私有仓库（免费版）：

| 资源 | 免费额度 |
|------|---------|
| 构建分钟 | 2000 分钟/月 |
| 存储 | 500 MB |

通常完全够用！

## 总结

✅ **推荐：** 使用 GitHub Actions 自动构建和推送

 reasons:
- 完全免费
- 自动化流程
- 集成度高
- 性能优秀
- 日志完善

🚀 **完整流程：**
1. 本地开发测试
2. 代码提交到 GitHub
3. 打 tag（v1.0.0）
4. GitHub Actions 自动构建
5. GitHub Actions 自动推送到 GHCR
6. 用户拉取镜像并部署（由用户控制）
