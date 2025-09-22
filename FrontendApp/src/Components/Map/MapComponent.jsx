import React, { useEffect, useRef, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import { ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import { Card, Checkbox, Button, Space, Typography, Tooltip } from 'antd';
import L from 'leaflet';
import { useMapStore } from '../../Store/mapStore';
import { useTrajectoryStore } from '../../Store/trajectoryStore';
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

// 地图更新组件（react-leaflet 4.x版本）
function MapUpdater({ center, zoom, bounds, mapRef }) {
  const map = useMap();
  
  useEffect(() => {
    if (bounds) {
      map.fitBounds(bounds);
    } else if (center && zoom) {
      map.setView(center, zoom);
    }
  }, [center, zoom, bounds, map]);

  return null;
}

// 轨迹线组件
const TrajectoryLine = ({ trajectory, color, weight }) => {
  if (!trajectory || trajectory.length < 2) return null;
  
  const positions = trajectory.map(point => [point.latitude, point.longitude]);
  
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
const TrajectoryPoints = ({ trajectory, color }) => {
  if (!trajectory || trajectory.length === 0) return null;

  return (
    <>
      {trajectory.map((point, index) => (
        <Marker
          key={`trajectory-point-${index}`}
          position={[point.latitude, point.longitude]}
          icon={L.divIcon({
            className: 'custom-trajectory-marker',
            html: `<div style="
              width: 8px;
              height: 8px;
              background-color: ${color};
              border: 2px solid white;
              border-radius: 50%;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [8, 8],
            iconAnchor: [4, 4],
          })}
        >
          <Popup>
            <div style={{ fontSize: '12px', minWidth: '200px' }}>
              <p><strong>时间:</strong> {point.datetime}</p>
              <p><strong>坐标:</strong> {point.latitude?.toFixed(6)}, {point.longitude?.toFixed(6)}</p>
              <p><strong>速度:</strong> {point.speed} km/h</p>
              <p><strong>方向:</strong> {point.heading}°</p>
      </div>
          </Popup>
        </Marker>
      ))}
    </>
  );
};

// 批量加载控制组件（暂时注释掉）
// const BatchLoadControl = ({ loading, onLoadBatch }) => {
//   const [vehicleCount, setVehicleCount] = useState(50);
//   const [matchToRoads, setMatchToRoads] = useState(false);

//   const handleLoad = () => {
//     onLoadBatch(vehicleCount, matchToRoads);
//   };

//   return (
//     <Card
//       className="map-card fade-in"
//       title={
//         <Space>
//           <CarOutlined style={{ color: '#1890ff' }} />
//           <span>批量加载车辆轨迹</span>
//         </Space>
//       }
//       size="small"
//       style={{
//         marginBottom: 16,
//         borderRadius: 8,
//         boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
//         border: '1px solid #f0f0f0'
//       }}
//       headStyle={{
//         background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
//         color: 'white',
//         borderRadius: '8px 8px 0 0',
//         border: 'none'
//       }}
//       bodyStyle={{ padding: '16px' }}
//     >
//       <Space direction="vertical" style={{ width: '100%' }} size="middle">
//         <div>
//           <Typography.Text strong style={{ marginBottom: 8, display: 'block' }}>
//             车辆数量
//           </Typography.Text>
//           <InputNumber
//             className="map-input"
//             min={1}
//             max={1000}
//             value={vehicleCount}
//             onChange={(value) => setVehicleCount(value || 1)}
//             style={{ width: '100%' }}
//             size="large"
//             addonAfter="辆"
//             placeholder="请输入车辆数量"
//           />
//         </div>

//         <Checkbox
//           checked={matchToRoads}
//           onChange={(e) => setMatchToRoads(e.target.checked)}
//           style={{ fontSize: '14px' }}
//         >
//           <EnvironmentOutlined style={{ marginRight: 4 }} />
//           吸附到道路
//         </Checkbox>

//         <Button
//           className="map-button"
//           type="primary"
//           size="large"
//           loading={loading}
//           onClick={handleLoad}
//           icon={<CarOutlined />}
//           style={{
//             width: '100%',
//             height: 40,
//             borderRadius: 6,
//             background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
//             border: 'none',
//             fontSize: '14px',
//             fontWeight: 500
//           }}
//         >
//           {loading ? '加载中...' : '加载轨迹'}
//         </Button>

//         <Divider style={{ margin: '8px 0' }} />

//         <Typography.Text type="secondary" style={{ fontSize: '12px', textAlign: 'center', display: 'block' }}>
//           ⚠️ 大量车辆轨迹可能影响地图性能
//         </Typography.Text>
//       </Space>
//     </Card>
//   );
// };

const MapComponent = ({ height = 400, showControls = true }) => {
  const mapRef = useRef();
  const [matchedPoints, setMatchedPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [, setCurrentPage] = useState(1);
  
  const { 
    trajectoryData
  } = useTrajectoryData();

  const {
    originalTrajectories,
    pagination,
    fetchOriginalTrajectories
  } = useTrajectoryStore();

  
  const {
    center,
    zoom,
    originalTrajectory,
    matchedTrajectory,
    showOriginal,
    showMatched,
    showRoadNetwork,
    resetMap,
    setShowOriginal,
    setShowMatched,
    setShowRoadNetwork
  } = useMapStore();

  // 使用useCallback稳定fetchOriginalTrajectories函数
  const stableFetchOriginalTrajectories = useCallback(fetchOriginalTrajectories, [fetchOriginalTrajectories]);

  // 加载初始轨迹数据
  useEffect(() => {
    const loadInitialData = async () => {
      try {
      setLoading(true);
        
        // 加载原始轨迹数据（从数据库分页查询）
        await stableFetchOriginalTrajectories(1, 20);
        
        // 加载匹配点数据
        const response = await matchingAPI.getMatchedPoints();
        if (response.data && response.data.matched_points) {
          setMatchedPoints(response.data.matched_points);
        }
      } catch (error) {
        console.error('加载数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    loadInitialData();
  }, [stableFetchOriginalTrajectories]); // 使用稳定的函数引用

  // const handleLoadBatch = async (limit, matchToRoads) => {
  //   await fetchBatchTrajectoryData(limit, matchToRoads);
  // };

  // 计算地图边界
  const calculateBounds = () => {
    const dataToUse = showOriginal ? originalTrajectories : trajectoryData;
    if (Object.keys(dataToUse).length === 0) return null;
    
    const allPoints = Object.values(dataToUse).flat();
    if (allPoints.length === 0) return null;

    const lats = allPoints.map(point => point.latitude);
    const lngs = allPoints.map(point => point.longitude);
      
      return [
        [Math.min(...lats), Math.min(...lngs)],
        [Math.max(...lats), Math.max(...lngs)]
      ];
  };

  const mapBounds = calculateBounds();

  // 渲染车辆轨迹线
  const renderVehicleTrajectories = () => {
    const dataToUse = showOriginal ? originalTrajectories : trajectoryData;
    return Object.entries(dataToUse).map(([plateNumber, points]) => {
      if (points.length < 2) return null;
      
      const positions = points.map(point => [point.latitude, point.longitude]);
      
      return (
        <Polyline
          key={`trajectory-${plateNumber}`}
          positions={positions}
          color="#1890ff"
          weight={3}
          opacity={0.8}
        />
      );
    });
  };

  // 渲染车辆轨迹点
  const renderVehicleTrajectoryPoints = () => {
    const dataToUse = showOriginal ? originalTrajectories : trajectoryData;
    return Object.entries(dataToUse).map(([plateNumber, points]) => {
      return points.map((point, index) => (
              <Marker
          key={`point-${plateNumber}-${index}`}
          position={[point.latitude, point.longitude]}
          icon={L.divIcon({
            className: 'custom-trajectory-point',
            html: `<div style="
              width: 8px;
              height: 8px;
              background-color: #1890ff;
              border: 2px solid white;
              border-radius: 50%;
              box-shadow: 0 2px 4px rgba(0,0,0,0.3);
            "></div>`,
            iconSize: [8, 8],
            iconAnchor: [4, 4],
          })}
              >
                <Popup>
            <div>
              <strong>车牌号:</strong> {plateNumber}<br/>
              <strong>时间:</strong> {point.datetime}<br/>
              <strong>速度:</strong> {point.speed} km/h<br/>
              <strong>方向:</strong> {point.heading}°
            </div>
                </Popup>
              </Marker>
      ));
    });
  };

  return (
    <div>
      {/* 地图容器 */}
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
            mapRef={mapRef}
        />

        {/* 吸附点 - 只显示匹配到道路上的点 */}
        <MatchedPoints matchedPoints={matchedPoints} />

          {/* 车辆轨迹线 - 原始轨迹 */}
          {showOriginal && renderVehicleTrajectories()}

          {/* 车辆轨迹点 - 原始轨迹点 */}
          {showOriginal && renderVehicleTrajectoryPoints()}

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
          <Tooltip title="重置地图" placement="right">
            <Button
              className="map-button pulse"
              type="primary"
              shape="circle"
              icon={<ReloadOutlined />}
            onClick={resetMap}
            style={{
                width: 40,
                height: 40,
                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                border: 'none',
                boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
            />
          </Tooltip>
        </div>

        {/* 控制面板 - 放在左下角 */}
      {showControls && (
          <Card
            className="map-card fade-in"
            title={
              <Space>
                <SettingOutlined style={{ color: '#1890ff' }} />
                <span>显示控制</span>
              </Space>
            }
            size="small"
            style={{
          position: 'absolute',
              bottom: 10,
              left: 10,
              width: 180,
              borderRadius: 8,
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          zIndex: 1000,
              border: '1px solid #f0f0f0'
            }}
            headStyle={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              padding: '8px 12px'
            }}
            bodyStyle={{ padding: '12px' }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <Checkbox
                checked={showOriginal}
                onChange={(e) => setShowOriginal(e.target.checked)}
                style={{ fontSize: '13px', width: '100%' }}
              >
                <span style={{ color: '#ff4d4f' }}>●</span> 原始轨迹
              </Checkbox>
              
              {/* 分页控制 */}
              {showOriginal && (
                <div style={{ marginTop: 8, fontSize: '12px' }}>
                  <div style={{ marginBottom: 4 }}>
                    第 {pagination.page || 1} 页 / 共 {pagination.total_pages || 0} 页
                  </div>
                  <Space size="small">
                    <Button 
                      size="small" 
                      disabled={!pagination.page || pagination.page <= 1}
                      onClick={() => {
                        const newPage = (pagination.page || 1) - 1;
                        setCurrentPage(newPage);
                        fetchOriginalTrajectories(newPage, pagination.page_size || 20);
                      }}
                    >
                      上一页
                    </Button>
                    <Button 
                      size="small" 
                      disabled={!pagination.total_pages || pagination.page >= pagination.total_pages}
                      onClick={() => {
                        const newPage = (pagination.page || 1) + 1;
                        setCurrentPage(newPage);
                        fetchOriginalTrajectories(newPage, pagination.pageSize || 20);
                      }}
                    >
                      下一页
                    </Button>
                  </Space>
                </div>
              )}
              
              <Checkbox
                checked={showMatched}
                onChange={(e) => setShowMatched(e.target.checked)}
                style={{ fontSize: '13px', width: '100%' }}
              >
                <span style={{ color: '#52c41a' }}>●</span> 匹配轨迹
              </Checkbox>
              <Checkbox
                checked={showRoadNetwork}
                onChange={(e) => setShowRoadNetwork(e.target.checked)}
                style={{ fontSize: '13px', width: '100%' }}
              >
                <span style={{ color: '#1890ff' }}>●</span> 道路网络
              </Checkbox>
            </Space>
          </Card>
        )}

        {/* 数据统计 - 放在右下角 */}
        {showControls && (
          <Card
            className="map-card fade-in"
            title="数据统计"
            size="small"
            style={{
              position: 'absolute',
              bottom: 10,
              right: 10,
              width: 200,
              borderRadius: 8,
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              zIndex: 1000,
              border: '1px solid #f0f0f0'
            }}
            headStyle={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: '8px 8px 0 0',
              border: 'none',
              padding: '8px 12px'
            }}
            bodyStyle={{ padding: '12px' }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="small">
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Space>
                  <span style={{ color: '#52c41a', fontSize: '16px' }}>●</span>
                  <Typography.Text style={{ fontSize: '13px' }}>车辆轨迹点</Typography.Text>
                </Space>
                <Typography.Text style={{ fontSize: '13px', fontWeight: 'bold', color: '#52c41a' }}>
                  {Object.values(originalTrajectories).flat().length}
                </Typography.Text>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Space>
                  <span style={{ color: '#faad14', fontSize: '16px' }}>●</span>
                  <Typography.Text style={{ fontSize: '13px' }}>车辆数量</Typography.Text>
                </Space>
                <Typography.Text style={{ fontSize: '13px', fontWeight: 'bold', color: '#faad14' }}>
                  {Object.keys(originalTrajectories).length}
                </Typography.Text>
              </div>
              
              {loading && (
                <div style={{ textAlign: 'center', padding: '8px 0' }}>
                  <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                    <ReloadOutlined spin style={{ marginRight: 4 }} />
                    加载中...
                  </Typography.Text>
                </div>
              )}
            </Space>
          </Card>
        )}
      </div>
            </div>
  );
};

export default MapComponent;