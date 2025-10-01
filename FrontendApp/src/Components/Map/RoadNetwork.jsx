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

  // 性能优化：根据缩放级别过滤道路
  const filteredRoadData = useMemo(() => {
    if (!roadData || roadData.length === 0) {
      return [];
    }

    // 根据缩放级别决定显示多少道路
    let maxRoads = 0;
    if (debouncedZoom >= 15) {
      maxRoads = roadData.length; // 高缩放级别显示所有道路
    } else if (debouncedZoom >= 13) {
      maxRoads = Math.min(roadData.length, 20000); // 中等缩放级别显示2万条
    } else if (debouncedZoom >= 11) {
      maxRoads = Math.min(roadData.length, 10000); // 低缩放级别显示1万条
    } else {
      maxRoads = Math.min(roadData.length, 5000); // 很低缩放级别显示5千条
    }

    // 优先显示有名称的道路
    const namedRoads = roadData.filter(road => road.name && road.name !== '未命名道路');
    const unnamedRoads = roadData.filter(road => !road.name || road.name === '未命名道路');

    const selectedRoads = [
      ...namedRoads.slice(0, Math.min(maxRoads * 0.7, namedRoads.length)),
      ...unnamedRoads.slice(0, Math.max(0, maxRoads - namedRoads.length))
    ];

    console.log(`缩放级别: ${debouncedZoom}, 原始道路: ${roadData.length}, 过滤后: ${selectedRoads.length}`);
    return selectedRoads;
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
          coordinates = road.geometry.coordinates[0].map(coord => {
            if (Array.isArray(coord) && coord.length >= 2) {
              return [coord[1], coord[0]]; // [纬度, 经度]
            }
            return null;
          }).filter(coord => coord !== null);
        }
      }

      if (coordinates.length < 2) {
        return null;
      }

      // 根据道路类型设置不同颜色
      let roadColor = '#666666';
      let roadWeight = 1;
      
      if (road.分类名称) {
        switch (road.分类名称) {
          case '有名称_服务区内部':
            roadColor = '#ff6b6b';
            roadWeight = 2;
            break;
          case '有名称_非服务区内部':
            roadColor = '#4ecdc4';
            roadWeight = 2;
            break;
          case '无名称_服务区内部':
            roadColor = '#ffe66d';
            roadWeight = 1;
            break;
          case '无名称_非服务区内部':
            roadColor = '#95a5a6';
            roadWeight = 1;
            break;
          default:
            roadColor = '#666666';
            roadWeight = 1;
        }
      }

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
