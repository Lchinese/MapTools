# MapTools Frontend

MapTools轨迹匹配系统的前端应用，基于React 18和Ant Design构建。

## 功能特性

- 🗺️ 交互式地图显示
- 📁 轨迹文件上传（支持GPX、KML、CSV、TXT格式）
- 🔄 实时地图匹配处理
- 📊 匹配结果可视化
- 📈 统计信息展示
- 📱 响应式设计

## 技术栈

- **React 18** - 前端框架
- **Ant Design 5** - UI组件库
- **React Router 6** - 路由管理
- **Leaflet** - 地图组件
- **Zustand** - 状态管理
- **Axios** - HTTP客户端

## 项目结构

```
src/
├── Components/          # 组件
│   ├── Common/         # 通用组件
│   ├── Layout/         # 布局组件
│   ├── Map/           # 地图组件
│   ├── Results/       # 结果展示组件
│   └── Upload/        # 上传组件
├── Hooks/             # 自定义Hooks
├── Pages/             # 页面组件
├── Services/          # API服务
├── Store/             # 状态管理
├── Utils/             # 工具函数
├── App.js             # 主应用组件
└── index.js           # 入口文件
```

## 快速开始

### 安装依赖

```bash
npm install
# 或
yarn install
```

### 启动开发服务器

```bash
npm start
# 或
yarn start
```

应用将在 http://localhost:3000 启动

### 构建生产版本

```bash
npm run build
# 或
yarn build
```

## 环境配置

创建 `.env` 文件并配置以下环境变量：

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
REACT_APP_MAP_ATTRIBUTION=© OpenStreetMap contributors
REACT_APP_MAX_FILE_SIZE=104857600
REACT_APP_SUPPORTED_FORMATS=.gpx,.kml,.csv,.txt
```

## 主要功能

### 1. 轨迹上传
- 支持拖拽上传
- 多种文件格式支持
- 实时上传进度显示
- 文件格式验证

### 2. 地图匹配
- 实时匹配状态监控
- 多种匹配算法支持
- 匹配结果可视化
- 质量指标展示

### 3. 结果展示
- 交互式地图显示
- 原始轨迹与匹配轨迹对比
- 详细统计信息
- 结果文件下载

### 4. 数据管理
- 轨迹文件管理
- 匹配任务历史
- 批量操作支持

## 组件说明

### MapComponent
地图显示组件，支持：
- 轨迹线绘制
- 轨迹点标记
- 地图控制
- 响应式布局

### FileUpload
文件上传组件，支持：
- 拖拽上传
- 文件验证
- 进度显示
- 格式检查

### ResultsDisplay
结果展示组件，支持：
- 统计信息展示
- 匹配点详情
- 质量指标
- 数据表格

## 状态管理

使用Zustand进行状态管理：

- `useTrajectoryStore` - 轨迹相关状态
- `useMapStore` - 地图相关状态

## API集成

与后端API的集成通过 `Services/api.js` 实现：

- 轨迹管理API
- 匹配任务API
- 文件管理API
- 系统状态API

## 开发指南

### 添加新页面
1. 在 `src/Pages/` 创建页面组件
2. 在 `src/App.js` 添加路由
3. 在 `src/Components/Layout/Sidebar.jsx` 添加菜单项

### 添加新组件
1. 在 `src/Components/` 相应目录创建组件
2. 导出组件并在需要的地方导入使用

### 添加新API
1. 在 `src/Services/api.js` 添加API方法
2. 在相应的Store中添加状态管理

## 部署

### 构建
```bash
npm run build
```

### 部署到Nginx
将 `build` 目录内容复制到Nginx的web根目录，配置反向代理到后端API。

### Docker部署
```dockerfile
FROM nginx:alpine
COPY build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

## 浏览器支持

- Chrome >= 88
- Firefox >= 85
- Safari >= 14
- Edge >= 88

## 许可证

MIT License
