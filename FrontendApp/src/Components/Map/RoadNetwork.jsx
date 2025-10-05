import React, { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { Polyline, useMap } from 'react-leaflet';
import { matchingAPI } from '../../Services/api';

// 添加CSS样式确保道路可见
const roadStyles = `
  .road-network-line {
    stroke: #4a90e2 !important;
    stroke-width: 1.5px !important;
    stroke-opacity: 0.6 !important;
    z-index: 1000 !important;
  }
`;

// 注入样式
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = roadStyles;
  document.head.appendChild(styleElement);
}

// 优化的坐标简化函数 - 根据缩放级别减少坐标点数量
const simplifyCoordinates = (coordinates, zoom) => {
  if (!coordinates || coordinates.length <= 2) {
    return coordinates;
  }

  // 根据缩放级别决定简化程度，更激进的简化
  let maxPoints;
  if (zoom < 8) {
    maxPoints = 5; // 极低缩放级别，最多5个点
  } else if (zoom < 10) {
    maxPoints = 8; // 很低缩放级别，最多8个点
  } else if (zoom < 12) {
    maxPoints = 15; // 低缩放级别，最多15个点
  } else if (zoom < 14) {
    maxPoints = 30; // 中等缩放级别，最多30个点
  } else if (zoom < 16) {
    maxPoints = 60; // 高缩放级别，最多60个点
  } else {
    return coordinates; // 最高缩放级别，保留所有点
  }

  if (coordinates.length <= maxPoints) {
    return coordinates;
  }

  const step = Math.floor(coordinates.length / maxPoints);
  const simplified = [];
  
  // 始终包含第一个点
  simplified.push(coordinates[0]);
  
  // 按步长采样中间点
  for (let i = step; i < coordinates.length - step; i += step) {
    simplified.push(coordinates[i]);
  }
  
  // 始终包含最后一个点
  if (coordinates.length > 1) {
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
  const [renderedRoads, setRenderedRoads] = useState([]);
  const [renderProgress, setRenderProgress] = useState(0);
  const renderingRef = useRef(false);
  const animationFrameRef = useRef(null);
  const lastRenderZoomRef = useRef(12);
  const map = useMap();

  // 组件卸载时清理渲染状态
  useEffect(() => {
    return () => {
      renderingRef.current = false;
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (showRoadNetwork) {
      loadRoadData();
    } else {
      setRoadData([]);
    }
  }, [showRoadNetwork]);

  // 监听地图缩放和移动事件
  useEffect(() => {
    if (!map) return;

    let updateTimer = null;

    const handleZoomEnd = () => {
      setCurrentZoom(map.getZoom());
    };

    // 地图移动时不重新渲染
    const handleMoveEnd = () => {
      // 移动时不做任何操作，保持当前渲染
    };

    map.on('zoomend', handleZoomEnd);
    map.on('moveend', handleMoveEnd);
    
    return () => {
      map.off('zoomend', handleZoomEnd);
      map.off('moveend', handleMoveEnd);
      if (updateTimer) {
        clearTimeout(updateTimer);
      }
    };
  }, [map]);

  // 增加防抖时间，减少重新渲染频率
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedZoom(currentZoom);
    }, 500); // 500ms防抖，减少频繁重新渲染

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

  // 分批渲染道路，防止页面卡死
  const batchRenderRoads = useCallback((roads) => {
    // 强制停止当前渲染
    renderingRef.current = false;
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
      animationFrameRef.current = null;
    }

    // 开始新的渲染
    renderingRef.current = true;
    setRenderedRoads([]);
    setRenderProgress(0);

    const BATCH_SIZE = 500; // 每批渲染500条道路
    let currentBatch = 0;
    const totalBatches = Math.ceil(roads.length / BATCH_SIZE);

    const renderBatch = () => {
      if (!renderingRef.current) {
        console.log('渲染被中断，renderingRef.current为false');
        return;
      }

      const startIndex = currentBatch * BATCH_SIZE;
      const endIndex = Math.min(startIndex + BATCH_SIZE, roads.length);
      const batchRoads = roads.slice(startIndex, endIndex);
      
      console.log(`渲染批次 ${currentBatch + 1}/${totalBatches}, 道路 ${startIndex}-${endIndex}`);

      const batchElements = batchRoads.map((road, index) => {
        const globalIndex = startIndex + index;
        
        // 处理不同的道路数据格式
        let coordinates = [];
        
        if (road.points && Array.isArray(road.points)) {
          // 新格式：从MongoDB道路数据集合
          let rawCoordinates = road.points.map(point => {
            // 处理两种可能的格式：
            // 1. {latitude: number, longitude: number} 对象格式
            // 2. [lat, lon] 或 (lat, lon) 数组/元组格式
            if (typeof point === 'object' && point !== null) {
              if (typeof point.latitude === 'number' && typeof point.longitude === 'number') {
                return [point.latitude, point.longitude];
              } else if (Array.isArray(point) && point.length >= 2) {
                return [point[0], point[1]]; // [lat, lon]
              }
            } else if (Array.isArray(point) && point.length >= 2) {
              return [point[0], point[1]]; // [lat, lon]
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
          console.log(`道路 ${road.id || globalIndex} 坐标点不足，跳过渲染`);
          return null;
        }

        const roadColor = '#4a90e2';  // 统一的蓝色
        const roadWeight = 1.5;       // 统一的线宽

        // 调试：打印前几条道路的详细信息
        if (globalIndex < 3) {
          console.log(`=== 道路 ${globalIndex} 渲染详情 ===`);
          console.log('道路ID:', road.id);
          console.log('坐标数量:', coordinates.length);
          console.log('前3个坐标:', coordinates.slice(0, 3));
          console.log('颜色:', roadColor);
          console.log('线宽:', roadWeight);
          console.log('========================');
        }

        return (
          <Polyline
            key={`road-${road.id || globalIndex}`}
            positions={coordinates}
            color={roadColor}
            weight={roadWeight}
            opacity={0.6}
            pathOptions={{
              className: 'road-network-line',
              smoothFactor: 1.0,      // 减少简化，保持更多细节
              noClip: false,          // 启用裁剪
              interactive: false,     // 禁用交互提升性能
              pane: 'overlayPane'     // 确保在顶层显示
            }}
            style={{
              zIndex: 1000,           // 高z-index确保在顶层
              stroke: roadColor,
              strokeWidth: roadWeight,
              strokeOpacity: 0.6
            }}
          />
        );
      }).filter(element => element !== null);

      setRenderedRoads(prev => [...prev, ...batchElements]);
      setRenderProgress(Math.round((currentBatch + 1) / totalBatches * 100));

      currentBatch++;

      if (currentBatch < totalBatches && renderingRef.current) {
        // 使用requestAnimationFrame确保不阻塞UI
        animationFrameRef.current = requestAnimationFrame(renderBatch);
      } else {
        renderingRef.current = false;
        animationFrameRef.current = null;
        setRenderProgress(100);
        console.log(`分批渲染完成，总共渲染 ${roads.length} 条道路`);
      }
    };

    // 开始渲染
    animationFrameRef.current = requestAnimationFrame(renderBatch);
  }, [debouncedZoom]);

  // 当道路数据改变时，重新分批渲染
  useEffect(() => {
    if (filteredRoadData && filteredRoadData.length > 0) {
      const zoomDiff = Math.abs(debouncedZoom - lastRenderZoomRef.current);
      
      // 只有缩放变化超过1级或首次加载时才重新渲染
      if (zoomDiff >= 3 || renderedRoads.length === 0) {
        console.log(`缩放变化 ${zoomDiff.toFixed(1)}，开始分批渲染 ${filteredRoadData.length} 条道路`);
        lastRenderZoomRef.current = debouncedZoom;
        batchRenderRoads(filteredRoadData);
      } else {
        console.log(`缩放变化 ${zoomDiff.toFixed(1)} 较小，保持当前渲染`);
      }
    } else {
      setRenderedRoads([]);
      setRenderProgress(0);
    }

    return () => {
      // 只在组件卸载时才停止渲染，不要在依赖变化时停止
      // renderingRef.current = false;
      // if (animationFrameRef.current) {
      //   cancelAnimationFrame(animationFrameRef.current);
      // }
    };
  }, [filteredRoadData, batchRenderRoads]);

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
      
      {renderedRoads}
      {renderingRef.current && (
        <div className="road-network-loading">
          渲染道路中... {renderProgress}%
        </div>
      )}
      {renderStats.roadCount > 0 && (
        <div className="road-network-stats">
          道路数量: {renderedRoads.length}/{renderStats.roadCount} | 
          缩放级别: {debouncedZoom} | 
          加载耗时: {renderStats.loadTime}ms | 
          渲染进度: {renderProgress}%
        </div>
      )}
    </>
  );
};

export default RoadNetwork;
