import React, { useState, useEffect } from 'react'
import { Layout, Menu, Avatar, Dropdown, Badge, Space, Typography } from 'antd'
import {
  DashboardOutlined,
  ToolOutlined,
  ApartmentOutlined,
  FileSearchOutlined,
  LineChartOutlined,
  BellOutlined,
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons'
import { useNavigate, useLocation } from 'react-router-dom'
import api from '../api'

const { Header, Sider, Content, Footer } = Layout
const { Text } = Typography

const menuItems = [
  { key: '/dashboard', icon: <DashboardOutlined />, label: '仪表盘' },
  { key: '/devices', icon: <ToolOutlined />, label: '设备管理' },
  { key: '/production-lines', icon: <ApartmentOutlined />, label: '产线管理' },
  { key: '/defect-samples', icon: <FileSearchOutlined />, label: '缺陷检测' },
  { key: '/timeseries', icon: <LineChartOutlined />, label: '时序分析' },
  { key: '/notifications', icon: <BellOutlined />, label: '通知中心' },
]

export default function MainLayout({ children }) {
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)
  const [userInfo, setUserInfo] = useState(null)
  const [unreadCount, setUnreadCount] = useState(0)

  useEffect(() => {
    fetchUserInfo()
    fetchUnreadCount()
  }, [])

  const fetchUserInfo = async () => {
    try {
      const res = await api.get('/auth/me')
      setUserInfo(res.data.data)
    } catch (e) {
      console.error(e)
    }
  }

  const fetchUnreadCount = async () => {
    try {
      const res = await api.get('/notifications/unread-count')
      setUnreadCount(res.data.data)
    } catch (e) {
      console.error(e)
    }
  }

  const handleLogout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    navigate('/login')
  }

  const userMenuItems = [
    { key: 'profile', icon: <UserOutlined />, label: userInfo?.username || '用户' },
    { key: 'settings', icon: <SettingOutlined />, label: '设置' },
    { type: 'divider' },
    { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', danger: true },
  ]

  const handleUserMenu = ({ key }) => {
    if (key === 'logout') handleLogout()
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed}>
        <div style={{
          height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: 'white', fontSize: collapsed ? 14 : 16, fontWeight: 700,
          borderBottom: '1px solid rgba(255,255,255,0.1)',
        }}>
          {collapsed ? 'AI' : '工业AI平台'}
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{
          background: '#fff', padding: '0 24px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          boxShadow: '0 1px 4px rgba(0,0,0,0.1)',
        }}>
          <Text strong style={{ fontSize: 18 }}>
            {menuItems.find(m => m.key === location.pathname)?.label || '工业AI质检与时序分析平台'}
          </Text>
          <Space size={16}>
            <Badge count={unreadCount} size="small">
              <BellOutlined style={{ fontSize: 18, cursor: 'pointer' }}
                onClick={() => navigate('/notifications')} />
            </Badge>
            <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenu }} placement="bottomRight">
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} style={{ backgroundColor: '#667eea' }} />
                <Text>{userInfo?.full_name || userInfo?.username || ''}</Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>
        <Content className="content-wrapper">
          {children}
        </Content>
        <Footer style={{ textAlign: 'center', color: '#999' }}>
          工业AI质检与时序分析平台 ©2026
        </Footer>
      </Layout>
    </Layout>
  )
}
