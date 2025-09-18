"""
MapTools 后端服务主应用
提供轨迹匹配、数据处理、文件管理等核心功能
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import sys
from pathlib import Path
import time  # 添加时间模块用于记录启动时间

# 添加项目根目录到Python路径
sys.path.append(str(Path(__file__).parent))

from CoreConfig.settings import get_settings
from CoreConfig.logging import setup_logging, get_logger
from CoreConfig.database import create_tables, check_connection
from ApiEndpoints import health_router
from ApiEndpoints.auth import router as auth_router

# 设置日志
setup_logging()
logger = get_logger(__name__)

# 获取配置
settings = get_settings()

# 记录应用启动时间
start_time = time.time()

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    description="Backend service for trajectory matching system",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（仅保留健康检查与认证）
app.include_router(health_router)
app.include_router(auth_router)


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    try:
        logger.info("MapTools 后端服务启动中...")
        
        # 检查数据库连接
        if not check_connection():
            logger.error("数据库连接失败")
            raise Exception("数据库连接失败")
        
        # 创建数据库表（当前仅 users ）
        create_tables()
        logger.info("数据库表创建完成")
        
        logger.info("MapTools 后端服务启动成功")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("MapTools 后端服务正在关闭...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "Welcome to MapTools Backend Service",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)  # 记录异常堆栈信息
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "服务器内部错误",
                "details": str(exc) if settings.DEBUG else "请查看服务器日志获取详细信息"
            },
            "timestamp": time.time()  # 添加时间戳
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)