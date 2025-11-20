# 统一日志系统说明

## 概述

本文档介绍了MapTools项目的统一日志系统，该系统实现了Python和Java应用程序之间的日志格式和目录结构统一，便于集中管理和分析。

## 主要改进

### 1. 统一日志目录
- 所有日志文件现在都存储在 `shared_logs` 目录下
- 目录结构统一，便于管理和查找

### 2. 统一日志格式
- Python和Java使用相同的日志格式
- 支持标准文本格式和JSON格式（用于ELK集成）

### 3. 增强的日志清理功能
- 新的日志清理脚本可以同时处理Python和Java日志
- 支持压缩和删除过期日志

### 4. ELK集成支持
- 提供JSON格式日志输出
- 配置文件支持ELK堆栈集成

## 目录结构

```
MapTools/
├── shared_logs/              # 统一日志目录
│   ├── app/                  # 应用日志
│   ├── error/                # 错误日志
│   ├── trajectory/           # 轨迹处理日志
│   └── business/             # 业务日志
├── BackendService/           # Python后端服务
├── JavaToolScripts/          # Java工具脚本
└── scripts/                  # 管理脚本
    └── unified_log_cleanup.py # 统一日志清理脚本
```

## 使用说明

### 日志清理

使用统一的日志清理脚本处理所有日志：

```bash
# 查看帮助
python scripts/unified_log_cleanup.py --help

# 执行日志清理
python scripts/unified_log_cleanup.py

# 预演日志清理（不实际执行）
python scripts/unified_log_cleanup.py --dry-run

# 查看日志统计信息
python scripts/unified_log_cleanup.py stats
```

### Java端配置

Java端使用Logback进行日志记录，配置文件位于：
- `JavaToolScripts/src/main/resources/logback.xml` - 基本配置
- `JavaToolScripts/src/main/resources/logback-spring.xml` - 支持JSON格式的配置

### Python端配置

Python端使用标准logging模块，配置文件位于：
- `BackendService/CoreConfig/logging_config.py` - 统一日志配置
- `BackendService/CoreConfig/settings.py` - 日志目录设置

## 日志格式

### 标准文本格式
```
2023-10-01 14:30:25 [MainThread] INFO  module.name - 日志消息内容
```

### JSON格式（用于ELK）
```json
{
  "@timestamp": "2023-10-01T14:30:25Z",
  "level": "INFO",
  "logger_name": "module.name",
  "message": "日志消息内容",
  "thread_name": "MainThread"
}
```

## ELK集成

参见 [ELK日志管理指南](elk_log_management.md) 了解如何配置和使用ELK堆栈进行集中日志管理。

## 最佳实践

### 1. 日志级别使用
- **DEBUG**: 详细的调试信息，仅在开发和问题排查时使用
- **INFO**: 一般信息，记录重要操作和状态变更
- **WARNING**: 警告信息，需要注意但不影响系统正常运行的情况
- **ERROR**: 错误信息，系统功能异常或失败
- **CRITICAL**: 严重错误，可能导致系统无法继续运行

### 2. 日志内容规范
- 使用有意义的日志消息
- 包含足够的上下文信息
- 避免记录敏感信息（如密码、密钥等）
- 保持日志格式一致

### 3. 性能考虑
- 合理设置日志级别，避免产生过多日志
- 定期清理过期日志文件
- 在生产环境中谨慎使用DEBUG级别

## 故障排除

### 常见问题

1. **日志文件未生成**
   - 检查日志目录权限
   - 确认日志配置是否正确
   - 检查磁盘空间是否充足

2. **日志格式不一致**
   - 确认配置文件是否正确应用
   - 检查是否有多个日志配置冲突

3. **日志清理失败**
   - 检查脚本执行权限
   - 确认日志目录路径是否正确

## 扩展功能

### 自定义日志处理
可以根据需要扩展日志处理功能，如：
- 添加日志告警机制
- 实现日志分析和报告功能
- 集成第三方日志服务

### 监控和告警
可以基于日志内容设置监控和告警规则，及时发现系统异常。