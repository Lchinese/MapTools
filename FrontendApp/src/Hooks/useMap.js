import { useState, useEffect, useCallback } from 'react';
import { useMapStore } from '../Store/mapStore';

/**
 * 地图相关Hook
 */
export const useMap = () => {
  const {
    center,
    zoom,
    bounds,
    originalTrajectory,
    matchedTrajectory,
    roadNetwork,
    showOriginal,
    showMatched,
    showRoadNetwork,
    setCenter,
    setZoom,
    setBounds,
    setOriginalTrajectory,
    setMatchedTrajectory,
    setRoadNetwork,
    toggleOriginal,
    toggleMatched,
    toggleRoadNetwork,
    resetMap,
    resetData,
    reset,
  } = useMapStore();

  // 计算地图边界
  const calculateMapBounds = useCallback(() => {
    const allPoints = [];
    
    if (showOriginal && originalTrajectory?.points) {
      allPoints.push(...originalTrajectory.points.map(p => [p.latitude, p.longitude]));
    }
    
    if (showMatched && matchedTrajectory?.points) {
      allPoints.push(...matchedTrajectory.points.map(p => [p.matched_latitude, p.matched_longitude]));
    }

    if (allPoints.length > 0) {
      const lats = allPoints.map(p => p[0]);
      const lngs = allPoints.map(p => p[1]);
      
      return [
        [Math.min(...lats), Math.min(...lngs)],
        [Math.max(...lats), Math.max(...lngs)]
      ];
    }
    
    return null;
  }, [showOriginal, showMatched, originalTrajectory, matchedTrajectory]);

  // 自动调整地图视图
  const fitToTrajectory = useCallback(() => {
    const newBounds = calculateMapBounds();
    if (newBounds) {
      setBounds(newBounds);
    }
  }, [calculateMapBounds, setBounds]);

  // 重置到默认视图
  const resetToDefault = useCallback(() => {
    resetMap();
  }, [resetMap]);

  // 清除所有数据
  const clearAllData = useCallback(() => {
    resetData();
  }, [resetData]);

  // 完全重置
  const resetAll = useCallback(() => {
    reset();
  }, [reset]);

  return {
    // 状态
    center,
    zoom,
    bounds,
    originalTrajectory,
    matchedTrajectory,
    roadNetwork,
    showOriginal,
    showMatched,
    showRoadNetwork,
    
    // 操作方法
    setCenter,
    setZoom,
    setBounds,
    setOriginalTrajectory,
    setMatchedTrajectory,
    setRoadNetwork,
    toggleOriginal,
    toggleMatched,
    toggleRoadNetwork,
    
    // 计算和工具方法
    calculateMapBounds,
    fitToTrajectory,
    resetToDefault,
    clearAllData,
    resetAll,
  };
};

/**
 * 地图事件处理Hook
 */
export const useMapEvents = (mapRef) => {
  const [isMapReady, setIsMapReady] = useState(false);
  const [mapInstance, setMapInstance] = useState(null);

  useEffect(() => {
    if (mapRef?.current) {
      const map = mapRef.current;
      setMapInstance(map);
      setIsMapReady(true);
    }
  }, [mapRef]);

  // 地图点击事件
  const handleMapClick = useCallback((event) => {
    console.log('Map clicked:', event.latlng);
  }, []);

  // 地图缩放事件
  const handleZoomChange = useCallback((event) => {
    console.log('Map zoom changed:', event.target.getZoom());
  }, []);

  // 地图移动事件
  const handleMoveEnd = useCallback((event) => {
    console.log('Map moved:', event.target.getCenter());
  }, []);

  return {
    isMapReady,
    mapInstance,
    handleMapClick,
    handleZoomChange,
    handleMoveEnd,
  };
};

/**
 * 轨迹数据处理Hook
 */
export const useTrajectoryProcessing = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingProgress, setProcessingProgress] = useState(0);

  // 处理轨迹数据
  const processTrajectoryData = useCallback(async (rawData) => {
    setIsProcessing(true);
    setProcessingProgress(0);

    try {
      // 模拟数据处理进度
      const progressInterval = setInterval(() => {
        setProcessingProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 20;
        });
      }, 200);

      // 这里可以添加实际的数据处理逻辑
      // 例如：数据清洗、格式转换、统计分析等
      
      await new Promise(resolve => setTimeout(resolve, 1000)); // 模拟处理时间
      
      clearInterval(progressInterval);
      setProcessingProgress(100);
      
      return rawData;
    } catch (error) {
      console.error('轨迹数据处理失败:', error);
      throw error;
    } finally {
      setIsProcessing(false);
      setTimeout(() => setProcessingProgress(0), 1000);
    }
  }, []);

  return {
    isProcessing,
    processingProgress,
    processTrajectoryData,
  };
};