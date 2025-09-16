import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from 'antd';
import Header from './Components/Layout/Header';
import Sidebar from './Components/Layout/Sidebar';
import Home from './Pages/Home';
import Upload from './Pages/Upload';
import Results from './Pages/Results';
import './App.css';

const { Content } = Layout;

function App() {
  return (
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
  );
}

export default App;
