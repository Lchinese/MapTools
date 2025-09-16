import React, { useState } from 'react';
import { Upload, Button, message, Progress, Typography } from 'antd';
import { InboxOutlined, UploadOutlined } from '@ant-design/icons';

const { Dragger } = Upload;
const { Text } = Typography;

const FileUpload = ({ 
  onUpload, 
  onProgress, 
  loading = false, 
  accept = '.gpx,.kml,.csv,.txt',
  maxSize = 100 * 1024 * 1024, // 100MB
  multiple = false 
}) => {
  const [fileList, setFileList] = useState([]);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleUpload = async (file) => {
    // 文件大小检查
    if (file.size > maxSize) {
      message.error(`文件大小不能超过 ${(maxSize / 1024 / 1024).toFixed(0)}MB`);
      return false;
    }

    // 文件类型检查
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const allowedExtensions = accept.split(',').map(ext => ext.replace('.', ''));
    if (!allowedExtensions.includes(fileExtension)) {
      message.error(`不支持的文件格式，请上传 ${accept} 格式的文件`);
      return false;
    }

    try {
      setUploadProgress(0);
      
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + Math.random() * 20;
        });
      }, 200);

      // 调用上传回调
      if (onUpload) {
        await onUpload(file);
      }

      clearInterval(progressInterval);
      setUploadProgress(100);
      
      message.success('文件上传成功！');
      
      // 延迟重置进度条
      setTimeout(() => {
        setUploadProgress(0);
      }, 1000);
      
      return false; // 阻止默认上传行为
    } catch (error) {
      message.error(`上传失败: ${error.message}`);
      setUploadProgress(0);
      return false;
    }
  };

  const uploadProps = {
    name: 'file',
    multiple,
    fileList,
    beforeUpload: handleUpload,
    onChange: (info) => {
      setFileList(info.fileList.slice(-1)); // 只保留最后一个文件
    },
    onRemove: () => {
      setFileList([]);
      setUploadProgress(0);
    },
    accept,
    showUploadList: {
      showPreviewIcon: false,
      showRemoveIcon: true,
      showDownloadIcon: false,
    },
  };

  return (
    <div>
      <Dragger {...uploadProps} disabled={loading}>
        <p className="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p className="ant-upload-text">
          {loading ? '正在上传...' : '点击或拖拽文件到此区域上传'}
        </p>
        <p className="ant-upload-hint">
          支持单个文件上传，支持 {accept} 格式，文件大小不超过 {(maxSize / 1024 / 1024).toFixed(0)}MB
        </p>
      </Dragger>

      {uploadProgress > 0 && (
        <div style={{ marginTop: 16 }}>
          <Progress 
            percent={Math.round(uploadProgress)} 
            status={uploadProgress === 100 ? 'success' : 'active'}
            strokeColor={{
              '0%': '#108ee9',
              '100%': '#87d068',
            }}
          />
          <Text type="secondary" style={{ fontSize: '12px' }}>
            {uploadProgress === 100 ? '上传完成' : '正在上传...'}
          </Text>
        </div>
      )}

      {fileList.length > 0 && (
        <div style={{ marginTop: 16 }}>
          <Text strong>已选择文件:</Text>
          <div style={{ marginTop: 8 }}>
            {fileList.map(file => (
              <div key={file.uid} style={{ 
                padding: '8px 12px', 
                background: '#f5f5f5', 
                borderRadius: '4px',
                marginBottom: '4px'
              }}>
                <Text>{file.name}</Text>
                <Text type="secondary" style={{ marginLeft: 8 }}>
                  ({(file.size / 1024 / 1024).toFixed(2)} MB)
                </Text>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default FileUpload;