import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Header from './Components/Layout/Header';
import Sidebar from './Components/Layout/Sidebar';
import ProtectedRoute from './Components/Common/ProtectedRoute';
import Home from './Pages/Home';
import Upload from './Pages/Upload';
import Results from './Pages/Results';
import Login from './Pages/Login';
import Register from './Pages/Register';
import './App.css';

const { Content } = Layout;

function App() {
  return (
    <Routes>
      {/* 公开路由 - 直接渲染，不使用 ProtectedRoute */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* 受保护的路由 */}
      <Route path="/*" element={
        <ProtectedRoute requireAuth={true}>
          <Layout style={{ minHeight: '100vh' }}>
            <Header />
            <Layout>
              <Sidebar />
              <Layout style={{ padding: '0 24px 24px' }}>
                <Content
                  style={{
                    padding: 24,
                    margin: 0,
                    minHeight: 280,
                    background: '#fff',
                  }}
                >
                  <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/upload" element={<Upload />} />
                    <Route path="/results" element={<Results />} />
                  </Routes>
                </Content>
              </Layout>
            </Layout>
          </Layout>
        </ProtectedRoute>
      } />
    </Routes>
  );
}

export default App;
