import { useState, useEffect, useCallback } from 'react';
import { authAPI } from '../Services/api';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  // 检查本地存储的token
  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      try {
        const parsedUser = JSON.parse(userData);
        setUser(parsedUser);
        setIsAuthenticated(true);
      } catch (error) {
        console.error('解析用户数据失败:', error);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
      }
    }
    setLoading(false);
  }, []);

  // 登录
  const login = useCallback(async (email, password) => {
    try {
      console.log('开始登录:', email);
      const response = await authAPI.login({ email, password });
      console.log('登录响应:', response);
      
      if (response.success) {
        const { token, user: userData } = response.data;
        
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        
        setUser(userData);
        setIsAuthenticated(true);
        
        console.log('登录成功，用户状态已更新');
        return response.data;
      } else {
        throw new Error(response.message || '登录失败');
      }
    } catch (error) {
      console.error('登录错误:', error);
      throw error;
    }
  }, []);

  // 注册
  const register = useCallback(async (userData) => {
    try {
      const response = await authAPI.register(userData);
      
      if (response.success) {
        return response.data;
      } else {
        throw new Error(response.message || '注册失败');
      }
    } catch (error) {
      console.error('注册错误:', error);
      throw error;
    }
  }, []);

  // 登出
  const logout = useCallback(() => {
    console.log('开始登出');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setIsAuthenticated(false);
    console.log('登出完成，状态已重置 - isAuthenticated: false, user: null');
  }, []);

  // 更新用户信息
  const updateUser = useCallback((userData) => {
    setUser(userData);
    localStorage.setItem('user', JSON.stringify(userData));
  }, []);

  // 检查token有效性
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      return false;
    }

    try {
      const response = await authAPI.verifyToken();
      if (response.success) {
        setUser(response.data.user);
        setIsAuthenticated(true);
        return true;
      } else {
        logout();
        return false;
      }
    } catch (error) {
      console.error('Token验证失败:', error);
      logout();
      return false;
    }
  }, [logout]);

  return {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    updateUser,
    checkAuth
  };
};
