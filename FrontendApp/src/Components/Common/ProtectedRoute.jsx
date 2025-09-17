import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../Hooks/useAuth';
import Loading from './Loading';

const ProtectedRoute = ({ children, requireAuth = true }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <Loading text="验证身份中..." />;
  }

  if (requireAuth && !isAuthenticated) {
    // 保存当前路径，登录后重定向
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!requireAuth && isAuthenticated) {
    // 已登录用户访问登录/注册页面，重定向到首页
    return <Navigate to="/" replace />;
  }

  return children;
};

export default ProtectedRoute;
