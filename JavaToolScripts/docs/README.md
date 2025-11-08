# Java GPS 数据处理工具

该目录包含用于处理 GPS 数据文件并将其存储到 MongoDB 的 Java 工具。

## 项目结构

```
JavaToolScripts/
├── docs/
│   └── README.md
├── logs/
│   ├── invalid_data.log
│   └── parsing_errors.log
├── scripts/
│   ├── build.bat
│   ├── compile.bat
│   ├── run.bat
│   └── run-all.bat
├── src/
│   └── main/
│       └── java/
│           └── com/
│               └── maptools/
│                   └── gpstools/
│                       ├── admin/
│                       │   ├── InitializeAdministrativeAreas.java
│                       │   └── UpdateAdministrativeAreas.java
│                       ├── algorithm/
│                       │   ├── AdjacencyConsistencyModel.java
│                       │   ├── HmmModel.java
│                       │   ├── JavaRoadMatcher.java
│                       │   └── RoadTransitionModel.java
│                       ├── model/
│                       │   ├── GPSDataPoint.java
│                       │   └── TrajectoryMetrics.java
│                       ├── parser/
│                       │   └── GPSDataParser.java
│                       ├── processor/
│                       │   ├── GPSDataProcessor.java
│                       │   ├── JavaTrajectoryProcessor.java
│                       │   └── TrajectoryCorrectionProcessor.java
│                       ├── service/
│                       │   ├── RoadMatcherService.java
│                       │   └── TrajectoryService.java
│                       ├── storage/
│                       │   ├── MongoDataStore.java
│                       │   └── MongoIndexManager.java
│                       ├── util/
│                       │   ├── ConfigManager.java
│                       │   ├── GeoFilter.java
│                       │   └── TrajectoryCorrectionUtils.java
│                       └── GPSDataProcessor.java (主处理类)
├── pom.xml
└── target/
    └── gps-data-processor-1.0-SNAPSHOT.jar
```

## 前提条件

- Java 8 或更高版本
- Maven
- 运行在 localhost:27017 的 MongoDB 服务器

## 构建项目

### 直接使用 Maven:
```bash
cd JavaToolScripts
mvn clean package
```

### 使用 Windows 批处理文件:
1. `scripts\compile.bat` - 编译源代码
2. `scripts\build.bat` - 构建 JAR 包
3. `scripts\run-all.bat` - 编译、构建和运行工具的一键脚本

## 运行工具

### 使用 Maven 运行数据处理:
```bash
cd JavaToolScripts
mvn exec:java -Dexec.mainClass=com.maptools.gpstools.processor.GPSDataProcessor -Dexec.args="../data/01"
```

### 使用 Maven 运行轨迹生成:
```bash
cd JavaToolScripts
mvn exec:java -Dexec.mainClass=com.maptools.gpstools.processor.JavaTrajectoryProcessor
```

### 使用 Maven 运行轨迹修正:
```bash
cd JavaToolScripts
mvn exec:java -Dexec.mainClass=com.maptools.gpstools.processor.TrajectoryCorrectionProcessor
```

### 使用 Java 运行 JAR 包:
```bash
cd JavaToolScripts
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.processor.GPSDataProcessor ../data/01
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.processor.JavaTrajectoryProcessor
java -cp target/gps-data-processor-1.0-SNAPSHOT.jar com.maptools.gpstools.processor.TrajectoryCorrectionProcessor
```

### 使用 Windows 批处理文件:
```bash
scripts\run.bat [数据目录]
```
或
```bash
scripts\run-all.bat [数据目录]
```

如果未指定数据目录，默认使用 `../data`。

## 数据处理说明

### 多阶段处理流程

Java工具现在包含三个主要处理阶段：

1. **原始数据处理** (`GPSDataProcessor`)
   - 读取原始GPS数据文件
   - 解析并验证数据
   - 存储到MongoDB的`gps_points_XX`集合

2. **轨迹生成** (`JavaTrajectoryProcessor`)
   - 从`gps_points_XX`集合读取数据
   - 按车牌号聚合生成轨迹
   - 进行道路匹配
   - 存储到`original_trajectories_XX`集合

3. **轨迹修正** (`TrajectoryCorrectionProcessor`)
   - 从`original_trajectories_XX`集合读取轨迹
   - 使用HMM模型、道路切换模型和相邻一致性模型进行异常点检测
   - 过滤异常点并优化轨迹
   - 存储到`corrected_trajectories_XX`集合

### 多线程处理
工具使用多线程处理数据文件，默认线程池大小为10。每个文件由一个独立线程处理，大大提高了处理速度。

### 进度跟踪
处理过程中会显示详细的进度信息：
- 正在处理的文件名和索引（例如：Starting to process file (1/281): 20160901_001-utf.txt）
- 每个文件处理完成后的记录数和耗时
- 总体进度（例如：[10/281 files completed]）

### 错误处理和日志
- 无效的GPS坐标数据会被跳过，并记录到 `logs/invalid_data.log` 文件中
- 解析错误会被记录到 `logs/parsing_errors.log` 文件中
- 终端只显示处理进度信息，不会显示错误详情

## 数据结构

GPS 数据文件包含以下格式的记录：
```
日期,时间,类型,车牌号,经度,纬度,速度,方向,保留字段,定位状态
```

示例：
```
20160831,235926,H,粤BL3F79,113.823601,22.614317,84.0,243,0,1
```

解析后的数据结构与 Python 脚本保持一致：
- plate_number: 车牌号
- datetime: 日期时间（ISO格式）
- date: 日期（YYYYMMDD）
- time: 时间（HHMMSS）
- record_type: 记录类型（H 或 L）
- location: 地理位置（GeoJSON 格式）
  - type: "Point"
  - coordinates: [经度, 纬度]
- speed: 速度
- heading: 方向
- reserved_field: 保留字段
- location_flag: 定位状态
- is_valid: 是否有效（location_flag == 1）
- source_file: 源文件名

## MongoDB 集合

数据处理涉及多个MongoDB集合：

### 原始GPS点集合
- `data/01/` 目录的数据 -> `gps_points_01` 集合
- `data/02/` 目录的数据 -> `gps_points_02` 集合
- `data/03/` 目录的数据 -> `gps_points_03` 集合

### 原始轨迹集合
- `gps_points_01` 数据 -> `original_trajectories_01` 集合
- `gps_points_02` 数据 -> `original_trajectories_02` 集合
- `gps_points_03` 数据 -> `original_trajectories_03` 集合

### 修正轨迹集合
- `original_trajectories_01` 数据 -> `corrected_trajectories_01` 集合
- `original_trajectories_02` 数据 -> `corrected_trajectories_02` 集合
- `original_trajectories_03` 数据 -> `corrected_trajectories_03` 集合

目录中的所有文件数据都会存储在同一个集合中，以提高查询效率。