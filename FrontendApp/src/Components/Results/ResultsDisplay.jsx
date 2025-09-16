import React from 'react';
import { Card, Row, Col, Statistic, Typography, Table, Tag, Progress } from 'antd';
import { 
  CheckCircleOutlined, 
  CloseCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined
} from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const ResultsDisplay = ({ task }) => {
  if (!task) {
    return <div>暂无数据</div>;
  }

  const statistics = [
    {
      title: '总点数',
      value: task.total_points || 0,
      icon: <BarChartOutlined style={{ color: '#1890ff' }} />,
    },
    {
      title: '匹配点数',
      value: task.matched_points_count || 0,
      icon: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
    },
    {
      title: '未匹配点数',
      value: task.unmatched_points_count || 0,
      icon: <CloseCircleOutlined style={{ color: '#ff4d4f' }} />,
    },
    {
      title: '匹配率',
      value: task.matched_points_count && task.total_points 
        ? ((task.matched_points_count / task.total_points) * 100).toFixed(1) + '%'
        : '0%',
      icon: <ClockCircleOutlined style={{ color: '#faad14' }} />,
    },
  ];

  const qualityMetrics = [
    {
      title: '平均距离误差',
      value: task.average_distance_error ? `${task.average_distance_error.toFixed(2)} m` : 'N/A',
      color: '#1890ff',
    },
    {
      title: '最大距离误差',
      value: task.max_distance_error ? `${task.max_distance_error.toFixed(2)} m` : 'N/A',
      color: '#ff4d4f',
    },
    {
      title: '平均置信度',
      value: task.average_confidence ? `${(task.average_confidence * 100).toFixed(1)}%` : 'N/A',
      color: '#52c41a',
    },
    {
      title: '处理时间',
      value: task.processing_time ? `${task.processing_time.toFixed(2)} s` : 'N/A',
      color: '#722ed1',
    },
  ];

  const matchedPointsColumns = [
    {
      title: '序号',
      dataIndex: 'sequence_number',
      key: 'sequence_number',
      width: 80,
    },
    {
      title: '原始坐标',
      key: 'original_coords',
      render: (_, record) => (
        <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
          {record.original_latitude.toFixed(6)}, {record.original_longitude.toFixed(6)}
        </span>
      ),
    },
    {
      title: '匹配坐标',
      key: 'matched_coords',
      render: (_, record) => (
        <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>
          {record.matched_latitude.toFixed(6)}, {record.matched_longitude.toFixed(6)}
        </span>
      ),
    },
    {
      title: '距离误差',
      dataIndex: 'distance',
      key: 'distance',
      render: (value) => (
        <span style={{ color: value > 50 ? '#ff4d4f' : value > 20 ? '#faad14' : '#52c41a' }}>
          {value ? `${value.toFixed(2)} m` : 'N/A'}
        </span>
      ),
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (value) => (
        <Progress 
          percent={value ? (value * 100) : 0} 
          size="small" 
          status={value > 0.8 ? 'success' : value > 0.5 ? 'normal' : 'exception'}
          style={{ width: 80 }}
        />
      ),
    },
    {
      title: '道路名称',
      dataIndex: 'road_name',
      key: 'road_name',
      render: (text) => text || '-',
    },
  ];

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card>
            <Title level={4}>任务信息</Title>
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <div><strong>任务ID:</strong> {task.task_id}</div>
              </Col>
              <Col span={6}>
                <div><strong>算法:</strong> <Tag color="blue">{task.algorithm}</Tag></div>
              </Col>
              <Col span={6}>
                <div><strong>状态:</strong> 
                  <Tag color={task.status === 'completed' ? 'success' : 'processing'}>
                    {task.status === 'completed' ? '已完成' : '处理中'}
                  </Tag>
                </div>
              </Col>
              <Col span={6}>
                <div><strong>创建时间:</strong> {new Date(task.created_at).toLocaleString()}</div>
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        {statistics.map((stat, index) => (
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

      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={24}>
          <Card title="质量指标">
            <Row gutter={[16, 16]}>
              {qualityMetrics.map((metric, index) => (
                <Col xs={24} sm={12} lg={6} key={index}>
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ 
                      fontSize: '24px', 
                      fontWeight: 'bold', 
                      color: metric.color,
                      marginBottom: '4px'
                    }}>
                      {metric.value}
                    </div>
                    <div style={{ color: '#666' }}>
                      {metric.title}
                    </div>
                  </div>
                </Col>
              ))}
            </Row>
          </Card>
        </Col>
      </Row>

      {task.matched_points && task.matched_points.length > 0 && (
        <Row gutter={[16, 16]}>
          <Col span={24}>
            <Card title="匹配点详情">
              <Table
                columns={matchedPointsColumns}
                dataSource={task.matched_points.slice(0, 100)} // 只显示前100个点
                rowKey="matched_point_id"
                pagination={{
                  pageSize: 20,
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `共 ${total} 个匹配点`,
                }}
                scroll={{ x: 800 }}
                size="small"
              />
              {task.matched_points.length > 100 && (
                <div style={{ marginTop: 16, textAlign: 'center', color: '#666' }}>
                  仅显示前100个匹配点，完整数据请下载查看
                </div>
              )}
            </Card>
          </Col>
        </Row>
      )}

      {task.error_message && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col span={24}>
            <Card title="错误信息" style={{ borderColor: '#ff4d4f' }}>
              <Paragraph style={{ color: '#ff4d4f' }}>
                {task.error_message}
              </Paragraph>
            </Card>
          </Col>
        </Row>
      )}
    </div>
  );
};

export default ResultsDisplay;