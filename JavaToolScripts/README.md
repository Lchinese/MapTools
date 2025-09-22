# MapTools Java Tools

MapTools轨迹匹配系统的Java数据处理工具，用于高性能的GPS数据处理和MongoDB数据存储。

## 🚀 快速开始

### 环境要求

- Java 11+ (推荐 17+)
- Maven 3.6+
- MongoDB 6.0+

### 安装依赖

```bash
# 进入Java工具目录
cd JavaToolScripts

# 安装依赖
mvn clean install

# 或跳过测试安装
mvn clean install -DskipTests
```

### 运行工具

```bash
# 编译项目
mvn compile

# 运行所有工具
./scripts/run-all.bat  # Windows
# 或
./scripts/run-all.sh   # Linux/macOS

# 运行单个工具
./scripts/run.bat      # Windows
# 或
./scripts/run.sh       # Linux/macOS
```

## 📦 依赖说明

### 核心依赖

| 包名 | 版本 | 说明 |
|------|------|------|
| maven-compiler-plugin | 3.11.0 | Java编译插件 |
| maven-surefire-plugin | 3.1.2 | 测试运行插件 |
| maven-jar-plugin | 3.3.0 | JAR打包插件 |

### MongoDB驱动

| 包名 | 版本 | 说明 |
|------|------|------|
| mongodb-driver-sync | 4.10.2 | MongoDB同步驱动 |
| mongodb-driver-core | 4.10.2 | MongoDB核心驱动 |
| bson | 4.10.2 | BSON数据处理 |

### 地理空间处理

| 包名 | 版本 | 说明 |
|------|------|------|
| geotools-core | 30.0 | 地理空间工具核心 |
| geotools-main | 30.0 | 主要功能模块 |
| geotools-geometry | 30.0 | 几何处理模块 |
| geotools-referencing | 30.0 | 坐标参考系统 |
| geotools-metadata | 30.0 | 元数据处理 |

### 数据处理

| 包名 | 版本 | 说明 |
|------|------|------|
| commons-csv | 1.10.0 | CSV文件处理 |
| commons-io | 2.11.0 | IO工具类 |
| commons-lang3 | 3.12.0 | 通用工具类 |

### 日志处理

| 包名 | 版本 | 说明 |
|------|------|------|
| slf4j-api | 2.0.9 | 日志接口 |
| logback-classic | 1.4.11 | 日志实现 |
| logback-core | 1.4.11 | 日志核心 |

## 🏗️ 项目结构

```
JavaToolScripts/
├── src/
│   └── main/
│       └── java/
│           └── com/
│               └── maptools/
│                   └── gpstools/
│                       ├── GPSDataParser.java      # GPS数据解析器
│                       ├── GPSDataPoint.java       # GPS数据点模型
│                       ├── GPSDataProcessor.java   # GPS数据处理器
│                       └── MongoDataStore.java     # MongoDB数据存储
├── scripts/
│   ├── build.bat          # 构建脚本 (Windows)
│   ├── build.sh           # 构建脚本 (Linux/macOS)
│   ├── compile.bat        # 编译脚本 (Windows)
│   ├── compile.sh         # 编译脚本 (Linux/macOS)
│   ├── run.bat            # 运行脚本 (Windows)
│   ├── run.sh             # 运行脚本 (Linux/macOS)
│   ├── run-all.bat        # 批量运行脚本 (Windows)
│   └── run-all.sh         # 批量运行脚本 (Linux/macOS)
├── docs/
│   └── README.md          # 文档
├── pom.xml                # Maven配置
└── target/                # 构建输出目录
```

## 🔧 配置说明

### Maven配置 (pom.xml)

```xml
<properties>
    <maven.compiler.source>11</maven.compiler.source>
    <maven.compiler.target>11</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
</properties>

<dependencies>
    <!-- MongoDB驱动 -->
    <dependency>
        <groupId>org.mongodb</groupId>
        <artifactId>mongodb-driver-sync</artifactId>
        <version>4.10.2</version>
    </dependency>
    
    <!-- 地理空间处理 -->
    <dependency>
        <groupId>org.geotools</groupId>
        <artifactId>gt-main</artifactId>
        <version>30.0</version>
    </dependency>
    
    <!-- 其他依赖... -->
</dependencies>
```

### 数据库配置

在代码中配置MongoDB连接：

```java
// MongoDB连接配置
String connectionString = "mongodb://localhost:27017";
String databaseName = "maptools";
String collectionName = "gps_points";
```

## 📋 工具说明

### 1. GPSDataParser

GPS数据解析器，支持多种格式的GPS数据文件。

**功能特性：**
- 支持CSV、TXT格式
- 自动识别数据格式
- 数据验证和清洗
- 批量处理支持

**使用方法：**
```java
GPSDataParser parser = new GPSDataParser();
List<GPSDataPoint> points = parser.parseFile("data/gps_data.txt");
```

### 2. GPSDataPoint

GPS数据点模型，表示单个GPS坐标点。

**属性：**
- `latitude`: 纬度
- `longitude`: 经度
- `timestamp`: 时间戳
- `altitude`: 海拔高度
- `speed`: 速度
- `heading`: 方向角

**示例：**
```java
GPSDataPoint point = new GPSDataPoint();
point.setLatitude(22.5431);
point.setLongitude(114.0579);
point.setTimestamp(System.currentTimeMillis());
```

### 3. GPSDataProcessor

GPS数据处理器，提供数据清洗和预处理功能。

**功能特性：**
- 数据去重
- 异常值检测
- 数据插值
- 轨迹平滑

**使用方法：**
```java
GPSDataProcessor processor = new GPSDataProcessor();
List<GPSDataPoint> cleanedPoints = processor.cleanData(rawPoints);
```

### 4. MongoDataStore

MongoDB数据存储类，负责数据的持久化存储。

**功能特性：**
- 批量插入
- 地理空间索引
- 数据查询
- 连接池管理

**使用方法：**
```java
MongoDataStore store = new MongoDataStore();
store.connect("mongodb://localhost:27017", "maptools");
store.insertGPSPoints(points);
```

## 🚀 使用示例

### 完整的数据处理流程

```java
public class DataProcessingExample {
    public static void main(String[] args) {
        try {
            // 1. 解析GPS数据
            GPSDataParser parser = new GPSDataParser();
            List<GPSDataPoint> rawPoints = parser.parseFile("data/input.txt");
            
            // 2. 数据清洗
            GPSDataProcessor processor = new GPSDataProcessor();
            List<GPSDataPoint> cleanedPoints = processor.cleanData(rawPoints);
            
            // 3. 存储到MongoDB
            MongoDataStore store = new MongoDataStore();
            store.connect("mongodb://localhost:27017", "maptools");
            store.insertGPSPoints(cleanedPoints);
            
            System.out.println("数据处理完成，共处理 " + cleanedPoints.size() + " 个点");
            
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}
```

### 批量处理多个文件

```java
public class BatchProcessingExample {
    public static void main(String[] args) {
        String[] files = {
            "data/file1.txt",
            "data/file2.txt",
            "data/file3.txt"
        };
        
        GPSDataParser parser = new GPSDataParser();
        GPSDataProcessor processor = new GPSDataProcessor();
        MongoDataStore store = new MongoDataStore();
        
        store.connect("mongodb://localhost:27017", "maptools");
        
        for (String file : files) {
            try {
                List<GPSDataPoint> points = parser.parseFile(file);
                List<GPSDataPoint> cleanedPoints = processor.cleanData(points);
                store.insertGPSPoints(cleanedPoints);
                System.out.println("处理完成: " + file);
            } catch (Exception e) {
                System.err.println("处理失败: " + file + " - " + e.getMessage());
            }
        }
    }
}
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
mvn test

# 运行特定测试类
mvn test -Dtest=GPSDataParserTest

# 生成测试报告
mvn surefire-report:report
```

### 测试配置

测试使用H2内存数据库，配置在 `src/test/resources/` 目录下。

## 📊 性能优化

### 1. 批量处理

```java
// 使用批量插入提高性能
List<GPSDataPoint> batch = new ArrayList<>();
for (GPSDataPoint point : points) {
    batch.add(point);
    if (batch.size() >= 1000) {
        store.insertGPSPoints(batch);
        batch.clear();
    }
}
if (!batch.isEmpty()) {
    store.insertGPSPoints(batch);
}
```

### 2. 连接池配置

```java
// 配置MongoDB连接池
MongoClientSettings settings = MongoClientSettings.builder()
    .applyConnectionString(new ConnectionString(connectionString))
    .applyToConnectionPoolSettings(builder -> 
        builder.maxSize(20)
               .minSize(5)
               .maxWaitTime(30, TimeUnit.SECONDS))
    .build();
```

### 3. 内存管理

```java
// 使用流式处理大文件
public void processLargeFile(String filename) {
    try (Stream<String> lines = Files.lines(Paths.get(filename))) {
        lines.forEach(this::processLine);
    } catch (IOException e) {
        e.printStackTrace();
    }
}
```

## 🚀 部署

### 构建JAR文件

```bash
# 构建可执行JAR
mvn clean package

# 运行JAR文件
java -jar target/maptools-java-tools-1.0.0.jar
```

### Docker部署

```dockerfile
FROM openjdk:17-jre-slim

COPY target/maptools-java-tools-1.0.0.jar app.jar

ENTRYPOINT ["java", "-jar", "app.jar"]
```

## 🔍 监控和调试

### 日志配置

在 `src/main/resources/logback.xml` 中配置日志：

```xml
<configuration>
    <appender name="STDOUT" class="ch.qos.logback.core.ConsoleAppender">
        <encoder>
            <pattern>%d{HH:mm:ss.SSS} [%thread] %-5level %logger{36} - %msg%n</pattern>
        </encoder>
    </appender>
    
    <root level="INFO">
        <appender-ref ref="STDOUT" />
    </root>
</configuration>
```

### 性能监控

```java
// 添加性能监控
long startTime = System.currentTimeMillis();
// ... 处理逻辑 ...
long endTime = System.currentTimeMillis();
System.out.println("处理耗时: " + (endTime - startTime) + "ms");
```

## 🤝 开发指南

### 添加新功能

1. 在 `src/main/java/com/maptools/gpstools/` 创建新类
2. 实现相应的接口或继承基类
3. 添加单元测试
4. 更新文档

### 代码规范

- 使用Java 11+特性
- 遵循Google Java Style Guide
- 添加适当的注释和文档
- 编写单元测试

### 错误处理

```java
public class ErrorHandlingExample {
    public void processData(String filename) {
        try {
            // 处理逻辑
        } catch (FileNotFoundException e) {
            logger.error("文件未找到: " + filename, e);
        } catch (IOException e) {
            logger.error("IO错误: " + filename, e);
        } catch (Exception e) {
            logger.error("未知错误: " + filename, e);
        }
    }
}
```

## 📄 许可证

MIT License
