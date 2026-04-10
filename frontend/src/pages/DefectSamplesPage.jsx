import React, { useState, useEffect } from 'react'
import { Table, Button, Input, Card, Space, Tag, Upload, Modal, Form, message } from 'antd'
import { UploadOutlined, SearchOutlined, DeleteOutlined, ExperimentOutlined } from '@ant-design/icons'
import api from '../api'

export default function DefectSamplesPage() {
  const [samples, setSamples] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [search, setSearch] = useState('')
  const [uploadModal, setUploadModal] = useState(false)
  const [uploadForm] = Form.useForm()
  const [selectedRowKeys, setSelectedRowKeys] = useState([])

  useEffect(() => { fetchSamples() }, [pagination.current, search])

  const fetchSamples = async () => {
    setLoading(true)
    try {
      const params = { page: pagination.current, page_size: pagination.pageSize }
      if (search) params.search = search
      const res = await api.get('/defect/samples', { params })
      setSamples(res.data.data)
      setPagination(p => ({ ...p, total: res.data.meta.total }))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleUpload = async (values) => {
    const formData = new FormData()
    formData.append('file', values.file.file)
    formData.append('sample_no', values.sample_no)
    if (values.name) formData.append('name', values.name)

    try {
      await api.post('/defect/samples/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      message.success('样本上传成功')
      setUploadModal(false)
      uploadForm.resetFields()
      fetchSamples()
    } catch (e) { /* handled */ }
  }

  const handleDetect = async () => {
    if (selectedRowKeys.length === 0) {
      message.warning('请选择要检测的样本')
      return
    }
    try {
      const res = await api.post('/defect/detect', { sample_ids: selectedRowKeys })
      message.success(res.data.message)
      setSelectedRowKeys([])
      fetchSamples()
    } catch (e) { /* handled */ }
  }

  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该样本吗？',
      onOk: async () => {
        await api.delete(`/defect/samples/${id}`)
        message.success('删除成功')
        fetchSamples()
      },
    })
  }

  const columns = [
    { title: '样本编号', dataIndex: 'sample_no', width: 140 },
    { title: '名称', dataIndex: 'name', width: 150 },
    { title: '文件名', dataIndex: 'file_name', width: 150 },
    { title: '设备', dataIndex: 'device_name', width: 120 },
    { title: '批次', dataIndex: 'batch_no', width: 120 },
    {
      title: '状态', dataIndex: 'status', width: 90,
      render: s => <Tag color={s === 'completed' ? 'green' : s === 'pending' ? 'orange' : 'default'}>
        {s === 'completed' ? '已检测' : s === 'pending' ? '待检测' : s}
      </Tag>,
    },
    {
      title: '检测结果', dataIndex: 'has_defect', width: 90,
      render: v => v === null ? '-' : v ? <Tag color="red">有缺陷</Tag> : <Tag color="green">正常</Tag>,
    },
    {
      title: '操作', width: 80, fixed: 'right',
      render: (_, r) => (
        <Button type="link" danger icon={<DeleteOutlined />} size="small"
          onClick={() => handleDelete(r.id)} />
      ),
    },
  ]

  return (
    <Card>
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between' }}>
        <Space>
          <Input.Search placeholder="搜索样本" allowClear style={{ width: 300 }}
            onSearch={v => { setSearch(v); setPagination(p => ({ ...p, current: 1 })) }} />
        </Space>
        <Space>
          <Button icon={<ExperimentOutlined />} onClick={handleDetect}
            disabled={selectedRowKeys.length === 0}
            type={selectedRowKeys.length > 0 ? 'primary' : 'default'}>
            缺陷检测 ({selectedRowKeys.length})
          </Button>
          <Button type="primary" icon={<UploadOutlined />} onClick={() => setUploadModal(true)}>
            上传样本
          </Button>
        </Space>
      </div>
      <Table
        columns={columns} dataSource={samples} rowKey="id"
        loading={loading} scroll={{ x: 900 }}
        rowSelection={{
          selectedRowKeys,
          onChange: setSelectedRowKeys,
          getCheckboxProps: r => ({ disabled: r.status === 'completed' }),
        }}
        pagination={{
          ...pagination, showSizeChanger: false, showTotal: t => `共 ${t} 条`,
          onChange: page => setPagination(p => ({ ...p, current: page })),
        }}
      />
      <Modal title="上传缺陷样本" open={uploadModal} onCancel={() => setUploadModal(false)}
        onOk={() => uploadForm.submit()} destroyOnClose>
        <Form form={uploadForm} layout="vertical" onFinish={handleUpload}>
          <Form.Item name="sample_no" label="样本编号" rules={[{ required: true }]}>
            <Input placeholder="如 DS20260304120001" />
          </Form.Item>
          <Form.Item name="name" label="样本名称">
            <Input placeholder="如 侧板划伤" />
          </Form.Item>
          <Form.Item name="file" label="选择图片" rules={[{ required: true, message: '请选择文件' }]}>
            <Upload beforeUpload={() => false} maxCount={1} accept="image/*">
              <Button icon={<UploadOutlined />}>选择文件</Button>
            </Upload>
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}
