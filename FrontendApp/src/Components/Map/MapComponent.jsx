import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import { ReloadOutlined } from '@ant-design/icons';
import L from 'leaflet';
import { useMapStore } from '../../Store/mapStore';
import { matchingAPI } from '../../Services/api';
import { useTrajectoryData } from '../../Hooks/useTrajectory';
import MatchedPoints from './MatchedPoints';
import 'leaflet/dist/leaflet.css';

// 修复Leaflet默认图标问题
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

// 地图更新组件
const MapUpdater = ({ center, zoom, bounds }) => {
  const map = useMap();

  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds);
    } else if (center) {
      map.setView(center, zoom);
    }
  }, [map, center, zoom, bounds]);

  return null;
};

// 批量加载控制组件
const BatchLoadControl = ({ loading, onLoadBatch }) => {
  const [vehicleCount, setVehicleCount] = useState(50);
  const [matchToRoads, setMatchToRoads] = useState(false);
  
  const handleLoad = () => {
    onLoadBatch(vehicleCount, matchToRoads);
  };

  return (
    <div style={{
      position: 'absolute',
      top: 10,
      left: 10,
      background: 'white',
      padding: '10px',
      borderRadius: '4px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      zIndex: 1000,
      maxWidth: '300px',
    }}>
      <h4 style={{ margin: '0 0 10px 0' }}>批量加载车辆轨迹</h4>
      
      <div style={{ marginBottom: '10px' }}>
        <label style={{ display: 'block', marginBottom: '5px' }}>
          车辆数量:
          <input 
            type="number" 
            min="1" 
            max="1000" 
            value={vehicleCount}
            onChange={(e) => setVehicleCount(Math.min(1000, Math.max(1, parseInt(e.target.value) || 1)))}
            style={{ width: '100%', padding: '5px', marginTop: '5px' }}
          />
        </label>
        <label style={{ display: 'block', marginBottom: '10px' }}>
          <input 
            type="checkbox" 
            checked={matchToRoads}
            onChange={(e) => setMatchToRoads(e.target.checked)}
          />
          吸附到道路
        </label>
        <button 
          onClick={handleLoad}
          disabled={loading}
          style={{ width: '100%', padding: '5px' }}
        >
          {loading ? '加载中...' : '加载轨迹'}
        </button>
      </div>
      
      <div style={{ fontSize: '12px', color: '#666' }}>
        注意：大量车辆轨迹可能影响地图性能
      </div>
    </div>
  );
};

const MapComponent = ({ height = 400, showControls = true }) => {
  const mapRef = useRef();
  const [matchedPoints, setMatchedPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // 使用新的轨迹数据Hook
  const { 
    trajectoryData, 
    plateNumbers,
    fetchBatchTrajectoryData
  } = useTrajectoryData();
  
  const {
    center,
    zoom,
    bounds,
    originalTrajectory,
    matchedTrajectory,
    showOriginal,
    showMatched,
    showRoadNetwork,
    roadNetwork,
    resetMap
  } = useMapStore();

  // 加载匹配点数据
  useEffect(() => {
    const loadMatchedPoints = async () => {
      setLoading(true);
      try {
        const response = await matchingAPI.matchToRoads();
        setMatchedPoints(response.matched_points_data || []);
      } catch (error) {
        console.error('加载匹配点失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadMatchedPoints();
  }, []);

  // 处理批量加载
  const handleLoadBatch = async (limit, matchToRoads) => {
    await fetchBatchTrajectoryData(limit, matchToRoads);
  };

  // 计算地图边界
  const calculateBounds = () => {
    const allPoints = [];
    
    // 添加匹配点
    if (matchedPoints.length > 0) {
      allPoints.push(...matchedPoints.map(p => [p.matched_latitude, p.matched_longitude]));
    }
    
    // 添加车辆轨迹数据点
    Object.values(trajectoryData).forEach(vehiclePoints => {
      if (vehiclePoints && vehiclePoints.length > 0) {
        // 检查是原始GPS点还是已匹配的点
        if (vehiclePoints[0].hasOwnProperty('matched_latitude')) {
          // 已匹配的点
          allPoints.push(...vehiclePoints.map(p => [p.matched_latitude, p.matched_longitude]));
        } else {
          // 原始GPS点
          allPoints.push(...vehiclePoints.map(p => [p.latitude, p.longitude]));
        }
      }
    });
    
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
  };

  const mapBounds = calculateBounds();

  // 渲染车辆轨迹线
  const renderVehicleTrajectories = () => {
    return Object.entries(trajectoryData).map(([plateNumber, points], index) => {
      // 为不同车辆生成不同颜色
      const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];
      const color = colors[index % colors.length];
      
      if (!points || points.length === 0) {
        return null;
      }
      
      // 检查是原始GPS点还是已匹配的点
      let positions;
      if (points[0].hasOwnProperty('matched_latitude')) {
        // 已匹配的点
        positions = points.map(point => [point.matched_latitude, point.matched_longitude]);
      } else {
        // 原始GPS点
        positions = points.map(point => [point.latitude, point.longitude]);
      }
      
      return (
        <Polyline
          key={plateNumber}
          positions={positions}
          color={color}
          weight={3}
          opacity={0.8}
        >
          <Popup>
            <div>
              <p><strong>车牌号:</strong> {plateNumber}</p>
              <p><strong>轨迹点数:</strong> {points.length}</p>
            </div>
          </Popup>
        </Polyline>
      );
    });
  };

  // 渲染车辆轨迹点
  const renderVehicleTrajectoryPoints = () => {
    return Object.entries(trajectoryData).map(([plateNumber, points], index) => {
      // 为不同车辆生成不同颜色
      const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1'];
      const color = colors[index % colors.length];
      
      if (!points || points.length === 0) {
        return null;
      }
      
      return (
        <>
          {points.map((point, pointIndex) => {
            // 检查是原始GPS点还是已匹配的点
            let position, popupContent;
            if (point.hasOwnProperty('matched_latitude')) {
              // 已匹配的点
              position = [point.matched_latitude, point.matched_longitude];
              popupContent = (
                <div style={{ fontSize: '12px' }}>
                  <p><strong>车牌号:</strong> {point.original_gps?.plate_number || plateNumber}</p>
                  <p><strong>时间:</strong> {point.original_gps?.datetime}</p>
                  <p><strong>原始坐标:</strong> {point.original_gps?.latitude?.toFixed(6)}, {point.original_gps?.longitude?.toFixed(6)}</p>
                  <p><strong>匹配坐标:</strong> {point.matched_latitude?.toFixed(6)}, {point.matched_longitude?.toFixed(6)}</p>
                  <p><strong>道路名称:</strong> {point.road_name}</p>
                  <p><strong>距离:</strong> {point.distance_to_road?.toFixed(2)} 米</p>
                </div>
              );
            } else {
              // 原始GPS点
              position = [point.latitude, point.longitude];
              popupContent = (
                <div style={{ fontSize: '12px' }}>
                  <p><strong>车牌号:</strong> {point.plate_number}</p>
                  <p><strong>时间:</strong> {point.datetime}</p>
                  <p><strong>坐标:</strong> {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}</p>
                  {point.speed && <p><strong>速度:</strong> {point.speed.toFixed(2)} km/h</p>}
                  {point.heading && <p><strong>方向:</strong> {point.heading.toFixed(2)} 度</p>}
                </div>
              );
            }
            
            return (
              <Marker
                key={`${plateNumber}-${pointIndex}`}
                position={position}
              >
                <Popup>
                  {popupContent}
                </Popup>
              </Marker>
            );
          })}
        </>
      );
    });
  };

  return (
    <div style={{ height, width: '100%', position: 'relative' }}>
      <MapContainer
        ref={mapRef}
        center={center}
        zoom={zoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        <MapUpdater 
          center={mapBounds ? null : center} 
          zoom={zoom} 
          bounds={mapBounds} 
        />

        {/* 吸附点 - 只显示匹配到道路上的点 */}
        <MatchedPoints matchedPoints={matchedPoints} />

        {/* 车辆轨迹线 */}
        {renderVehicleTrajectories()}

        {/* 车辆轨迹点 */}
        {renderVehicleTrajectoryPoints()}

        {/* 原始轨迹 */}
        {showOriginal && originalTrajectory && (
          <TrajectoryLine 
            trajectory={originalTrajectory} 
            color="#ff4d4f" 
            weight={3}
          />
        )}

        {/* 匹配轨迹 */}
        {showMatched && matchedTrajectory && (
          <TrajectoryLine 
            trajectory={matchedTrajectory} 
            color="#52c41a" 
            weight={4}
          />
        )}

        {/* 轨迹点 */}
        {showOriginal && originalTrajectory && (
          <TrajectoryPoints 
            trajectory={originalTrajectory} 
            color="#ff4d4f"
          />
        )}

        {showMatched && matchedTrajectory && (
          <TrajectoryPoints 
            trajectory={matchedTrajectory} 
            color="#52c41a"
          />
        )}
      </MapContainer>

      {/* 批量加载控制 */}
      <BatchLoadControl 
        loading={loading}
        onLoadBatch={handleLoadBatch}
      />

      {/* 重置按钮 - 放在左侧缩放控件下方 */}
      <div style={{
        position: 'absolute',
        top: '30%',
        left: 10,
        transform: 'translateY(-50%)',
        zIndex: 1000,
      }}>
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}>
          {/* 重置按钮 - 方块样式 */}
          <div
            onClick={resetMap}
            style={{
              width: 30,
              height: 30,
              background: 'white',
              border: '2px solid #ccc',
              borderRadius: '4px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
              fontSize: '12px',
              color: '#666',
              marginBottom: 2,
            }}
            title="重置地图"
          >
            <div style={{
              width: 12,
              height: 12,
              border: '1px solid #666',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <div style={{
                width: 4,
                height: 4,
                background: '#666',
                borderRadius: '50%',
              }} />
            </div>
          </div>
        </div>
      </div>

      {/* 图例 - 放在右上角 */}
      {showControls && (
        <div style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: 'white',
          padding: '8px 12px',
          borderRadius: '4px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          zIndex: 1000,
        }}>
          <div style={{ fontSize: '12px' }}>
            <div style={{ color: '#1890ff' }}>● 道路吸附点 ({matchedPoints.length})</div>
            <div style={{ color: '#1890ff' }}>● 车辆轨迹点 ({Object.values(trajectoryData).flat().length})</div>
            <div style={{ color: '#1890ff' }}>● 车辆数量 ({Object.keys(trajectoryData).length})</div>
            {loading && <div style={{ color: '#999' }}>加载中...</div>}
          </div>
        </div>
      )}
    </div>
  );
};

// 轨迹线组件
const TrajectoryLine = ({ trajectory, color = '#1890ff', weight = 3 }) => {
  if (!trajectory || !trajectory.points || trajectory.points.length === 0) {
    return null;
  }

  const positions = trajectory.points
    .sort((a, b) => a.sequence_number - b.sequence_number)
    .map(point => [point.latitude, point.longitude]);

  return (
    <Polyline
      positions={positions}
      color={color}
      weight={weight}
      opacity={0.8}
    />
  );
};

// 轨迹点组件
const TrajectoryPoints = ({ trajectory, color = '#1890ff' }) => {
  if (!trajectory || !trajectory.points || trajectory.points.length === 0) {
    return null;
  }

  return (
    <>
      {trajectory.points.map((point, index) => (
        <Marker
          key={point.point_id || index}
          position={[point.latitude, point.longitude]}
        >
          <Popup>
            <div>
              <p><strong>序列:</strong> {point.sequence_number}</p>
              <p><strong>时间:</strong> {new Date(point.timestamp).toLocaleString()}</p>
              <p><strong>坐标:</strong> {point.latitude.toFixed(6)}, {point.longitude.toFixed(6)}</p>
              {point.speed && <p><strong>速度:</strong> {point.speed.toFixed(2)} km/h</p>}
              {point.accuracy && <p><strong>精度:</strong> {point.accuracy.toFixed(2)} m</p>}
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
};

export default MapComponent;