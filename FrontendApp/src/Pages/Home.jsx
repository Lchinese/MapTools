import React, { useEffect } from 'react';
import { Card, Row, Col, Statistic, Typography, Button, Space } from 'antd';
import { 
  UploadOutlined, 
  BarChartOutlined, 
  FileTextOutlined,
  ClockCircleOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTrajectoryStore } from '../Store/trajectoryStore';
import MapComponent from '../Components/Map/MapComponent';

const { Title, Paragraph } = Typography;

const Home = () => {
  const navigate = useNavigate();
  const { trajectories, matchingTasks, loading, fetchTrajectories, fetchMatchingTasks } = useTrajectoryStore();

  useEffect(() => {
    fetchTrajectories();
    fetchMatchingTasks();
  }, [fetchTrajectories, fetchMatchingTasks]);

  const stats = [
    {
      title: '轨迹总数',
      value: trajectories.length,
      icon: <FileTextOutlined style={{ color: '#1890ff' }} />,
    },
    {
      title: '匹配任务',
      value: matchingTasks.length,
      icon: <BarChartOutlined style={{ color: '#52c41a' }} />,
    },
    {
      title: '进行中任务',
      value: matchingTasks.filter(task => task.status === 'processing').length,
      icon: <ClockCircleOutlined style={{ color: '#faad14' }} />,
    },
    {
      title: '已完成任务',
      value: matchingTasks.filter(task => task.status === 'completed').length,
      icon: <BarChartOutlined style={{ color: '#52c41a' }} />,
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>MapTools 轨迹匹配系统</Title>
        <Paragraph>
          欢迎使用MapTools轨迹匹配系统！您可以上传GPS轨迹文件，系统将自动将其匹配到道路网络上。
          支持多种文件格式，包括GPX、KML、CSV等。
        </Paragraph>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                prefix={stat.icon}
                loading={loading}
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
                上传轨迹文件
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

          <Card title="最近任务" style={{ marginTop: 16 }}>
            {matchingTasks.slice(0, 5).map((task) => (
              <div key={task.task_id} style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>{task.algorithm}</span>
                  <span style={{ 
                    color: task.status === 'completed' ? '#52c41a' : 
                           task.status === 'processing' ? '#faad14' : '#d9d9d9'
                  }}>
                    {task.status}
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#666' }}>
                  {new Date(task.created_at).toLocaleString()}
                </div>
              </div>
            ))}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Home;