# MapTools API 规范文档

## OpenAPI 3.0 规范

本文档定义了 MapTools 后端服务的 OpenAPI 3.0 规范，可用于自动生成客户端 SDK 和 API 文档。

```yaml
openapi: 3.0.3
info:
  title: MapTools Backend API
  description: |
    MapTools 后端服务提供轨迹匹配、数据处理、文件管理等核心功能的 RESTful API 接口。
    
    ## 功能特性
    - 轨迹文件上传和管理
    - 多种地图匹配算法（HMM、Greedy）
    - 实时任务状态监控
    - 结果文件下载
    - 路网数据管理
    
    ## 认证
    当前版本支持可选的 JWT Token 认证，未来版本将支持 OAuth 2.0。
    
    ## 限流
    API 请求限制为每分钟 1000 次，超出限制将返回 429 状态码。
    
    ## 测试
    项目包含完整的单元测试和集成测试套件，确保 API 功能的稳定性和可靠性。
    - 单元测试：覆盖核心业务逻辑和工具函数
    - 集成测试：验证 API 端点和数据库操作
    - 使用 pytest 或 unittest 运行测试
  version: 0.1.0
  contact:
    name: MapTools Support
    email: support@maptools.com
    url: https://docs.maptools.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8000
    description: 开发环境
  - url: https://api.maptools.com
    description: 生产环境

tags:
  - name: Health
    description: 健康检查相关接口
  - name: Trajectories
    description: 轨迹管理相关接口
  - name: Matching
    description: 地图匹配相关接口
  - name: RoadNetworks
    description: 路网管理相关接口
  - name: Files
    description: 文件管理相关接口