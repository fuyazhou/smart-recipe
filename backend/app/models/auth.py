from sqlalchemy import (
    Column, String, Boolean, ForeignKey, DateTime, Integer, Text
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .user import Base

class VerificationCode(Base):
    """验证码表 - 用于邮箱/手机验证"""
    __tablename__ = "verification_codes"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    identifier = Column(String(255), nullable=False)  # 邮箱或手机号
    code = Column(String(10), nullable=False)  # 验证码
    code_type = Column(String(20), nullable=False)  # register, login, reset_password, change_email, change_phone
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)  # 验证尝试次数
    max_attempts = Column(Integer, default=3)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    region = Column(String(10), nullable=False)  # china 或 us

class PasswordResetToken(Base):
    """密码重置令牌表"""
    __tablename__ = "password_reset_tokens"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    token = Column(String(255), unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    user = relationship("User")

class ThirdPartyAuth(Base):
    """第三方登录关联表"""
    __tablename__ = "third_party_auths"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    provider = Column(String(20), nullable=False)  # wechat, qq, weibo, google, facebook, apple
    provider_user_id = Column(String(255), nullable=False)  # 第三方平台用户ID
    provider_username = Column(String(255))  # 第三方平台用户名
    provider_email = Column(String(255))  # 第三方平台邮箱
    provider_avatar = Column(String(500))  # 第三方平台头像
    access_token = Column(Text)  # 访问令牌
    refresh_token = Column(Text)  # 刷新令牌
    expires_at = Column(DateTime)  # 令牌过期时间
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    updated_at = Column(DateTime, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
    
    user = relationship("User")

class LoginAttempt(Base):
    """登录尝试记录表 - 用于安全控制"""
    __tablename__ = "login_attempts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    identifier = Column(String(255), nullable=False)  # 用户名/邮箱/手机号
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text)
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100))  # wrong_password, user_not_found, account_locked, etc.
    created_at = Column(DateTime, server_default=func.current_timestamp())

class AccountLock(Base):
    """账户锁定表"""
    __tablename__ = "account_locks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(__import__('uuid').uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    lock_type = Column(String(20), nullable=False)  # login_attempts, security_violation
    lock_reason = Column(String(255))
    locked_until = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.current_timestamp())
    
    user = relationship("User") 