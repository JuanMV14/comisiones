import apiClient from './client'

// Obtener productos con filtros opcionales
export const getProductos = async (params = {}) => {
  const response = await apiClient.get('/catalogo/productos', { params })
  return response.data
}

// Obtener un producto por ID
export const getProducto = async (productoId) => {
  const response = await apiClient.get(`/catalogo/productos/${productoId}`)
  return response.data
}

// Crear un nuevo producto
export const crearProducto = async (producto) => {
  const response = await apiClient.post('/catalogo/productos', producto)
  return response.data
}

// Actualizar un producto
export const actualizarProducto = async (productoId, producto) => {
  const response = await apiClient.put(`/catalogo/productos/${productoId}`, producto)
  return response.data
}

// Eliminar/desactivar un producto
export const eliminarProducto = async (productoId) => {
  const response = await apiClient.delete(`/catalogo/productos/${productoId}`)
  return response.data
}

// Obtener resumen del catálogo
export const getResumenCatalogo = async () => {
  const response = await apiClient.get('/catalogo/productos/stats/resumen')
  return response.data
}
