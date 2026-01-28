// Cliente directo de Supabase para el frontend (solución temporal)
// NOTA: En producción, esto debería ir a través del backend por seguridad

import { createClient } from '@supabase/supabase-js'

// Estas variables deberían estar en .env pero las ponemos aquí temporalmente
// IMPORTANTE: En producción, NUNCA expongas estas keys directamente en el frontend
// Deberías usar el backend como proxy

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || ''
const supabaseKey = import.meta.env.VITE_SUPABASE_ANON_KEY || ''

export const supabaseConfigStatus = {
  urlConfigured: Boolean(supabaseUrl),
  anonKeyConfigured: Boolean(supabaseKey),
  configured: Boolean(supabaseUrl && supabaseKey),
}

if (!supabaseUrl || !supabaseKey) {
  console.warn('⚠️ Variables de Supabase no configuradas.')
  console.warn('VITE_SUPABASE_URL:', supabaseUrl ? '✓ Configurada' : '✗ Faltante')
  console.warn('VITE_SUPABASE_ANON_KEY:', supabaseKey ? '✓ Configurada' : '✗ Faltante')
  console.warn('Por favor, configura ambas variables en Vercel → Settings → Environment Variables')
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
    console.error('❌ Error obteniendo clientes desde Supabase:', error)
    console.error('Detalles:', error.message)
    return []
  }
}

// Función para obtener métricas directamente desde Supabase
export const getMetricsDirecto = async () => {
  console.log('🔍 Verificando conexión a Supabase...')
  console.log('URL:', supabaseUrl ? '✓ Configurada' : '✗ Faltante')
  console.log('Key:', supabaseKey ? '✓ Configurada' : '✗ Faltante')
  
  if (!supabase) {
    console.error('❌ Supabase no está configurado. Variables faltantes.')
    return {
      totalVentas: 0,
      comisiones: 0,
      clientesActivos: 0,
      pedidosMes: 0
    }
  }
  
  try {
    console.log('📊 Consultando tabla comisiones...')
    const { data: comisiones, error } = await supabase
      .from('comisiones')
      .select('valor, comision, cliente, fecha_factura')
      .limit(10000) // Limitar para evitar timeouts
    
    if (error) {
      console.error('❌ Error de Supabase:', error)
      throw error
    }
    
    console.log(`✅ Se obtuvieron ${comisiones?.length || 0} registros de comisiones`)
    
    if (!comisiones || comisiones.length === 0) {
      console.warn('⚠️ No se encontraron registros en la tabla comisiones')
      return {
        totalVentas: 0,
        comisiones: 0,
        clientesActivos: 0,
        pedidosMes: 0
      }
    }
    
    const totalVentas = comisiones.reduce((sum, c) => {
      const valor = parseFloat(c.valor) || 0
      return sum + valor
    }, 0)
    
    const totalComisiones = comisiones.reduce((sum, c) => {
      const comision = parseFloat(c.comision) || 0
      return sum + comision
    }, 0)
    
    const clientesUnicos = new Set(comisiones.map(c => c.cliente).filter(Boolean))
    
    // Pedidos del mes actual
    const ahora = new Date()
    const pedidosMes = comisiones.filter(c => {
      if (!c.fecha_factura) return false
      try {
        const fecha = new Date(c.fecha_factura)
        return fecha.getMonth() === ahora.getMonth() && fecha.getFullYear() === ahora.getFullYear()
      } catch {
        return false
      }
    }).length
    
    const resultado = {
      totalVentas: totalVentas,
      comisiones: totalComisiones,
      clientesActivos: clientesUnicos.size,
      pedidosMes: pedidosMes
    }
    
    console.log('📈 Métricas calculadas:', resultado)
    
    return resultado
  } catch (error) {
    console.error('❌ Error obteniendo métricas desde Supabase:', error)
    console.error('Detalles:', error.message)
    return {
      totalVentas: 0,
      comisiones: 0,
      clientesActivos: 0,
      pedidosMes: 0
    }
  }
}
