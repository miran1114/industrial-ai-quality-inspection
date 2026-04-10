import React, { useState, useEffect } from 'react'
import { List, Card, Button, Tag, Badge, Space, Empty, message } from 'antd'
import { BellOutlined, CheckOutlined } from '@ant-design/icons'
import api from '../api'

const typeColors = { info: 'blue', alert: 'red', warning: 'orange', success: 'green' }

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState([])
  const [loading, setLoading] = useState(false)
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)

  useEffect(() => { fetchNotifications() }, [page])

  const fetchNotifications = async () => {
    setLoading(true)
    try {
      const res = await api.get('/notifications', { params: { page, page_size: 20 } })
      setNotifications(res.data.data.items)
      setTotal(res.data.data.total)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleMarkRead = async (id) => {
    try {
      await api.post(`/notifications/${id}/read`)
      fetchNotifications()
    } catch (e) { /* handled */ }
  }

  const handleMarkAllRead = async () => {
    try {
      await api.post('/notifications/read-all')
      message.success('已全部标记为已读')
      fetchNotifications()
    } catch (e) { /* handled */ }
  }

  return (
    <Card
      title={<Space><BellOutlined /> 通知中心</Space>}
      extra={<Button icon={<CheckOutlined />} onClick={handleMarkAllRead}>全部已读</Button>}
    >
      {notifications.length === 0 ? (
        <Empty description="暂无通知" />
      ) : (
        <List
          loading={loading}
          dataSource={notifications}
          pagination={{
            current: page, pageSize: 20, total,
            onChange: p => setPage(p), showTotal: t => `共 ${t} 条`,
          }}
          renderItem={item => (
            <List.Item
              actions={[
                !item.is_read && (
                  <Button type="link" size="small" onClick={() => handleMarkRead(item.id)}>
                    标记已读
                  </Button>
                ),
              ].filter(Boolean)}
            >
              <List.Item.Meta
                avatar={
                  <Badge dot={!item.is_read}>
                    <BellOutlined style={{ fontSize: 20, color: typeColors[item.type] || '#999' }} />
                  </Badge>
                }
                title={
                  <Space>
                    <span style={{ fontWeight: item.is_read ? 400 : 600 }}>{item.title}</span>
                    <Tag color={typeColors[item.type]}>{item.type}</Tag>
                  </Space>
                }
                description={
                  <div>
                    <div>{item.content}</div>
                    <div style={{ color: '#999', fontSize: 12, marginTop: 4 }}>
                      {item.created_at?.slice(0, 19).replace('T', ' ')}
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      )}
    </Card>
  )
}
