import React, { useEffect, useRef, useState, useCallback } from 'react';
import { MapContainer, TileLayer, Polyline, Marker, Popup, useMap } from 'react-leaflet';
import { ReloadOutlined, SettingOutlined } from '@ant-design/icons';
import { Card, Checkbox, Button, Space, Typography, Tooltip } from 'antd';
import L from 'leaflet';
import { useMapStore } from '../../Store/mapStore';
import { useTrajectoryStore } from '../../Store/trajectoryStore';
import { matchingAPI, trajectoryAPI } from '../../Services/api';
// import { useTrajectoryData } from '../../Hooks/useTrajectory'; // 不再需要，trajectoryData 作为 prop 传入
import MatchedPoints from './MatchedPoints';
import RoadNetwork from './RoadNetwork';
import 'leaflet/dist/leaflet.css';
import './MapComponent.css';

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

const MapComponent = ({ height = 400, showControls = true, trajectoryData = {} }) => {
  const mapRef = useRef();
  const [matchedPoints, setMatchedPoints] = useState([]);
  const [loading, setLoading] = useState(false);
  const [, setCurrentPage] = useState(1);
  
  // trajectoryData 现在作为 prop 传入

  const {
    originalTrajectories,
    pagination,
    fetchOriginalTrajectories,
    setOriginalTrajectories
  } = useTrajectoryStore();

  
  const {
    center,
    zoom,
    originalTrajectory,
    correctedTrajectory,
    showOriginal,
    showCorrected,
    showRoadNetwork,
    resetMap,
    setShowOriginal,
    setShowCorrected,
    setShowRoadNetwork,
    setCorrectedTrajectory
  } = useMapStore();

  // 使用useCallback稳定fetchOriginalTrajectories函数
  // const stableFetchOriginalTrajectories = useCallback(fetchOriginalTrajectories, [fetchOriginalTrajectories]);

  // 监听单车辆轨迹数据变化，替换初始化的内容
  useEffect(() => {
    console.log('trajectoryData变化:', Object.keys(trajectoryData).length, trajectoryData);
    if (Object.keys(trajectoryData).length > 0) {
      console.log('检测到新的单车辆轨迹数据:', trajectoryData);
      // 当有新的单车辆轨迹数据时，同时更新原始轨迹数据
      setOriginalTrajectories(trajectoryData);
      console.log('已更新originalTrajectories为:', trajectoryData);
    }
  }, [trajectoryData, setOriginalTrajectories]); // eslint-disable-line react-hooks/exhaustive-deps

  // 加载初始轨迹数据（第一天第一辆车）
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        console.log('开始加载初始轨迹数据...');
        setLoading(true);
        
        // 加载第一天第一辆车的轨迹数据
        const response = await trajectoryAPI.getFirstDayFirstVehicleTrajectory();
        console.log('初始轨迹数据响应:', response);
        let currentPlateNumber = null;
        
        if (response.success && response.data && response.data.length > 0) {
          // 将单车辆数据转换为与批量数据相同的格式
          const firstVehicleData = { [response.plate_number]: response.data };
          currentPlateNumber = response.plate_number;
          console.log('设置初始轨迹数据:', firstVehicleData);
          setOriginalTrajectories(firstVehicleData);
          console.log('✅ 初始轨迹数据加载成功');
        } else {
          console.log('❌ 初始轨迹数据获取失败，无备选方案');
        }
        
        // 加载修正轨迹数据（与原始轨迹保持一致的车辆）
        if (currentPlateNumber) {
          try {
            const correctedResponse = await trajectoryAPI.getCorrectedTrajectoryData(1, 1, currentPlateNumber);
            if (correctedResponse.success && correctedResponse.data && correctedResponse.data[currentPlateNumber]) {
              const trajectoryPoints = correctedResponse.data[currentPlateNumber];
              console.log('修正轨迹数据:', trajectoryPoints.length, '个点，车牌:', currentPlateNumber);
              setCorrectedTrajectory(trajectoryPoints);
              console.log('✅ 修正轨迹数据加载成功');
            } else {
              console.log('❌ 未找到对应车牌号的修正轨迹:', currentPlateNumber);
            }
          } catch (error) {
            console.error('❌ 修正轨迹数据加载失败:', error);
          }
        }
      } catch (error) {
        console.error('❌ 加载初始数据失败:', error);
      } finally {
        setLoading(false);
      }
    };

    // 只有在没有任何轨迹数据时才加载初始数据
    if (Object.keys(trajectoryData).length === 0 && Object.keys(originalTrajectories).length === 0) {
      loadInitialData();
    }
  }, []); // 只在组件挂载时执行一次

  // const handleLoadBatch = async (limit, matchToRoads) => {
  //   await fetchBatchTrajectoryData(limit, matchToRoads);
  // };

  // 计算地图边界
  const calculateBounds = () => {
    // 优先使用单车辆轨迹数据，如果没有则使用原始轨迹数据
    const dataToUse = Object.keys(trajectoryData).length > 0 ? trajectoryData : originalTrajectories;
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
    // 优先使用单车辆轨迹数据，如果没有则使用原始轨迹数据
    const hasTrajectoryData = Object.keys(trajectoryData).length > 0;
    const dataToUse = hasTrajectoryData ? trajectoryData : originalTrajectories;
    
    console.log('=== 渲染轨迹线调试信息 ===');
    console.log('trajectoryData长度:', Object.keys(trajectoryData).length);
    console.log('trajectoryData内容:', trajectoryData);
    console.log('originalTrajectories长度:', Object.keys(originalTrajectories).length);
    console.log('originalTrajectories内容:', originalTrajectories);
    console.log('hasTrajectoryData:', hasTrajectoryData);
    console.log('dataToUse长度:', Object.keys(dataToUse).length);
    console.log('dataToUse内容:', dataToUse);
    console.log('showOriginal状态:', showOriginal);
    console.log('========================');
    
    if (Object.keys(dataToUse).length === 0) {
      console.log('没有数据可渲染');
      return null;
    }
    
    return Object.entries(dataToUse).map(([plateNumber, points]) => {
      console.log(`渲染车牌 ${plateNumber} 的轨迹，点数:`, points.length);
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
    // 优先使用单车辆轨迹数据，如果没有则使用原始轨迹数据
    const dataToUse = Object.keys(trajectoryData).length > 0 ? trajectoryData : originalTrajectories;
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

        {/* 道路网络 */}
        <RoadNetwork showRoadNetwork={showRoadNetwork} />

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

        {/* 修正轨迹 */}
        {showCorrected && correctedTrajectory && (
          <TrajectoryLine 
            trajectory={correctedTrajectory} 
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

        {showCorrected && correctedTrajectory && (
          <TrajectoryPoints 
            trajectory={correctedTrajectory} 
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
              
              {/* 分页控制 - 只在多车辆模式下显示 */}
              {showOriginal && Object.keys(originalTrajectories).length > 1 && (
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
              
              {/* 单车辆模式提示 */}
              {showOriginal && Object.keys(originalTrajectories).length === 1 && (
                <div style={{ marginTop: 8, fontSize: '12px', color: '#1890ff', textAlign: 'center' }}>
                  单车辆轨迹模式
                </div>
              )}
              
              <Checkbox
                checked={showCorrected}
                onChange={(e) => setShowCorrected(e.target.checked)}
                style={{ fontSize: '13px', width: '100%' }}
              >
                <span style={{ color: '#52c41a' }}>●</span> 修正轨迹
              </Checkbox>
              <Checkbox
                checked={showRoadNetwork}
                onChange={(e) => setShowRoadNetwork(e.target.checked)}
                style={{ fontSize: '13px', width: '100%' }}
              >
                <span style={{ color: '#722ed1' }}>●</span> 道路网络
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
                  {Object.values(Object.keys(trajectoryData).length > 0 ? trajectoryData : originalTrajectories).flat().length}
                </Typography.Text>
              </div>
              
              {/* 只在多车辆模式下显示车辆数量 */}
              {Object.keys(originalTrajectories).length > 1 && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Space>
                    <span style={{ color: '#faad14', fontSize: '16px' }}>●</span>
                    <Typography.Text style={{ fontSize: '13px' }}>车辆数量</Typography.Text>
                  </Space>
                  <Typography.Text style={{ fontSize: '13px', fontWeight: 'bold', color: '#faad14' }}>
                    {Object.keys(originalTrajectories).length}
                  </Typography.Text>
                </div>
              )}
              
              {/* 单车辆模式显示车牌号 */}
              {Object.keys(originalTrajectories).length === 1 && (
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Space>
                    <span style={{ color: '#1890ff', fontSize: '16px' }}>●</span>
                    <Typography.Text style={{ fontSize: '13px' }}>当前车辆</Typography.Text>
                  </Space>
                  <Typography.Text style={{ fontSize: '13px', fontWeight: 'bold', color: '#1890ff' }}>
                    {Object.keys(originalTrajectories)[0]}
                  </Typography.Text>
                </div>
              )}
              
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