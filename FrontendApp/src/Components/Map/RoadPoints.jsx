import React, { useState, useEffect, useCallback } from 'react';
import { useMapEvents, CircleMarker, Popup } from 'react-leaflet';
import { matchingAPI } from '../../Services/api';

const RoadPoints = ({ showRoadNetwork }) => {
  const [roadPoints, setRoadPoints] = useState([]);
  const [clickedPoint, setClickedPoint] = useState(null);
  const [loading, setLoading] = useState(false);
  
  const map = useMapEvents({
    click: async (e) => {
      // 只有当地图上没有显示道路时才启用此功能
      if (showRoadNetwork) return;
      
      const { lat, lng } = e.latlng;
      // 查找最近的道路点
      findNearestRoadPoint(lat, lng);
    },
  });

  // 加载道路点数据
  const loadRoadPoints = useCallback(async () => {
    try {
      setLoading(true);
      // 获取道路网络数据，但我们只使用其中的点数据
      const response = await matchingAPI.getRoadNetwork();
      if (response && response.roads) {
        // 提取所有道路的所有点
        const allPoints = [];
        response.roads.forEach(road => {
          if (road.points && Array.isArray(road.points)) {
            road.points.forEach((point, index) => {
              if (typeof point === 'object' && point !== null) {
                if (typeof point.latitude === 'number' && typeof point.longitude === 'number') {
                  allPoints.push({
                    latitude: point.latitude,
                    longitude: point.longitude,
                    roadId: road.id,
                    roadName: road.name || road.id,
                    pointIndex: index
                  });
                } else if (Array.isArray(point) && point.length >= 2) {
                  allPoints.push({
                    latitude: point[0],
                    longitude: point[1],
                    roadId: road.id,
                    roadName: road.name || road.id,
                    pointIndex: index
                  });
                }
              } else if (Array.isArray(point) && point.length >= 2) {
                allPoints.push({
                  latitude: point[0],
                  longitude: point[1],
                  roadId: road.id,
                  roadName: road.name || road.id,
                  pointIndex: index
                });
              }
            });
          }
        });
        setRoadPoints(allPoints);
      }
    } catch (err) {
      console.error('加载道路点数据失败:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  // 查找最近的道路点
  const findNearestRoadPoint = useCallback((lat, lng) => {
    if (roadPoints.length === 0) return;

    let nearestPoint = null;
    let minDistance = Infinity;

    // 计算点击位置与所有道路点之间的距离
    roadPoints.forEach(point => {
      const distance = Math.sqrt(
        Math.pow(point.latitude - lat, 2) + Math.pow(point.longitude - lng, 2)
      );
      
      if (distance < minDistance) {
        minDistance = distance;
        nearestPoint = point;
      }
    });

    if (nearestPoint) {
      setClickedPoint({
        ...nearestPoint,
        latitude: parseFloat(nearestPoint.latitude.toFixed(6)),
        longitude: parseFloat(nearestPoint.longitude.toFixed(6))
      });
    }
  }, [roadPoints]);

  // 当道路网络显示状态改变时，如果变为隐藏，则加载道路点数据
  useEffect(() => {
    if (!showRoadNetwork && roadPoints.length === 0 && !loading) {
      loadRoadPoints();
    }
  }, [showRoadNetwork, roadPoints.length, loading, loadRoadPoints]);

  // 添加一个useEffect来处理地图点击事件的清理
  useEffect(() => {
    // 当showRoadNetwork变为true时，清除已点击的点
    if (showRoadNetwork) {
      setClickedPoint(null);
    }
  }, [showRoadNetwork]);

  return (
    <>
      {/* 只有当地图上没有显示道路时才渲染这些点 */}
      {!showRoadNetwork && clickedPoint && (
        <CircleMarker
          center={[clickedPoint.latitude, clickedPoint.longitude]}
          radius={6}
          color="#4a90e2"
          fillColor="#4a90e2"
          fillOpacity={0.8}
          weight={2}
          // 添加key以确保每次点击都创建新的标记
          key={`point-${clickedPoint.roadId}-${clickedPoint.pointIndex}-${Date.now()}`}
          eventHandlers={{
            click: (e) => {
              // 阻止事件冒泡，避免重复触发
              e.originalEvent.stopPropagation();
            }
          }}
        >
          <Popup>
            <div style={{ fontSize: '12px', minWidth: '200px' }}>
              <h3 style={{ margin: '0 0 8px 0', fontSize: '14px' }}>道路点信息</h3>
              <p><strong>点索引:</strong> {clickedPoint.pointIndex}</p>
              <p><strong>坐标:</strong> {clickedPoint.latitude}, {clickedPoint.longitude}</p>
              <p><strong>道路ID:</strong> {clickedPoint.roadId}</p>
              <p><strong>道路名称:</strong> {clickedPoint.roadName}</p>
            </div>
          </Popup>
        </CircleMarker>
      )}
    </>
  );
};

export default RoadPoints;