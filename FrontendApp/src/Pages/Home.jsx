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
        <Title level={2}>MapTools GPS道路吸附系统</Title>
        <Paragraph>
          基于sample-utf.txt出租车GPS数据，使用道路匹配算法将GPS点吸附到最近的道路上。
        </Paragraph>
        <Alert type="success" showIcon message="功能说明" description="地图上显示的是从sample-utf.txt解析的GPS点，经过道路匹配算法吸附到道路上的小圆点。" />
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
          <Card title="GPS数据道路吸附展示" style={{ height: 500 }}>
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