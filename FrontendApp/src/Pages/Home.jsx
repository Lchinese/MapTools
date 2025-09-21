import React, { useState } from 'react';
import { Card, Row, Col, Statistic, Typography, Button, Space, Alert, Divider, InputNumber, Checkbox } from 'antd';
import { 
  UploadOutlined, 
  BarChartOutlined, 
  FileTextOutlined,
  ClockCircleOutlined,
  EnvironmentOutlined,
  RocketOutlined,
  CarOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import MapComponent from '../Components/Map/MapComponent';
import { useTrajectoryData } from '../Hooks/useTrajectory';

const { Title, Paragraph } = Typography;

const Home = () => {
  const navigate = useNavigate();
  const { fetchBatchTrajectoryData } = useTrajectoryData();
  const [loading, setLoading] = useState(false);
  const [vehicleCount, setVehicleCount] = useState(0);
  const [matchToRoads, setMatchToRoads] = useState(false);

  const handleLoadBatch = async (limit, matchToRoads) => {
    setLoading(true);
    try {
      await fetchBatchTrajectoryData(limit, matchToRoads);
    } finally {
      setLoading(false);
    }
  };

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
    <div style={{ background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)', minHeight: '100vh', padding: '24px' }}>
      {/* 页面头部 */}
      <div style={{ 
        marginBottom: 32, 
        textAlign: 'center',
        background: 'white',
        padding: '32px',
        borderRadius: 16,
        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        border: '1px solid rgba(255,255,255,0.2)'
      }}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          <div>
            <Title level={1} style={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              margin: 0,
              fontSize: '2.5rem',
              fontWeight: 'bold'
            }}>
              <EnvironmentOutlined style={{ marginRight: 16, color: '#667eea' }} />
              MapTools GPS道路吸附系统
            </Title>
            <Paragraph style={{ fontSize: '16px', color: '#666', margin: '16px 0 0 0' }}>
              基于MongoDB数据库的车辆轨迹数据，支持分页查询和道路匹配展示
            </Paragraph>
          </div>
          
          <Alert 
            type="success" 
            showIcon 
            message="功能说明" 
            description="地图上显示的是从MongoDB数据库加载的车辆轨迹数据，支持原始轨迹和道路匹配轨迹的切换显示。" 
            style={{ borderRadius: 8 }}
          />
        </Space>
      </div>

      {/* 统计卡片 */}
      <Row gutter={[24, 24]} style={{ marginBottom: 32 }}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card 
              className="stat-card fade-in"
              style={{ 
                borderRadius: 12,
                boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                border: '1px solid #e8e8e8',
                background: 'white',
                cursor: 'pointer',
                transition: 'all 0.3s ease'
              }}
              hoverable
              bodyStyle={{ padding: '24px' }}
            >
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                valueStyle={{ 
                  color: '#1890ff',
                  fontSize: '24px',
                  fontWeight: 'bold'
                }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      {/* 主要内容区域 */}
      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card 
            title={
              <Space>
                <RocketOutlined style={{ color: '#1890ff' }} />
                <span>车辆轨迹数据展示</span>
              </Space>
            }
            style={{ 
              height: 600,
              borderRadius: 16,
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid #e8e8e8',
              background: 'white',
              overflow: 'hidden'
            }}
            headStyle={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: '16px 16px 0 0',
              border: 'none',
              padding: '16px 24px'
            }}
            bodyStyle={{ padding: 0, height: 'calc(100% - 57px)' }}
          >
            <MapComponent height={520} />
          </Card>
        </Col>
        
        <Col xs={24} lg={8}>
          <Card 
            title={
              <Space>
                <BarChartOutlined style={{ color: '#1890ff' }} />
                <span>快速操作</span>
              </Space>
            }
            style={{ 
              borderRadius: 16,
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
              border: '1px solid #e8e8e8',
              background: 'white'
            }}
            headStyle={{ 
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: '16px 16px 0 0',
              border: 'none',
              padding: '16px 24px'
            }}
            bodyStyle={{ padding: '24px' }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Button 
                type="primary" 
                icon={<UploadOutlined />}
                size="large"
                block
                onClick={() => navigate('/upload')}
                style={{ 
                  height: 48,
                  borderRadius: 8,
                  background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                  border: 'none',
                  fontSize: '16px',
                  fontWeight: 500
                }}
              >
                上传文件
              </Button>
              
              <Button 
                icon={<BarChartOutlined />}
                size="large"
                block
                onClick={() => navigate('/results')}
                style={{ 
                  height: 48,
                  borderRadius: 8,
                  fontSize: '16px',
                  fontWeight: 500
                }}
              >
                查看匹配结果
              </Button>
              
              <Button 
                icon={<FileTextOutlined />}
                size="large"
                block
                onClick={() => navigate('/files')}
                style={{ 
                  height: 48,
                  borderRadius: 8,
                  fontSize: '16px',
                  fontWeight: 500
                }}
              >
                管理文件
              </Button>
              
              <Divider style={{ margin: '16px 0' }} />
              
              {/* 批量加载车辆轨迹 */}
              <div style={{ 
                padding: '16px', 
                background: '#f8f9fa', 
                borderRadius: 8,
                border: '1px solid #e8e8e8'
              }}>
                <Space direction="vertical" style={{ width: '100%' }} size="middle">
                  <div style={{ textAlign: 'center', marginBottom: '8px' }}>
                    <Typography.Text strong style={{ fontSize: '14px', color: '#1890ff' }}>
                      <CarOutlined style={{ marginRight: 4 }} />
                      批量加载车辆轨迹
                    </Typography.Text>
                  </div>
                  
                  <div>
                    <Typography.Text style={{ fontSize: '12px', marginBottom: 4, display: 'block' }}>
                      车辆数量
                    </Typography.Text>
                    <InputNumber
                      min={1}
                      max={1000}
                      value={vehicleCount}
                      onChange={(value) => setVehicleCount(value || 1)}
                      style={{ width: '100%' }}
                      size="small"
                      addonAfter="辆"
                    />
                  </div>

                  <Checkbox
                    checked={matchToRoads}
                    onChange={(e) => setMatchToRoads(e.target.checked)}
                    style={{ fontSize: '12px' }}
                  >
                    <EnvironmentOutlined style={{ marginRight: 4 }} />
                    吸附到道路
                  </Checkbox>

                  <Button
                    type="primary"
                    size="small"
                    loading={loading}
                    onClick={() => handleLoadBatch(vehicleCount, matchToRoads)}
                    icon={<CarOutlined />}
                    style={{
                      width: '100%',
                      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                      border: 'none',
                      fontSize: '12px'
                    }}
                  >
                    {loading ? '加载中...' : '加载轨迹'}
                  </Button>
                </Space>
              </div>
              
              <div style={{ textAlign: 'center', padding: '8px 0' }}>
                <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
                  💡 提示：点击地图上的轨迹点可查看详细信息
                </Typography.Text>
              </div>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Home;