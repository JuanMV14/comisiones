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

// Interceptor para manejar errores
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (!error.response) {
      // Error de red o CORS
      console.error('❌ Error de conexión:', error.message)
      if (error.message.includes('Network Error') || error.code === 'ERR_NETWORK') {
        console.error('⚠️ No se puede conectar al backend. Verifica:')
        console.error('   1. Que el backend esté desplegado y funcionando')
        console.error('   2. Que VITE_API_URL esté configurada correctamente en producción')
        console.error('   3. Que CORS esté configurado en el backend')
      }
    }
    return Promise.reject(error)
  }
)

export default apiClient

// Exportar también la URL para compatibilidad
export { API_URL }
