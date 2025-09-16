# MapTools 日志系统

基于日志系统设计文档实现的完整日志解决方案，支持多级别、多输出、结构化日志记录。

## 快速开始

### 1. 基本使用

```python
from LoggingSystem.logger import get_logger

# 获取日志器
logger = get_logger(__name__)

# 记录日志
logger.info("这是一条信息日志")
logger.error("这是一条错误日志", extra={"user_id": "123"})
```

### 2. 类中使用日志

```python
from LoggingSystem.logger import LoggerMixin

class MyService(LoggerMixin):
    def process_data(self, data):
        self.logger.info("开始处理数据", extra={"data_size": len(data)})
        # 处理逻辑...
        self.logger.info("数据处理完成")
```

### 3. 使用装饰器

```python
from LoggingSystem.logger import log_performance, log_audit

@log_performance
def expensive_operation():
    # 性能监控的耗时操作
    pass

@log_audit(action="delete_user", resource="user")
def delete_user(user_id):
    # 审计日志记录的操作
    pass
```

## 配置文件

### 环境配置

- `logging.env` - 环境变量配置
- `logging.conf` - 日志配置文件
- `docker-logging.yml` - Docker环境日志配置

### 代码配置

- `config.py` - 核心配置参数
- `formatters.py` - 日志格式化器
- `handlers.py` - 日志处理器
- `logger.py` - 核心日志器

## 日志级别

| 级别 | 数值 | 用途 | 示例场景 |
|------|------|------|----------|
| DEBUG | 10 | 详细调试信息 | 算法参数调试、数据流追踪 |
| INFO | 20 | 一般信息记录 | 用户操作、系统状态 |
| WARNING | 30 | 警告信息 | 数据异常、性能下降 |
| ERROR | 40 | 错误信息 | 业务逻辑错误、外部服务异常 |
| CRITICAL | 50 | 严重错误 | 系统崩溃、数据丢失 |

## 日志格式

### JSON格式（推荐）

```json
{
  "timestamp": "2025-09-16T18:30:45.123Z",
  "level": "INFO",
  "module": "MatchingAlgorithms.gotrackit_adapter",
  "function": "match_trajectory",
  "line": 45,
  "message": "开始执行轨迹匹配",
  "request_id": "req_123456789",
  "trajectory_id": "traj_001",
  "duration_ms": 1250,
  "extra": {
    "algorithm": "HMM",
    "points_count": 150
  }
}
```

### 详细格式

```
[2025-09-16 18:30:45.123] [INFO] MatchingAlgorithms.gotrackit_adapter match_trajectory:45 - 开始执行轨迹匹配 | algorithm=HMM | points_count=150
```

## 模块配置

每个模块都有独立的日志配置：

- **MatchingAlgorithms**: 算法执行日志（DEBUG级别）
- **DataModels**: 数据操作日志（INFO级别）
- **ApiEndpoints**: API请求响应日志（INFO级别）
- **BusinessServices**: 业务逻辑日志（INFO级别）
- **AsyncTasks**: 异步任务日志（INFO级别）
- **UtilityTools**: 工具函数日志（WARNING级别）

## 日志轮转

- **按时间轮转**: 每天生成新文件
- **按大小轮转**: 文件超过100MB时轮转
- **保留策略**: 保留30天的日志文件
- **压缩策略**: 7天后的文件自动压缩

## 性能优化

- **异步写入**: 避免阻塞主业务逻辑
- **批量处理**: 减少I/O操作次数
- **内存限制**: 缓冲区大小限制为10MB
- **自动刷新**: 定期刷新缓冲区

## 安全特性

- **敏感信息脱敏**: 自动过滤密码、密钥等敏感信息
- **访问控制**: 日志文件权限管理
- **审计追踪**: 完整的操作审计记录

## 监控和告警

- **实时监控**: 日志级别分布、错误率统计
- **性能指标**: 写入延迟、内存使用监控
- **告警规则**: 高错误率、磁盘空间告警

## 使用脚本

### 设置日志系统

```bash
python scripts/setup_logging.py
```

### 清理日志文件

```bash
# 清理所有过期日志
python scripts/log_cleanup.py cleanup

# 查看日志统计
python scripts/log_cleanup.py stats

# 只压缩旧日志
python scripts/log_cleanup.py compress
```

### 运行示例

```bash
python examples/logging_example.py
```

## Docker集成

使用Docker Compose时，日志配置会自动应用：

```bash
# 使用Docker日志配置
docker-compose -f docker-compose.yml -f docker-logging.yml up
```

## 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| ENVIRONMENT | development | 运行环境 |
| DEBUG | false | 调试模式 |
| LOG_LEVEL | INFO | 日志级别 |
| LOG_FORMAT | json | 日志格式 |
| LOG_TO_FILE | true | 是否输出到文件 |
| LOG_TO_CONSOLE | true | 是否输出到控制台 |
| LOG_ASYNC | true | 是否异步写入 |

## 故障排查

### 常见问题

1. **日志文件不生成**
   - 检查目录权限
   - 确认环境变量设置

2. **日志格式不正确**
   - 检查formatter配置
   - 确认日志级别设置

3. **性能问题**
   - 检查异步配置
   - 调整缓冲区大小

### 调试方法

1. 启用DEBUG级别日志
2. 检查控制台输出
3. 查看错误日志文件
4. 使用日志分析工具

## 扩展开发

### 添加新的格式化器

```python
from LoggingSystem.formatters import JSONFormatter

class CustomFormatter(JSONFormatter):
    def format(self, record):
        # 自定义格式化逻辑
        return super().format(record)
```

### 添加新的处理器

```python
from LoggingSystem.handlers import AsyncFileHandler

class CustomHandler(AsyncFileHandler):
    def emit(self, record):
        # 自定义处理逻辑
        super().emit(record)
```

## 最佳实践

1. **使用结构化日志**: 优先使用JSON格式
2. **合理设置日志级别**: 避免过多DEBUG日志
3. **添加上下文信息**: 使用extra参数添加有用信息
4. **处理异常**: 使用exc_info=True记录异常堆栈
5. **性能考虑**: 避免在循环中记录大量日志
6. **安全考虑**: 注意敏感信息脱敏

## 更新日志

- **v1.0** (2025-09-16): 初始版本，支持基础日志功能
- 支持多级别、多输出日志记录
- 支持结构化JSON格式
- 支持日志轮转和压缩
- 支持异步写入和性能优化
- 支持敏感信息脱敏
- 支持Docker集成

---

**维护人员**: MapTools 开发团队  
**文档版本**: v1.0  
**最后更新**: 2025-09-16
