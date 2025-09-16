// 文件工具函数

/**
 * 格式化文件大小
 * @param {number} bytes 字节数
 * @returns {string} 格式化后的文件大小
 */
export const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

/**
 * 获取文件扩展名
 * @param {string} filename 文件名
 * @returns {string} 文件扩展名
 */
export const getFileExtension = (filename) => {
  return filename.split('.').pop().toLowerCase();
};

/**
 * 检查文件类型是否支持
 * @param {string} filename 文件名
 * @param {Array} allowedTypes 允许的文件类型
 * @returns {boolean} 是否支持
 */
export const isFileTypeSupported = (filename, allowedTypes = ['.gpx', '.kml', '.csv', '.txt']) => {
  const extension = getFileExtension(filename);
  return allowedTypes.some(type => type.replace('.', '') === extension);
};

/**
 * 验证文件大小
 * @param {File} file 文件对象
 * @param {number} maxSize 最大文件大小（字节）
 * @returns {boolean} 是否通过验证
 */
export const validateFileSize = (file, maxSize = 100 * 1024 * 1024) => {
  return file.size <= maxSize;
};

/**
 * 读取文件内容为文本
 * @param {File} file 文件对象
 * @returns {Promise<string>} 文件内容
 */
export const readFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(e);
    reader.readAsText(file);
  });
};

/**
 * 读取文件内容为ArrayBuffer
 * @param {File} file 文件对象
 * @returns {Promise<ArrayBuffer>} 文件内容
 */
export const readFileAsArrayBuffer = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = (e) => reject(e);
    reader.readAsArrayBuffer(file);
  });
};

/**
 * 下载文件
 * @param {Blob} blob 文件数据
 * @param {string} filename 文件名
 */
export const downloadFile = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

/**
 * 生成唯一文件名
 * @param {string} originalName 原始文件名
 * @returns {string} 唯一文件名
 */
export const generateUniqueFilename = (originalName) => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 8);
  const extension = getFileExtension(originalName);
  const nameWithoutExt = originalName.replace(/\.[^/.]+$/, '');
  
  return `${nameWithoutExt}_${timestamp}_${random}.${extension}`;
};

/**
 * 解析GPX文件
 * @param {string} gpxContent GPX文件内容
 * @returns {Object} 解析后的轨迹数据
 */
export const parseGPX = (gpxContent) => {
  try {
    const parser = new DOMParser();
    const xmlDoc = parser.parseFromString(gpxContent, 'text/xml');
    
    const trackPoints = xmlDoc.querySelectorAll('trkpt');
    const points = Array.from(trackPoints).map((point, index) => {
      const lat = parseFloat(point.getAttribute('lat'));
      const lon = parseFloat(point.getAttribute('lon'));
      const ele = point.querySelector('ele')?.textContent;
      const time = point.querySelector('time')?.textContent;
      
      return {
        sequence_number: index + 1,
        latitude: lat,
        longitude: lon,
        elevation: ele ? parseFloat(ele) : null,
        timestamp: time ? new Date(time).toISOString() : null,
      };
    });
    
    return {
      points,
      metadata: {
        name: xmlDoc.querySelector('name')?.textContent || 'Unknown Track',
        description: xmlDoc.querySelector('desc')?.textContent || '',
        total_points: points.length,
      }
    };
  } catch (error) {
    throw new Error(`GPX解析失败: ${error.message}`);
  }
};

/**
 * 解析CSV文件
 * @param {string} csvContent CSV文件内容
 * @returns {Object} 解析后的轨迹数据
 */
export const parseCSV = (csvContent) => {
  try {
    const lines = csvContent.split('\n').filter(line => line.trim());
    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    
    // 查找必要的列
    const latIndex = headers.findIndex(h => h.includes('lat') || h.includes('纬度'));
    const lonIndex = headers.findIndex(h => h.includes('lon') || h.includes('lng') || h.includes('经度'));
    const timeIndex = headers.findIndex(h => h.includes('time') || h.includes('时间'));
    const eleIndex = headers.findIndex(h => h.includes('ele') || h.includes('海拔'));
    
    if (latIndex === -1 || lonIndex === -1) {
      throw new Error('CSV文件必须包含经纬度列');
    }
    
    const points = lines.slice(1).map((line, index) => {
      const values = line.split(',').map(v => v.trim());
      
      return {
        sequence_number: index + 1,
        latitude: parseFloat(values[latIndex]),
        longitude: parseFloat(values[lonIndex]),
        elevation: eleIndex !== -1 ? parseFloat(values[eleIndex]) : null,
        timestamp: timeIndex !== -1 ? new Date(values[timeIndex]).toISOString() : null,
      };
    }).filter(point => !isNaN(point.latitude) && !isNaN(point.longitude));
    
    return {
      points,
      metadata: {
        name: 'CSV Track',
        description: 'Imported from CSV file',
        total_points: points.length,
      }
    };
  } catch (error) {
    throw new Error(`CSV解析失败: ${error.message}`);
  }
};

/**
 * 根据文件类型解析轨迹数据
 * @param {File} file 文件对象
 * @returns {Promise<Object>} 解析后的轨迹数据
 */
export const parseTrajectoryFile = async (file) => {
  const content = await readFileAsText(file);
  const extension = getFileExtension(file.name);
  
  switch (extension) {
    case 'gpx':
      return parseGPX(content);
    case 'csv':
      return parseCSV(content);
    case 'kml':
      // KML解析需要额外的库，这里返回基础结构
      return {
        points: [],
        metadata: {
          name: file.name,
          description: 'KML file (parsing not implemented)',
          total_points: 0,
        }
      };
    default:
      throw new Error(`不支持的文件格式: ${extension}`);
  }
};