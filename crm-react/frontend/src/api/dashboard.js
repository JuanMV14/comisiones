import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const getDashboardMetrics = async () => {
  const response = await axios.get(`${API_URL}/dashboard/metrics`)
  return response.data
}

export const getSalesChart = async () => {
  const response = await axios.get(`${API_URL}/dashboard/sales-chart`)
  return response.data
}

export const getColombiaMap = async () => {
  const response = await axios.get(`${API_URL}/dashboard/colombia-map`)
  return response.data
}
