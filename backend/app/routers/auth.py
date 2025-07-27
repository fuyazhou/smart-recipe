from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database import get_db
from app.services.auth_service import get_auth_service, AuthService
from app.schemas.auth import (
    RegisterRequest, RegisterResponse,
    LoginRequest, LoginResponse,
    SendVerificationCodeRequest, SendVerificationCodeResponse,
    VerifyCodeRequest, VerifyCodeResponse,
    ForgotPasswordRequest, ForgotPasswordResponse,
    ResetPasswordRequest, ResetPasswordResponse,
    ChangePasswordRequest,
    ThirdPartyLoginRequest, ThirdPartyLoginResponse,
    RefreshTokenRequest, RefreshTokenResponse,
    LogoutRequest, LogoutResponse,
    VerificationStatusResponse,
    AccountStatusResponse,
    AuthErrorResponse
)
from app.utils.auth import verify_token, hash_token
from app.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter()

# ==================== 用户注册 ====================

@router.post("/send-register-code", response_model=SendVerificationCodeResponse)
async def send_register_verification_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """发送注册验证码"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service.send_register_code(request.identifier, request.region)
        return SendVerificationCodeResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败"
        )

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service.register_user(request)
        return RegisterResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败"
        )

# ==================== 用户登录 ====================

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: LoginRequest,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """用户登录"""
    try:
        # 获取客户端信息
        ip_address = http_request.client.host
        user_agent = http_request.headers.get("User-Agent", "")
        
        auth_service = get_auth_service(db)
        result = await auth_service.login_user(request, ip_address, user_agent)
        return LoginResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败"
        )

@router.post("/refresh-token", response_model=RefreshTokenResponse)
async def refresh_access_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """刷新访问令牌"""
    try:
        # 验证刷新令牌
        payload = verify_token(request.refresh_token, "refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="刷新令牌无效或已过期"
            )
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌格式错误"
            )
        
        # 验证用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在"
            )
        
        # 生成新的令牌
        from app.utils.auth import create_user_tokens
        tokens = create_user_tokens(user)
        
        return RefreshTokenResponse(**tokens)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="刷新令牌失败"
        )

@router.post("/logout", response_model=LogoutResponse)
async def logout_user(
    request: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """用户登出"""
    try:
        from app.models.auth import UserSession
        
        if request.logout_all_devices:
            # 注销所有设备
            db.query(UserSession).filter(
                UserSession.user_id == current_user.id,
                UserSession.is_active == True
            ).update({"is_active": False})
        else:
            # 只注销当前会话
            # 这里需要从请求头中获取当前令牌并找到对应的会话
            # 简化实现，注销所有会话
            db.query(UserSession).filter(
                UserSession.user_id == current_user.id,
                UserSession.is_active == True
            ).update({"is_active": False})
        
        db.commit()
        
        return LogoutResponse(message="登出成功")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登出失败"
        )

# ==================== 密码管理 ====================

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """忘记密码"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service.forgot_password(request)
        return ForgotPasswordResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="处理忘记密码请求失败"
        )

@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """重置密码"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service.reset_password(request)
        return ResetPasswordResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败"
        )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """修改密码"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service.change_password(current_user.id, request)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="修改密码失败"
        )

# ==================== 验证码管理 ====================

@router.post("/send-verification-code", response_model=SendVerificationCodeResponse)
async def send_verification_code(
    request: SendVerificationCodeRequest,
    db: Session = Depends(get_db)
):
    """发送验证码"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service._send_verification_code(
            request.identifier, request.code_type, request.region
        )
        return SendVerificationCodeResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败"
        )

@router.post("/verify-code", response_model=VerifyCodeResponse)
async def verify_verification_code(
    request: VerifyCodeRequest,
    db: Session = Depends(get_db)
):
    """验证验证码"""
    try:
        auth_service = get_auth_service(db)
        is_valid = await auth_service._verify_code(
            request.identifier, request.code, request.code_type
        )
        
        token = None
        if is_valid and request.code_type in ["reset_password", "change_email", "change_phone"]:
            # 为某些操作生成临时令牌
            from app.utils.auth import generate_secure_token
            token = generate_secure_token()
        
        return VerifyCodeResponse(
            valid=is_valid,
            message="验证码正确" if is_valid else "验证码错误",
            token=token
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="验证失败"
        )

# ==================== 第三方登录 ====================

@router.post("/third-party/login", response_model=ThirdPartyLoginResponse)
async def third_party_login(
    request: ThirdPartyLoginRequest,
    db: Session = Depends(get_db)
):
    """第三方登录"""
    try:
        auth_service = get_auth_service(db)
        result = await auth_service.third_party_login(request)
        return ThirdPartyLoginResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="第三方登录失败"
        )

# ==================== 用户状态查询 ====================

@router.get("/verification-status", response_model=VerificationStatusResponse)
async def get_verification_status(
    current_user: User = Depends(get_current_user)
):
    """获取用户验证状态"""
    return VerificationStatusResponse(
        user_id=current_user.id,
        email_verified=bool(current_user.email and current_user.is_verified),
        phone_verified=bool(current_user.phone and current_user.is_verified),
        email=current_user.email,
        phone=current_user.phone
    )

@router.get("/account-status", response_model=AccountStatusResponse)
async def get_account_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取账户状态"""
    try:
        from app.models.auth import AccountLock, LoginAttempt
        from datetime import datetime, timedelta
        
        # 检查是否被锁定
        lock = db.query(AccountLock).filter(
            AccountLock.user_id == current_user.id,
            AccountLock.is_active == True,
            AccountLock.locked_until > datetime.utcnow()
        ).first()
        
        # 统计失败登录次数
        failed_attempts = db.query(LoginAttempt).filter(
            LoginAttempt.identifier.in_([
                current_user.username,
                current_user.email,
                current_user.phone
            ]),
            LoginAttempt.success == False,
            LoginAttempt.created_at > datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        # 获取最后登录时间
        last_login = db.query(LoginAttempt).filter(
            LoginAttempt.identifier.in_([
                current_user.username,
                current_user.email,
                current_user.phone
            ]),
            LoginAttempt.success == True
        ).order_by(LoginAttempt.created_at.desc()).first()
        
        return AccountStatusResponse(
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            is_locked=bool(lock),
            lock_reason=lock.lock_reason if lock else None,
            locked_until=lock.locked_until if lock else None,
            failed_login_attempts=failed_attempts,
            last_login=last_login.created_at if last_login else None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取账户状态失败"
        )

# ==================== 健康检查 ====================

@router.get("/health")
async def auth_health_check():
    """认证服务健康检查"""
    return {
        "status": "healthy",
        "service": "auth",
        "timestamp": "2024-01-01T00:00:00Z"
    } 