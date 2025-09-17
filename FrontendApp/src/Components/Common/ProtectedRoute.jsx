import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../../Hooks/useAuth';
import Loading from './Loading';

const ProtectedRoute = ({ children, requireAuth = true }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  console.log('ProtectedRoute 状态:', { isAuthenticated, loading, requireAuth, path: location.pathname });

  if (loading) {
    return <Loading text="验证身份中..." />;
  }

  if (requireAuth && !isAuthenticated) {
    console.log('需要认证但未登录，重定向到登录页');
    // 保存当前路径，登录后重定向
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (!requireAuth && isAuthenticated) {
    console.log('已登录用户访问登录页，重定向到首页');
    // 已登录用户访问登录/注册页面，重定向到首页
    return <Navigate to="/" replace />;
  }

  if (!requireAuth && !isAuthenticated) {
    console.log('未登录用户访问公开页面，允许访问');
  }

  console.log('允许访问受保护的内容');
  return children;
};

export default ProtectedRoute;
