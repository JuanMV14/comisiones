import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

export const getClientes = async () => {
  const response = await axios.get(`${API_URL}/clientes`)
  return response.data
}

export const getClienteById = async (id) => {
  const response = await axios.get(`${API_URL}/clientes/${id}`)
  return response.data
}

export const getClienteDetalle = async (clienteNombre) => {
  const response = await axios.get(`${API_URL}/clientes/detalle`, {
    params: { nombre: clienteNombre }
  })
  return response.data
}
