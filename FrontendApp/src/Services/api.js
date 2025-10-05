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
  getRoadNetwork: (limit = null, zoomLevel = null) => {
    const params = {};
    if (limit) params.limit = limit;
    if (zoomLevel) params.zoom_level = zoomLevel;
    return axios.get('http://localhost:8000/matching/road-network', { params }).then(r => r.data);
  },
  getVehiclesData: (params = {}) => axios.get('http://localhost:8000/matching/vehicles', { params }).then(r => r.data),
  getMatchedPoints: () => axios.get('http://localhost:8000/matching/match').then(r => r.data),
  
  // OSRM路径规划API（通过后端代理）
  getOSRMRoute: (waypoints) => {
    return axios.post('http://localhost:8000/matching/osrm-route', {
      waypoints: waypoints
    }).then(r => r.data);
  },
};

// 轨迹数据API
export const trajectoryAPI = {
  // 从数据库获取原始轨迹数据（分页查询）
  getOriginalTrajectoryData: (page = 1, pageSize = 20, plateNumber = null) => axios.get('http://localhost:8000/trajectory/original', { 
    params: { page, page_size: pageSize, plate_number: plateNumber } 
  }).then(r => r.data),
  
  // 批量获取指定数量车辆的轨迹数据
  getBatchTrajectoryData: (limit = 50, matchToRoads = false) => axios.get('http://localhost:8000/trajectory/batch', { 
    params: { limit, match_to_roads: matchToRoads } 
  }).then(r => r.data),
  
  // 分页获取所有车辆列表
  getAllTrajectoryData: (page = 1, pageSize = 10) => axios.get('http://localhost:8000/trajectory/all', { 
    params: { page, page_size: pageSize } 
  }).then(r => r.data),
  
  // 根据车牌号获取轨迹数据
  getTrajectoryDataByPlate: (plateNumber) => axios.get('http://localhost:8000/trajectory/by-plate', { 
    params: { plate_number: plateNumber } 
  }).then(r => r.data),
  
  // 获取所有车牌号
  getAllPlateNumbers: () => axios.get('http://localhost:8000/trajectory/plates').then(r => r.data),
  
  // 获取轨迹摘要信息
  getTrajectorySummary: (plateNumber) => axios.get('http://localhost:8000/trajectory/summary', {
    params: { plate_number: plateNumber }
  }).then(r => r.data),
  
  // 根据车牌号和时间范围获取单车辆轨迹数据
  getSingleVehicleTrajectory: (plateNumber, startTime, endTime, matchToRoads = false) => axios.get('http://localhost:8000/trajectory/single-vehicle', {
    params: { 
      plate_number: plateNumber,
      start_time: startTime,
      end_time: endTime,
      match_to_roads: matchToRoads
    }
  }).then(r => r.data),
  
  // 获取第一天第一辆车的轨迹数据（用于初始化）
  getFirstDayFirstVehicleTrajectory: () => axios.get('http://localhost:8000/trajectory/first-day-first-vehicle').then(r => r.data),
  
  // 修正轨迹相关API
  // 分页获取修正轨迹数据
  getCorrectedTrajectoryData: (page = 1, pageSize = 20, plateNumber = null) => axios.get('http://localhost:8000/trajectory/corrected', { 
    params: { page, page_size: pageSize, plate_number: plateNumber } 
  }).then(r => r.data),
  
  // 根据车牌号和时间范围获取单车辆修正轨迹数据
  getSingleVehicleCorrectedTrajectory: (plateNumber, startTime, endTime) => axios.get('http://localhost:8000/trajectory/corrected/single-vehicle', {
    params: { 
      plate_number: plateNumber,
      start_time: startTime,
      end_time: endTime
    }
  }).then(r => r.data),
};