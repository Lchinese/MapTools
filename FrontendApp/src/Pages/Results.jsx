import React, { useEffect, useState } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Tag, 
  Space, 
  Typography, 
  Row, 
  Col, 
  Statistic,
  Progress,
  message,
  Modal,
  Select
} from 'antd';
import { 
  PlayCircleOutlined, 
  DownloadOutlined, 
  EyeOutlined,
  ReloadOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTrajectoryStore } from '../Store/trajectoryStore';
import { useMapStore } from '../Store/mapStore';
import MapComponent from '../Components/Map/MapComponent';
import ResultsDisplay from '../Components/Results/ResultsDisplay';

const { Title, Paragraph } = Typography;
const { Option } = Select;

const ResultsPage = () => {
  const navigate = useNavigate();
  const { 
    trajectories, 
    matchingTasks, 
    loading, 
    fetchTrajectories, 
    fetchMatchingTasks,
    startMatching,
    fetchTaskResult
  } = useTrajectoryStore();
  
  const { setOriginalTrajectory, setMatchedTrajectory } = useMapStore();
  const [selectedTask, setSelectedTask] = useState(null);
  const [resultModalVisible, setResultModalVisible] = useState(false);
  const [algorithm, setAlgorithm] = useState('distance_matching');

  useEffect(() => {
    fetchTrajectories();
    fetchMatchingTasks();
  }, [fetchTrajectories, fetchMatchingTasks]);

  // 轮询任务状态
  useEffect(() => {
    const interval = setInterval(() => {
      const processingTasks = matchingTasks.filter(task => task.status === 'processing');
      if (processingTasks.length > 0) {
        fetchMatchingTasks();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [matchingTasks, fetchMatchingTasks]);

  const handleStartMatching = async (trajectoryId) => {
    try {
      await startMatching(trajectoryId, algorithm);
      message.success('匹配任务已开始');
      fetchMatchingTasks();
    } catch (error) {
      message.error(`启动匹配失败: ${error.message}`);
    }
  };

  const handleViewResult = async (task) => {
    try {
      const result = await fetchTaskResult(task.task_id);
      setSelectedTask(result);
      setResultModalVisible(true);
      
      // 设置地图数据
      if (result.original_trajectory) {
        setOriginalTrajectory(result.original_trajectory);
      }
      if (result.matched_trajectory) {
        setMatchedTrajectory(result.matched_trajectory);
      }
    } catch (error) {
      message.error(`获取结果失败: ${error.message}`);
    }
  };

  const handleDownload = (taskId, format = 'gpx') => {
    // 实现下载功能
    message.info(`下载${format.toUpperCase()}格式文件`);
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'processing';
      case 'failed': return 'error';
      case 'queued': return 'default';
      default: return 'default';
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'processing': return '处理中';
      case 'failed': return '失败';
      case 'queued': return '排队中';
      default: return '未知';
    }
  };

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 200,
      render: (text) => (
        <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
          {text.substring(0, 8)}...
        </span>
      ),
    },
    {
      title: '轨迹名称',
      dataIndex: 'trajectory_name',
      key: 'trajectory_name',
      render: (text, record) => {
        const trajectory = trajectories.find(t => t.trajectory_id === record.trajectory_id);
        return trajectory?.name || '未知轨迹';
      },
    },
    {
      title: '算法',
      dataIndex: 'algorithm',
      key: 'algorithm',
      render: (text) => (
        <Tag color="blue">{text}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status, record) => (
        <Space>
          <Tag color={getStatusColor(status)}>
            {getStatusText(status)}
          </Tag>
          {status === 'processing' && (
            <Progress 
              percent={record.progress || 0} 
              size="small" 
              style={{ width: 100 }}
            />
          )}
        </Space>
      ),
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (text) => new Date(text).toLocaleString(),
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          {record.status === 'completed' && (
            <>
              <Button 
                type="link" 
                icon={<EyeOutlined />}
                onClick={() => handleViewResult(record)}
              >
                查看
              </Button>
              <Button 
                type="link" 
                icon={<DownloadOutlined />}
                onClick={() => handleDownload(record.task_id)}
              >
                下载
              </Button>
            </>
          )}
          {record.status === 'failed' && (
            <Button 
              type="link" 
              icon={<ReloadOutlined />}
              onClick={() => handleStartMatching(record.trajectory_id)}
            >
              重试
            </Button>
          )}
        </Space>
      ),
    },
  ];

  const stats = [
    {
      title: '总任务数',
      value: matchingTasks.length,
      color: '#1890ff',
    },
    {
      title: '已完成',
      value: matchingTasks.filter(t => t.status === 'completed').length,
      color: '#52c41a',
    },
    {
      title: '处理中',
      value: matchingTasks.filter(t => t.status === 'processing').length,
      color: '#faad14',
    },
    {
      title: '失败',
      value: matchingTasks.filter(t => t.status === 'failed').length,
      color: '#ff4d4f',
    },
  ];

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>匹配结果</Title>
        <Paragraph>
          查看和管理轨迹匹配任务的结果。您可以查看匹配详情、下载结果文件。
        </Paragraph>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {stats.map((stat, index) => (
          <Col xs={24} sm={12} lg={6} key={index}>
            <Card>
              <Statistic
                title={stat.title}
                value={stat.value}
                valueStyle={{ color: stat.color }}
                loading={loading}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card 
            title="匹配任务列表"
            extra={
              <Space>
                <Select
                  value={algorithm}
                  onChange={setAlgorithm}
                  style={{ width: 150 }}
                >
                  <Option value="distance_matching">最短距离</Option>
                  <Option value="hmm_matching">隐马尔可夫</Option>
                </Select>
                <Button 
                  icon={<ReloadOutlined />}
                  onClick={() => fetchMatchingTasks()}
                >
                  刷新
                </Button>
              </Space>
            }
          >
            <Table
              columns={columns}
              dataSource={matchingTasks}
              rowKey="task_id"
              loading={loading}
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `共 ${total} 条记录`,
              }}
            />
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="地图预览">
            <MapComponent height={400} />
          </Card>

          <Card title="快速操作" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                type="primary"
                icon={<PlayCircleOutlined />}
                block
                onClick={() => navigate('/upload')}
              >
                上传新轨迹
              </Button>
              
              <Button 
                icon={<BarChartOutlined />}
                block
                onClick={() => navigate('/files')}
              >
                管理文件
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>

      <Modal
        title="匹配结果详情"
        open={resultModalVisible}
        onCancel={() => setResultModalVisible(false)}
        width={1200}
        footer={[
          <Button key="close" onClick={() => setResultModalVisible(false)}>
            关闭
          </Button>,
          <Button 
            key="download" 
            type="primary"
            icon={<DownloadOutlined />}
            onClick={() => selectedTask && handleDownload(selectedTask.task_id)}
          >
            下载结果
          </Button>,
        ]}
      >
        {selectedTask && <ResultsDisplay task={selectedTask} />}
      </Modal>
    </div>
  );
};

export default ResultsPage;