/**
 * Utilidad para detectar el entorno y configurar URLs de API
 */

// Detectar si estamos en producción (Vercel o cualquier dominio que no sea localhost)
const isProduction = import.meta.env.PROD || (typeof window !== 'undefined' && window.location.hostname !== 'localhost' && !window.location.hostname.startsWith('127.0.0.1'))

// Obtener la URL de la API
// En producción, debe estar configurada como VITE_API_URL en Vercel
// En desarrollo, usa localhost o la variable de entorno
const getApiUrl = () => {
  // Si está definida explícitamente, usarla
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL
  }
  
  // En producción sin VITE_API_URL, usar ruta relativa como fallback
  if (isProduction) {
    // Intentar usar ruta relativa (asumiendo que el backend está en el mismo dominio)
    // Si esto no funciona, el usuario debe configurar VITE_API_URL
    console.warn('⚠️ VITE_API_URL no está configurada. Usando ruta relativa /api')
    console.warn('⚠️ Si esto no funciona, configura VITE_API_URL en Vercel Dashboard → Environment Variables')
    return '/api'
  }
  
  // En desarrollo, usar localhost
  return 'http://localhost:8000/api'
}

export const API_URL = getApiUrl()
export const IS_PRODUCTION = isProduction
export const IS_DEVELOPMENT = !isProduction

// Log para debugging (solo en desarrollo)
if (IS_DEVELOPMENT) {
  console.log('🔧 Entorno: DESARROLLO')
  console.log('🔧 API URL:', API_URL)
} else {
  console.log('🌐 Entorno: PRODUCCIÓN')
  console.log('🌐 API URL:', API_URL)
  if (!import.meta.env.VITE_API_URL) {
    console.warn('⚠️ VITE_API_URL no configurada. Asegúrate de configurarla en Vercel.')
  }
}
