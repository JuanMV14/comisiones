import apiClient from './client'

export const getDevoluciones = async (facturaId = null, cliente = null, mes = null, afectaComision = null) => {
  const params = {}
  if (facturaId) params.factura_id = facturaId
  if (cliente) params.cliente = cliente
  if (mes) params.mes = mes
  if (afectaComision !== null) params.afecta_comision = afectaComision
  
  const response = await apiClient.get('/devoluciones', { params })
  return response.data
}

export const getFacturasDisponibles = async () => {
  const response = await apiClient.get('/devoluciones/facturas-disponibles')
  return response.data
}

export const crearDevolucion = async (devolucionData) => {
  const response = await apiClient.post('/devoluciones', devolucionData)
  return response.data
}

export const actualizarDevolucion = async (devolucionId, devolucionData) => {
  const response = await apiClient.put(`/devoluciones/${devolucionId}`, devolucionData)
  return response.data
}

export const eliminarDevolucion = async (devolucionId) => {
  const response = await apiClient.delete(`/devoluciones/${devolucionId}`)
  return response.data
}
