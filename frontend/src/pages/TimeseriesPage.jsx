import React, { useState, useEffect } from 'react'
import {
  Table, Button, Card, Space, Tag, Modal, Form, Input, InputNumber,
  DatePicker, message, Tabs, Descriptions,
} from 'antd'
import { PlusOutlined, DeleteOutlined, ThunderboltOutlined, LineChartOutlined } from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import dayjs from 'dayjs'
import api from '../api'

const { RangePicker } = DatePicker

export default function TimeseriesPage() {
  const [datasets, setDatasets] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [loading, setLoading] = useState(false)
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 })
  const [simModal, setSimModal] = useState(false)
  const [chartModal, setChartModal] = useState(false)
  const [chartData, setChartData] = useState(null)
  const [simForm] = Form.useForm()
  const [activeTab, setActiveTab] = useState('datasets')

  useEffect(() => {
    if (activeTab === 'datasets') fetchDatasets()
    else fetchAnomalies()
  }, [pagination.current, activeTab])

  const fetchDatasets = async () => {
    setLoading(true)
    try {
      const res = await api.get('/timeseries/datasets', {
        params: { page: pagination.current, page_size: pagination.pageSize },
      })
      setDatasets(res.data.data)
      setPagination(p => ({ ...p, total: res.data.meta.total }))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const fetchAnomalies = async () => {
    setLoading(true)
    try {
      const res = await api.get('/timeseries/anomalies', {
        params: { page: pagination.current, page_size: pagination.pageSize },
      })
      setAnomalies(res.data.data)
      setPagination(p => ({ ...p, total: res.data.meta.total }))
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }

  const handleSimulate = async (values) => {
    const payload = {
      ...values,
      start_time: values.time_range[0].toISOString(),
      end_time: values.time_range[1].toISOString(),
    }
    delete payload.time_range
    try {
      await api.post('/timeseries/datasets/simulate', payload)
      message.success('模拟数据生成成功')
      setSimModal(false)
      simForm.resetFields()
      fetchDatasets()
    } catch (e) { /* handled */ }
  }

  const handleViewChart = async (datasetId) => {
    try {
      const res = await api.get(`/timeseries/datasets/${datasetId}/data?limit=2000`)
      setChartData(res.data.data)
      setChartModal(true)
    } catch (e) { /* handled */ }
  }

  const handleAnalyze = async (datasetId) => {
    try {
      const res = await api.post('/timeseries/analyze', {
        dataset_id: datasetId,
        anomaly_method: 'zscore',
        anomaly_threshold: 3.0,
      })
      message.success(res.data.data.message)
    } catch (e) { /* handled */ }
  }

  const handleDelete = (id) => {
    Modal.confirm({
      title: '确认删除',
      content: '确定要删除该数据集吗？相关数据点将一并删除。',
      onOk: async () => {
        await api.delete(`/timeseries/datasets/${id}`)
        message.success('删除成功')
        fetchDatasets()
      },
    })
  }

  const getChartOption = () => {
    if (!chartData) return {}
    return {
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category',
        data: chartData.points.map(p => p.timestamp.slice(11, 19)),
        axisLabel: { rotate: 45 },
      },
      yAxis: { type: 'value', name: chartData.unit || '' },
      series: [{
        type: 'line', data: chartData.points.map(p => p.value),
        smooth: true, lineStyle: { width: 1 }, symbol: 'none',
        areaStyle: { opacity: 0.1 },
      }],
      dataZoom: [{ type: 'inside' }, { type: 'slider' }],
      grid: { left: 60, right: 20, bottom: 80, top: 30 },
    }
  }

  const datasetColumns = [
    { title: '名称', dataIndex: 'name', width: 160 },
    { title: '设备', dataIndex: 'device_name', width: 120 },
    { title: '传感器', dataIndex: 'sensor_name', width: 100 },
    { title: '数据点', dataIndex: 'point_count', width: 80 },
    {
      title: '状态', dataIndex: 'status', width: 80,
      render: s => <Tag color={s === 'active' ? 'green' : 'default'}>{s === 'active' ? '正常' : s}</Tag>,
    },
    {
      title: '操作', width: 200, fixed: 'right',
      render: (_, r) => (
        <Space>
          <Button type="link" icon={<LineChartOutlined />} size="small" onClick={() => handleViewChart(r.id)}>
            查看
          </Button>
          <Button type="link" icon={<ThunderboltOutlined />} size="small" onClick={() => handleAnalyze(r.id)}>
            分析
          </Button>
          <Button type="link" danger icon={<DeleteOutlined />} size="small" onClick={() => handleDelete(r.id)} />
        </Space>
      ),
    },
  ]

  const anomalyColumns = [
    { title: '时间', dataIndex: 'timestamp', width: 160, render: v => v?.slice(0, 19) },
    { title: '数值', dataIndex: 'value', width: 100, render: v => v?.toFixed(4) },
    { title: '类型', dataIndex: 'anomaly_type', width: 100 },
    {
      title: '严重度', dataIndex: 'severity', width: 80,
      render: s => <Tag color={s === 'high' ? 'red' : s === 'medium' ? 'orange' : 'blue'}>{s}</Tag>,
    },
    { title: '得分', dataIndex: 'score', width: 80, render: v => v?.toFixed(2) },
    { title: '方法', dataIndex: 'detection_method', width: 80 },
    { title: '描述', dataIndex: 'description', width: 200 },
  ]

  return (
    <Card>
      <Tabs activeKey={activeTab} onChange={k => { setActiveTab(k); setPagination(p => ({ ...p, current: 1 })) }}
        tabBarExtraContent={
          activeTab === 'datasets' ? (
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setSimModal(true)}>
              生成模拟数据
            </Button>
          ) : null
        }
        items={[
          {
            key: 'datasets', label: '数据集列表',
            children: (
              <Table columns={datasetColumns} dataSource={datasets} rowKey="id"
                loading={loading} scroll={{ x: 800 }}
                pagination={{
                  ...pagination, showSizeChanger: false, showTotal: t => `共 ${t} 条`,
                  onChange: page => setPagination(p => ({ ...p, current: page })),
                }} />
            ),
          },
          {
            key: 'anomalies', label: '异常检测结果',
            children: (
              <Table columns={anomalyColumns} dataSource={anomalies} rowKey="id"
                loading={loading} scroll={{ x: 800 }}
                pagination={{
                  ...pagination, showSizeChanger: false, showTotal: t => `共 ${t} 条`,
                  onChange: page => setPagination(p => ({ ...p, current: page })),
                }} />
            ),
          },
        ]}
      />

      <Modal title="生成模拟时序数据" open={simModal} onCancel={() => setSimModal(false)}
        onOk={() => simForm.submit()} destroyOnClose width={500}>
        <Form form={simForm} layout="vertical" onFinish={handleSimulate}
          initialValues={{
            sensor_name: 'temperature', parameter_name: '温度', unit: '°C',
            frequency_seconds: 60, base_value: 25, noise_std: 1, anomaly_ratio: 0.02,
          }}>
          <Form.Item name="name" label="数据集名称" rules={[{ required: true }]}>
            <Input placeholder="如 产线温度监测-3月" />
          </Form.Item>
          <Form.Item name="time_range" label="时间范围" rules={[{ required: true }]}>
            <RangePicker showTime />
          </Form.Item>
          <Form.Item name="sensor_name" label="传感器名称">
            <Input />
          </Form.Item>
          <Form.Item name="unit" label="单位">
            <Input />
          </Form.Item>
          <Form.Item name="frequency_seconds" label="采样间隔(秒)">
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="base_value" label="基准值">
            <InputNumber style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="noise_std" label="噪声标准差">
            <InputNumber min={0} step={0.1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="anomaly_ratio" label="异常比例">
            <InputNumber min={0} max={1} step={0.01} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title={chartData?.dataset_name || '时序数据'} open={chartModal}
        onCancel={() => setChartModal(false)} footer={null} width={900}>
        {chartData && (
          <>
            {chartData.statistics && (
              <Descriptions size="small" bordered column={5} style={{ marginBottom: 16 }}>
                <Descriptions.Item label="数据点">{chartData.statistics.count}</Descriptions.Item>
                <Descriptions.Item label="均值">{chartData.statistics.mean?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="标准差">{chartData.statistics.std?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="最小值">{chartData.statistics.min?.toFixed(2)}</Descriptions.Item>
                <Descriptions.Item label="最大值">{chartData.statistics.max?.toFixed(2)}</Descriptions.Item>
              </Descriptions>
            )}
            <ReactECharts option={getChartOption()} style={{ height: 400 }} />
          </>
        )}
      </Modal>
    </Card>
  )
}
