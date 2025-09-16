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
  - name: System
    description: 系统管理相关接口
  - name: DataSources
    description: 数据源管理相关接口
  - name: OriginDestination
    description: 起始终止数据管理相关接口

paths:
  /health:
    get:
      tags:
        - Health
      summary: 服务健康检查
      description: 检查服务运行状态和依赖服务连接情况
      operationId: healthCheck
      responses:
        '200':
          description: 服务运行正常
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/HealthResponse'
        '500':
          description: 服务异常
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/trajectories/upload:
    post:
      tags:
        - Trajectories
      summary: 上传轨迹文件
      description: 上传轨迹文件（支持 GPX、KML、CSV 格式）
      operationId: uploadTrajectory
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: 轨迹文件
                name:
                  type: string
                  description: 轨迹名称
                  example: "测试轨迹"
                description:
                  type: string
                  description: 轨迹描述
                  example: "这是一个测试轨迹"
                data_type:
                  type: string
                  enum: [auto, taxi_gps, bus_card, metro_card, taxi_transaction, bus_gps, gpx, csv]
                  description: 数据类型
                  example: "taxi_gps"
      responses:
        '201':
          description: 文件上传成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrajectoryUploadResponse'
        '400':
          description: 请求参数错误
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '413':
          description: 文件过大
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '415':
          description: 不支持的文件格式
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/trajectories:
    get:
      tags:
        - Trajectories
      summary: 获取轨迹列表
      description: 获取用户轨迹列表，支持分页和筛选
      operationId: getTrajectories
      parameters:
        - name: page
          in: query
          description: 页码
          required: false
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          description: 每页数量
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: status
          in: query
          description: 轨迹状态
          required: false
          schema:
            type: string
            enum: [uploaded, processing, completed, failed]
        - name: start_date
          in: query
          description: 开始日期
          required: false
          schema:
            type: string
            format: date-time
        - name: end_date
          in: query
          description: 结束日期
          required: false
          schema:
            type: string
            format: date-time
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrajectoryListResponse'

  /api/v1/trajectories/{trajectory_id}:
    get:
      tags:
        - Trajectories
      summary: 获取轨迹详情
      description: 获取指定轨迹的详细信息
      operationId: getTrajectory
      parameters:
        - name: trajectory_id
          in: path
          required: true
          description: 轨迹ID
          schema:
            type: string
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrajectoryDetailResponse'
        '404':
          description: 轨迹不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
    delete:
      tags:
        - Trajectories
      summary: 删除轨迹
      description: 删除指定的轨迹
      operationId: deleteTrajectory
      parameters:
        - name: trajectory_id
          in: path
          required: true
          description: 轨迹ID
          schema:
            type: string
      responses:
        '200':
          description: 删除成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TrajectoryDeleteResponse'
        '404':
          description: 轨迹不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/matching/start:
    post:
      tags:
        - Matching
      summary: 开始地图匹配
      description: 开始对轨迹进行地图匹配
      operationId: startMatching
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MatchingRequest'
      responses:
        '201':
          description: 匹配任务已创建
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MatchingStartResponse'
        '400':
          description: 请求参数错误
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '404':
          description: 轨迹不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/matching/status/{task_id}:
    get:
      tags:
        - Matching
      summary: 查询匹配状态
      description: 查询地图匹配任务的状态
      operationId: getMatchingStatus
      parameters:
        - name: task_id
          in: path
          required: true
          description: 任务ID
          schema:
            type: string
      responses:
        '200':
          description: 查询成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MatchingStatusResponse'
        '404':
          description: 任务不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/matching/result/{task_id}:
    get:
      tags:
        - Matching
      summary: 获取匹配结果
      description: 获取地图匹配的详细结果
      operationId: getMatchingResult
      parameters:
        - name: task_id
          in: path
          required: true
          description: 任务ID
          schema:
            type: string
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/MatchingResultResponse'
        '404':
          description: 任务不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/matching/download/{task_id}:
    get:
      tags:
        - Matching
      summary: 下载匹配结果
      description: 下载匹配结果为文件
      operationId: downloadMatchingResult
      parameters:
        - name: task_id
          in: path
          required: true
          description: 任务ID
          schema:
            type: string
        - name: format
          in: query
          description: 文件格式
          required: false
          schema:
            type: string
            enum: [gpx, kml, csv, geojson]
            default: gpx
      responses:
        '200':
          description: 下载成功
          content:
            application/gpx+xml:
              schema:
                type: string
                format: binary
            application/vnd.google-earth.kml+xml:
              schema:
                type: string
                format: binary
            text/csv:
              schema:
                type: string
                format: binary
            application/geo+json:
              schema:
                type: string
                format: binary
        '404':
          description: 任务不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/roadnetworks:
    get:
      tags:
        - RoadNetworks
      summary: 获取路网信息
      description: 获取可用的路网数据源
      operationId: getRoadNetworks
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RoadNetworkListResponse'

  /api/v1/roadnetworks/{network_id}/stats:
    get:
      tags:
        - RoadNetworks
      summary: 获取路网统计
      description: 获取指定路网的统计信息
      operationId: getRoadNetworkStats
      parameters:
        - name: network_id
          in: path
          required: true
          description: 路网ID
          schema:
            type: string
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/RoadNetworkStatsResponse'
        '404':
          description: 路网不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/files:
    get:
      tags:
        - Files
      summary: 获取文件列表
      description: 获取用户上传的文件列表
      operationId: getFiles
      parameters:
        - name: page
          in: query
          description: 页码
          required: false
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          description: 每页数量
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: type
          in: query
          description: 文件类型
          required: false
          schema:
            type: string
            enum: [gpx, kml, csv]
        - name: status
          in: query
          description: 处理状态
          required: false
          schema:
            type: string
            enum: [uploaded, processing, completed, failed]
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FileListResponse'

  /api/v1/files/{file_id}:
    delete:
      tags:
        - Files
      summary: 删除文件
      description: 删除指定的文件
      operationId: deleteFile
      parameters:
        - name: file_id
          in: path
          required: true
          description: 文件ID
          schema:
            type: string
      responses:
        '200':
          description: 删除成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/FileDeleteResponse'
        '404':
          description: 文件不存在
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  /api/v1/system/status:
    get:
      tags:
        - System
      summary: 获取系统状态
      description: 获取系统运行状态和资源使用情况
      operationId: getSystemStatus
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemStatusResponse'

  /api/v1/system/queue:
    get:
      tags:
        - System
      summary: 获取任务队列状态
      description: 获取 Celery 任务队列状态
      operationId: getQueueStatus
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/QueueStatusResponse'

  /api/v1/datasources/supported:
    get:
      tags:
        - DataSources
      summary: 获取支持的数据源
      description: 获取系统支持的数据源类型和格式
      operationId: getSupportedDataSources
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DataSourcesResponse'

  /api/v1/datasources/parse:
    post:
      tags:
        - DataSources
      summary: 解析数据文件
      description: 解析上传的数据文件并返回预览信息
      operationId: parseDataFile
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              required:
                - file
              properties:
                file:
                  type: string
                  format: binary
                  description: 数据文件
                data_type:
                  type: string
                  enum: [auto, taxi_gps, bus_card, metro_card, taxi_transaction, bus_gps, gpx, csv]
                  description: 数据类型
                  example: "auto"
      responses:
        '200':
          description: 解析成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/DataParseResponse'

  /api/v1/origin-destination/records:
    get:
      tags:
        - OriginDestination
      summary: 获取起始终止记录
      description: 获取起始终止记录列表
      operationId: getOriginDestinationRecords
      parameters:
        - name: page
          in: query
          description: 页码
          required: false
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          description: 每页数量
          required: false
          schema:
            type: integer
            default: 20
            maximum: 100
        - name: record_type
          in: query
          description: 记录类型
          required: false
          schema:
            type: string
            enum: [bus_card, metro_card, taxi_transaction]
        - name: status
          in: query
          description: 配对状态
          required: false
          schema:
            type: string
            enum: [paired, unpaired, processed]
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OriginDestinationRecordsResponse'

  /api/v1/origin-destination/pair:
    post:
      tags:
        - OriginDestination
      summary: 配对起始终止记录
      description: 配对起始终止记录（进出站配对）
      operationId: pairOriginDestinationRecords
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/PairingRequest'
      responses:
        '200':
          description: 配对成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PairingResponse'

  /api/v1/origin-destination/pairing-status:
    get:
      tags:
        - OriginDestination
      summary: 获取数据配对状态
      description: 获取数据配对状态统计
      operationId: getPairingStatus
      responses:
        '200':
          description: 获取成功
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/PairingStatusResponse'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
      description: JWT Token 认证（可选）

  schemas:
    # 基础响应模型
    BaseResponse:
      type: object
      required:
        - success
        - timestamp
      properties:
        success:
          type: boolean
          description: 操作是否成功
        message:
          type: string
          description: 响应消息
        timestamp:
          type: string
          format: date-time
          description: 响应时间戳

    ErrorResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: object
              required:
                - code
                - message
              properties:
                code:
                  type: string
                  description: 错误码
                  example: "INVALID_PARAMETER"
                message:
                  type: string
                  description: 错误消息
                  example: "请求参数无效"
                details:
                  type: object
                  description: 错误详情
                  additionalProperties: true

    # 健康检查模型
    HealthResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                status:
                  type: string
                  enum: [healthy, unhealthy]
                  example: "healthy"
                version:
                  type: string
                  example: "0.1.0"
                uptime:
                  type: integer
                  description: 运行时间（秒）
                  example: 3600
                services:
                  type: object
                  properties:
                    database:
                      type: string
                      enum: [connected, disconnected]
                      example: "connected"
                    redis:
                      type: string
                      enum: [connected, disconnected]
                      example: "connected"
                    celery:
                      type: string
                      enum: [running, stopped]
                      example: "running"

    # 轨迹相关模型
    TrajectoryUploadResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                trajectory_id:
                  type: string
                  example: "traj_123456"
                filename:
                  type: string
                  example: "example.gpx"
                file_size:
                  type: integer
                  description: 文件大小（字节）
                  example: 1024
                point_count:
                  type: integer
                  description: 轨迹点数量
                  example: 150
                upload_time:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"
                status:
                  type: string
                  enum: [uploaded, processing, completed, failed]
                  example: "uploaded"

    TrajectoryInfo:
      type: object
      properties:
        trajectory_id:
          type: string
          example: "traj_123456"
        name:
          type: string
          example: "示例轨迹"
        description:
          type: string
          example: "测试轨迹"
        filename:
          type: string
          example: "example.gpx"
        point_count:
          type: integer
          example: 150
        status:
          type: string
          enum: [uploaded, processing, completed, failed]
          example: "completed"
        created_at:
          type: string
          format: date-time
          example: "2024-01-01T00:00:00Z"
        updated_at:
          type: string
          format: date-time
          example: "2024-01-01T00:05:00Z"

    PaginationInfo:
      type: object
      properties:
        page:
          type: integer
          minimum: 1
          example: 1
        limit:
          type: integer
          minimum: 1
          maximum: 100
          example: 20
        total:
          type: integer
          minimum: 0
          example: 100
        pages:
          type: integer
          minimum: 0
          example: 5

    TrajectoryListResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                trajectories:
                  type: array
                  items:
                    $ref: '#/components/schemas/TrajectoryInfo'
                pagination:
                  $ref: '#/components/schemas/PaginationInfo'

    TrajectoryPoint:
      type: object
      properties:
        point_id:
          type: string
          example: "pt_001"
        latitude:
          type: number
          format: float
          example: 39.9042
        longitude:
          type: number
          format: float
          example: 116.4074
        elevation:
          type: number
          format: float
          nullable: true
          example: 50.0
        timestamp:
          type: string
          format: date-time
          example: "2024-01-01T00:00:00Z"
        accuracy:
          type: number
          format: float
          nullable: true
          example: 5.0

    BoundingBox:
      type: object
      properties:
        min_lat:
          type: number
          format: float
          example: 39.9
        max_lat:
          type: number
          format: float
          example: 40.0
        min_lng:
          type: number
          format: float
          example: 116.3
        max_lng:
          type: number
          format: float
          example: 116.4

    TrajectoryDetailResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              allOf:
                - $ref: '#/components/schemas/TrajectoryInfo'
                - type: object
                  properties:
                    file_size:
                      type: integer
                      example: 1024
                    bounds:
                      $ref: '#/components/schemas/BoundingBox'
                    points:
                      type: array
                      items:
                        $ref: '#/components/schemas/TrajectoryPoint'

    TrajectoryDeleteResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                trajectory_id:
                  type: string
                  example: "traj_123456"
                deleted_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"

    # 地图匹配相关模型
    MatchingRequest:
      type: object
      required:
        - trajectory_id
        - algorithm
      properties:
        trajectory_id:
          type: string
          description: 轨迹ID
          example: "traj_123456"
        algorithm:
          type: string
          enum: [hmm, greedy]
          description: 匹配算法
          example: "hmm"
        parameters:
          type: object
          description: 算法参数
          properties:
            sigma:
              type: number
              format: float
              description: HMM 算法参数
              example: 4.07
            beta:
              type: number
              format: float
              description: HMM 算法参数
              example: 0.0096
            max_dist:
              type: number
              format: float
              description: 最大匹配距离（米）
              example: 200
        road_network:
          type: string
          description: 路网数据源
          default: "default"
          example: "default"

    MatchingStartResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                task_id:
                  type: string
                  example: "task_789012"
                trajectory_id:
                  type: string
                  example: "traj_123456"
                algorithm:
                  type: string
                  example: "hmm"
                status:
                  type: string
                  enum: [queued, running, completed, failed]
                  example: "queued"
                estimated_time:
                  type: integer
                  description: 预计处理时间（秒）
                  example: 30
                created_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"

    MatchingStatusResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                task_id:
                  type: string
                  example: "task_789012"
                status:
                  type: string
                  enum: [queued, running, completed, failed]
                  example: "completed"
                progress:
                  type: integer
                  minimum: 0
                  maximum: 100
                  description: 处理进度（百分比）
                  example: 100
                result:
                  type: object
                  nullable: true
                  properties:
                    matched_points:
                      type: integer
                      example: 145
                    unmatched_points:
                      type: integer
                      example: 5
                    accuracy:
                      type: number
                      format: float
                      example: 96.7
                    processing_time:
                      type: number
                      format: float
                      example: 25.3
                created_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"
                completed_at:
                  type: string
                  format: date-time
                  nullable: true
                  example: "2024-01-01T00:00:25Z"

    MatchedPoint:
      type: object
      properties:
        point_id:
          type: string
          example: "pt_001"
        original_lat:
          type: number
          format: float
          example: 39.9042
        original_lng:
          type: number
          format: float
          example: 116.4074
        matched_lat:
          type: number
          format: float
          example: 39.9043
        matched_lng:
          type: number
          format: float
          example: 116.4075
        road_id:
          type: string
          example: "road_001"
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
          example: 0.95
        distance:
          type: number
          format: float
          example: 12.5

    MatchingStatistics:
      type: object
      properties:
        total_points:
          type: integer
          example: 150
        matched_points:
          type: integer
          example: 145
        unmatched_points:
          type: integer
          example: 5
        accuracy:
          type: number
          format: float
          example: 96.7
        avg_confidence:
          type: number
          format: float
          example: 0.89
        processing_time:
          type: number
          format: float
          example: 25.3

    MatchingResultResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                task_id:
                  type: string
                  example: "task_789012"
                trajectory_id:
                  type: string
                  example: "traj_123456"
                algorithm:
                  type: string
                  example: "hmm"
                status:
                  type: string
                  example: "completed"
                result:
                  type: object
                  properties:
                    matched_trajectory:
                      type: object
                      properties:
                        points:
                          type: array
                          items:
                            $ref: '#/components/schemas/MatchedPoint'
                        total_distance:
                          type: number
                          format: float
                          example: 1500.0
                        matched_distance:
                          type: number
                          format: float
                          example: 1450.0
                    statistics:
                      $ref: '#/components/schemas/MatchingStatistics'
                created_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"
                completed_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:25Z"

    # 路网相关模型
    RoadNetworkInfo:
      type: object
      properties:
        network_id:
          type: string
          example: "default"
        name:
          type: string
          example: "默认路网"
        description:
          type: string
          example: "基于 OpenStreetMap 的路网数据"
        coverage:
          type: object
          properties:
            bounds:
              $ref: '#/components/schemas/BoundingBox'
            area:
              type: string
              example: "北京市"
        statistics:
          type: object
          properties:
            total_roads:
              type: integer
              example: 50000
            total_length:
              type: number
              format: float
              example: 15000.5
        last_updated:
          type: string
          format: date-time
          example: "2024-01-01T00:00:00Z"

    RoadNetworkListResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                networks:
                  type: array
                  items:
                    $ref: '#/components/schemas/RoadNetworkInfo'

    RoadNetworkStatsResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                network_id:
                  type: string
                  example: "default"
                statistics:
                  type: object
                  properties:
                    total_roads:
                      type: integer
                      example: 50000
                    total_length:
                      type: number
                      format: float
                      example: 15000.5
                    road_types:
                      type: object
                      additionalProperties:
                        type: integer
                      example:
                        highway: 25000
                        primary: 15000
                        secondary: 10000
                    coverage_area:
                      type: number
                      format: float
                      example: 16410.54
                last_updated:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"

    # 文件管理相关模型
    FileInfo:
      type: object
      properties:
        file_id:
          type: string
          example: "file_123456"
        filename:
          type: string
          example: "example.gpx"
        file_type:
          type: string
          enum: [gpx, kml, csv, txt]
          example: "txt"
        data_source:
          type: string
          enum: [gpx, taxi_gps, bus_card, metro_card, taxi_transaction, bus_gps, csv]
          example: "taxi_gps"
        data_category:
          type: string
          enum: [continuous_trajectory, origin_destination, time_range]
          example: "continuous_trajectory"
        file_size:
          type: integer
          example: 1024
        status:
          type: string
          enum: [uploaded, processing, completed, failed]
          example: "processed"
        uploaded_at:
          type: string
          format: date-time
          example: "2024-01-01T00:00:00Z"

    FileListResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                files:
                  type: array
                  items:
                    $ref: '#/components/schemas/FileInfo'
                pagination:
                  $ref: '#/components/schemas/PaginationInfo'

    FileDeleteResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                file_id:
                  type: string
                  example: "file_123456"
                deleted_at:
                  type: string
                  format: date-time
                  example: "2024-01-01T00:00:00Z"

    # 系统管理相关模型
    SystemStatusResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                system:
                  type: object
                  properties:
                    uptime:
                      type: integer
                      example: 3600
                    version:
                      type: string
                      example: "0.1.0"
                    environment:
                      type: string
                      example: "production"
                services:
                  type: object
                  properties:
                    database:
                      type: object
                      properties:
                        status:
                          type: string
                          enum: [connected, disconnected]
                          example: "connected"
                        response_time:
                          type: number
                          format: float
                          example: 5.2
                    redis:
                      type: object
                      properties:
                        status:
                          type: string
                          enum: [connected, disconnected]
                          example: "connected"
                        memory_usage:
                          type: string
                          example: "45%"
                    celery:
                      type: object
                      properties:
                        status:
                          type: string
                          enum: [running, stopped]
                          example: "running"
                        active_tasks:
                          type: integer
                          example: 2
                        queued_tasks:
                          type: integer
                          example: 5
                resources:
                  type: object
                  properties:
                    cpu_usage:
                      type: string
                      example: "25%"
                    memory_usage:
                      type: string
                      example: "60%"
                    disk_usage:
                      type: string
                      example: "40%"

    QueueStatusResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                queues:
                  type: object
                  additionalProperties:
                    type: object
                    properties:
                      active:
                        type: integer
                        example: 2
                      scheduled:
                        type: integer
                        example: 3
                      reserved:
                        type: integer
                        example: 1
                workers:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        example: "celery@worker-1"
                      status:
                        type: string
                        enum: [online, offline]
                        example: "online"
                      active_tasks:
                        type: integer
                        example: 1
                      processed_tasks:
                        type: integer
                        example: 150

    # 数据源相关模型
    DataSourceInfo:
      type: object
      properties:
        type:
          type: string
          example: "taxi_gps"
        name:
          type: string
          example: "出租车GPS数据"
        description:
          type: string
          example: "出租车GPS轨迹数据"
        format:
          type: string
          example: "日期,时间,类型,车牌号,经度,纬度,速度,方向,状态,未知"
        example:
          type: string
          example: "20160831,235926,H,粤BL3F79,113.823601,22.614317,84.0,243,0,1"
        supported_extensions:
          type: array
          items:
            type: string
          example: [".txt", ".csv"]

    DataSourcesResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                data_sources:
                  type: array
                  items:
                    $ref: '#/components/schemas/DataSourceInfo'

    DataParseResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                detected_type:
                  type: string
                  example: "taxi_gps"
                total_records:
                  type: integer
                  example: 100
                sample_data:
                  type: array
                  items:
                    type: object
                  example:
                    - date: "20160831"
                      time: "235926"
                      type: "H"
                      vehicle_id: "粤BL3F79"
                      longitude: 113.823601
                      latitude: 22.614317
                      speed: 84.0
                      direction: 243
                      status: 0
                fields:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                      type:
                        type: string
                      description:
                        type: string
                  example:
                    - name: "date"
                      type: "string"
                      description: "日期 (YYYYMMDD)"
                    - name: "time"
                      type: "string"
                      description: "时间 (HHMMSS)"
                    - name: "vehicle_id"
                      type: "string"
                      description: "车牌号"

    # 起始终止数据相关模型
    OriginDestinationRecord:
      type: object
      properties:
        record_id:
          type: string
          example: "od_123456"
        trajectory_id:
          type: string
          example: "traj_123456"
        record_type:
          type: string
          enum: [bus_card, metro_card, taxi_transaction]
          example: "bus_card"
        passenger_id:
          type: string
          example: "291403498"
        origin_station:
          type: string
          example: "东湖客运站"
        destination_station:
          type: string
          example: "世界之窗"
        origin_time:
          type: string
          format: date-time
          example: "2025-09-16T07:00:51Z"
        destination_time:
          type: string
          format: date-time
          example: "2025-09-16T07:30:15Z"
        line_id:
          type: string
          example: "605路31"
        vehicle_id:
          type: string
          example: "粤B72366"
        fare:
          type: number
          example: 200
        distance:
          type: number
          example: 15000
        duration:
          type: integer
          example: 1764
        status:
          type: string
          enum: [paired, unpaired, processed]
          example: "paired"

    OriginDestinationRecordsResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                records:
                  type: array
                  items:
                    $ref: '#/components/schemas/OriginDestinationRecord'
                pagination:
                  $ref: '#/components/schemas/PaginationInfo'

    PairingRequest:
      type: object
      required:
        - record_type
      properties:
        record_type:
          type: string
          enum: [bus_card, metro_card, taxi_transaction]
          example: "metro_card"
        pairing_criteria:
          type: object
          properties:
            time_window:
              type: integer
              description: 时间窗口（秒）
              example: 3600
            max_distance:
              type: number
              description: 最大距离（米）
              example: 1000

    PairingResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                paired_count:
                  type: integer
                  example: 150
                unpaired_count:
                  type: integer
                  example: 25
                pairing_results:
                  type: array
                  items:
                    type: object
                    properties:
                      record_id:
                        type: string
                      status:
                        type: string
                        enum: [paired, unpaired, failed]
                      confidence:
                        type: number
                        format: float

    PairingStatusResponse:
      allOf:
        - $ref: '#/components/schemas/BaseResponse'
        - type: object
          properties:
            success:
              type: boolean
              example: true
            data:
              type: object
              properties:
                total_records:
                  type: integer
                  example: 1000
                paired_records:
                  type: integer
                  example: 850
                unpaired_records:
                  type: integer
                  example: 150
                pairing_rate:
                  type: number
                  format: float
                  example: 85.0
                by_type:
                  type: object
                  properties:
                    bus_card:
                      type: object
                      properties:
                        total:
                          type: integer
                        paired:
                          type: integer
                        rate:
                          type: number
                          format: float
                    metro_card:
                      type: object
                      properties:
                        total:
                          type: integer
                        paired:
                          type: integer
                        rate:
                          type: number
                          format: float
                    taxi_transaction:
                      type: object
                      properties:
                        total:
                          type: integer
                        paired:
                          type: integer
                        rate:
                          type: number
                          format: float

security:
  - BearerAuth: []
```

## 使用说明

### 1. 生成客户端 SDK

可以使用 OpenAPI Generator 根据此规范生成各种语言的客户端 SDK：

```bash
# 生成 Python 客户端
openapi-generator generate -i api-spec.yaml -g python -o ./clients/python

# 生成 JavaScript 客户端
openapi-generator generate -i api-spec.yaml -g javascript -o ./clients/javascript

# 生成 Java 客户端
openapi-generator generate -i api-spec.yaml -g java -o ./clients/java
```

### 2. 生成 API 文档

可以使用 Swagger UI 或 Redoc 生成交互式 API 文档：

```bash
# 使用 Swagger UI
npx swagger-ui-serve api-spec.yaml

# 使用 Redoc
npx redoc-cli serve api-spec.yaml
```

### 3. 验证 API 实现

可以使用 OpenAPI 规范验证 API 实现是否符合规范：

```bash
# 使用 swagger-codegen 验证
swagger-codegen validate -i api-spec.yaml

# 使用 spectral 验证
npx @stoplight/spectral lint api-spec.yaml
```

## 更新日志

### v0.1.0 (2024-01-01)
- 初始版本发布
- 定义完整的 API 规范
- 支持所有核心功能接口
- 提供详细的模型定义和示例
