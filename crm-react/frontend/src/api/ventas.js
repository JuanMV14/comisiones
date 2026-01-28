import apiClient from './client'

export const crearVenta = async (ventaData) => {
  const response = await apiClient.post('/ventas/nueva-venta', ventaData)
  return response.data
}
