# Navidrome 语义音乐推荐系统 - 前端

基于 React + Vite + TypeScript + TailwindCSS 构建的前端界面。

## 技术栈

- **React 18** - UI 框架
- **Vite** - 构建工具
- **TypeScript** - 类型安全
- **TailwindCSS** - CSS 框架
- **React Router** - 路由管理
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库

## 安装依赖

```bash
npm install
```

## 开发模式

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动，并自动代理 API 请求到后端 `http://localhost:8000`。

## 构建生产版本

```bash
npm run build
```

## 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── api/           # API 客户端
│   ├── components/    # 通用组件
│   ├── pages/         # 页面组件
│   ├── types/         # TypeScript 类型定义
│   ├── App.tsx        # 主应用组件
│   ├── main.tsx       # 入口文件
│   └── index.css      # 全局样式
├── public/            # 静态资源
├── index.html         # HTML 模板
├── vite.config.ts     # Vite 配置
├── tailwind.config.js # TailwindCSS 配置
└── package.json       # 项目配置
```

## 页面说明

- **首页** (`/`) - 显示系统概览和统计数据
- **推荐** (`/recommend`) - 获取个性化音乐推荐
- **查询** (`/query`) - 根据语义标签搜索歌曲
- **标签生成** (`/tagging`) - 管理语义标签生成任务
- **分析** (`/analyze`) - 查看详细的数据分析

## API 配置

API 请求通过 Vite 代理转发到后端服务。如需修改后端地址，请编辑 `vite.config.ts`：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 修改为你的后端地址
      changeOrigin: true,
    },
  },
}
```

## 注意事项

1. 确保后端 API 服务已启动（默认运行在 `http://localhost:8000`）
2. 首次运行需要安装依赖：`npm install`
3. 开发模式下，修改代码会自动热更新
