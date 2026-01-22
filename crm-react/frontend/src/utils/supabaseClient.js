// Cliente directo de Supabase para el frontend (solución temporal)
// NOTA: En producción, esto debería ir a través del backend por seguridad

import { createClient } from '@supabase/supabase-js'

// Estas variables deberían estar en .env pero las ponemos aquí temporalmente
// IMPORTANTE: En producción, NUNCA expongas estas keys directamente en el frontend
// Deberías usar el backend como proxy

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

if (!supabaseUrl || !supabaseKey) {
  console.warn('⚠️ Variables de Supabase no configuradas. Usando datos de ejemplo.')
}

export const supabase = supabaseUrl && supabaseKey 
  ? createClient(supabaseUrl, supabaseKey)
  : null

// Función para obtener clientes directamente desde Supabase
export const getClientesDirecto = async () => {
  if (!supabase) {
    // Retornar datos de ejemplo si Supabase no está configurado
    return []
  }
  
  try {
    // Obtener clientes de la tabla comisiones
    const { data: comisiones, error } = await supabase
      .from('comisiones')
      .select('cliente, ciudad_destino')
      .limit(1000)
    
    if (error) throw error
    
    // Obtener clientes únicos
    const clientesUnicos = [...new Set(comisiones.map(c => c.cliente).filter(Boolean))]
    
    return clientesUnicos.map((nombre, index) => ({
      id: index + 1,
      nombre: nombre,
      contacto: nombre,
      ciudad: comisiones.find(c => c.cliente === nombre)?.ciudad_destino || 'N/A',
      estado: 'activo',
      credito: 0,
      creditoUsado: 0,
      ventas: 0
    }))
  } catch (error) {
    console.error('Error obteniendo clientes:', error)
    return []
  }
}

// Función para obtener métricas directamente desde Supabase
export const getMetricsDirecto = async () => {
  if (!supabase) {
    return {
      totalVentas: 0,
      comisiones: 0,
      clientesActivos: 0,
      pedidosMes: 0
    }
  }
  
  try {
    const { data: comisiones, error } = await supabase
      .from('comisiones')
      .select('valor, comision, cliente, fecha_factura')
    
    if (error) throw error
    
    const totalVentas = comisiones.reduce((sum, c) => sum + (parseFloat(c.valor) || 0), 0)
    const totalComisiones = comisiones.reduce((sum, c) => sum + (parseFloat(c.comision) || 0), 0)
    const clientesUnicos = new Set(comisiones.map(c => c.cliente).filter(Boolean))
    
    // Pedidos del mes actual
    const ahora = new Date()
    const pedidosMes = comisiones.filter(c => {
      if (!c.fecha_factura) return false
      const fecha = new Date(c.fecha_factura)
      return fecha.getMonth() === ahora.getMonth() && fecha.getFullYear() === ahora.getFullYear()
    }).length
    
    return {
      totalVentas: totalVentas,
      comisiones: totalComisiones,
      clientesActivos: clientesUnicos.size,
      pedidosMes: pedidosMes
    }
  } catch (error) {
    console.error('Error obteniendo métricas:', error)
    return {
      totalVentas: 0,
      comisiones: 0,
      clientesActivos: 0,
      pedidosMes: 0
    }
  }
}
