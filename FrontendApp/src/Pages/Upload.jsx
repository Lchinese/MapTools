import React, { useState } from 'react';
import { 
  Card, 
  Upload, 
  Form, 
  Input, 
  Button, 
  message, 
  Progress,
  Typography,
  Row,
  Col,
  Space,
  Alert
} from 'antd';
import { 
  InboxOutlined, 
  UploadOutlined,
  FileTextOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';

const { Title, Paragraph } = Typography;
const { Dragger } = Upload;
const { TextArea } = Input;

const UploadPage = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [uploadProgress, setUploadProgress] = useState(0);
  const [fileList, setFileList] = useState([]);

  const handleUpload = async (file) => {
    try {
      setUploadProgress(0);
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return prev;
          }
          return prev + 10;
        });
      }, 200);

      // 本版本不上传至后端，仅作占位
      await new Promise(r => setTimeout(r, 800));
      clearInterval(progressInterval);
      setUploadProgress(100);
      message.success('模拟上传完成（本版本未启用后端上传接口）');
      return false;
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
      setFileList(info.fileList.slice(-1));
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
        <Title level={2}>上传文件</Title>
        <Paragraph>
          当前版本未启用后端上传与匹配接口，上传操作仅为占位演示。
        </Paragraph>
        <Alert type="info" showIcon message="提示" description="启用后端接口后可恢复完整上传与匹配流程。" />
      </div>

      <Row gutter={[24, 24]}>
        <Col xs={24} lg={16}>
          <Card title="文件上传">
            <Form
              form={form}
              layout="vertical"
            >
              <Form.Item label="选择文件">
                <Dragger {...uploadProps} style={{ marginBottom: 16 }}>
                  <p className="ant-upload-drag-icon">
                    <InboxOutlined />
                  </p>
                  <p className="ant-upload-text">
                    点击或拖拽文件到此区域上传（本版本为占位演示）
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
          <Card title="快速操作" style={{ marginTop: 0 }}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                icon={<FileTextOutlined />}
                block
                onClick={() => navigate('/results')}
              >
                查看匹配结果（占位）
              </Button>
              
              <Button 
                icon={<UploadOutlined />}
                block
                onClick={() => navigate('/')}
              >
                返回首页
              </Button>
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default UploadPage;