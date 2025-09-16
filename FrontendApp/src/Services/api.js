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

// API接口定义
export const trajectoryAPI = {
  // 上传轨迹文件
  upload: (formData) => api.post('/trajectories/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  
  // 获取轨迹列表
  list: (params) => api.get('/trajectories', { params }),
  
  // 获取轨迹详情
  get: (id) => api.get(`/trajectories/${id}`),
  
  // 删除轨迹
  delete: (id) => api.delete(`/trajectories/${id}`),
  
  // 下载轨迹
  download: (id, format = 'gpx') => api.get(`/trajectories/${id}/download`, {
    params: { format },
    responseType: 'blob'
  }),
};

export const matchingAPI = {
  // 开始匹配任务
  start: (data) => api.post('/matching/start', data),
  
  // 获取任务状态
  status: (taskId) => api.get(`/matching/status/${taskId}`),
  
  // 获取匹配结果
  result: (taskId) => api.get(`/matching/result/${taskId}`),
  
  // 下载匹配结果
  download: (taskId, format = 'gpx') => api.get(`/matching/download/${taskId}`, {
    params: { format },
    responseType: 'blob'
  }),
  
  // 获取任务列表
  list: (params) => api.get('/matching/tasks', { params }),
};

export const fileAPI = {
  // 获取文件列表
  list: (params) => api.get('/files', { params }),
  
  // 获取文件详情
  get: (id) => api.get(`/files/${id}`),
  
  // 删除文件
  delete: (id) => api.delete(`/files/${id}`),
  
  // 下载文件
  download: (id) => api.get(`/files/${id}/download`, {
    responseType: 'blob'
  }),
};

export const roadNetworkAPI = {
  // 获取路网列表
  list: (params) => api.get('/road-networks', { params }),
  
  // 获取路网详情
  get: (id) => api.get(`/road-networks/${id}`),
  
  // 获取道路段
  segments: (networkId, params) => api.get(`/road-networks/${networkId}/segments`, { params }),
};

export const systemAPI = {
  // 健康检查
  health: () => api.get('/health'),
  
  // 系统状态
  status: () => api.get('/system/status'),
  
  // 队列状态
  queue: () => api.get('/system/queue'),
};

export default api;