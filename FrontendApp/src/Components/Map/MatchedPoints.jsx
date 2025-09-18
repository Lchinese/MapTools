import React from 'react';
import { Marker, Popup } from 'react-leaflet';
import L from 'leaflet';

// 创建小的圆形图标
const createSmallCircleIcon = (color = '#1890ff', size = 6) => {
  return L.divIcon({
    className: 'custom-circle-marker',
    html: `<div style="
      width: ${size}px;
      height: ${size}px;
      background-color: ${color};
      border: 1px solid white;
      border-radius: 50%;
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [size, size],
    iconAnchor: [size/2, size/2],
  });
};

const MatchedPoints = ({ matchedPoints = [] }) => {
  if (!matchedPoints || matchedPoints.length === 0) {
    return null;
  }

  return (
    <>
      {matchedPoints.map((point, index) => (
        <Marker
          key={point.original_gps?.id || index}
          position={[point.matched_latitude, point.matched_longitude]}
          icon={createSmallCircleIcon('#1890ff', 6)}
        >
          <Popup>
            <div style={{ fontSize: '12px', minWidth: '200px' }}>
              <p><strong>车牌号:</strong> {point.original_gps?.plate_number}</p>
              <p><strong>匹配道路:</strong> {point.road_name}</p>
              <p><strong>道路类型:</strong> {point.road_type}</p>
              <p><strong>吸附距离:</strong> {point.distance_to_road?.toFixed(2)} 米</p>
              <p><strong>原始坐标:</strong> {point.original_gps?.latitude?.toFixed(6)}, {point.original_gps?.longitude?.toFixed(6)}</p>
              <p><strong>匹配坐标:</strong> {point.matched_latitude?.toFixed(6)}, {point.matched_longitude?.toFixed(6)}</p>
              <p><strong>时间:</strong> {point.original_gps?.datetime}</p>
              <p><strong>速度:</strong> {point.original_gps?.speed} km/h</p>
            </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
};

export default MatchedPoints;
