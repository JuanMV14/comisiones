import apiClient from './client'

export const getFacturas = async (mes = null, cliente = null, soloPropios = false) => {
  const params = {}
  if (mes) params.mes = mes
  if (cliente) params.cliente = cliente
  params.solo_propios = soloPropios

  const response = await apiClient.get('/comisiones/facturas', { params })
  return response.data
}

export const actualizarFactura = async (facturaId, facturaData) => {
  const response = await apiClient.put(`/comisiones/facturas/${facturaId}`, facturaData)
  return response.data
}

export const marcarFacturaPagado = async (facturaId, fechaPago = null, diasPago = null) => {
  const response = await apiClient.patch(`/comisiones/facturas/${facturaId}/marcar-pagado`, {
    fecha_pago: fechaPago,
    dias_pago: diasPago
  })
  return response.data
}

export const subirComprobantePago = async (facturaId, archivo, fechaPago = null) => {
  const formData = new FormData()
  formData.append('archivo', archivo)
  if (fechaPago) {
    formData.append('fecha_pago', fechaPago)
  }

  const response = await apiClient.post(`/comisiones/facturas/${facturaId}/comprobante`, formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
  return response.data
}

export const obtenerComprobantePago = async (facturaId) => {
  const response = await apiClient.get(`/comisiones/facturas/${facturaId}/comprobante`)
  return response.data
}
