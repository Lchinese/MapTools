import axios from 'axios';

// 创建axios实例
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data;
  },
  (error) => {
    if (error.response?.status === 401) {
      // 处理未授权
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 仅保留认证相关接口
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 用户登录
  login: (credentials) => api.post('/auth/login', credentials),
  
  // 验证令牌
  verify: () => api.get('/auth/verify'),
  
  // 用户登出
  logout: () => api.post('/auth/logout'),
};

// 健康检查（直接访问后端根健康接口）
export const healthAPI = {
  health: () => axios.get('http://localhost:8000/health').then(r => r.data)
};

// 地图匹配API - 直接访问后端，不使用/api/v1前缀
export const matchingAPI = {
  getGPSData: (params = {}) => axios.get('http://localhost:8000/matching/gps-data', { params }).then(r => r.data),
  matchToRoads: (params = {}) => axios.get('http://localhost:8000/matching/match', { params }).then(r => r.data),
  getRoadNetwork: () => axios.get('http://localhost:8000/matching/road-network').then(r => r.data),
  getVehiclesData: (params = {}) => axios.get('http://localhost:8000/matching/vehicles', { params }).then(r => r.data),
};

export default api;