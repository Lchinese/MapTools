import { useState, useEffect, useCallback } from 'react';
import { trajectoryAPI } from '../Services/api';

/**
 * 轨迹数据Hook
 * 用于从MongoDB获取轨迹数据
 */
export const useTrajectoryData = () => {
  const [trajectoryData, setTrajectoryData] = useState({});
  const [plateNumbers, setPlateNumbers] = useState([]);
  const [pagination, setPagination] = useState({
    currentPage: 1,
    pageSize: 10,
    totalItems: 0,
    totalPages: 0
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 批量获取指定数量车辆的轨迹数据
  const fetchBatchTrajectoryData = useCallback(async (limit = 50, matchToRoads = false) => {
    setLoading(true);
    setError(null);
    try {
      const response = await trajectoryAPI.getBatchTrajectoryData(limit, matchToRoads);
      if (response.success) {
        setTrajectoryData(response.data);
        // 提取车牌号列表
        const plates = Object.keys(response.data);
        setPlateNumbers(plates);
      } else {
        throw new Error(response.message || '批量获取轨迹数据失败');
      }
    } catch (err) {
      console.error('批量获取轨迹数据失败:', err);
      setError(err.message || '批量获取轨迹数据失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 分页获取车辆列表
  const fetchVehicleList = useCallback(async (page = 1, pageSize = 10) => {
    setLoading(true);
    setError(null);
    try {
      const response = await trajectoryAPI.getAllTrajectoryData(page, pageSize);
      if (response.success) {
        setPlateNumbers(response.data.plate_numbers);
        setPagination(response.data.pagination);
      } else {
        throw new Error(response.message || '获取车辆列表失败');
      }
    } catch (err) {
      console.error('获取车辆列表失败:', err);
      setError(err.message || '获取车辆列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 根据车牌号获取轨迹数据
  const fetchTrajectoryDataByPlate = useCallback(async (plateNumber) => {
    setLoading(true);
    setError(null);
    try {
      const response = await trajectoryAPI.getTrajectoryDataByPlate(plateNumber);
      if (response.success) {
        setTrajectoryData(prev => ({
          ...prev,
          ...response.data
        }));
        // 如果车牌号列表中没有这个车牌号，则添加到列表中
        if (!plateNumbers.includes(plateNumber)) {
          setPlateNumbers(prev => [...prev, plateNumber]);
        }
      } else {
        throw new Error(response.message || '获取轨迹数据失败');
      }
    } catch (err) {
      console.error('获取轨迹数据失败:', err);
      setError(err.message || '获取轨迹数据失败');
    } finally {
      setLoading(false);
    }
  }, [plateNumbers]);

  // 获取车辆轨迹摘要信息
  const fetchTrajectorySummary = useCallback(async (plateNumber) => {
    setLoading(true);
    setError(null);
    try {
      const response = await trajectoryAPI.getTrajectorySummary(plateNumber);
      if (response.success) {
        // 可以在这里处理摘要信息，比如存储到状态中
        return response.data;
      } else {
        throw new Error(response.message || '获取轨迹摘要信息失败');
      }
    } catch (err) {
      console.error('获取轨迹摘要信息失败:', err);
      setError(err.message || '获取轨迹摘要信息失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 获取所有车牌号
  const fetchAllPlateNumbers = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await trajectoryAPI.getAllPlateNumbers();
      if (response.success) {
        setPlateNumbers(response.data.plate_numbers);
      } else {
        throw new Error(response.message || '获取车牌号列表失败');
      }
    } catch (err) {
      console.error('获取车牌号列表失败:', err);
      setError(err.message || '获取车牌号列表失败');
    } finally {
      setLoading(false);
    }
  }, []);

  // 清除错误
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 清除轨迹数据
  const clearTrajectoryData = useCallback(() => {
    setTrajectoryData({});
  }, []);

  return {
    trajectoryData,
    plateNumbers,
    pagination,
    loading,
    error,
    fetchBatchTrajectoryData,
    fetchVehicleList,
    fetchTrajectoryDataByPlate,
    fetchTrajectorySummary,
    fetchAllPlateNumbers,
    clearError,
    clearTrajectoryData
  };
};

/**
 * 轨迹相关Hook
 */
export const useTrajectory = () => {
  const {
    trajectories,
    currentTrajectory,
    matchingTasks,
    currentTask,
    loading,
    error,
    fetchTrajectories,
    fetchTrajectory,
    uploadTrajectory,
    deleteTrajectory,
    startMatching,
    fetchMatchingTasks,
    fetchTaskStatus,
    fetchTaskResult,
    clearError,
    reset,
  } = useTrajectoryStore();

  // 上传轨迹文件
  const handleUpload = useCallback(async (file, metadata = {}) => {
    try {
      // 解析文件内容
      const parsedData = await parseTrajectoryFile(file);
      
      // 合并元数据
      const uploadMetadata = {
        ...metadata,
        name: metadata.name || parsedData.metadata.name,
        description: metadata.description || parsedData.metadata.description,
      };

      return await uploadTrajectory(file, uploadMetadata);
    } catch (error) {
      console.error('轨迹上传失败:', error);
      throw error;
    }
  }, [uploadTrajectory]);

  // 开始匹配任务
  const handleStartMatching = useCallback(async (trajectoryId, algorithm = 'distance_matching', parameters = {}) => {
    try {
      return await startMatching(trajectoryId, algorithm, parameters);
    } catch (error) {
      console.error('启动匹配失败:', error);
      throw error;
    }
  }, [startMatching]);

  // 轮询任务状态
  const pollTaskStatus = useCallback(async (taskId, onComplete, onError) => {
    const pollInterval = setInterval(async () => {
      try {
        const status = await fetchTaskStatus(taskId);
        
        if (status.status === 'completed') {
          clearInterval(pollInterval);
          if (onComplete) onComplete(status);
        } else if (status.status === 'failed') {
          clearInterval(pollInterval);
          if (onError) onError(status);
        }
      } catch (error) {
        clearInterval(pollInterval);
        if (onError) onError(error);
      }
    }, 2000); // 每2秒轮询一次

    return pollInterval;
  }, [fetchTaskStatus]);

  // 获取轨迹统计信息
  const getTrajectoryStats = useCallback((trajectory) => {
    if (!trajectory || !trajectory.points) {
      return {
        totalPoints: 0,
        totalDistance: 0,
        duration: 0,
        averageSpeed: 0,
        bounds: null,
      };
    }

    const points = trajectory.points;
    const totalPoints = points.length;
    
    // 计算总距离
    let totalDistance = 0;
    for (let i = 1; i < points.length; i++) {
      const prev = points[i - 1];
      const curr = points[i];
      const distance = calculateDistance(
        prev.latitude, prev.longitude,
        curr.latitude, curr.longitude
      );
      totalDistance += distance;
    }

    // 计算持续时间
    let duration = 0;
    if (points.length > 1) {
      const startTime = new Date(points[0].timestamp);
      const endTime = new Date(points[points.length - 1].timestamp);
      duration = (endTime - startTime) / 1000; // 秒
    }

    // 计算平均速度
    const averageSpeed = duration > 0 ? (totalDistance / duration) * 3.6 : 0; // km/h

    // 计算边界
    const lats = points.map(p => p.latitude);
    const lngs = points.map(p => p.longitude);
    const bounds = {
      minLat: Math.min(...lats),
      maxLat: Math.max(...lats),
      minLon: Math.min(...lngs),
      maxLon: Math.max(...lngs),
    };

    return {
      totalPoints,
      totalDistance,
      duration,
      averageSpeed,
      bounds,
    };
  }, []);

  // 获取匹配任务统计信息
  const getMatchingStats = useCallback(() => {
    const total = matchingTasks.length;
    const completed = matchingTasks.filter(t => t.status === 'completed').length;
    const processing = matchingTasks.filter(t => t.status === 'processing').length;
    const failed = matchingTasks.filter(t => t.status === 'failed').length;
    const queued = matchingTasks.filter(t => t.status === 'queued').length;

    return {
      total,
      completed,
      processing,
      failed,
      queued,
      completionRate: total > 0 ? (completed / total) * 100 : 0,
    };
  }, [matchingTasks]);

  return {
    // 状态
    trajectories,
    currentTrajectory,
    matchingTasks,
    currentTask,
    loading,
    error,

    // 基础操作
    fetchTrajectories,
    fetchTrajectory,
    uploadTrajectory: handleUpload,
    deleteTrajectory,
    startMatching: handleStartMatching,
    fetchMatchingTasks,
    fetchTaskStatus,
    fetchTaskResult,
    clearError,
    reset,

    // 高级操作
    pollTaskStatus,
    getTrajectoryStats,
    getMatchingStats,
  };
};

/**
 * 轨迹文件处理Hook
 */
export const useTrajectoryFile = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);
  const [fileInfo, setFileInfo] = useState(null);

  // 处理文件
  const processFile = useCallback(async (file) => {
    setIsProcessing(true);
    setProcessingProgress(0);
    setFileInfo(null);

    try {
      // 解析文件
      const parsedData = await parseTrajectoryFile(file);
      
      // 模拟处理进度
      const progressInterval = setInterval(() => {
        setProcessingProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 20;
        });
      }, 200);

      // 计算文件信息
      const info = {
        name: file.name,
        size: file.size,
        type: file.type,
        lastModified: file.lastModified,
        points: parsedData.points.length,
        metadata: parsedData.metadata,
      };

      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟处理时间
      
      clearInterval(progressInterval);
      setProcessingProgress(100);
      setFileInfo(info);

      return parsedData;
    } catch (error) {
      console.error('文件处理失败:', error);
      throw error;
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingProgress(0), 1000);
    }
  }, []);

  // 重置状态
  const reset = useCallback(() => {
    setIsProcessing(false);
    setProcessingProgress(0);
    setFileInfo(null);
  }, []);

  return {
    isProcessing,
    processingProgress,
    fileInfo,
    processFile,
    reset,
  };
};

// 辅助函数：计算两点间距离
const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000; // 地球半径（米）
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

const toRadians = (degrees) => {
  return degrees * (Math.PI / 180);
};