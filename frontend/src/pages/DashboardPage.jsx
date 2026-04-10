import React, { useState, useEffect } from 'react'
import { Row, Col, Card, Statistic, Spin, Typography, Tag } from 'antd'
import {
  ToolOutlined, CheckCircleOutlined, WarningOutlined,
  BugOutlined, LineChartOutlined, AlertOutlined,
} from '@ant-design/icons'
import ReactECharts from 'echarts-for-react'
import api from '../api'

const { Title } = Typography

export default function DashboardPage() {
  const [overview, setOverview] = useState(null)
  const [trend, setTrend] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [overviewRes, trendRes] = await Promise.all([
        api.get('/dashboard/overview'),
        api.get('/dashboard/defect-trend?days=30'),
      ])
      setOverview(overviewRes.data.data)
      setTrend(trendRes.data.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const getTrendOption = () => ({
    tooltip: { trigger: 'axis' },
    legend: { data: ['检测总数', '缺陷数'] },
    xAxis: { type: 'category', data: trend.map(t => t.date.slice(5)), axisLabel: { rotate: 45 } },
    yAxis: { type: 'value' },
    series: [
      { name: '检测总数', type: 'bar', data: trend.map(t => t.total), itemStyle: { color: '#1890ff' } },
      { name: '缺陷数', type: 'bar', data: trend.map(t => t.defect), itemStyle: { color: '#ff4d4f' } },
    ],
    grid: { left: 40, right: 20, bottom: 50, top: 40 },
  })

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />

  const devices = overview?.devices || {}
  const defect = overview?.defect_detection || {}
  const ts = overview?.timeseries || {}

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="设备总数" value={devices.total || 0} prefix={<ToolOutlined />}
              valueStyle={{ color: '#1890ff' }} />
            <div style={{ marginTop: 8 }}>
              <Tag color="green">在线 {devices.online || 0}</Tag>
              <Tag color="red">离线 {devices.offline || 0}</Tag>
              <Tag color="orange">告警 {devices.warning || 0}</Tag>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="产线数量" value={overview?.production_lines || 0}
              prefix={<CheckCircleOutlined />} valueStyle={{ color: '#52c41a' }} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="缺陷样本" value={defect.total_samples || 0}
              prefix={<BugOutlined />} valueStyle={{ color: '#fa8c16' }} />
            <div style={{ marginTop: 8 }}>
              <Tag color="red">缺陷 {defect.defect_found || 0}</Tag>
              <Tag>缺陷率 {defect.defect_rate || 0}%</Tag>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title="时序数据集" value={ts.datasets || 0}
              prefix={<LineChartOutlined />} valueStyle={{ color: '#722ed1' }} />
            <div style={{ marginTop: 8 }}>
              <Tag color="orange"><AlertOutlined /> 异常 {ts.anomalies_detected || 0}</Tag>
            </div>
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card title="缺陷检测趋势（近30天）">
            {trend.length > 0 ? (
              <ReactECharts option={getTrendOption()} style={{ height: 350 }} />
            ) : (
              <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>暂无数据</div>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}
