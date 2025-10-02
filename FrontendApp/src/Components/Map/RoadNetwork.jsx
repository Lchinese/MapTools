import React, { useEffect, useState, useMemo } from 'react';
import { Polyline, useMap } from 'react-leaflet';
import { matchingAPI } from '../../Services/api';

// 坐标简化函数 - 根据缩放级别减少坐标点数量
const simplifyCoordinates = (coordinates, zoom) => {
  if (!coordinates || coordinates.length <= 2) {
    return coordinates;
  }

  // 根据缩放级别决定简化程度
  let step = 1;
  if (zoom < 10) {
    step = Math.max(1, Math.floor(coordinates.length / 10)); // 很低缩放级别，最多保留10个点
  } else if (zoom < 12) {
    step = Math.max(1, Math.floor(coordinates.length / 20)); // 低缩放级别，最多保留20个点
  } else if (zoom < 14) {
    step = Math.max(1, Math.floor(coordinates.length / 50)); // 中等缩放级别，最多保留50个点
  } else {
    step = 1; // 高缩放级别，保留所有点
  }

  const simplified = [];
  for (let i = 0; i < coordinates.length; i += step) {
    simplified.push(coordinates[i]);
  }

  // 确保起点和终点都被包含
  if (simplified[simplified.length - 1] !== coordinates[coordinates.length - 1]) {
    simplified.push(coordinates[coordinates.length - 1]);
  }

  return simplified;
};

const RoadNetwork = ({ showRoadNetwork }) => {
  const [roadData, setRoadData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [renderStats, setRenderStats] = useState({ loadTime: 0, renderTime: 0, roadCount: 0 });
  const [currentZoom, setCurrentZoom] = useState(12);
  const [debouncedZoom, setDebouncedZoom] = useState(12);
  const map = useMap();

  useEffect(() => {
    if (showRoadNetwork) {
      loadRoadData();
    } else {
      setRoadData([]);
    }
  }, [showRoadNetwork]);

  // 监听地图缩放级别变化
  useEffect(() => {
    if (!map) return;

    const handleZoomEnd = () => {
      setCurrentZoom(map.getZoom());
    };

    map.on('zoomend', handleZoomEnd);
    return () => {
      map.off('zoomend', handleZoomEnd);
    };
  }, [map]);

  // 防抖处理缩放级别变化
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedZoom(currentZoom);
    }, 300); // 300ms防抖

    return () => clearTimeout(timer);
  }, [currentZoom]);

  const loadRoadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const loadStartTime = Date.now();
      console.log('开始加载道路网络数据...');
      
      // 根据当前缩放级别决定加载多少道路数据
      let limit = null;
      if (currentZoom < 10) {
        limit = 5000; // 很低缩放级别，只加载5千条
      } else if (currentZoom < 12) {
        limit = 10000; // 低缩放级别，加载1万条
      } else if (currentZoom < 14) {
        limit = 20000; // 中等缩放级别，加载2万条
      }
      // 高缩放级别不限制，加载所有数据
      
      const response = await matchingAPI.getRoadNetwork(limit, currentZoom);
      console.log('道路网络API响应:', response);
      
      if (response && response.roads) {
        setRoadData(response.roads);
        const loadTime = Date.now() - loadStartTime;
        setRenderStats(prev => ({ ...prev, loadTime, roadCount: response.roads.length }));
        console.log(`成功加载 ${response.roads.length} 条道路数据，耗时: ${loadTime}ms`);
      } else {
        console.warn('道路网络数据格式异常:', response);
        setRoadData([]);
      }
    } catch (err) {
      console.error('加载道路网络数据失败:', err);
      setError(err.message);
      setRoadData([]);
    } finally {
      setLoading(false);
    }
  };

  // 显示所有道路，不进行过滤
  const filteredRoadData = useMemo(() => {
    if (!roadData || roadData.length === 0) {
      return [];
    }


    console.log(`缩放级别: ${debouncedZoom}, 显示道路: ${roadData.length}`);
    return roadData;
  }, [roadData, debouncedZoom]);

  // 使用useMemo优化道路渲染
  const roadElements = useMemo(() => {
    if (!filteredRoadData || filteredRoadData.length === 0) {
      return null;
    }

    console.log(`开始渲染 ${filteredRoadData.length} 条道路`);
    const renderStart = Date.now();

    const elements = filteredRoadData.map((road, index) => {
      // 处理不同的道路数据格式
      let coordinates = [];
      
      if (road.points && Array.isArray(road.points)) {
        // 新格式：从MongoDB道路数据集合
        let rawCoordinates = road.points.map(point => {
          // 确保坐标格式正确 [纬度, 经度]
          if (typeof point.latitude === 'number' && typeof point.longitude === 'number') {
            return [point.latitude, point.longitude];
          }
          return null;
        }).filter(coord => coord !== null);

        // 根据缩放级别简化坐标点
        coordinates = simplifyCoordinates(rawCoordinates, debouncedZoom);
      } else if (road.geometry && road.geometry.coordinates) {
        // GeoJSON格式 - 坐标是 [经度, 纬度]，需要转换为 [纬度, 经度]
        if (road.geometry.type === 'LineString') {
          coordinates = road.geometry.coordinates.map(coord => {
            if (Array.isArray(coord) && coord.length >= 2) {
              return [coord[1], coord[0]]; // [纬度, 经度]
            }
            return null;
          }).filter(coord => coord !== null);
        } else if (road.geometry.type === 'MultiLineString') {
          // 修复：渲染所有子线段，而不是只渲染第一段
          coordinates = road.geometry.coordinates
            .filter(line => Array.isArray(line))
            .flatMap(line => line
              .filter(coord => Array.isArray(coord) && coord.length >= 2)
              .map(coord => [coord[1], coord[0]]) // [纬度, 经度]
            );
        }
      }

      if (coordinates.length < 2) {
        return null;
      }


      const roadColor = '#4a90e2';  // 统一的蓝色
      const roadWeight = 1.5;       // 统一的线宽

      return (
        <Polyline
          key={`road-${road.id || index}`}
          positions={coordinates}
          color={roadColor}
          weight={roadWeight}
          opacity={0.6}
          pathOptions={{
            className: 'road-network-line'
          }}
        />
      );
    });

    const renderTime = Date.now() - renderStart;
    setRenderStats(prev => ({ ...prev, renderTime }));
    console.log(`道路网络渲染完成，耗时: ${renderTime}ms`);

    return elements;
  }, [roadData]);

  if (!showRoadNetwork || loading) {
    return loading ? (
      <div className="road-network-loading">
        加载道路网络中...
      </div>
    ) : null;
  }

  if (error) {
    console.error('道路网络加载错误:', error);
    return (
      <div className="road-network-loading" style={{ color: '#ff4d4f' }}>
        道路网络加载失败
      </div>
    );
  }

  if (!roadData || roadData.length === 0) {
    console.log('没有道路数据可显示');
    return null;
  }

  return (
    <>
      {roadElements}
      {renderStats.roadCount > 0 && (
        <div className="road-network-stats">
          道路数量: {filteredRoadData.length}/{renderStats.roadCount} | 
          缩放级别: {debouncedZoom} | 
          加载耗时: {renderStats.loadTime}ms | 
          渲染耗时: {renderStats.renderTime}ms
        </div>
      )}
    </>
  );
};

export default RoadNetwork;
