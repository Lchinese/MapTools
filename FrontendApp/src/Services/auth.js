import api from './api';

// 认证相关API
export const authAPI = {
  // 用户登录
  login: (credentials) => api.post('/auth/login', credentials),
  
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 验证token
  verifyToken: () => api.get('/auth/verify'),
  
  // 刷新token
  refreshToken: () => api.post('/auth/refresh'),
  
  // 忘记密码
  forgotPassword: (email) => api.post('/auth/forgot-password', { email }),
  
  // 重置密码
  resetPassword: (token, newPassword) => api.post('/auth/reset-password', { 
    token, 
    password: newPassword 
  }),
  
  // 修改密码
  changePassword: (oldPassword, newPassword) => api.post('/auth/change-password', {
    oldPassword,
    newPassword
  }),
  
  // 更新用户资料
  updateProfile: (userData) => api.put('/auth/profile', userData),
  
  // 获取用户信息
  getProfile: () => api.get('/auth/profile'),
  
  // 登出
  logout: () => api.post('/auth/logout'),
};