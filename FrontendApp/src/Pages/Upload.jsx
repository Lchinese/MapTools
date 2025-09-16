import React, { useState } from 'react';
import { 
  Card, 
  Upload, 
  Form, 
  Input, 
  Select, 
  Button, 
  message, 
  Progress,
  Typography,
  Row,
  Col,
  Space
} from 'antd';
import { 
  InboxOutlined, 
  UploadOutlined,
  FileTextOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useTrajectoryStore } from '../Store/trajectoryStore';

const { Title, Paragraph } = Typography;
const { Dragger } = Upload;
const { TextArea } = Input;
const { Option } = Select;

const UploadPage = () => {
  const navigate = useNavigate();
  const { uploadTrajectory, loading } = useTrajectoryStore();
  const [form] = Form.useForm();
  const [uploadProgress, setUploadProgress] = useState(0);
  const [fileList, setFileList] = useState([]);

  const dataSourceOptions = [
    { value: 'gpx', label: 'GPX文件' },
    { value: 'csv', label: 'CSV文件' },
    { value: 'kml', label: 'KML文件' },
    { value: 'auto', label: '自动识别' },
  ];

  const dataCategoryOptions = [
    { value: 'continuous_trajectory', label: '连续轨迹' },
    { value: 'origin_destination', label: '起终点记录' },
    { value: 'time_range', label: '时间段记录' },
  ];

  const handleUpload = async (file) => {
    const formData = form.getFieldsValue();
    
    try {
      setUploadProgress(0);
      
      // 模拟上传进度
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      const result = await uploadTrajectory(file, {
        name: formData.name || file.name,
        description: formData.description,
        dataSource: formData.dataSource,
        dataCategory: formData.dataCategory,
      });

      clearInterval(progressInterval);
      setUploadProgress(100);
      
      message.success('文件上传成功！');
      
      // 跳转到结果页面
      setTimeout(() => {
        navigate('/results');
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
    multiple: false,
    fileList,
    beforeUpload: handleUpload,
    onChange: (info) => {
      setFileList(info.fileList.slice(-1)); // 只保留最后一个文件
    },
    onRemove: () => {
      setFileList([]);
      setUploadProgress(0);
    },
    accept: '.gpx,.kml,.csv,.txt',
  };

  return (
    <div>
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>上传轨迹文件</Title>
        <Paragraph>
          支持上传GPX、KML、CSV等格式的轨迹文件。系统将自动解析文件内容并进行地图匹配。
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card title="文件上传">
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                dataSource: 'auto',
                dataCategory: 'continuous_trajectory',
              }}
            >
              <Form.Item
                name="name"
                label="轨迹名称"
                rules={[{ required: true, message: '请输入轨迹名称' }]}
              >
                <Input placeholder="请输入轨迹名称" />
              </Form.Item>

              <Form.Item
                name="description"
                label="描述"
              >
                <TextArea 
                  rows={3} 
                  placeholder="请输入轨迹描述（可选）" 
                />
              </Form.Item>

              <Row gutter={16}>
                <Col span={12}>
                  <Form.Item
                    name="dataSource"
                    label="数据源类型"
                    rules={[{ required: true, message: '请选择数据源类型' }]}
                  >
                    <Select placeholder="选择数据源类型">
                      {dataSourceOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="dataCategory"
                    label="数据类别"
                    rules={[{ required: true, message: '请选择数据类别' }]}
                  >
                    <Select placeholder="选择数据类别">
                      {dataCategoryOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Form.Item label="选择文件">
                <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">
                    点击或拖拽文件到此区域上传
                  </p>
                  <p className="ant-upload-hint">
                    支持单个文件上传，支持GPX、KML、CSV、TXT格式
                  </p>
                </Dragger>
              </Form.Item>

              {uploadProgress > 0 && (
                <Form.Item>
                  <Progress 
                    percent={uploadProgress} 
                    status={uploadProgress === 100 ? 'success' : 'active'}
                  />
                </Form.Item>
              )}
            </Form>
          </Card>
        </Col>

        <Col xs={24} lg={8}>
          <Card title="上传说明">
            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              <div>
                <Title level={5}>支持的文件格式：</Title>
                <ul>
                  <li>GPX - GPS交换格式</li>
                  <li>KML - Google Earth格式</li>
                  <li>CSV - 逗号分隔值</li>
                  <li>TXT - 文本格式</li>
                </ul>
              </div>

              <div>
                <Title level={5}>文件要求：</Title>
                <ul>
                  <li>文件大小不超过100MB</li>
                  <li>包含有效的经纬度坐标</li>
                  <li>时间戳格式正确</li>
                </ul>
              </div>

              <div>
                <Title level={5}>处理流程：</Title>
                <ol>
                  <li>上传文件并解析</li>
                  <li>验证数据格式</li>
                  <li>开始地图匹配</li>
                  <li>生成匹配结果</li>
                </ol>
              </div>
            </Space>
          </Card>

          <Card title="快速操作" style={{ marginTop: 16 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                icon={<FileTextOutlined />}
                block
                onClick={() => navigate('/files')}
              >
                查看已上传文件
              </Button>
              
              <Button 
                icon={<UploadOutlined />}
                block
                onClick={() => navigate('/results')}
              >
                查看匹配结果
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default UploadPage;