import apiClient from './client'

// Obtener listado de clientes B2B con estadísticas
export const getClientesB2B = async (params = {}) => {
  const response = await apiClient.get('/clientes/b2b/listado', { params })
  return response.data
}

// Obtener compras de un cliente específico
export const getComprasCliente = async (clienteId, params = {}) => {
  const response = await apiClient.get(`/clientes/b2b/${clienteId}/compras`, { params })
  return response.data
}

// Obtener resumen de clientes B2B
export const getResumenClientesB2B = async () => {
  const response = await apiClient.get('/clientes/b2b/stats/resumen')
  return response.data
}

// Crear cliente B2B (reutiliza endpoint existente)
export const crearClienteB2B = async (cliente) => {
  const response = await apiClient.post('/clientes', cliente)
  return response.data
}

// Actualizar cliente B2B (reutiliza endpoint existente)
export const actualizarClienteB2B = async (clienteId, cliente) => {
  const response = await apiClient.put(`/clientes/${clienteId}`, cliente)
  return response.data
}

// Eliminar/desactivar cliente B2B (reutiliza endpoint existente)
export const eliminarClienteB2B = async (clienteId) => {
  const response = await apiClient.delete(`/clientes/${clienteId}`)
  return response.data
}

export const cargarComprasExcel = async (archivo, nitCliente = null) => {
  const formData = new FormData()
  formData.append('archivo', archivo)
  
  const url = nitCliente 
    ? `/clientes/b2b/cargar-compras-excel?nit_cliente=${nitCliente}`
    : '/clientes/b2b/cargar-compras-excel'
  
  const response = await apiClient.post(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}
