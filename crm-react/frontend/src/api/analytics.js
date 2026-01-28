import apiClient from './client'

// Endpoint para análisis geográfico completo (incluye distribución, ranking y segmentación)
export const getAnalisisGeografico = async (periodo = 'historico') => {
  const response = await apiClient.get('/analytics/geografico', {
    params: { periodo }
  })
  return response.data
}

// Endpoint para análisis comercial
export const getAnalisisComercial = async () => {
  const response = await apiClient.get('/analytics/comercial')
  return response.data
}

// Endpoint para comisiones mensuales del vendedor
export const getComisionesMensuales = async () => {
  const response = await apiClient.get('/analytics/comisiones-mensuales')
  return response.data
}

// Endpoint para comisiones de gerencia
export const getComisionesGerencia = async () => {
  const response = await apiClient.get('/analytics/comisiones-gerencia')
  return response.data
}

// Endpoints individuales (para compatibilidad)
export const getRankingClientes = async (periodoMeses = 12) => {
  const response = await apiClient.get('/analytics/ranking-clientes', {
    params: { periodo_meses: periodoMeses }
  })
  return response.data
}

export const getDistribucionGeografica = async (periodo = 'historico', fechaInicio = null, fechaFin = null) => {
  const response = await apiClient.get('/analytics/distribucion-geografica', {
    params: { periodo, fecha_inicio: fechaInicio, fecha_fin: fechaFin }
  })
  return response.data
}

export const getSegmentacionClientes = async () => {
  const response = await apiClient.get('/analytics/segmentacion-clientes')
  return response.data
}

// Endpoint para facturas sin fecha de pago
export const getFacturasSinFechaPago = async () => {
  const response = await apiClient.get('/analytics/facturas-sin-fecha-pago')
  return response.data
}

// Endpoint para obtener facturas de un mes específico
export const getFacturasPorMes = async (mes) => {
  const response = await apiClient.get(`/analytics/comisiones-mensuales/${mes}/facturas`)
  return response.data
}

// Endpoint para análisis de compras
export const getAnalisisCompras = async (periodo = '12') => {
  const response = await apiClient.get('/analytics/compras', {
    params: { periodo }
  })
  return response.data
}
