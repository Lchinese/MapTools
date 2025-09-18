import React from 'react';
import { Layout, Typography, Space, Button, Dropdown, Avatar } from 'antd';
import { UserOutlined, SettingOutlined, LogoutOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../Hooks/useAuth';

const { Header: AntHeader } = Layout;
const { Title } = Typography;

const Header = () => {
  const navigate = useNavigate();
  // eslint-disable-next-line no-unused-vars
  const { user, logout, isAuthenticated } = useAuth();
  
  console.log('Header 渲染 - isAuthenticated:', isAuthenticated, 'user:', user);

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人资料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '设置',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
    },
  ];

  const handleMenuClick = ({ key }) => {
    switch (key) {
      case 'profile':
        // 处理个人资料
        break;
      case 'settings':
        // 处理设置
        break;
      case 'logout':
        logout();
        navigate('/login');
        break;
      default:
        break;
    }
  };

  return (
    <AntHeader style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'space-between',
      padding: '0 24px',
      background: '#001529'
    }}>
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Title 
          level={3} 
          style={{ 
            color: '#fff', 
            margin: 0, 
            marginRight: 24,
            cursor: 'pointer'
          }}
          onClick={() => navigate('/')}
        >
          MapTools
        </Title>
      </div>
      
      <Space>
        {isAuthenticated ? (
          <>
            <Button 
              type="primary" 
              onClick={() => navigate('/upload')}
            >
              上传文件
            </Button>
            
            <Dropdown
              menu={{
                items: userMenuItems,
                onClick: handleMenuClick,
              }}
              placement="bottomRight"
            >
              <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
                <Avatar 
                  icon={<UserOutlined />} 
                  style={{ marginRight: 8 }}
                />
                <span style={{ color: '#fff' }}>
                  {user?.username || '用户'}
                </span>
              </div>
            </Dropdown>
          </>
        ) : (
          <Button 
            type="primary" 
            onClick={() => {
              console.log('点击登录按钮，准备跳转到登录页');
              navigate('/login');
            }}
          >
            登录
          </Button>
        )}
      </Space>
    </AntHeader>
  );
};

export default Header;
