import apiClient from './client'

// Obtener todos los presupuestos
export const getPresupuestos = async () => {
  const response = await apiClient.get('/presupuestos/presupuestos')
  return response.data
}

// Obtener presupuesto de un mes específico
export const getPresupuestoMes = async (mes) => {
  const response = await apiClient.get(`/presupuestos/presupuestos/${mes}`)
  return response.data
}

// Crear un nuevo presupuesto
export const crearPresupuesto = async (presupuesto) => {
  const response = await apiClient.post('/presupuestos/presupuestos', presupuesto)
  return response.data
}

// Actualizar un presupuesto existente
export const actualizarPresupuesto = async (mes, presupuesto) => {
  const response = await apiClient.put(`/presupuestos/presupuestos/${mes}`, presupuesto)
  return response.data
}

// Eliminar un presupuesto
export const eliminarPresupuesto = async (mes) => {
  const response = await apiClient.delete(`/presupuestos/presupuestos/${mes}`)
  return response.data
}

// Obtener presupuestos por marca para un mes específico
export const getPresupuestosMarcas = async (mes) => {
  const response = await apiClient.get(`/presupuestos/presupuestos-marcas/${mes}`)
  return response.data
}

// Crear o actualizar presupuesto total por marca (para las 4 marcas combinadas)
export const crearPresupuestoMarca = async (presupuesto) => {
  const response = await apiClient.post('/presupuestos/presupuestos-marcas', presupuesto)
  return response.data
}

// Actualizar presupuesto total por marca
export const actualizarPresupuestoMarca = async (mes, presupuesto) => {
  const response = await apiClient.put(`/presupuestos/presupuestos-marcas/${mes}`, presupuesto)
  return response.data
}