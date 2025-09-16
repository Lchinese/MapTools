// 地理工具函数

/**
 * 计算两点之间的距离（米）
 * @param {number} lat1 纬度1
 * @param {number} lon1 经度1
 * @param {number} lat2 纬度2
 * @param {number} lon2 经度2
 * @returns {number} 距离（米）
 */
export const calculateDistance = (lat1, lon1, lat2, lon2) => {
  const R = 6371000; // 地球半径（米）
  const dLat = toRadians(lat2 - lat1);
  const dLon = toRadians(lon2 - lon1);
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
};

/**
 * 角度转弧度
 * @param {number} degrees 角度
 * @returns {number} 弧度
 */
export const toRadians = (degrees) => {
  return degrees * (Math.PI / 180);
};

/**
 * 弧度转角度
 * @param {number} radians 弧度
 * @returns {number} 角度
 */
export const toDegrees = (radians) => {
  return radians * (180 / Math.PI);
};

/**
 * 计算轨迹的总距离
 * @param {Array} points 轨迹点数组
 * @returns {number} 总距离（米）
 */
export const calculateTotalDistance = (points) => {
  if (points.length < 2) return 0;
  
  let totalDistance = 0;
  for (let i = 1; i < points.length; i++) {
    const prev = points[i - 1];
    const curr = points[i];
    totalDistance += calculateDistance(
      prev.latitude, prev.longitude,
      curr.latitude, curr.longitude
    );
  }
  return totalDistance;
};

/**
 * 计算轨迹的边界框
 * @param {Array} points 轨迹点数组
 * @returns {Object} 边界框 {minLat, maxLat, minLon, maxLon}
 */
export const calculateBounds = (points) => {
  if (points.length === 0) {
    return { minLat: 0, maxLat: 0, minLon: 0, maxLon: 0 };
  }
  
  const lats = points.map(p => p.latitude);
  const lons = points.map(p => p.longitude);
  
  return {
    minLat: Math.min(...lats),
    maxLat: Math.max(...lats),
    minLon: Math.min(...lons),
    maxLon: Math.max(...lons),
  };
};

/**
 * 计算轨迹的中心点
 * @param {Array} points 轨迹点数组
 * @returns {Object} 中心点 {lat, lon}
 */
export const calculateCenter = (points) => {
  if (points.length === 0) {
    return { lat: 0, lon: 0 };
  }
  
  const bounds = calculateBounds(points);
  return {
    lat: (bounds.minLat + bounds.maxLat) / 2,
    lon: (bounds.minLon + bounds.maxLon) / 2,
  };
};

/**
 * 计算两点之间的方位角
 * @param {number} lat1 纬度1
 * @param {number} lon1 经度1
 * @param {number} lat2 纬度2
 * @param {number} lon2 经度2
 * @returns {number} 方位角（度）
 */
export const calculateBearing = (lat1, lon1, lat2, lon2) => {
  const dLon = toRadians(lon2 - lon1);
  const lat1Rad = toRadians(lat1);
  const lat2Rad = toRadians(lat2);
  
  const y = Math.sin(dLon) * Math.cos(lat2Rad);
  const x = Math.cos(lat1Rad) * Math.sin(lat2Rad) - 
            Math.sin(lat1Rad) * Math.cos(lat2Rad) * Math.cos(dLon);
  
  let bearing = toDegrees(Math.atan2(y, x));
  return (bearing + 360) % 360;
};

/**
 * 计算轨迹点的速度
 * @param {Array} points 轨迹点数组
 * @returns {Array} 带速度信息的点数组
 */
export const calculateSpeeds = (points) => {
  if (points.length < 2) return points;
  
  const pointsWithSpeed = [...points];
  
  for (let i = 1; i < pointsWithSpeed.length; i++) {
    const prev = pointsWithSpeed[i - 1];
    const curr = pointsWithSpeed[i];
    
    if (prev.timestamp && curr.timestamp) {
      const distance = calculateDistance(
        prev.latitude, prev.longitude,
        curr.latitude, curr.longitude
      );
      const timeDiff = (new Date(curr.timestamp) - new Date(prev.timestamp)) / 1000; // 秒
      
      if (timeDiff > 0) {
        curr.speed = (distance / timeDiff) * 3.6; // 转换为 km/h
      }
    }
  }
  
  return pointsWithSpeed;
};

/**
 * 过滤异常轨迹点
 * @param {Array} points 轨迹点数组
 * @param {Object} options 过滤选项
 * @returns {Array} 过滤后的点数组
 */
export const filterOutliers = (points, options = {}) => {
  const {
    maxSpeed = 200, // km/h
    minAccuracy = 1000, // 米
    maxDistance = 10000, // 米
  } = options;
  
  if (points.length < 2) return points;
  
  const filteredPoints = [points[0]]; // 保留第一个点
  
  for (let i = 1; i < points.length; i++) {
    const prev = filteredPoints[filteredPoints.length - 1];
    const curr = points[i];
    
    // 检查距离
    const distance = calculateDistance(
      prev.latitude, prev.longitude,
      curr.latitude, curr.longitude
    );
    
    if (distance > maxDistance) {
      continue; // 跳过距离过远的点
    }
    
    // 检查速度
    if (curr.speed && curr.speed > maxSpeed) {
      continue; // 跳过速度过快的点
    }
    
    // 检查精度
    if (curr.accuracy && curr.accuracy > minAccuracy) {
      continue; // 跳过精度过差的点
    }
    
    filteredPoints.push(curr);
  }
  
  return filteredPoints;
};

/**
 * 简化轨迹（Douglas-Peucker算法）
 * @param {Array} points 轨迹点数组
 * @param {number} tolerance 容差（米）
 * @returns {Array} 简化后的点数组
 */
export const simplifyTrajectory = (points, tolerance = 10) => {
  if (points.length <= 2) return points;
  
  const douglasPeucker = (pointList, epsilon) => {
    if (pointList.length <= 2) return pointList;
    
    let maxDistance = 0;
    let maxIndex = 0;
    const start = pointList[0];
    const end = pointList[pointList.length - 1];
    
    for (let i = 1; i < pointList.length - 1; i++) {
      const distance = perpendicularDistance(pointList[i], start, end);
      if (distance > maxDistance) {
        maxDistance = distance;
        maxIndex = i;
      }
    }
    
    if (maxDistance > epsilon) {
      const left = douglasPeucker(pointList.slice(0, maxIndex + 1), epsilon);
      const right = douglasPeucker(pointList.slice(maxIndex), epsilon);
      return left.slice(0, -1).concat(right);
    } else {
      return [start, end];
    }
  };
  
  return douglasPeucker(points, tolerance);
};

/**
 * 计算点到线段的垂直距离
 * @param {Object} point 点
 * @param {Object} lineStart 线段起点
 * @param {Object} lineEnd 线段终点
 * @returns {number} 距离（米）
 */
const perpendicularDistance = (point, lineStart, lineEnd) => {
  const A = point.latitude - lineStart.latitude;
  const B = point.longitude - lineStart.longitude;
  const C = lineEnd.latitude - lineStart.latitude;
  const D = lineEnd.longitude - lineStart.longitude;
  
  const dot = A * C + B * D;
  const lenSq = C * C + D * D;
  
  if (lenSq === 0) {
    return calculateDistance(point.latitude, point.longitude, lineStart.latitude, lineStart.longitude);
  }
  
  const param = dot / lenSq;
  
  let xx, yy;
  if (param < 0) {
    xx = lineStart.latitude;
    yy = lineStart.longitude;
  } else if (param > 1) {
    xx = lineEnd.latitude;
    yy = lineEnd.longitude;
  } else {
    xx = lineStart.latitude + param * C;
    yy = lineStart.longitude + param * D;
  }
  
  return calculateDistance(point.latitude, point.longitude, xx, yy);
};

/**
 * 格式化坐标显示
 * @param {number} lat 纬度
 * @param {number} lon 经度
 * @param {number} precision 精度
 * @returns {string} 格式化后的坐标
 */
export const formatCoordinate = (lat, lon, precision = 6) => {
  return `${lat.toFixed(precision)}, ${lon.toFixed(precision)}`;
};

/**
 * 检查坐标是否在中国境内（粗略检查）
 * @param {number} lat 纬度
 * @param {number} lon 经度
 * @returns {boolean} 是否在中国境内
 */
export const isInChina = (lat, lon) => {
  return lat >= 3.86 && lat <= 53.55 && lon >= 73.66 && lon <= 135.05;
};