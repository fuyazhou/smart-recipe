from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime

# ==================== 基础认证模式 ====================

class LoginRequest(BaseModel):
    """登录请求"""
    identifier: str = Field(..., description="用户名、邮箱或手机号")
    password: str = Field(..., min_length=6, max_length=128)
    login_type: Literal["username", "email", "phone"] = Field(default="username")
    remember_me: Optional[bool] = False
    region: str = Field(..., description="地区：china 或 us")

class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: dict  # 用户基本信息

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    password: str = Field(..., min_length=6, max_length=128, description="密码")
    email: Optional[EmailStr] = Field(None, description="邮箱")
    phone: Optional[str] = Field(None, description="手机号")
    verification_code: str = Field(..., description="验证码")
    region: str = Field(..., description="地区：china 或 us")
    
    @validator('phone')
    def validate_phone(cls, v, values):
        if v:
            region = values.get('region', 'china')
            if region == 'china':
                # 中国手机号验证 (简化版)
                if not v.startswith('+86'):
                    v = '+86' + v.lstrip('+86')
                if len(v) != 14:  # +86 + 11位数字
                    raise ValueError('中国手机号格式不正确')
            else:  # us
                # 美国手机号验证 (简化版)
                if not v.startswith('+1'):
                    v = '+1' + v.lstrip('+1')
                if len(v) != 12:  # +1 + 10位数字
                    raise ValueError('美国手机号格式不正确')
        return v
    
    @validator('root')
    def validate_contact(cls, values):
        email = values.get('email')
        phone = values.get('phone')
        if not email and not phone:
            raise ValueError('邮箱或手机号至少填写一个')
        return values

class RegisterResponse(BaseModel):
    """注册响应"""
    message: str
    user_id: str
    need_verification: bool = True

# ==================== 验证码相关 ====================

class SendVerificationCodeRequest(BaseModel):
    """发送验证码请求"""
    identifier: str = Field(..., description="邮箱或手机号")
    code_type: Literal["register", "login", "reset_password", "change_email", "change_phone"]
    region: str = Field(..., description="地区：china 或 us")

class SendVerificationCodeResponse(BaseModel):
    """发送验证码响应"""
    message: str
    expires_in: int  # 验证码有效期（秒）
    can_resend_at: datetime  # 可重新发送时间

class VerifyCodeRequest(BaseModel):
    """验证码验证请求"""
    identifier: str = Field(..., description="邮箱或手机号")
    code: str = Field(..., description="验证码")
    code_type: Literal["register", "login", "reset_password", "change_email", "change_phone"]

class VerifyCodeResponse(BaseModel):
    """验证码验证响应"""
    valid: bool
    message: str
    token: Optional[str] = None  # 验证成功后的临时令牌

# ==================== 密码重置 ====================

class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    identifier: str = Field(..., description="邮箱或手机号")
    region: str = Field(..., description="地区：china 或 us")

class ForgotPasswordResponse(BaseModel):
    """忘记密码响应"""
    message: str
    reset_method: Literal["email", "sms"]

class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v

class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    message: str
    success: bool

class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=128, description="新密码")
    confirm_password: str = Field(..., min_length=6, max_length=128, description="确认新密码")
    
    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('两次输入的密码不一致')
        return v

# ==================== 第三方登录 ====================

class ThirdPartyLoginRequest(BaseModel):
    """第三方登录请求"""
    provider: Literal["wechat", "qq", "weibo", "google", "facebook", "apple"]
    code: str = Field(..., description="授权码")
    state: Optional[str] = Field(None, description="状态参数")
    region: str = Field(..., description="地区：china 或 us")

class ThirdPartyLoginResponse(BaseModel):
    """第三方登录响应"""
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    user: Optional[dict] = None
    need_bind: bool = False  # 是否需要绑定已有账户
    bind_token: Optional[str] = None  # 绑定令牌

class BindThirdPartyRequest(BaseModel):
    """绑定第三方账户请求"""
    bind_token: str = Field(..., description="绑定令牌")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")

class UnbindThirdPartyRequest(BaseModel):
    """解绑第三方账户请求"""
    provider: Literal["wechat", "qq", "weibo", "google", "facebook", "apple"]
    password: str = Field(..., description="账户密码确认")

# ==================== Token 相关 ====================

class RefreshTokenRequest(BaseModel):
    """刷新令牌请求"""
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    """刷新令牌响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutRequest(BaseModel):
    """登出请求"""
    logout_all_devices: bool = False

class LogoutResponse(BaseModel):
    """登出响应"""
    message: str

# ==================== 用户验证状态 ====================

class VerificationStatusResponse(BaseModel):
    """验证状态响应"""
    user_id: str
    email_verified: bool
    phone_verified: bool
    email: Optional[str] = None
    phone: Optional[str] = None

class UpdateContactRequest(BaseModel):
    """更新联系方式请求"""
    contact_type: Literal["email", "phone"]
    new_contact: str
    verification_code: str
    password: str = Field(..., description="账户密码确认")

# ==================== 安全相关 ====================

class SecurityLogResponse(BaseModel):
    """安全日志响应"""
    id: str
    action: str
    ip_address: str
    user_agent: Optional[str]
    success: bool
    created_at: datetime

class AccountStatusResponse(BaseModel):
    """账户状态响应"""
    is_active: bool
    is_verified: bool
    is_locked: bool
    lock_reason: Optional[str] = None
    locked_until: Optional[datetime] = None
    failed_login_attempts: int
    last_login: Optional[datetime] = None

# ==================== 错误响应 ====================

class AuthErrorResponse(BaseModel):
    """认证错误响应"""
    error: str
    error_description: str
    error_code: Optional[str] = None 