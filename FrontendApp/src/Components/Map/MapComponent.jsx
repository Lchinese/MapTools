import React, { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import { ReloadOutlined } from '@ant-design/icons';
import L from 'leaflet';
import { useMapStore } from '../../Store/mapStore';
import { matchingAPI } from '../../Services/api';
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

const MapComponent = ({ height = 400, showControls = true }) => {
  const mapRef = useRef();
  const [matchedPoints, setMatchedPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  
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

  // 计算地图边界
  const calculateBounds = () => {
    const allPoints = [];
    
    // 添加匹配点
    if (matchedPoints.length > 0) {
      allPoints.push(...matchedPoints.map(p => [p.matched_latitude, p.matched_longitude]));
    }
    
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
            {loading && <div style={{ color: '#999' }}>加载中...</div>}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapComponent;