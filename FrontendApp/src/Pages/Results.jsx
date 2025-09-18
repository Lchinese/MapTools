import React from 'react';
import { Card, Typography, Alert } from 'antd';
import MapComponent from '../Components/Map/MapComponent';

const { Title, Paragraph } = Typography;

const ResultsPage = () => {
  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>匹配结果</Title>
        <Paragraph>
          当前版本未启用后端匹配接口。此页面展示占位信息与地图预览。
        </Paragraph>
        <Alert type="info" showIcon message="提示" description="需要启用后端匹配接口后方可查看任务与结果。" />
      </div>

      <Card title="地图预览">
        <MapComponent height={400} />
      </Card>
    </div>
  );
};

export default ResultsPage;