import React from 'react';
import { Layout, Menu } from 'antd';
import { 
  HomeOutlined, 
  UploadOutlined, 
  BarChartOutlined,
  FileTextOutlined,
  SettingOutlined
} from '@ant-design/icons';
import { useNavigate, useLocation } from 'react-router-dom';

const { Sider } = Layout;

const Sidebar = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: '首页',
    },
    {
      key: '/upload',
      icon: <UploadOutlined />,
      label: '上传轨迹',
    },
    {
      key: '/results',
      icon: <BarChartOutlined />,
      label: '匹配结果',
    },
    {
      key: '/files',
      icon: <FileTextOutlined />,
      label: '文件管理',
    },
    {
      key: '/settings',
      icon: <SettingOutlined />,
      label: '系统设置',
    },
  ];

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Sider 
      width={200} 
      style={{
        background: '#fff',
        boxShadow: '2px 0 8px rgba(0, 0, 0, 0.1)',
      }}
    >
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        style={{ 
          height: '100%', 
          borderRight: 0,
          paddingTop: 16
        }}
        items={menuItems}
        onClick={handleMenuClick}
      />
    </Sider>
  );
};

export default Sidebar;
