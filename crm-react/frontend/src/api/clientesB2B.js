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
  
  // Construir URL con query params si hay NIT
  let url = '/clientes/b2b/cargar-compras-excel'
  if (nitCliente && nitCliente.trim()) {
    url += `?nit_cliente=${encodeURIComponent(nitCliente.trim())}`
  }
  
  console.log('📡 Enviando archivo a:', url)
  
  try {
    const response = await apiClient.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 60000, // 60 segundos de timeout para archivos grandes
    })
    return response.data
  } catch (error) {
    console.error('❌ Error en cargarComprasExcel:', error)
    if (error.response) {
      // El servidor respondió con un código de error
      throw {
        ...error,
        message: error.response.data?.detail || error.response.data?.message || error.message || 'Error desconocido'
      }
    } else if (error.request) {
      // La petición se hizo pero no hubo respuesta
      throw {
        ...error,
        message: 'No se pudo conectar con el servidor. Verifica que el backend esté corriendo.'
      }
    } else {
      // Algo más causó el error
      throw error
    }
  }
}
