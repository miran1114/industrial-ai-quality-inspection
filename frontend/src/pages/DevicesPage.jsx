import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Card, Space, Tag, Modal, Form, Select, message, Progress } from 'antd'
import { PlusOutlined, SearchOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../api'

export default function DevicesPage() {
  const [devices, setDevices] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => { fetchDevices() }, [pagination.current, search])

  const fetchDevices = async () => {
    setLoading(true)
    try {
      const params = { page: pagination.current, page_size: pagination.pageSize }
      if (search) params.search = search
      const res = await api.get('/industrial/devices', { params })
      setDevices(res.data.data)
      setPagination(p => ({ ...p, total: res.data.meta.total }))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleCreate = async (values) => {
    try {
      await api.post('/industrial/devices', values)
      message.success('设备创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchDevices()
    } catch (e) { /* handled */ }
  }

  const handleDelete = (id, name) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除设备 "${name}" 吗？`,
      onOk: async () => {
        await api.delete(`/industrial/devices/${id}`)
        message.success('删除成功')
        fetchDevices()
      },
    })
  }

  const statusColor = { online: 'green', offline: 'default', warning: 'orange', maintenance: 'blue' }
  const statusText = { online: '在线', offline: '离线', warning: '告警', maintenance: '维护中' }

  const columns = [
    { title: '设备编号', dataIndex: 'code', width: 120 },
    { title: '设备名称', dataIndex: 'name', width: 150 },
    { title: '设备类型', dataIndex: 'device_type', width: 120 },
    {
      title: '运行状态', dataIndex: 'status', width: 100,
      render: (s) => <Tag color={statusColor[s] || 'default'}>{statusText[s] || s}</Tag>,
    },
    {
      title: '健康评分', dataIndex: 'health_score', width: 150,
      render: (v) => <Progress percent={v || 0} size="small"
        strokeColor={v >= 80 ? '#52c41a' : v >= 60 ? '#faad14' : '#ff4d4f'} />,
    },
    { title: '所属产线', dataIndex: 'production_line_name', width: 120 },
    { title: '位置', dataIndex: 'location', width: 120 },
    {
      title: '操作', width: 120, fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button type="link" icon={<EditOutlined />} size="small" />
          <Button type="link" danger icon={<DeleteOutlined />} size="small"
            onClick={() => handleDelete(record.id, record.name)} />
        </Space>
      ),
    },
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Input.Search placeholder="搜索设备编号或名称" allowClear style={{ width: 300 }}
          onSearch={v => { setSearch(v); setPagination(p => ({ ...p, current: 1 })) }} />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新增设备
        </Button>
      </div>
      <Table
        columns={columns} dataSource={devices} rowKey="id"
        loading={loading} scroll={{ x: 1000 }}
        pagination={{
          ...pagination, showSizeChanger: false, showTotal: t => `共 ${t} 条`,
          onChange: (page) => setPagination(p => ({ ...p, current: page })),
        }}
      />
      <Modal title="新增设备" open={modalOpen} onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="code" label="设备编号" rules={[{ required: true }]}>
            <Input placeholder="如 DEV001" />
          </Form.Item>
          <Form.Item name="name" label="设备名称" rules={[{ required: true }]}>
            <Input placeholder="设备名称" />
          </Form.Item>
          <Form.Item name="device_type" label="设备类型">
            <Select placeholder="选择类型" allowClear options={[
              { value: 'sensor', label: '传感器' },
              { value: 'camera', label: '相机' },
              { value: 'robot', label: '机械臂' },
              { value: 'plc', label: 'PLC控制器' },
              { value: 'other', label: '其他' },
            ]} />
          </Form.Item>
          <Form.Item name="manufacturer" label="制造商">
            <Input placeholder="制造商" />
          </Form.Item>
          <Form.Item name="location" label="设备位置">
            <Input placeholder="如 A区1号位" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
