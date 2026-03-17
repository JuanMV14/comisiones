/**
 * Cliente centralizado de Axios para todas las llamadas API
 * Maneja automáticamente la configuración de URL según el entorno
 */
import axios from 'axios'
import { API_URL } from '../utils/env'

// Crear instancia de axios con configuración base
const apiClient = axios.create({
  baseURL: API_URL || '/api', // Fallback a ruta relativa si no hay API_URL
  timeout: 30000, // 30 segundos de timeout
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor de request: si es FormData, no establecer Content-Type (Axios lo hace automáticamente)
apiClient.interceptors.request.use(
  (config) => {
    // Si el data es FormData, eliminar Content-Type para que Axios lo establezca automáticamente con el boundary
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor para manejar errores
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Error de red o CORS
      const apiUrl = API_URL || 'no configurada'
      console.error('❌ Error de conexión:', error.message)
      console.error('📍 URL del backend:', apiUrl)
      
      if (error.message.includes('Network Error') || error.code === 'ERR_NETWORK') {
        console.error('⚠️ No se puede conectar al backend. Verifica:')
        console.error('   1. Que el backend esté desplegado y funcionando')
        console.error('   2. Que VITE_API_URL esté configurada correctamente en producción')
        console.error('   3. Que CORS esté configurado en el backend')
        console.error('')
        console.error('🔧 Para solucionarlo:')
        console.error('   - Ve a Vercel Dashboard → Tu proyecto frontend')
        console.error('   - Settings → Environment Variables')
        console.error('   - Agrega: VITE_API_URL=https://tu-backend.vercel.app/api')
        console.error('   - Redesplegar el frontend')
      }
    } else {
      // Error de respuesta del servidor
      console.error('❌ Error del servidor:', error.response.status, error.response.statusText)
    }
    return Promise.reject(error)
  }
)

export default apiClient

// Exportar también la URL para compatibilidad
export { API_URL }
