import asyncio
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
import logging

from app.config.settings import settings

logger = logging.getLogger(__name__)

# ==================== 邮件发送 ====================

class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.region = settings.REGION
    
    async def send_verification_email(self, email: str, code: str, code_type: str) -> bool:
        """发送验证码邮件"""
        subject_map = {
            "register": "验证您的邮箱地址" if self.region == "china" else "Verify Your Email Address",
            "reset_password": "重置您的密码" if self.region == "china" else "Reset Your Password",
            "change_email": "更改邮箱验证" if self.region == "china" else "Change Email Verification",
            "login": "登录验证码" if self.region == "china" else "Login Verification Code"
        }
        
        template_map = {
            "register": self._get_register_email_template,
            "reset_password": self._get_reset_password_email_template,
            "change_email": self._get_change_email_template,
            "login": self._get_login_email_template
        }
        
        subject = subject_map.get(code_type, "验证码")
        template_func = template_map.get(code_type, self._get_default_email_template)
        
        html_content = template_func(code)
        
        return await self._send_email(email, subject, html_content)
    
    async def send_password_reset_email(self, email: str, reset_link: str) -> bool:
        """发送密码重置邮件"""
        subject = "重置您的密码" if self.region == "china" else "Reset Your Password"
        html_content = self._get_password_reset_link_template(reset_link)
        
        return await self._send_email(email, subject, html_content)
    
    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件的底层实现"""
        try:
            if self.region == "china":
                # 使用阿里云邮件服务
                return await self._send_via_aliyun(to_email, subject, html_content)
            else:
                # 使用SendGrid
                return await self._send_via_sendgrid(to_email, subject, html_content)
        except Exception as e:
            logger.error(f"发送邮件失败: {e}")
            return False
    
    async def _send_via_aliyun(self, to_email: str, subject: str, html_content: str) -> bool:
        """通过阿里云发送邮件"""
        # 这里实现阿里云邮件发送逻辑
        # 由于需要具体的API密钥，这里提供模拟实现
        logger.info(f"[阿里云邮件] 发送至 {to_email}, 主题: {subject}")
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return True
    
    async def _send_via_sendgrid(self, to_email: str, subject: str, html_content: str) -> bool:
        """通过SendGrid发送邮件"""
        # 这里实现SendGrid邮件发送逻辑
        logger.info(f"[SendGrid] 发送至 {to_email}, 主题: {subject}")
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return True
    
    def _get_register_email_template(self, code: str) -> str:
        """注册验证邮件模板"""
        if self.region == "china":
            return f"""
            <html>
            <body>
                <h2>欢迎注册智能食谱</h2>
                <p>您的验证码是：<strong style="font-size: 20px; color: #007bff;">{code}</strong></p>
                <p>验证码将在10分钟后过期，请尽快完成验证。</p>
                <p>如果您没有注册账户，请忽略此邮件。</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>Welcome to Smart Recipe</h2>
                <p>Your verification code is: <strong style="font-size: 20px; color: #007bff;">{code}</strong></p>
                <p>This code will expire in 10 minutes. Please complete verification as soon as possible.</p>
                <p>If you didn't sign up for an account, please ignore this email.</p>
            </body>
            </html>
            """
    
    def _get_reset_password_email_template(self, code: str) -> str:
        """密码重置验证邮件模板"""
        if self.region == "china":
            return f"""
            <html>
            <body>
                <h2>密码重置验证</h2>
                <p>您请求重置密码的验证码是：<strong style="font-size: 20px; color: #ff6b6b;">{code}</strong></p>
                <p>验证码将在10分钟后过期。</p>
                <p>如果您没有请求重置密码，请忽略此邮件。</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>Password Reset Verification</h2>
                <p>Your password reset verification code is: <strong style="font-size: 20px; color: #ff6b6b;">{code}</strong></p>
                <p>This code will expire in 10 minutes.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
            </body>
            </html>
            """
    
    def _get_change_email_template(self, code: str) -> str:
        """更改邮箱验证模板"""
        if self.region == "china":
            return f"""
            <html>
            <body>
                <h2>更改邮箱验证</h2>
                <p>您的验证码是：<strong style="font-size: 20px; color: #28a745;">{code}</strong></p>
                <p>验证码将在10分钟后过期。</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>Change Email Verification</h2>
                <p>Your verification code is: <strong style="font-size: 20px; color: #28a745;">{code}</strong></p>
                <p>This code will expire in 10 minutes.</p>
            </body>
            </html>
            """
    
    def _get_login_email_template(self, code: str) -> str:
        """登录验证码模板"""
        if self.region == "china":
            return f"""
            <html>
            <body>
                <h2>登录验证码</h2>
                <p>您的登录验证码是：<strong style="font-size: 20px; color: #6c757d;">{code}</strong></p>
                <p>验证码将在5分钟后过期。</p>
                <p>如果这不是您的操作，请立即更改密码。</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>Login Verification Code</h2>
                <p>Your login verification code is: <strong style="font-size: 20px; color: #6c757d;">{code}</strong></p>
                <p>This code will expire in 5 minutes.</p>
                <p>If this wasn't you, please change your password immediately.</p>
            </body>
            </html>
            """
    
    def _get_default_email_template(self, code: str) -> str:
        """默认邮件模板"""
        return f"""
        <html>
        <body>
            <h2>验证码</h2>
            <p>您的验证码是：<strong>{code}</strong></p>
        </body>
        </html>
        """
    
    def _get_password_reset_link_template(self, reset_link: str) -> str:
        """密码重置链接模板"""
        if self.region == "china":
            return f"""
            <html>
            <body>
                <h2>重置您的密码</h2>
                <p>请点击下面的链接重置您的密码：</p>
                <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">重置密码</a></p>
                <p>如果按钮无法点击，请复制以下链接到浏览器地址栏：</p>
                <p>{reset_link}</p>
                <p>此链接将在1小时后过期。</p>
                <p>如果您没有请求重置密码，请忽略此邮件。</p>
            </body>
            </html>
            """
        else:
            return f"""
            <html>
            <body>
                <h2>Reset Your Password</h2>
                <p>Please click the link below to reset your password:</p>
                <p><a href="{reset_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <p>{reset_link}</p>
                <p>This link will expire in 1 hour.</p>
                <p>If you didn't request a password reset, please ignore this email.</p>
            </body>
            </html>
            """

# ==================== 短信发送 ====================

class SMSService:
    """短信服务类"""
    
    def __init__(self):
        self.region = settings.REGION
    
    async def send_verification_sms(self, phone: str, code: str, code_type: str) -> bool:
        """发送验证码短信"""
        template_map = {
            "register": "注册验证码" if self.region == "china" else "Registration verification code",
            "reset_password": "密码重置验证码" if self.region == "china" else "Password reset code",
            "change_phone": "更改手机号验证码" if self.region == "china" else "Change phone verification code",
            "login": "登录验证码" if self.region == "china" else "Login verification code"
        }
        
        message_type = template_map.get(code_type, "验证码")
        
        try:
            if self.region == "china":
                return await self._send_via_aliyun_sms(phone, code, message_type)
            else:
                return await self._send_via_twilio(phone, code, message_type)
        except Exception as e:
            logger.error(f"发送短信失败: {e}")
            return False
    
    async def _send_via_aliyun_sms(self, phone: str, code: str, message_type: str) -> bool:
        """通过阿里云发送短信"""
        message = f"【智能食谱】您的{message_type}是：{code}，有效期10分钟，请勿泄露。"
        logger.info(f"[阿里云短信] 发送至 {phone}: {message}")
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return True
    
    async def _send_via_twilio(self, phone: str, code: str, message_type: str) -> bool:
        """通过Twilio发送短信"""
        message = f"Smart Recipe: Your {message_type} is {code}. Valid for 10 minutes. Do not share."
        logger.info(f"[Twilio] 发送至 {phone}: {message}")
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return True

# ==================== 通知服务工厂 ====================

def get_email_service() -> EmailService:
    """获取邮件服务实例"""
    return EmailService()

def get_sms_service() -> SMSService:
    """获取短信服务实例"""
    return SMSService()

# ==================== 统一通知接口 ====================

async def send_verification_code(identifier: str, code: str, code_type: str) -> bool:
    """统一发送验证码接口"""
    if "@" in identifier:
        # 邮箱
        email_service = get_email_service()
        return await email_service.send_verification_email(identifier, code, code_type)
    else:
        # 手机号
        sms_service = get_sms_service()
        return await sms_service.send_verification_sms(identifier, code, code_type)

async def send_password_reset_notification(identifier: str, reset_token: str = None, code: str = None) -> bool:
    """发送密码重置通知"""
    if "@" in identifier:
        # 邮箱
        email_service = get_email_service()
        if reset_token:
            # 发送重置链接
            base_url = "https://www.smartrecipe.cn" if settings.REGION == "china" else "https://www.smartrecipe.com"
            reset_link = f"{base_url}/reset-password?token={reset_token}"
            return await email_service.send_password_reset_email(identifier, reset_link)
        elif code:
            # 发送验证码
            return await email_service.send_verification_email(identifier, code, "reset_password")
    else:
        # 手机号
        if code:
            sms_service = get_sms_service()
            return await sms_service.send_verification_sms(identifier, code, "reset_password")
    
    return False 