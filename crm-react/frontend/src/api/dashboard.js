import apiClient, { API_URL } from './client'

export const getDashboardMetrics = async (mes = null) => {
  const params = mes ? { mes } : {}
  const response = await apiClient.get('/dashboard/metrics', { params })
  return response.data
}

export const getSalesChart = async () => {
  const response = await apiClient.get('/dashboard/sales-chart')
  return response.data
}

export const getColombiaMap = async (periodo = 'historico') => {
  const response = await apiClient.get('/dashboard/colombia-map', {
    params: { periodo }
  })
  return response.data
}

export const getReferenciasPorCiudad = async () => {
  const response = await apiClient.get('/dashboard/referencias-por-ciudad')
  return response.data
}

export const getClientesClave = async (mes = null) => {
  const params = mes ? { mes } : {}
  const response = await apiClient.get('/dashboard/clientes-clave', { params })
  return response.data
}

export const getMesesDisponibles = async () => {
  const response = await apiClient.get('/dashboard/meses-disponibles')
  return response.data
}

export const getMapaInteractivo = async (referencia = null) => {
  const params = referencia ? { referencia } : {}
  const response = await apiClient.get('/dashboard/mapa-interactivo', { params })
  return response.data
}
