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
import RoadPoints from './RoadPoints';  // 新增导入
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
const TrajectoryPoints = ({ trajectory, color, type }) => {
  if (!trajectory || trajectory.length === 0) return null;

  return (
    <>
      {trajectory.map((point, index) => (
        <Marker
          key={`trajectory-point-${type}-${index}`}
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
              <p><strong>编号:</strong> {index + 1}</p>
              <p><strong>坐标:</strong> {point.latitude?.toFixed(6)}, {point.longitude?.toFixed(6)}</p>
              {point.datetime && <p><strong>时间:</strong> {point.datetime}</p>}
              {point.speed !== undefined && <p><strong>速度:</strong> {point.speed} km/h</p>}
              {point.heading !== undefined && <p><strong>方向:</strong> {point.heading}°</p>}
              {point.roadName && <p><strong>道路:</strong> {point.roadName}</p>}
              {point.originalLatitude && point.originalLongitude && (
                <>
                  <p><strong>原始坐标:</strong> {point.originalLatitude?.toFixed(6)}, {point.originalLongitude?.toFixed(6)}</p>
                </>
              )}
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
  const [osrmRoute, setOsrmRoute] = useState(null);
  const [osrmLoading, setOsrmLoading] = useState(false);
  
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
    showOSRMRoute,
    showRoadNetwork,
    resetMap,
    setShowOriginal,
    setShowCorrected,
    setShowOSRMRoute,
    setShowRoadNetwork,
    setCorrectedTrajectory
  } = useMapStore();

  // 暴露设置修正轨迹的方法到全局，供 Home 组件调用
  useEffect(() => {
    window.setCorrectedTrajectory = (trajectoryData) => {
      console.log('从外部设置修正轨迹数据:', trajectoryData.length, '个点');
      setCorrectedTrajectory(trajectoryData);
      setShowCorrected(true); // 自动开启修正轨迹显示
    };
    
    return () => {
      delete window.setCorrectedTrajectory;
    };
  }, [setCorrectedTrajectory, setShowCorrected, setShowOSRMRoute]);

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

  // OSRM路径规划
  useEffect(() => {
    console.log('OSRM useEffect触发:', {
      showCorrected,
      correctedTrajectory: correctedTrajectory ? correctedTrajectory.length : 'null',
      correctedTrajectoryType: typeof correctedTrajectory
    });
    
    // 防止重复调用
    if (osrmLoading) {
      console.log('OSRM正在处理中，跳过重复调用');
      return;
    }
    
    if (showOSRMRoute && correctedTrajectory && correctedTrajectory.length > 2) {
      const fetchOSRMRoute = async () => {
        setOsrmLoading(true);
        try {
          let allCoordinates = [];
          
          if (correctedTrajectory.length > 100) {
            // 超过100个点时进行分批处理
            console.log('OSRM路径点（分批处理）:', correctedTrajectory.length, '个点');
            allCoordinates = await processBatchOSRM(correctedTrajectory);
          } else {
            // 100个点以内直接处理
            console.log('OSRM路径点（单次处理）:', correctedTrajectory.length, '个点');
            const response = await matchingAPI.getOSRMRoute(correctedTrajectory);
            
            if (response && response.success && response.data && response.data.routes && response.data.routes.length > 0) {
              const route = response.data.routes[0];
              if (route.geometry && route.geometry.coordinates) {
                allCoordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
              }
            }
          }
          
          if (allCoordinates.length > 0) {
            setOsrmRoute(allCoordinates);
            console.log('OSRM路径坐标:', allCoordinates.length, '个点');
          } else {
            console.warn('OSRM路径规划失败');
          }
        } catch (error) {
          console.error('OSRM路径规划失败:', error);
          setOsrmRoute(null);
        } finally {
          setOsrmLoading(false);
        }
      };

      fetchOSRMRoute();
    } else {
      setOsrmRoute(null);
    }
  }, [showOSRMRoute, correctedTrajectory?.length]);

  // 分批处理OSRM请求（并发版本）
  const processBatchOSRM = async (points) => {
    const batchSize = 100; // 每批最多100个点
    const overlap = 2; // 批次间重叠点数，确保连续性
    
    console.log(`开始并发分批处理 ${points.length} 个点，每批 ${batchSize} 个点`);
    
    // 创建所有批次
    const batches = [];
    for (let i = 0; i < points.length; i += batchSize - overlap) {
      const endIndex = Math.min(i + batchSize, points.length);
      const batch = points.slice(i, endIndex);
      batches.push({ 
        index: i, 
        data: batch, 
        batchNumber: Math.floor(i / (batchSize - overlap)) + 1,
        startIndex: i,
        endIndex: endIndex - 1,
        length: batch.length
      });
    }
    
    console.log(`创建了 ${batches.length} 个批次，开始并发处理...`);
    
    // 并发处理所有批次
    const results = await Promise.all(
      batches.map(async (batch) => {
        console.log(`启动批次 ${batch.batchNumber}: 点 ${batch.startIndex} 到 ${batch.endIndex} (${batch.length}个点)`);
        
        try {
          const response = await matchingAPI.getOSRMRoute(batch.data);
          
          if (response && response.success && response.data && response.data.routes && response.data.routes.length > 0) {
            const route = response.data.routes[0];
            if (route.geometry && route.geometry.coordinates) {
              const batchCoordinates = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);
              console.log(`批次 ${batch.batchNumber} 完成，返回 ${batchCoordinates.length} 个坐标`);
              return { 
                success: true, 
                coordinates: batchCoordinates, 
                batchNumber: batch.batchNumber,
                index: batch.index
              };
            }
          }
          
          console.warn(`批次 ${batch.batchNumber} 失败: OSRM响应异常`);
          return { success: false, batchNumber: batch.batchNumber, index: batch.index };
        } catch (error) {
          console.error(`批次 ${batch.batchNumber} 错误:`, error);
          return { success: false, error, batchNumber: batch.batchNumber, index: batch.index };
        }
      })
    );
    
    // 合并结果，按顺序排列
    const allCoordinates = [];
    const successfulResults = results
      .filter(result => result.success)
      .sort((a, b) => a.index - b.index);
    
    successfulResults.forEach((result, idx) => {
      if (idx === 0) {
        // 第一批，添加所有坐标
        allCoordinates.push(...result.coordinates);
      } else {
        // 后续批次，去掉重叠部分
        allCoordinates.push(...result.coordinates.slice(overlap));
      }
    });
    
    console.log(`并发分批处理完成，成功处理了 ${successfulResults.length}/${batches.length} 个批次，总共 ${allCoordinates.length} 个坐标点`);
    return allCoordinates;
  };

  // 智能简化路径点（基于距离和方向变化）
  const getSmartWaypoints = (points) => {
    console.log('getSmartWaypoints输入:', points.length, '个点');
    
    if (points.length <= 2) {
      return points;
    }

    const waypoints = [];
    const maxPoints = 100; // 最大路径点数
    
    // 总是添加起点
    waypoints.push(points[0]);
    
    if (points.length <= maxPoints) {
      // 如果点数不多，直接返回所有点
      return points;
    }
    
    // 计算简化间隔
    const interval = Math.max(1, Math.floor(points.length / maxPoints));
    
    // 添加关键点（基于间隔）
    for (let i = interval; i < points.length - 1; i += interval) {
      waypoints.push(points[i]);
    }
    
    // 总是添加终点
    waypoints.push(points[points.length - 1]);
    
    console.log('getSmartWaypoints输出:', waypoints.length, '个路径点');
    return waypoints;
  };

  // 获取路径点（首尾 + 中间关键点）- 保留原函数以防需要
  const getWaypoints = (points) => {
    console.log('getWaypoints输入:', points.length, '个点');
    console.log('第一个点:', points[0]);
    
    if (points.length <= 2) {
      return points;
    }

    const waypoints = [];
    
    // 添加起点
    waypoints.push(points[0]);
    
    // 添加中间点（每N个点取一个）
    const interval = Math.max(1, Math.floor(points.length / 10)); // 最多10个中间点
    for (let i = interval; i < points.length - 1; i += interval) {
      waypoints.push(points[i]);
    }
    
    // 添加终点
    waypoints.push(points[points.length - 1]);
    
    console.log('getWaypoints输出:', waypoints.length, '个路径点');
    return waypoints;
  };

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
          color="#ff4d4f"
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

        {/* OSRM路径规划 */}
        {showOSRMRoute && osrmRoute && osrmRoute.length > 1 && (
          <Polyline
            positions={osrmRoute}
            color="#ff6b35"
            weight={3}
            opacity={0.8}
            pathOptions={{
              className: 'osrm-route-line',
              smoothFactor: 1.0,
              noClip: false,
              interactive: false
            }}
          />
        )}

        {/* 轨迹点 */}
        {showOriginal && originalTrajectory && (
          <TrajectoryPoints 
            trajectory={originalTrajectory} 
            color="#ff4d4f"
            type="original"
          />
        )}

        {showCorrected && correctedTrajectory && (
          <TrajectoryPoints 
            trajectory={correctedTrajectory} 
            color="#52c41a"
            type="corrected"
          />
        )}

        {/* 道路网络 - 放在最后确保在顶层显示 */}
        <RoadNetwork showRoadNetwork={showRoadNetwork} />
        {/* 道路点交互 - 即使道路网络未显示也能交互 */}
        <RoadPoints showRoadNetwork={showRoadNetwork} />

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
                checked={showOSRMRoute}
                onChange={(e) => setShowOSRMRoute(e.target.checked)}
                style={{ fontSize: '13px', width: '100%' }}
              >
                <span style={{ color: '#ff6b35' }}>●</span> OSRM规划
                {osrmLoading && <span style={{ color: '#ff6b35', marginLeft: 4 }}> (规划中...)</span>}
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