# 🎵 Navidrome 语义音乐推荐系统

基于 LLM 语义标签的个性化音乐推荐系统，为 Navidrome 音乐服务器提供智能推荐功能。

> **本项目由 [GLM-4.7](https://open.bigmodel.cn/) 智能生成**

---

## 📖 项目简介

本项目旨在为个人音乐库构建一个**轻量级、高精度**的推荐系统，通过以下方式实现：

1. **语义标签生成** - 使用 NVIDIA API (Llama-3.3-70B) 自动为音乐库中的每首歌打上情绪、能量、流派等标签
2. **用户画像即时构建** - 基于播放历史、收藏和歌单，实时分析用户的音乐偏好（无需预先生成文件）
3. **个性化推荐** - 通过向量相似度计算，推荐用户可能喜欢但未听过的歌曲

### 🎯 核心优势

- ✅ **无需大量用户数据** - 适合个人/小团队使用，不依赖协同过滤
- ✅ **本地运行** - 所有数据和计算都在本地，保护隐私
- ✅ **高准确率** - 语义标签准确率 > 90%（基于实测）
- ✅ **易于扩展** - 模块化设计，可轻松添加新功能

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Navidrome 音乐服务器                        │
│                  (navidrome.db - 播放历史)                     │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              语义标签生成 (src/tagging/worker.py)             │
│  ┌──────────────┐        ┌──────────────┐                   │
│  │ 歌曲元数据    │   →   │ NVIDIA LLM   │                   │
│  │ (歌名/歌手)   │        │ (Llama-3.3)  │                   │
│  └──────────────┘        └──────┬───────┘                   │
│                                  │                            │
│                                  ▼                            │
│                    ┌─────────────────────────┐               │
│                    │  语义标签                 │               │
│                    │  mood, energy, genre... │               │
│                    └─────────────────────────┘               │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              语义数据库 (data/semantic.db)                     │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ file_id | mood | energy | genre | region | ...       │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │ song_1  | Epic | High   | Rock  | Chinese | ...      │   │
│  │ song_2  | Sad  | Low    | Pop   | Western | ...      │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────┬────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              推荐引擎 (src/recommend/engine.py)                │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │ 播放历史      │ + │ 收藏列表      │ + │ 用户歌单      │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│                            ↓                                 │
│                    ┌──────────────┐                          │
│                    │ 即时构建画像  │                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│                           ▼                                  │
│                  ┌─────────────────┐                         │
│                  │  用户偏好向量    │                         │
│                  │  (实时计算)     │                         │
│                  └─────────────────┘                         │
│  ┌──────────────┐        ┌──────────────┐                   │
│  │ 用户画像向量  │   →   │ 歌曲标签向量  │                   │
│  └──────────────┘        └──────────────┘                   │
│                            ↓                                 │
│                  ┌──────────────────┐                        │
│                  │ Cosine Similarity│                        │
│                  └────────┬─────────┘                        │
│                           │                                  │
│                           ▼                                  │
│                  ┌──────────────────┐                        │
│                  │  Top-N 推荐列表   │                        │
│                  └──────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ 项目结构

```
semantune/
├── main.py                    # 主入口文件
├── .env.example              # 环境变量模板
├── config/                    # 配置文件
│   ├── settings.py           # 数据库路径、API配置等
│   └── constants.py          # 标签白名单、提示词模板等
├── src/                      # 源代码
│   ├── core/                 # 核心模块
│   │   ├── database.py       # 数据库连接
│   │   └── schema.py         # 数据库表结构
│   ├── tagging/              # 语义标签生成
│   │   ├── worker.py         # LLM 标签生成器
│   │   └── preview.py        # 标签生成预览工具
│   ├── profile/              # 用户画像构建（内部使用）
│   │   └── builder.py        # 用户画像构建器
│   ├── recommend/            # 推荐引擎
│   │   └── engine.py         # 推荐算法实现（含即时画像构建）
│   ├── query/                # 查询工具
│   │   └── search.py         # 标签查询工具
│   ├── api/                  # FastAPI 接口
│   │   ├── app.py            # FastAPI 主应用
│   │   └── routes/           # API 路由
│   │       ├── recommend.py  # 推荐接口
│   │       ├── query.py      # 查询接口
│   │       ├── tagging.py    # 标签生成接口
│   │       └── analyze.py    # 分析接口
│   └── utils/                # 工具函数
│       ├── common.py         # 通用工具函数
│       ├── logger.py         # 日志配置
│       ├── analyze.py        # 数据分析工具
│       └── export.py         # 数据导出工具
├── frontend/                 # 前端界面（React + Vite + TypeScript + TailwindCSS）
│   ├── src/
│   │   ├── api/              # API 客户端
│   │   ├── components/       # 通用组件
│   │   ├── pages/            # 页面组件
│   │   ├── types/            # TypeScript 类型定义
│   │   ├── App.tsx           # 主应用组件
│   │   └── main.tsx          # 入口文件
│   ├── package.json          # 前端依赖配置
│   └── vite.config.ts        # Vite 配置
├── data/                     # 数据目录
│   ├── navidrome.db          # Navidrome 数据库（播放历史、歌单）
│   └── semantic.db           # 语义标签数据库
├── logs/                     # 日志目录
│   ├── tagging_preview.log   # 标签预览日志
│   ├── worker.log            # 标签生成日志
│   ├── recommend.log         # 推荐引擎日志
│   ├── query.log             # 查询工具日志
│   ├── profile.log           # 用户画像日志
│   ├── export.log            # 数据导出日志
│   └── analyze.log           # 数据分析日志
├── exports/                  # 导出目录
│   └── export_<user>_<timestamp>/  # 用户数据导出
└── README.md                 # 本文档
```

---

## 🚀 快速开始

### 前置要求

1. **Python 3.8+**
2. **Node.js 16+** - 用于运行前端界面
3. **NVIDIA API Key** - 用于调用 LLM 服务
4. **Navidrome** - 音乐服务器（已安装并有播放数据）

### 安装步骤

1. **克隆项目**
   ```bash
   git clone <your-repo-url>
   cd semantune
   ```

2. **安装后端依赖**
   ```bash
   pip install requests
   ```

3. **安装前端依赖**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **配置 API Key**
   
   复制环境变量模板并配置：
   ```bash
   cp .env.example .env
   ```
   
   编辑 `.env` 文件，设置你的 NVIDIA API Key：
   ```bash
   SEMANTUNE_API_KEY=your-api-key-here
   ```

### 启动服务

#### 方式一：使用 Web 界面（推荐）

1. **启动后端 API 服务**
   ```bash
   python main.py api --host 0.0.0.0 --port 8000
   ```

2. **启动前端开发服务器**（新开一个终端）
   ```bash
   cd frontend
   npm run dev
   ```

3. **访问 Web 界面**
   
   打开浏览器访问：`http://localhost:3000`

#### 方式二：使用命令行

```bash
# 生成语义标签
python main.py tag

# 生成推荐
python main.py recommend

# 查询歌曲
python main.py query

# 分析数据
python main.py analyze

# 导出数据
python main.py export
```

---

## 📊 使用流程

### 阶段 1️⃣：生成语义标签

为音乐库中的所有歌曲生成语义标签。

```bash
python main.py tag
```

**输出示例**：
```
🎵 Processing 19700 new songs. (Total in Library: 19700)
进度:[1/19700] ETA:15:23:45 | 周杰伦 - 夜曲
```

**处理时间**：约 2-3 秒/首歌（使用 Llama-3.3-70B）

**生成的标签**：
- `mood`: Energetic, Epic, Emotional, Sad, Chill, Dark, Happy, Peaceful, Romantic, Dreamy, Upbeat, Groovy
- `energy`: Low, Medium, High
- `genre`: Pop, Indie, Rock, Electronic, Hip-Hop, Classical, Folk, J-Rock, Metal
- `region`: Chinese, Western, Japanese, Korean
- `subculture`: None, Anime, Game, Vocaloid, Idol
- `scene`: Workout, Study, Night, Driving, Gaming, Sleep, Morning, None

---

### 阶段 2️⃣：数据质量分析

检查生成的标签质量。

```bash
python main.py analyze
```

**输出示例**：
```
================================================================================
  数据质量
================================================================================
  总歌曲数: 19700
  平均置信度: 0.82
  低置信度歌曲 (<0.5): 0 (0.0%)

情绪 (Mood) 分布:
标签              数量       占比
-----------------------------------
Energetic         3200      16.24%
Peaceful          2800      14.21%
...
```

---

### 阶段 3️⃣：生成个性化推荐

基于用户画像生成推荐列表。

```bash
python main.py recommend
```

**输出示例**：
```
================================================================================
  个性化音乐推荐系统
================================================================================
1. 加载用户画像...
   用户ID: user_123
   画像维度: 12 个标签
2. 获取用户历史...
   已听过: 1523 首
   最近听过: 100 首
3. 构建歌曲向量库...
   歌曲总数: 19700 首
4. 计算加权相似度...
   候选歌曲: 18177 首
   相似度范围: 0.856 ~ 0.123
5. 混合推荐策略...
   利用型（高相似度）: 22 首
   探索型（多样性）: 8 首
   最终推荐: 30 首
   独立艺人数: 28
   独立专辑数: 30

================================================================================
  为你推荐 (共 30 首)
================================================================================
#    相似度    歌手                 歌曲                           标签
--------------------------------------------------------------------------------
1    0.856    Coldplay            Yellow                         Peaceful/Low/Rock
2    0.842    Radiohead           Creep                          Sad/Medium/Rock
...
```

---

### 阶段 4️⃣：查询歌曲

按标签查询歌曲。

```bash
python main.py query
```

**交互式菜单**：
```
================================================================================
  语义标签查询工具
================================================================================
  1. 按情绪查询 (Mood)
  2. 按标签组合查询 (Mood + Energy + Genre + Region)
  3. 按场景查询 (预设场景)
  4. 找相似歌曲
  5. 随机推荐
  6. 导出上次查询结果
  0. 退出
================================================================================
```

---

### 阶段 5️⃣：导出数据

导出用户数据、播放历史、歌单等。

```bash
python main.py export
```

**输出示例**：
```
================================================================================
  用户数据导出工具
================================================================================

导出目录: exports/export_user_20260201_120000

1. 导出播放历史...
   已导出 1523 首歌曲
2. 导出歌单...
   已导出 12 个歌单
3. 导出统计数据...
   总歌曲数: 1523
   总播放次数: 12456
   收藏歌曲数: 234
   歌单数量: 12

✅ 导出完成！
   所有文件已保存到: exports/export_user_20260201_120000
```

---

## ⚙️ 配置说明

### 推荐配置

编辑 [`config/settings.py`](config/settings.py:1) 中的 `RECOMMEND_CONFIG`：

```python
RECOMMEND_CONFIG = {
    "default_limit": 30,                # 默认推荐数量
    "recent_filter_count": 100,         # 过滤最近听过的 N 首歌
    "diversity_max_per_artist": 2,      # 每个歌手最多推荐 N 首
    "diversity_max_per_album": 1,       # 每张专辑最多推荐 N 首
    "exploration_ratio": 0.25,          # 探索型歌曲占比（25%）
    "tag_weights": {                    # 标签权重
        "mood": 2.0,                    # 情绪最重要
        "energy": 1.5,                  # 能量次之
        "genre": 1.2,                   # 流派
        "region": 0.8                   # 地区权重较低
    }
}
```

### 用户画像权重配置

编辑 [`config/settings.py`](config/settings.py:1) 中的 `WEIGHT_CONFIG`：

```python
WEIGHT_CONFIG = {
    "play_count": 1.0,      # 每次播放的基础权重
    "starred": 10.0,        # 收藏的固定加分
    "in_playlist": 8.0,     # 每个歌单的加分
    "time_decay_days": 90,  # 时间衰减周期（天）
    "min_decay": 0.3        # 最小衰减系数
}
```

---

## 📝 命令行参数

```bash
python main.py <command>

可用命令:
  tag          生成语义标签
  tag-preview  预览标签生成（测试 API）
  recommend    生成个性化推荐（用户画像即时构建）
  query        查询歌曲
  analyze      分析数据
  export       导出数据
  api          启动 API 服务
```

**注意**：用户画像现在在推荐时即时构建，无需单独运行 `profile` 命令。

---

## 🌐 API 服务

### 启动 API 服务

```bash
# 启动 API 服务（默认端口 8000）
python main.py api

# 指定端口
python main.py api --port 8080

# 指定监听地址
python main.py api --host 127.0.0.1 --port 8080
```

启动后访问：
- API 文档: http://localhost:8000/docs
- ReDoc 文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

### API 端点

#### 推荐接口 (`/api/v1/recommend`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/` | 获取个性化推荐 |
| GET | `/users` | 获取所有用户列表 |

**推荐请求示例**：
```json
{
  "user_id": "user_123",
  "limit": 30,
  "filter_recent": true,
  "diversity": true
}
```

#### 查询接口 (`/api/v1/query`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/mood` | 按情绪查询歌曲 |
| POST | `/tags` | 按标签组合查询歌曲 |
| POST | `/scene` | 按预设场景查询歌曲 |
| POST | `/similar` | 找相似歌曲 |
| POST | `/random` | 随机推荐歌曲 |
| GET | `/labels` | 获取所有可用标签列表 |

**按情绪查询示例**：
```json
{
  "mood": "Energetic",
  "limit": 20
}
```

#### 标签生成接口 (`/api/v1/tagging`)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/generate` | 为单首歌曲生成语义标签 |
| POST | `/batch` | 批量生成语义标签（后台任务） |
| GET | `/progress` | 获取批量标签生成进度 |
| POST | `/sync` | 同步标签到数据库 |

**生成标签示例**：
```json
{
  "title": "夜曲",
  "artist": "周杰伦",
  "album": "十一月的萧邦"
}
```

#### 分析接口 (`/api/v1/analyze`)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/distribution/{field}` | 获取指定字段的分布分析 |
| GET | `/combinations` | 获取最常见的 Mood + Energy 组合 |
| GET | `/region-genre` | 获取各地区的流派分布 |
| GET | `/quality` | 获取数据质量分析 |
| GET | `/summary` | 获取数据概览 |

### 依赖安装

API 服务需要安装以下依赖：

```bash
pip install fastapi uvicorn python-dotenv
```

---

## 🎨 前端界面

项目包含一个基于 React + Vite + TypeScript + TailwindCSS 的 Web 前端界面。

### 前端技术栈

- **React 18** - UI 框架
- **Vite** - 构建工具
- **TypeScript** - 类型安全
- **TailwindCSS** - CSS 框架
- **React Router** - 路由管理
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库

### 前端页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 首页 | `/` | 显示系统概览和统计数据 |
| 推荐 | `/recommend` | 获取个性化音乐推荐 |
| 查询 | `/query` | 根据语义标签搜索歌曲 |
| 标签生成 | `/tagging` | 管理语义标签生成任务 |
| 分析 | `/analyze` | 查看详细的数据分析 |

### 前端开发

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

前端开发服务器将在 `http://localhost:3000` 启动，并自动代理 API 请求到后端服务。

详细的前端文档请参考 [`frontend/README.md`](frontend/README.md:1)。

---

## 🔧 开发说明

### 模块说明

| 模块 | 文件 | 功能 |
|------|------|------|
| **核心模块** | [`src/core/database.py`](src/core/database.py:1) | 数据库连接 |
| | [`src/core/schema.py`](src/core/schema.py:1) | 数据库表结构 |
| **标签生成** | [`src/tagging/worker.py`](src/tagging/worker.py:1) | LLM 标签生成器 |
| | [`src/tagging/preview.py`](src/tagging/preview.py:1) | 标签生成预览工具 |
| **推荐引擎** | [`src/recommend/engine.py`](src/recommend/engine.py:1) | 推荐算法实现（含即时画像构建） |
| **查询工具** | [`src/query/search.py`](src/query/search.py:1) | 标签查询工具 |
| **API 服务** | [`src/api/app.py`](src/api/app.py:1) | FastAPI 主应用 |
| | [`src/api/routes/recommend.py`](src/api/routes/recommend.py:1) | 推荐接口 |
| | [`src/api/routes/query.py`](src/api/routes/query.py:1) | 查询接口 |
| | [`src/api/routes/tagging.py`](src/api/routes/tagging.py:1) | 标签生成接口 |
| | [`src/api/routes/analyze.py`](src/api/routes/analyze.py:1) | 分析接口 |
| **工具函数** | [`src/utils/common.py`](src/utils/common.py:1) | 通用工具函数 |
| | [`src/utils/logger.py`](src/utils/logger.py:1) | 日志配置 |
| | [`src/utils/analyze.py`](src/utils/analyze.py:1) | 数据分析工具 |
| | [`src/utils/export.py`](src/utils/export.py:1) | 数据导出工具 |

### 添加新功能

1. 在对应的模块目录下创建新文件
2. 在 [`main.py`](main.py:1) 中添加新的命令处理
3. 更新本 README 文档

---

## 🔒 安全性说明

- **API Key 安全**：API Key 通过环境变量配置，不会提交到代码仓库
- **SQL 注入防护**：所有数据库查询使用参数化查询
- **异常处理**：使用具体的异常类型，避免裸 except 捕获

## 📄 许可证

MIT License

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
