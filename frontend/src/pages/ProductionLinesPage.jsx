import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Card, Space, Tag, Modal, Form, message } from 'antd'
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons'
import api from '../api'

export default function ProductionLinesPage() {
  const [lines, setLines] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [search, setSearch] = useState('')
  const [modalOpen, setModalOpen] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => { fetchLines() }, [pagination.current, search])

  const fetchLines = async () => {
    setLoading(true)
    try {
      const params = { page: pagination.current, page_size: pagination.pageSize }
      if (search) params.search = search
      const res = await api.get('/industrial/production-lines', { params })
      setLines(res.data.data)
      setPagination(p => ({ ...p, total: res.data.meta.total }))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleCreate = async (values) => {
    try {
      await api.post('/industrial/production-lines', values)
      message.success('产线创建成功')
      setModalOpen(false)
      form.resetFields()
      fetchLines()
    } catch (e) { /* handled */ }
  }

  const handleDelete = (id, name) => {
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除产线 "${name}" 吗？`,
      onOk: async () => {
        await api.delete(`/industrial/production-lines/${id}`)
        message.success('删除成功')
        fetchLines()
      },
    })
  }

  const columns = [
    { title: '产线编号', dataIndex: 'code', width: 120 },
    { title: '产线名称', dataIndex: 'name', width: 150 },
    { title: '描述', dataIndex: 'description', width: 200 },
    { title: '位置', dataIndex: 'location', width: 120 },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: s => <Tag color={s === 'active' ? 'green' : 'default'}>{s === 'active' ? '运行中' : s}</Tag>,
    },
    { title: '设备数', dataIndex: 'device_count', width: 80 },
    {
      title: '操作', width: 80, fixed: 'right',
      render: (_, r) => (
        <Button type="link" danger icon={<DeleteOutlined />} size="small"
          onClick={() => handleDelete(r.id, r.name)} />
      ),
    },
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Input.Search placeholder="搜索产线" allowClear style={{ width: 300 }}
          onSearch={v => { setSearch(v); setPagination(p => ({ ...p, current: 1 })) }} />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalOpen(true)}>
          新增产线
        </Button>
      </div>
      <Table
        columns={columns} dataSource={lines} rowKey="id"
        loading={loading} scroll={{ x: 800 }}
        pagination={{
          ...pagination, showSizeChanger: false, showTotal: t => `共 ${t} 条`,
          onChange: page => setPagination(p => ({ ...p, current: page })),
        }}
      />
      <Modal title="新增产线" open={modalOpen} onCancel={() => setModalOpen(false)}
        onOk={() => form.submit()} destroyOnClose>
        <Form form={form} layout="vertical" onFinish={handleCreate}>
          <Form.Item name="code" label="产线编号" rules={[{ required: true }]}>
            <Input placeholder="如 PL001" />
          </Form.Item>
          <Form.Item name="name" label="产线名称" rules={[{ required: true }]}>
            <Input placeholder="产线名称" />
          </Form.Item>
          <Form.Item name="location" label="位置">
            <Input placeholder="如 A栋一楼" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
