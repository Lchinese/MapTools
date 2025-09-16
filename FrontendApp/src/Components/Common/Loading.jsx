import React from 'react';
import { Spin, Typography } from 'antd';
import { LoadingOutlined } from '@ant-design/icons';

const { Text } = Typography;

const Loading = ({ 
  size = 'large', 
  text = '加载中...', 
  spinning = true,
  children,
  style = {}
}) => {
  const antIcon = <LoadingOutlined style={{ fontSize: size === 'large' ? 24 : size === 'small' ? 14 : 20 }} spin />;

  if (children) {
    return (
      <Spin 
        spinning={spinning} 
        indicator={antIcon}
        style={style}
      >
        {children}
      </Spin>
    );
  }

  return (
    <div style={{ 
      textAlign: 'center', 
      padding: '50px 0',
      ...style 
    }}>
      <Spin 
        indicator={antIcon} 
        size={size}
      />
      {text && (
        <div style={{ marginTop: 16 }}>
          <Text type="secondary">{text}</Text>
        </div>
      )}
    </div>
  );
};

export default Loading;