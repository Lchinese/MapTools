# MapTools - 轨迹路径匹配系统

一个基于MongoDB的轨迹路径匹配系统，支持GPS轨迹数据的地图匹配、可视化和分析。

## 📋 项目概述

MapTools是一个完整的轨迹匹配解决方案，包含前端Web应用、后端API服务和数据处理工具。系统采用多语言架构，充分利用不同技术的优势。

## 🏗️ 系统架构

### 技术栈

- **前端**: React 18 + Ant Design + Leaflet + Vite
- **后端**: FastAPI + Python 3.13 + MongoDB
- **数据处理**: Java + Maven
- **数据库**: MongoDB 6.0+
- **容器化**: Docker + Docker Compose

### 项目结构

```
MapTools/
├── FrontendApp/           # React前端应用
├── BackendService/        # FastAPI后端服务
├── JavaToolScripts/       # Java数据处理工具
├── data/                  # 轨迹数据文件
├── ExternalData/          # 外部数据（天地图）
├── UserUploads/           # 用户上传文件
├── Docs/                  # 项目文档
└── docker-compose.yml     # 容器编排配置
```

## 🚀 快速开始

### 环境要求

- **Node.js**: 18.0+ (推荐 22.x)
- **Python**: 3.11+ (推荐 3.13)
- **Java**: 11+ (推荐 17+)
- **MongoDB**: 6.0+
- **Git**: 2.0+

### 1. 克隆项目

```bash
git clone <repository-url>
cd MapTools
```

### 2. 环境配置

#### 后端环境配置

```bash
cd BackendService
cp env.example .env
# 编辑 .env 文件，配置数据库连接等参数
```

#### 前端环境配置

```bash
cd FrontendApp
# 前端使用代理配置，无需额外环境变量
```

### 3. 安装依赖

#### 后端依赖

```bash
cd BackendService
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt
```

#### 前端依赖

```bash
cd FrontendApp
npm install
```

#### Java工具依赖

```bash
cd JavaToolScripts
# Maven会自动下载依赖
```

### 4. 数据库初始化

```bash
cd BackendService
# 启动MongoDB服务
# 运行数据库初始化脚本
python scripts/init_database.py
```

### 5. 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
# Windows PowerShell
powershell -ExecutionPolicy Bypass -File start.ps1

# Linux/macOS
./start.sh
```

#### 方式二：手动启动

```bash
# 终端1：启动后端
cd BackendService
uv run python main.py

# 终端2：启动前端
cd FrontendApp
npm start
```

### 6. 访问应用

- **前端应用**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 📦 详细依赖说明

### 后端依赖 (BackendService)

#### 核心框架
- `fastapi==0.104.1` - Web框架
- `uvicorn[standard]==0.24.0` - ASGI服务器
- `pydantic==2.5.0` - 数据验证

#### 数据库相关
- `motor==3.3.2` - MongoDB异步驱动
- `pymongo==4.6.0` - MongoDB同步驱动
- `beanie==1.23.6` - MongoDB ODM

#### 地理空间处理
- `geopy==2.4.1` - 地理编码
- `shapely==2.0.2` - 几何计算
- `pyproj==3.6.1` - 坐标转换

#### 数据处理
- `pandas==2.1.4` - 数据分析
- `numpy==1.25.2` - 数值计算
- `scipy==1.11.4` - 科学计算

#### 异步任务
- `celery==5.3.4` - 分布式任务队列
- `redis==5.0.1` - 消息代理

#### 其他工具
- `python-multipart==0.0.6` - 文件上传
- `python-jose[cryptography]==3.3.0` - JWT认证
- `passlib[bcrypt]==1.7.4` - 密码哈希
- `python-dotenv==1.0.0` - 环境变量

### 前端依赖 (FrontendApp)

#### 核心框架
- `react@^18.2.0` - UI框架
- `react-dom@^18.2.0` - DOM渲染
- `react-router-dom@^6.8.1` - 路由管理

#### UI组件库
- `antd@^5.3.0` - 企业级UI组件
- `@ant-design/icons@^5.0.1` - 图标库

#### 地图相关
- `leaflet@^1.9.3` - 地图库
- `react-leaflet@^4.2.0` - React地图组件

#### 状态管理
- `zustand@^4.3.6` - 轻量级状态管理

#### 数据处理
- `axios@^1.3.4` - HTTP客户端
- `lodash@^4.17.21` - 工具库
- `dayjs@^1.11.7` - 日期处理
- `papaparse@^5.4.1` - CSV解析

#### 文件处理
- `file-saver@^2.0.5` - 文件下载
- `gpx-parser-builder@^1.0.0` - GPX文件处理
- `togeojson@^0.16.0` - 地理数据转换

#### 开发工具
- `react-scripts@^5.0.1` - Create React App脚本
- `@testing-library/react@^13.3.0` - 测试工具
- `@testing-library/jest-dom@^5.16.4` - DOM测试
- `@testing-library/user-event@^13.5.0` - 用户事件测试

### Java工具依赖 (JavaToolScripts)

#### 核心依赖
- `maven-compiler-plugin@3.11.0` - Java编译
- `maven-surefire-plugin@3.1.2` - 测试运行

#### MongoDB驱动
- `mongodb-driver-sync@4.10.2` - MongoDB同步驱动
- `mongodb-driver-core@4.10.2` - MongoDB核心驱动
- `bson@4.10.2` - BSON处理

#### 地理空间处理
- `geotools-core@30.0` - 地理空间工具
- `geotools-main@30.0` - 主要功能
- `geotools-geometry@30.0` - 几何处理

## 🔧 开发环境配置

### 1. 代码编辑器配置

推荐使用VS Code，安装以下扩展：

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.pylint",
    "bradlc.vscode-tailwindcss",
    "esbenp.prettier-vscode",
    "ms-vscode.vscode-typescript-next",
    "redhat.vscode-yaml"
  ]
}
```

### 2. Git配置

```bash
# 配置用户信息
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# 配置换行符处理
git config --global core.autocrlf true
```

### 3. 环境变量配置

#### 后端环境变量 (.env)

```env
# 数据库配置
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=maptools

# 应用配置
APP_NAME=MapTools
APP_VERSION=1.0.0
DEBUG=True
LOG_LEVEL=INFO

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 文件上传配置
MAX_FILE_SIZE=104857600
UPLOAD_DIR=UserUploads

# 地图配置
TIANDITU_TOKEN=your-tianditu-token
DEFAULT_CENTER_LAT=22.5431
DEFAULT_CENTER_LNG=114.0579
DEFAULT_ZOOM=12
```

#### 前端环境变量 (.env)

```env
REACT_APP_API_URL=http://localhost:8000/api/v1
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_MAP_TILE_URL=https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png
REACT_APP_MAP_ATTRIBUTION=© OpenStreetMap contributors
```

## 🐳 Docker部署

### 使用Docker Compose

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 单独构建镜像

```bash
# 构建后端镜像
cd BackendService
docker build -t maptools-backend .

# 构建前端镜像
cd FrontendApp
docker build -t maptools-frontend .
```

## 📚 开发指南

### 1. 添加新功能

#### 后端API开发
1. 在 `ApiEndpoints/` 创建新的API文件
2. 在 `BusinessServices/` 实现业务逻辑
3. 在 `DataModels/` 定义数据模型
4. 在 `DataSchemas/` 定义验证模式
5. 更新 `main.py` 注册路由

#### 前端组件开发
1. 在 `src/Components/` 创建组件
2. 在 `src/Pages/` 创建页面
3. 在 `src/Services/` 添加API调用
4. 在 `src/Store/` 管理状态
5. 更新路由配置

### 2. 数据库操作

#### 连接数据库
```python
from BackendService.CoreConfig.database import get_database
db = await get_database()
```

#### 查询数据
```python
from BackendService.DataModels.MongoModels import GPSPoint
points = await GPSPoint.find_all().to_list()
```

### 3. 测试

#### 后端测试
```bash
cd BackendService
python -m pytest Tests/ -v
```

#### 前端测试
```bash
cd FrontendApp
npm test
```

## 🚨 常见问题

### 1. 端口冲突
- 后端默认端口：8000
- 前端默认端口：3000
- MongoDB默认端口：27017

### 2. 依赖安装失败
- 检查网络连接
- 清除npm缓存：`npm cache clean --force`
- 删除node_modules重新安装

### 3. MongoDB连接失败
- 确保MongoDB服务正在运行
- 检查连接字符串配置
- 验证数据库权限

### 4. 地图不显示
- 检查网络连接
- 验证地图瓦片服务
- 检查Leaflet版本兼容性

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📞 支持

如有问题，请通过以下方式联系：

- 创建 Issue
- 发送邮件至项目维护者
- 查看项目文档

---

**MapTools** - 让轨迹匹配更简单、更高效！