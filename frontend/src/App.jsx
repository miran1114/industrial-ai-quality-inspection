import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './layouts/MainLayout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import DevicesPage from './pages/DevicesPage'
import ProductionLinesPage from './pages/ProductionLinesPage'
import DefectSamplesPage from './pages/DefectSamplesPage'
import TimeseriesPage from './pages/TimeseriesPage'
import NotificationsPage from './pages/NotificationsPage'

function PrivateRoute({ children }) {
  const token = localStorage.getItem('access_token')
  return token ? children : <Navigate to="/login" />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <MainLayout>
              <Routes>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/devices" element={<DevicesPage />} />
                <Route path="/production-lines" element={<ProductionLinesPage />} />
                <Route path="/defect-samples" element={<DefectSamplesPage />} />
                <Route path="/timeseries" element={<TimeseriesPage />} />
                <Route path="/notifications" element={<NotificationsPage />} />
              </Routes>
            </MainLayout>
          </PrivateRoute>
        }
      />
    </Routes>
  )
}
