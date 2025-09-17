"""
Celery 配置
异步任务队列配置
"""

import os
from celery import Celery

# 创建Celery应用实例
celery_app = Celery("maptools")

# 从环境变量获取配置，如果没有则使用默认值
celery_app.conf.update(
    broker_url=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0"),
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "app.tasks.process_matching_task": "main-queue",
    },
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)

# 自动发现任务
celery_app.autodiscover_tasks(["app.tasks"])