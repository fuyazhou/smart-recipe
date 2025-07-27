import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';

// 用户信息类型
interface User {
  id: string;
  username: string;
  email?: string;
  phone?: string;
  is_verified: boolean;
  region: string;
  avatar_url?: string;
  is_paid: boolean;
}

// 登录请求类型
interface LoginRequest {
  identifier: string;
  password: string;
  login_type: 'username' | 'email' | 'phone';
  remember_me: boolean;
  region: string;
}

// 注册请求类型
interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  phone?: string;
  verification_code: string;
  region: string;
}

// 认证状态类型
interface AuthState {
  // 状态
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // 操作
  login: (data: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: (logoutAllDevices?: boolean) => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  sendVerificationCode: (identifier: string, type: string, region: string) => Promise<void>;
  forgotPassword: (identifier: string, region: string) => Promise<void>;
  resetPassword: (token: string, newPassword: string, confirmPassword: string) => Promise<void>;
  changePassword: (oldPassword: string, newPassword: string, confirmPassword: string) => Promise<void>;
  
  // 工具方法
  setTokens: (accessToken: string, refreshToken: string) => void;
  clearAuth: () => void;
  setUser: (user: User) => void;
  setLoading: (loading: boolean) => void;
}

// API基础URL
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

// Axios实例
const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  timeout: 10000,
});

// 请求拦截器 - 添加认证头
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器 - 处理token过期
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        await useAuthStore.getState().refreshAccessToken();
        const newToken = useAuthStore.getState().accessToken;
        if (newToken) {
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // 刷新失败，清除认证状态
        useAuthStore.getState().clearAuth();
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// 创建认证store
export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // 初始状态
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,

      // 登录
      login: async (data: LoginRequest) => {
        set({ isLoading: true });
        try {
          const response = await api.post('/auth/login', data);
          const { access_token, refresh_token, user } = response.data;
          
          set({
            user,
            accessToken: access_token,
            refreshToken: refresh_token,
            isAuthenticated: true,
            isLoading: false
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      // 注册
      register: async (data: RegisterRequest) => {
        set({ isLoading: true });
        try {
          const response = await api.post('/auth/register', data);
          set({ isLoading: false });
          return response.data;
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },

      // 登出
      logout: async (logoutAllDevices = false) => {
        set({ isLoading: true });
        try {
          await api.post('/auth/logout', { logout_all_devices: logoutAllDevices });
        } catch (error) {
          console.error('登出API调用失败:', error);
        } finally {
          set({
            user: null,
            accessToken: null,
            refreshToken: null,
            isAuthenticated: false,
            isLoading: false
          });
        }
      },

      // 刷新访问令牌
      refreshAccessToken: async () => {
        const { refreshToken } = get();
        if (!refreshToken) {
          throw new Error('没有刷新令牌');
        }

        try {
          const response = await api.post('/auth/refresh-token', {
            refresh_token: refreshToken
          });
          
          const { access_token, refresh_token: new_refresh_token } = response.data;
          
          set({
            accessToken: access_token,
            refreshToken: new_refresh_token
          });
        } catch (error) {
          // 刷新失败，清除认证状态
          get().clearAuth();
          throw error;
        }
      },

      // 发送验证码
      sendVerificationCode: async (identifier: string, type: string, region: string) => {
        await api.post('/auth/send-verification-code', {
          identifier,
          code_type: type,
          region
        });
      },

      // 忘记密码
      forgotPassword: async (identifier: string, region: string) => {
        await api.post('/auth/forgot-password', {
          identifier,
          region
        });
      },

      // 重置密码
      resetPassword: async (token: string, newPassword: string, confirmPassword: string) => {
        await api.post('/auth/reset-password', {
          token,
          new_password: newPassword,
          confirm_password: confirmPassword
        });
      },

      // 修改密码
      changePassword: async (oldPassword: string, newPassword: string, confirmPassword: string) => {
        await api.post('/auth/change-password', {
          old_password: oldPassword,
          new_password: newPassword,
          confirm_password: confirmPassword
        });
      },

      // 设置令牌
      setTokens: (accessToken: string, refreshToken: string) => {
        set({ 
          accessToken, 
          refreshToken, 
          isAuthenticated: true 
        });
      },

      // 清除认证状态
      clearAuth: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          isLoading: false
        });
      },

      // 设置用户信息
      setUser: (user: User) => {
        set({ user });
      },

      // 设置加载状态
      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      }
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated
      }), // 只持久化这些字段
    }
  )
);

// 导出API实例供其他地方使用
export { api }; 