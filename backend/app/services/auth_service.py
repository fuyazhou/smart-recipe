from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets

from app.models.user import User, UserPreference
from app.models.auth import (
    VerificationCode, PasswordResetToken, ThirdPartyAuth, 
    LoginAttempt, AccountLock, UserSession
)
from app.schemas.auth import (
    RegisterRequest, LoginRequest, ForgotPasswordRequest, 
    ResetPasswordRequest, ChangePasswordRequest, ThirdPartyLoginRequest
)
from app.schemas.user import UserCreate, UserPreferenceCreate, UserInDB
from app.utils.auth import (
    hash_password, verify_password, authenticate_user, create_user_tokens,
    generate_verification_code, generate_secure_token, hash_token,
    check_account_locked, record_login_attempt, is_password_strong,
    normalize_phone_number, validate_email_format, validate_phone_format
)
from app.utils.notification import send_verification_code, send_password_reset_notification
from app.services.user_service import create_user, get_user_by_email, get_user_by_username, get_user_by_phone
from app.config.settings import settings

class AuthService:
    """认证服务类"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 注册相关 ====================
    
    async def register_user(self, request: RegisterRequest) -> Dict[str, Any]:
        """用户注册"""
        # 验证验证码
        await self._verify_code(request.email or request.phone, request.verification_code, "register")
        
        # 检查用户名是否已存在
        if get_user_by_username(self.db, request.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已被使用"
            )
        
        # 检查邮箱是否已存在
        if request.email and get_user_by_email(self.db, request.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
        
        # 检查手机号是否已存在
        if request.phone:
            normalized_phone = normalize_phone_number(request.phone, request.region)
            if get_user_by_phone(self.db, normalized_phone):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="手机号已被注册"
                )
        
        # 检查密码强度
        is_strong, errors = is_password_strong(request.password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码强度不足: {', '.join(errors)}"
            )
        
        # 创建用户
        user_data = UserCreate(
            username=request.username,
            email=request.email,
            phone=normalize_phone_number(request.phone, request.region) if request.phone else None,
            password=request.password,
            region=request.region
        )
        
        user = create_user(self.db, user_data)
        
        # 标记验证码已使用
        self._mark_code_used(request.email or request.phone, request.verification_code, "register")
        
        # 如果是邮箱注册，设置为已验证；如果是手机号注册，也设置为已验证
        user.is_verified = True
        self.db.commit()
        
        return {
            "message": "注册成功",
            "user_id": user.id,
            "need_verification": False
        }
    
    async def send_register_code(self, identifier: str, region: str) -> Dict[str, Any]:
        """发送注册验证码"""
        # 验证标识符格式
        if "@" in identifier:
            if not validate_email_format(identifier):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="邮箱格式不正确"
                )
        else:
            normalized_phone = normalize_phone_number(identifier, region)
            if not validate_phone_format(normalized_phone, region):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="手机号格式不正确"
                )
            identifier = normalized_phone
        
        # 检查是否已注册
        if "@" in identifier:
            if get_user_by_email(self.db, identifier):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该邮箱已被注册"
                )
        else:
            if get_user_by_phone(self.db, identifier):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="该手机号已被注册"
                )
        
        return await self._send_verification_code(identifier, "register", region)
    
    # ==================== 登录相关 ====================
    
    async def login_user(self, request: LoginRequest, ip_address: str, user_agent: str) -> Dict[str, Any]:
        """用户登录"""
        # 标准化手机号
        identifier = request.identifier
        if request.login_type == "phone":
            identifier = normalize_phone_number(identifier, request.region)
        
        # 检查账户是否被锁定
        user = None
        if request.login_type == "email":
            user = get_user_by_email(self.db, identifier)
        elif request.login_type == "phone":
            user = get_user_by_phone(self.db, identifier)
        else:
            user = get_user_by_username(self.db, identifier)
        
        if user:
            is_locked, locked_until = check_account_locked(self.db, user.id)
            if is_locked:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"账户已被锁定，解锁时间：{locked_until}"
                )
        
        # 认证用户
        authenticated_user = authenticate_user(self.db, identifier, request.password)
        
        if not authenticated_user:
            # 记录失败的登录尝试
            record_login_attempt(
                self.db, identifier, ip_address, user_agent, False, "wrong_credentials"
            )
            
            # 检查失败次数，必要时锁定账户
            await self._check_and_lock_account(identifier, ip_address)
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        # 记录成功的登录尝试
        record_login_attempt(
            self.db, identifier, ip_address, user_agent, True
        )
        
        # 创建令牌
        tokens = create_user_tokens(authenticated_user)
        
        # 创建会话记录
        session = self._create_user_session(
            authenticated_user.id,
            hash_token(tokens["refresh_token"]),
            {"user_agent": user_agent, "login_type": request.login_type},
            ip_address,
            datetime.utcnow() + timedelta(days=30)
        )
        
        return {
            **tokens,
            "user": {
                "id": authenticated_user.id,
                "username": authenticated_user.username,
                "email": authenticated_user.email,
                "is_verified": authenticated_user.is_verified,
                "region": authenticated_user.region
            }
        }
    
    # ==================== 密码重置 ====================
    
    async def forgot_password(self, request: ForgotPasswordRequest) -> Dict[str, Any]:
        """忘记密码"""
        identifier = request.identifier
        
        # 标准化手机号
        if not "@" in identifier:
            identifier = normalize_phone_number(identifier, request.region)
        
        # 查找用户
        user = None
        if "@" in identifier:
            user = get_user_by_email(self.db, identifier)
        else:
            user = get_user_by_phone(self.db, identifier)
        
        if not user:
            # 为了安全，即使用户不存在也返回成功
            return {
                "message": "如果该邮箱/手机号已注册，您将收到重置密码的指引",
                "reset_method": "email" if "@" in request.identifier else "sms"
            }
        
        # 生成重置令牌
        reset_token = generate_secure_token(64)
        
        # 保存重置令牌
        password_reset = PasswordResetToken(
            user_id=user.id,
            token=hash_token(reset_token),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        self.db.add(password_reset)
        self.db.commit()
        
        # 发送重置通知
        if "@" in identifier:
            await send_password_reset_notification(identifier, reset_token=reset_token)
            return {
                "message": "密码重置链接已发送到您的邮箱",
                "reset_method": "email"
            }
        else:
            # 对于手机号，发送验证码
            code = generate_verification_code()
            await self._save_verification_code(identifier, code, "reset_password", request.region)
            await send_password_reset_notification(identifier, code=code)
            return {
                "message": "密码重置验证码已发送到您的手机",
                "reset_method": "sms"
            }
    
    async def reset_password(self, request: ResetPasswordRequest) -> Dict[str, Any]:
        """重置密码"""
        # 验证重置令牌
        hashed_token = hash_token(request.token)
        reset_record = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == hashed_token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_record:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置令牌无效或已过期"
            )
        
        # 检查密码强度
        is_strong, errors = is_password_strong(request.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码强度不足: {', '.join(errors)}"
            )
        
        # 更新密码
        user = reset_record.user
        user.password_hash = hash_password(request.new_password)
        
        # 标记令牌已使用
        reset_record.is_used = True
        
        # 清除用户所有会话
        self.db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).update({"is_active": False})
        
        self.db.commit()
        
        return {
            "message": "密码重置成功",
            "success": True
        }
    
    async def change_password(self, user_id: str, request: ChangePasswordRequest) -> Dict[str, Any]:
        """修改密码"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 验证旧密码
        if not verify_password(request.old_password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码不正确"
            )
        
        # 检查新密码强度
        is_strong, errors = is_password_strong(request.new_password)
        if not is_strong:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"密码强度不足: {', '.join(errors)}"
            )
        
        # 更新密码
        user.password_hash = hash_password(request.new_password)
        self.db.commit()
        
        return {"message": "密码修改成功"}
    
    # ==================== 验证码管理 ====================
    
    async def _send_verification_code(self, identifier: str, code_type: str, region: str) -> Dict[str, Any]:
        """发送验证码"""
        # 检查发送频率限制
        recent_code = self.db.query(VerificationCode).filter(
            VerificationCode.identifier == identifier,
            VerificationCode.code_type == code_type,
            VerificationCode.created_at > datetime.utcnow() - timedelta(minutes=1)
        ).first()
        
        if recent_code:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="发送验证码过于频繁，请稍后再试"
            )
        
        # 生成验证码
        code = generate_verification_code()
        
        # 保存验证码
        await self._save_verification_code(identifier, code, code_type, region)
        
        # 发送验证码
        success = await send_verification_code(identifier, code, code_type)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="发送验证码失败，请稍后重试"
            )
        
        return {
            "message": "验证码已发送",
            "expires_in": 600,  # 10分钟
            "can_resend_at": datetime.utcnow() + timedelta(minutes=1)
        }
    
    async def _save_verification_code(self, identifier: str, code: str, code_type: str, region: str):
        """保存验证码"""
        # 使旧的验证码失效
        self.db.query(VerificationCode).filter(
            VerificationCode.identifier == identifier,
            VerificationCode.code_type == code_type,
            VerificationCode.is_used == False
        ).update({"is_used": True})
        
        # 创建新的验证码记录
        verification_code = VerificationCode(
            identifier=identifier,
            code=code,
            code_type=code_type,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            region=region
        )
        self.db.add(verification_code)
        self.db.commit()
    
    async def _verify_code(self, identifier: str, code: str, code_type: str) -> bool:
        """验证验证码"""
        verification_code = self.db.query(VerificationCode).filter(
            VerificationCode.identifier == identifier,
            VerificationCode.code == code,
            VerificationCode.code_type == code_type,
            VerificationCode.is_used == False,
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        if not verification_code:
            # 增加尝试次数
            self.db.query(VerificationCode).filter(
                VerificationCode.identifier == identifier,
                VerificationCode.code_type == code_type,
                VerificationCode.is_used == False
            ).update({"attempts": VerificationCode.attempts + 1})
            self.db.commit()
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码无效或已过期"
            )
        
        # 检查尝试次数
        if verification_code.attempts >= verification_code.max_attempts:
            verification_code.is_used = True
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码尝试次数过多，请重新获取"
            )
        
        return True
    
    def _mark_code_used(self, identifier: str, code: str, code_type: str):
        """标记验证码已使用"""
        self.db.query(VerificationCode).filter(
            VerificationCode.identifier == identifier,
            VerificationCode.code == code,
            VerificationCode.code_type == code_type
        ).update({"is_used": True})
        self.db.commit()
    
    # ==================== 安全功能 ====================
    
    async def _check_and_lock_account(self, identifier: str, ip_address: str):
        """检查并锁定账户"""
        # 检查最近的失败登录次数
        failed_attempts = self.db.query(LoginAttempt).filter(
            LoginAttempt.identifier == identifier,
            LoginAttempt.success == False,
            LoginAttempt.created_at > datetime.utcnow() - timedelta(hours=1)
        ).count()
        
        if failed_attempts >= 5:
            # 查找用户
            user = None
            if "@" in identifier:
                user = get_user_by_email(self.db, identifier)
            elif identifier.startswith("+"):
                user = get_user_by_phone(self.db, identifier)
            else:
                user = get_user_by_username(self.db, identifier)
            
            if user:
                # 锁定账户
                account_lock = AccountLock(
                    user_id=user.id,
                    lock_type="login_attempts",
                    lock_reason=f"连续{failed_attempts}次登录失败",
                    locked_until=datetime.utcnow() + timedelta(hours=1)
                )
                self.db.add(account_lock)
                self.db.commit()
    
    def _create_user_session(self, user_id: str, token_hash: str, device_info: dict, 
                           ip_address: str, expires_at: datetime) -> UserSession:
        """创建用户会话"""
        session = UserSession(
            user_id=user_id,
            token_hash=token_hash,
            device_info=device_info,
            ip_address=ip_address,
            expires_at=expires_at
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session
    
    # ==================== 第三方登录 ====================
    
    async def third_party_login(self, request: ThirdPartyLoginRequest) -> Dict[str, Any]:
        """第三方登录"""
        # 这里需要实现具体的第三方登录逻辑
        # 根据不同的provider调用相应的API
        
        # 模拟实现
        provider_user_info = await self._get_third_party_user_info(
            request.provider, request.code, request.state
        )
        
        # 查找是否已有关联账户
        third_party_auth = self.db.query(ThirdPartyAuth).filter(
            ThirdPartyAuth.provider == request.provider,
            ThirdPartyAuth.provider_user_id == provider_user_info["id"],
            ThirdPartyAuth.is_active == True
        ).first()
        
        if third_party_auth:
            # 已有关联账户，直接登录
            user = third_party_auth.user
            tokens = create_user_tokens(user)
            
            return {
                **tokens,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "is_verified": user.is_verified,
                    "region": user.region
                },
                "need_bind": False
            }
        else:
            # 没有关联账户，需要绑定或创建新账户
            bind_token = generate_secure_token()
            
            # 临时存储第三方用户信息
            # 这里可以使用Redis或数据库临时表
            
            return {
                "need_bind": True,
                "bind_token": bind_token,
                "provider_info": {
                    "username": provider_user_info.get("username"),
                    "email": provider_user_info.get("email"),
                    "avatar": provider_user_info.get("avatar")
                }
            }
    
    async def _get_third_party_user_info(self, provider: str, code: str, state: str) -> Dict[str, Any]:
        """获取第三方用户信息"""
        # 这里需要实现具体的第三方API调用
        # 根据provider类型调用相应的API
        
        # 模拟返回
        return {
            "id": "third_party_user_id",
            "username": "third_party_username",
            "email": "user@example.com",
            "avatar": "https://example.com/avatar.jpg"
        }

# ==================== 服务工厂 ====================

def get_auth_service(db: Session) -> AuthService:
    """获取认证服务实例"""
    return AuthService(db) 