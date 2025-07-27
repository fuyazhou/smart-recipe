import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  FormControlLabel,
  Checkbox,
  Alert,
  InputAdornment,
  IconButton,
  Tab,
  Tabs,
  Link,
  CircularProgress
} from '@mui/material';
import {
  Visibility,
  VisibilityOff,
  Email,
  Phone,
  Person
} from '@mui/icons-material';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { useAuthStore } from '../../stores/authStore';
import { toast } from 'react-hot-toast';

// 验证模式
const loginSchema = yup.object().shape({
  identifier: yup.string().required('请输入用户名、邮箱或手机号'),
  password: yup.string().required('请输入密码').min(6, '密码至少6位'),
  rememberMe: yup.boolean(),
  loginType: yup.string().oneOf(['username', 'email', 'phone']).required()
});

interface LoginFormData {
  identifier: string;
  password: string;
  rememberMe: boolean;
  loginType: 'username' | 'email' | 'phone';
}

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
  onSwitchToForgotPassword?: () => void;
}

const LoginForm: React.FC<LoginFormProps> = ({
  onSuccess,
  onSwitchToRegister,
  onSwitchToForgotPassword
}) => {
  const [showPassword, setShowPassword] = useState(false);
  const [loginType, setLoginType] = useState<'username' | 'email' | 'phone'>('username');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuthStore();

  const {
    control,
    handleSubmit,
    setValue,
    watch,
    formState: { errors }
  } = useForm<LoginFormData>({
    resolver: yupResolver(loginSchema),
    defaultValues: {
      identifier: '',
      password: '',
      rememberMe: false,
      loginType: 'username'
    }
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: 'username' | 'email' | 'phone') => {
    setLoginType(newValue);
    setValue('loginType', newValue);
    setValue('identifier', ''); // 清空输入
  };

  const onSubmit = async (data: LoginFormData) => {
    try {
      setIsLoading(true);
      
      const region = process.env.REACT_APP_REGION || 'china';
      
      await login({
        identifier: data.identifier,
        password: data.password,
        login_type: data.loginType,
        remember_me: data.rememberMe,
        region
      });

      toast.success('登录成功！');
      onSuccess?.();
    } catch (error: any) {
      console.error('登录失败:', error);
      
      // 处理不同类型的错误
      if (error.response?.status === 401) {
        toast.error('用户名或密码错误');
      } else if (error.response?.status === 423) {
        toast.error('账户已被锁定，请稍后再试');
      } else if (error.response?.data?.detail) {
        toast.error(error.response.data.detail);
      } else {
        toast.error('登录失败，请稍后重试');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const getInputPlaceholder = () => {
    switch (loginType) {
      case 'email':
        return '请输入邮箱地址';
      case 'phone':
        return '请输入手机号';
      default:
        return '请输入用户名';
    }
  };

  const getInputIcon = () => {
    switch (loginType) {
      case 'email':
        return <Email />;
      case 'phone':
        return <Phone />;
      default:
        return <Person />;
    }
  };

  return (
    <Card sx={{ maxWidth: 400, mx: 'auto', mt: 4 }}>
      <CardContent sx={{ p: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom align="center">
          登录
        </Typography>
        
        <Typography variant="body2" color="text.secondary" align="center" sx={{ mb: 3 }}>
          欢迎回到智能食谱
        </Typography>

        {/* 登录方式选择 */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
          <Tabs
            value={loginType}
            onChange={handleTabChange}
            variant="fullWidth"
          >
            <Tab label="用户名" value="username" />
            <Tab label="邮箱" value="email" />
            <Tab label="手机号" value="phone" />
          </Tabs>
        </Box>

        <form onSubmit={handleSubmit(onSubmit)}>
          {/* 登录标识符输入 */}
          <Controller
            name="identifier"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                label={loginType === 'email' ? '邮箱' : loginType === 'phone' ? '手机号' : '用户名'}
                placeholder={getInputPlaceholder()}
                error={!!errors.identifier}
                helperText={errors.identifier?.message}
                margin="normal"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      {getInputIcon()}
                    </InputAdornment>
                  ),
                }}
              />
            )}
          />

          {/* 密码输入 */}
          <Controller
            name="password"
            control={control}
            render={({ field }) => (
              <TextField
                {...field}
                fullWidth
                type={showPassword ? 'text' : 'password'}
                label="密码"
                placeholder="请输入密码"
                error={!!errors.password}
                helperText={errors.password?.message}
                margin="normal"
                InputProps={{
                  endAdornment: (
                    <InputAdornment position="end">
                      <IconButton
                        aria-label="toggle password visibility"
                        onClick={() => setShowPassword(!showPassword)}
                        edge="end"
                      >
                        {showPassword ? <VisibilityOff /> : <Visibility />}
                      </IconButton>
                    </InputAdornment>
                  ),
                }}
              />
            )}
          />

          {/* 记住我 */}
          <Controller
            name="rememberMe"
            control={control}
            render={({ field }) => (
              <FormControlLabel
                control={
                  <Checkbox
                    {...field}
                    checked={field.value}
                  />
                }
                label="记住我"
                sx={{ mt: 1, mb: 2 }}
              />
            )}
          />

          {/* 登录按钮 */}
          <Button
            type="submit"
            fullWidth
            variant="contained"
            size="large"
            disabled={isLoading}
            sx={{ mt: 2, mb: 2 }}
          >
            {isLoading ? (
              <>
                <CircularProgress size={20} sx={{ mr: 1 }} />
                登录中...
              </>
            ) : (
              '登录'
            )}
          </Button>

          {/* 忘记密码和注册链接 */}
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 2 }}>
            <Link
              component="button"
              variant="body2"
              onClick={(e) => {
                e.preventDefault();
                onSwitchToForgotPassword?.();
              }}
            >
              忘记密码？
            </Link>
            <Link
              component="button"
              variant="body2"
              onClick={(e) => {
                e.preventDefault();
                onSwitchToRegister?.();
              }}
            >
              注册新账户
            </Link>
          </Box>
        </form>
      </CardContent>
    </Card>
  );
};

export default LoginForm; 