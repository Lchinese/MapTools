import React from 'react';
import { Card, Row, Col, Statistic, Typography, Button, Space, Alert } from 'antd';
import { 
  UploadOutlined, 
  BarChartOutlined, 
  FileTextOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import MapComponent from '../Components/Map/MapComponent';

const { Title, Paragraph } = Typography;

const Home = () => {
  const navigate = useNavigate();

  const stats = [
    {
      title: '轨迹总数',
      value: 0,
      icon: <FileTextOutlined style={{ color: '#1890ff' }} />,
    },
    {
      title: '匹配任务',
      value: 0,
      icon: <BarChartOutlined style={{ color: '#52c41a' }} />,
    },
    {
      title: '进行中任务',
      value: 0,
      icon: <ClockCircleOutlined style={{ color: '#faad14' }} />,
    },
    {
      title: '已完成任务',
      value: 0,
      icon: <BarChartOutlined style={{ color: '#52c41a' }} />,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>MapTools 轨迹匹配系统</Title>
        <Paragraph>
          当前版本仅保留认证与健康检查接口。轨迹/匹配等后端接口已移除，页面展示为占位信息。
        </Paragraph>
        <Alert type="info" showIcon message="提示" description="如需恢复完整功能，请启用后端轨迹与匹配接口后再刷新页面。" />
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="地图预览" style={{ height: 500 }}>
            <MapComponent height={400} />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card title="快速操作">
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                type="primary" 
                icon={<UploadOutlined />}
                size="large"
                block
                onClick={() => navigate('/upload')}
              >
                上传文件
              </Button>
              
              <Button 
                icon={<BarChartOutlined />}
                size="large"
                block
                onClick={() => navigate('/results')}
              >
                查看匹配结果
              </Button>
              
              <Button 
                icon={<FileTextOutlined />}
                size="large"
                block
                onClick={() => navigate('/files')}
              >
                管理文件
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Home;