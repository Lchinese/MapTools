"""
用户认证API接口
提供登录、注册、密码重置等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging
from datetime import datetime, timedelta
from jose import jwt
import uuid
from passlib.context import CryptContext

from CoreConfig.database import get_db
from CoreConfig.logging import get_logger
from CoreConfig.settings import get_settings
from DataModels.Models import User
from DataSchemas import UserCreate, UserLogin, UserResponse

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter(prefix="/api/v1/auth", tags=["认证"])

# OAuth2 方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# 密码加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

@router.post("/register", response_model=Dict[str, Any])
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    try:
        logger.info(f"用户注册: {user_data.email}")
        
        # 检查邮箱是否已存在
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 检查用户名是否已存在
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        
        # 创建新用户
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            user_id=str(uuid.uuid4()),
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            password_hash=hashed_password,
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"用户注册成功: {new_user.user_id}")
        
        return {
            "success": True,
            "message": "注册成功",
            "data": {
                "user_id": new_user.user_id,
                "username": new_user.username,
                "email": new_user.email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"注册失败: {str(e)}"
        )

@router.post("/login", response_model=Dict[str, Any])
async def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录"""
    try:
        logger.info(f"用户登录: {login_data.email}")
        
        # 查找用户 - 支持用户名或邮箱登录
        user = db.query(User).filter(
            (User.email == login_data.email) | (User.username == login_data.email)
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        # 验证密码
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名/邮箱或密码错误"
            )
        
        # 检查用户状态
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="账户已被禁用"
            )
        
        # 生成访问令牌
        access_token = create_access_token(
            data={"sub": user.user_id, "email": user.email}
        )
        
        # 更新最后登录时间
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"用户登录成功: {user.user_id}")
        
        return {
            "success": True,
            "message": "登录成功",
            "data": {
                "token": access_token,
                "user": {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "phone": user.phone,
                    "is_active": user.is_active,
                    "created_at": user.created_at.isoformat(),
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"用户登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录失败: {str(e)}"
        )

# 依赖项：获取当前用户
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """获取当前用户"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

@router.get("/verify", response_model=Dict[str, Any])
async def verify_token(current_user: User = Depends(get_current_user)):
    """验证令牌"""
    return {
        "success": True,
        "message": "令牌有效",
        "data": {
            "user": {
                "user_id": current_user.user_id,
                "username": current_user.username,
                "email": current_user.email,
                "phone": current_user.phone,
                "is_active": current_user.is_active
            }
        }
    }

@router.post("/logout", response_model=Dict[str, Any])
async def logout():
    """用户登出"""
    return {
        "success": True,
        "message": "登出成功"
    }
