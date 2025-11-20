# ELK集中式日志管理指南

## 概述

本文档介绍了如何使用ELK（Elasticsearch, Logstash, Kibana）堆栈来集中管理MapTools项目的日志。通过统一日志目录和格式，我们能够更有效地监控、分析和排查系统问题。

## 架构设计

```
MapTools应用
     |
     | (日志文件)
     v
  Logstash
     |
     | (处理和解析)
     v
 Elasticsearch
     |
     | (存储和索引)
     v
  Kibana
     |
     | (可视化和查询)
     v
   用户界面
```

## 日志目录结构

```
shared_logs/
├── app/                 # 应用日志
│   ├── app.log          # 标准日志文件
│   ├── app.json         # JSON格式日志（用于ELK）
│   └── app.YYYY-MM-DD.i.log
├── error/               # 错误日志
│   ├── error.log
│   ├── error.json
│   └── error.YYYY-MM-DD.i.log
├── trajectory/          # 轨迹处理日志
│   ├── trajectory.log
│   └── trajectory.YYYY-MM-DD.i.log
└── business/            # 业务日志
    ├── business.log
    └── business.YYYY-MM-DD.i.log
```

## 日志格式标准化

### 标准文本格式
```
2023-10-01 14:30:25 [main] INFO  c.m.g.processor.JavaTrajectoryProcessor - 开始处理GPS点集合
```

字段说明：
- 时间戳: `yyyy-MM-dd HH:mm:ss`
- 线程名: `[thread_name]`
- 日志级别: `INFO`, `WARN`, `ERROR` 等
- 记录器名: `c.m.g.processor.JavaTrajectoryProcessor` (简化包名)
- 日志消息: 实际的日志内容

### JSON格式（用于ELK）
```json
{
  "@timestamp": "2023-10-01T14:30:25.123Z",
  "level": "INFO",
  "logger_name": "com.maptools.gpstools.processor.JavaTrajectoryProcessor",
  "message": "开始处理GPS点集合",
  "thread_name": "main"
}
```

## ELK配置

### 1. Elasticsearch配置

确保Elasticsearch运行在默认端口9200上，或根据需要修改配置。

### 2. Logstash配置

创建配置文件 `logstash/maptools.conf`:

```conf
input {
  file {
    path => "/path/to/MapTools/shared_logs/**/*.json"
    start_position => "beginning"
    sincedb_path => "/dev/null"
    codec => "json"
  }
}

filter {
  # 解析时间戳
  date {
    match => [ "@timestamp", "ISO8601" ]
  }
  
  # 添加额外字段
  mutate {
    add_field => { "project" => "MapTools" }
  }
}

output {
  elasticsearch {
    hosts => ["localhost:9200"]
    index => "maptools-logs-%{+YYYY.MM.dd}"
  }
  
  # 可选：输出到控制台进行调试
  stdout {
    codec => rubydebug
  }
}
```

### 3. Kibana配置

在Kibana中创建索引模式：
1. 打开Kibana界面 (http://localhost:5601)
2. 进入 "Management" > "Index Patterns"
3. 创建新的索引模式: `maptools-logs-*`
4. 选择时间字段: `@timestamp`

## 使用说明

### 启动ELK堆栈

1. 启动Elasticsearch:
   ```bash
   ./elasticsearch
   ```

2. 启动Logstash:
   ```bash
   ./logstash -f logstash/maptools.conf
   ```

3. 启动Kibana:
   ```bash
   ./kibana
   ```

### 在Kibana中查看日志

1. 打开浏览器访问 http://localhost:5601
2. 进入 "Discover" 面板
3. 选择索引模式 `maptools-logs-*`
4. 设置时间范围以查看最新日志

### 常用查询示例

1. 查找错误日志:
   ```
   level: "ERROR"
   ```

2. 查找特定类的日志:
   ```
   logger_name: "com.maptools.gpstools.processor.JavaTrajectoryProcessor"
   ```

3. 查找包含特定关键词的日志:
   ```
   message: "处理完成"
   ```

## 监控和告警

### 常见监控指标

1. 错误日志数量
2. 处理延迟
3. 系统资源使用情况

### 设置告警规则

在Kibana中可以设置以下告警：

1. 错误日志数量超过阈值
2. 特定类型日志缺失
3. 处理时间异常

## 最佳实践

### 1. 日志级别管理
- DEBUG: 详细调试信息，仅在开发和问题排查时启用
- INFO: 一般信息，记录重要操作和状态
- WARN: 警告信息，不影响系统运行但需要注意
- ERROR: 错误信息，系统功能异常
- FATAL: 严重错误，系统可能无法继续运行

### 2. 日志内容规范
- 使用统一格式和编码
- 避免记录敏感信息（如密码、密钥等）
- 包含足够的上下文信息以便问题排查
- 避免记录过大的对象或数据

### 3. 性能考虑
- 合理设置日志级别，避免产生过多日志
- 定期清理过期日志文件
- 使用异步日志记录提高性能

## 故障排除

### 常见问题

1. **日志未出现在Kibana中**
   - 检查Logstash是否正常运行
   - 检查日志文件路径配置是否正确
   - 检查Elasticsearch索引是否创建成功

2. **日志格式解析错误**
   - 检查JSON格式是否正确
   - 确认Logstash配置中的codec设置

3. **性能问题**
   - 检查日志文件大小和数量
   - 调整Logstash批处理大小
   - 优化Elasticsearch索引设置

## 扩展功能

### 1. 多环境日志管理
为不同环境（开发、测试、生产）设置不同的索引前缀和配置。

### 2. 日志归档
配置长期日志存储方案，如冷热数据分离。

### 3. 安全日志审计
增加安全相关日志记录和分析功能。