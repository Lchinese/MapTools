# MapTools Java Tools

MapTools轨迹匹配系统的Java数据处理工具，用于高性能的GPS数据处理和MongoDB数据存储。

## 🚀 快速开始

### 环境要求

- Java 8+ (使用Maven编译)
- Maven 3.6+
- MongoDB 3.0+

### 安装依赖

```bash
# 进入Java工具目录
cd JavaToolScripts

# 安装依赖并打包
mvn clean package

# 或跳过测试安装
mvn clean package -DskipTests
```

### 运行工具

```bash
# 编译项目
mvn compile

# 打包项目
mvn package

# 运行数据处理工具
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.GPSDataProcessor <data_directory>
```

## 📦 依赖说明

### 核心依赖

| 包名 | 版本 | 说明 |
|------|------|------|
| maven-compiler-plugin | 3.8.1 | Java编译插件 |
| maven-jar-plugin | 3.2.0 | JAR打包插件 |
| maven-shade-plugin | 3.2.4 | JAR打包插件 |

### MongoDB驱动

| 包名 | 版本 | 说明 |
|------|------|------|
| mongo-java-driver | 3.12.11 | MongoDB驱动 |

### 地理空间处理

| 包名 | 版本 | 说明 |
|------|------|------|
| geotools-main | 24.0 | 地理空间工具核心 |
| geotools-geojson | 24.0 | GeoJSON处理 |
| geotools-geometry | 24.0 | 几何处理模块 |
| jts-core | 1.17.1 | JTS拓扑套件 |

### 数据处理

| 包名 | 版本 | 说明 |
|------|------|------|
| gson | 2.8.9 | JSON处理 |

### 日志处理

| 包名 | 版本 | 说明 |
|------|------|------|
| logback-classic | 1.2.3 | 日志处理 |

## 🏗️ 项目结构

```
JavaToolScripts/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/
│       │       └── maptools/
│       │           └── gpstools/
│       │               ├── ConfigManager.java          # 配置管理器
│       │               ├── GPSDataPoint.java           # GPS数据点模型
│       │               ├── GPSDataParser.java          # GPS数据解析器
│       │               ├── GPSDataProcessor.java       # GPS数据处理器
│       │               ├── GeoFilter.java              # 地理筛选器
│       │               ├── MongoDataStore.java         # MongoDB数据存储
│       │               ├── APIRateLimiter.java         # API频率限制器
│       │               ├── InitializeAdministrativeAreas.java  # 初始化行政区划数据
│       │               ├── UpdateAdministrativeAreas.java      # 更新行政区划数据
│       │               ├── JavaRoadMatcher.java        # Java道路匹配器
│       │               └── JavaTrajectoryProcessor.java # Java轨迹处理器
│       └── resources/
│           ├── application.properties                  # 配置文件
│           └── application.properties.example          # 配置文件示例
├── pom.xml                                            # Maven配置
└── target/                                            # 构建输出目录
```

## 🔧 配置说明

### Maven配置 (pom.xml)

```xml
<properties>
    <maven.compiler.source>1.8</maven.compiler.source>
    <maven.compiler.target>1.8</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>

<dependencies>
    <!-- MongoDB驱动 -->
    <dependency>
        <groupId>org.mongodb</groupId>
        <artifactId>mongo-java-driver</artifactId>
        <version>3.12.11</version>
    </dependency>
    
    <!-- 地理空间处理 -->
    <dependency>
        <groupId>org.geotools</groupId>
        <artifactId>gt-main</artifactId>
        <version>24.0</version>
    </dependency>
    
    <!-- 其他依赖... -->
</dependencies>
```

### 配置文件

复制配置文件示例并根据需要进行修改：

```bash
cp src/main/resources/application.properties.example src/main/resources/application.properties
```

配置参数说明：

```properties
# MongoDB配置
mongodb.connection.string=mongodb://localhost:27017
mongodb.database.name=MapTools

# 天地图API配置
tianditu.api.key=your_real_tianditu_api_key_here
tianditu.admin.api.url=http://api.tianditu.gov.cn/v2/administrative

# 地理筛选配置
default.area.code=156440300
default.area.name=深圳市

# API请求频率控制
api.rate.limit.min.interval=1000
api.rate.limit.daily.max=10000

# 日志配置
log.directory=logs
```

## 📋 工具说明

### 1. GPSDataParser

GPS数据解析器，支持解析特定格式的GPS数据文件。

**功能特性：**
- 支持特定格式的TXT文件
- 解析经纬度、时间、车牌号等信息
- 数据验证
- 单行数据解析接口，支持流式处理

**使用方法：**
```java
GPSDataParser parser = new GPSDataParser();
List<GPSDataPoint> points = parser.parseFile("data/gps_data.txt");
// 或者解析单行数据
GPSDataPoint point = parser.parseLine(line, lineNumber, sourceFile);
```

### 2. GPSDataPoint

GPS数据点模型，表示单个GPS坐标点。

**属性：**
- `latitude`: 纬度
- `longitude`: 经度
- `plateNumber`: 车牌号
- `datetime`: 时间

### 3. GPSDataProcessor

GPS数据处理器，提供数据处理和筛选功能。

**功能特性：**
- 递归处理目录中的所有数据文件
- 地理区域筛选（基于行政区划边界）
- 数据存储到MongoDB
- 内存优化的流式处理，避免大文件导致的内存溢出
- 可配置的线程池大小和批处理大小

**使用方法：**
```bash
# 处理数据目录中的所有文件，不进行地理筛选
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.GPSDataProcessor <data_directory> --no-filter

# 处理数据目录中的所有文件，使用默认区域筛选
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.GPSDataProcessor <data_directory> --filter-area=156440300
```

### 4. GeoFilter

地理筛选器，提供基于行政区划边界的地理筛选功能。

**功能特性：**
- 点是否在指定区域内的判断
- 基于行政区划代码的批量筛选
- 边界数据缓存到MongoDB
- 使用天地图API获取行政区划边界

### 5. MongoDataStore

MongoDB数据存储类，负责数据的持久化存储。

**功能特性：**
- 连接MongoDB
- 插入GPS点数据
- 存储行政区划边界数据
- 创建地理空间索引
- 批量插入优化，提高写入效率
- 异常处理机制，增强数据存储可靠性

### 6. APIRateLimiter

API频率限制器，控制对天地图API的请求频率。

**功能特性：**
- 请求间隔控制（避免请求过于频繁）
- 每日请求次数限制
- 自动等待机制

### 7. InitializeAdministrativeAreas

初始化行政区划数据工具，创建行政区划数据集合。

### 8. UpdateAdministrativeAreas

更新行政区划边界数据工具，从天地图API获取最新的行政区划边界数据。

### 9. JavaRoadMatcher

Java道路匹配器，用于将GPS点匹配到最近的道路。

**功能特性：**
- 从MongoDB加载道路网络数据
- 将GPS点匹配到最近的道路
- 多线程处理支持
- 内存优化和缓存机制

### 10. JavaTrajectoryProcessor

Java轨迹处理器，用于将GPS点转换为轨迹数据。

**功能特性：**
- 将GPS点按车牌号聚合为轨迹
- 支持道路匹配（可选）
- 多线程处理支持
- 内存管理和优化
- 防止重复处理机制
- 批量处理优化，减少内存占用

## 🚀 使用示例

### 完整的数据处理流程

```
# 1. 初始化行政区划数据
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.InitializeAdministrativeAreas

# 2. 更新行政区划边界数据（需要配置天地图API密钥）
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.UpdateAdministrativeAreas

# 3. 处理GPS数据
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.GPSDataProcessor ../data

# 4. 处理轨迹数据（带道路匹配）
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.JavaTrajectoryProcessor true

# 5. 处理轨迹数据（不带道路匹配）
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.JavaTrajectoryProcessor false
```

## 📊 性能优化

### 1. 批量处理

工具自动递归处理整个目录结构，批量处理所有数据文件。最新优化版本采用流式处理，避免一次性加载大文件到内存中。

### 2. 数据缓存

行政区划边界数据会缓存到MongoDB中，避免重复API请求。

### 3. API频率控制

实现API请求频率控制，避免因请求过于频繁而被限制访问。

### 4. 多线程处理

JavaRoadMatcher和JavaTrajectoryProcessor支持多线程处理，提高处理效率。GPS数据处理器采用可配置线程池，默认线程数已优化以平衡性能和资源消耗。

### 5. 内存管理

实现内存管理和优化机制，包括软引用缓存和定期垃圾回收建议。最新的优化包括：
- 分批处理大文件数据，显著降低内存峰值使用
- 调整线程池大小以减少并发内存压力
- 优化MongoDB写入操作，增加容错处理机制

### 6. 数据库优化

MongoDB写入操作经过优化，包括：
- 批量插入以提高写入效率
- 异常处理机制，当批量插入失败时自动降级为逐条插入
- 索引创建优化，避免重复创建索引

## 🚀 部署

### 构建JAR文件

```
# 构建可执行JAR
mvn clean package
```

生成的JAR文件位于 `target/gps-data-processor-1.0-SNAPSHOT.jar`。

### 运行JAR文件

```
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.GPSDataProcessor <data_directory>
```

## 🔍 监控和调试

工具会在控制台输出处理进度和结果，并在logs目录下生成日志文件。

## 🤝 开发指南

### 添加新功能

1. 在 `src/main/java/com/maptools/gpstools/` 创建新类
2. 实现相应的功能
3. 更新文档

### 代码规范

- 使用Java 8特性
- 遵循标准Java命名规范
- 添加适当的注释

## 📄 许可证

MIT License
