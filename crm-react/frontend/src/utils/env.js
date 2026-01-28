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

// Log para debugging con información detallada
if (IS_DEVELOPMENT) {
  console.log('🔧 Entorno: DESARROLLO')
  console.log('🔧 API URL:', API_URL)
} else {
  console.log('🌐 Entorno: PRODUCCIÓN')
  console.log('🌐 API URL:', API_URL)
  
  // Debug detallado de variables de entorno
  console.log('🔍 Debug de variables de entorno:')
  console.log('   import.meta.env.VITE_API_URL:', import.meta.env.VITE_API_URL || 'NO DEFINIDA')
  console.log('   import.meta.env.MODE:', import.meta.env.MODE)
  console.log('   import.meta.env.PROD:', import.meta.env.PROD)
  console.log('   window.location.hostname:', typeof window !== 'undefined' ? window.location.hostname : 'N/A')
  
  if (!import.meta.env.VITE_API_URL) {
    console.error('❌ VITE_API_URL NO ESTÁ CONFIGURADA')
    console.error('')
    console.error('📋 VERIFICACIONES:')
    console.error('   1. Ve a Vercel Dashboard → Tu proyecto frontend')
    console.error('   2. Settings → Environment Variables')
    console.error('   3. Verifica que VITE_API_URL esté en el nivel de PROYECTO (no Team)')
    console.error('   4. Verifica que el valor sea: https://backend-navy-eight-27.vercel.app/api')
    console.error('   5. Verifica que esté marcada para: Production, Preview y Development')
    console.error('   6. IMPORTANTE: Después de agregar/cambiar, REDESPLEGAR el frontend')
    console.error('   7. Las variables de Vite solo están disponibles en BUILD TIME')
    console.error('')
    console.error('💡 SOLUCIÓN ALTERNATIVA:')
    console.error('   Si después de redesplegar sigue sin funcionar:')
    console.error('   - Elimina la variable')
    console.error('   - Guarda')
    console.error('   - Vuelve a agregarla')
    console.error('   - Redesplegar INMEDIATAMENTE')
  } else {
    console.log('✅ VITE_API_URL configurada correctamente:', import.meta.env.VITE_API_URL)
  }
}
