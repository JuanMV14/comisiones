import apiClient from './client'

export const getClientes = async () => {
  const response = await apiClient.get('/clientes')
  return response.data
}

export const getClienteById = async (id) => {
  const response = await apiClient.get(`/clientes/${id}`)
  return response.data
}

export const getClienteDetalle = async (clienteNombre) => {
  const response = await apiClient.get('/clientes/detalle', {
    params: { nombre: clienteNombre }
  })
  return response.data
}

export const crearCliente = async (clienteData) => {
  const response = await apiClient.post('/clientes', clienteData)
  return response.data
}

export const actualizarCliente = async (clienteId, clienteData) => {
  const response = await apiClient.put(`/clientes/${clienteId}`, clienteData)
  return response.data
}

export const eliminarCliente = async (clienteId) => {
  const response = await apiClient.delete(`/clientes/${clienteId}`)
  return response.data
}