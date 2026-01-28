import React from 'react'
import { AlertCircle, RefreshCw } from 'lucide-react'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    // Actualiza el estado para que la siguiente renderización muestre la UI de error
    return { hasError: true }
  }

  componentDidCatch(error, errorInfo) {
    // Registra el error en la consola
    console.error('❌ Error capturado por ErrorBoundary:', error)
    console.error('❌ Error Info:', errorInfo)
    this.setState({
      error,
      errorInfo
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null, errorInfo: null })
    window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
          <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-8 max-w-2xl w-full">
            <div className="flex items-center gap-4 mb-4">
              <AlertCircle className="w-8 h-8 text-red-400" />
              <h1 className="text-2xl font-bold text-red-400">Error en la Aplicación</h1>
            </div>
            
            <p className="text-slate-300 mb-4">
              Ocurrió un error al cargar esta página. Esto puede deberse a:
            </p>
            
            <ul className="list-disc list-inside text-slate-300 mb-6 space-y-2">
              <li>Problemas de conexión con el backend</li>
              <li>Variables de entorno no configuradas</li>
              <li>Error en el código del componente</li>
            </ul>

            {this.state.error && (
              <div className="bg-slate-800 rounded-lg p-4 mb-4">
                <p className="text-red-400 font-semibold mb-2">Detalles del Error:</p>
                <p className="text-slate-300 text-sm font-mono break-all">
                  {this.state.error.toString()}
                </p>
              </div>
            )}

            <div className="flex gap-4">
              <button
                onClick={this.handleReset}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                <RefreshCw className="w-4 h-4" />
                Recargar Página
              </button>
              
              <button
                onClick={() => window.history.back()}
                className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
              >
                Volver Atrás
              </button>
            </div>

            <div className="mt-6 pt-6 border-t border-slate-700">
              <p className="text-slate-400 text-sm">
                💡 <strong>Sugerencia:</strong> Abre la consola del navegador (F12) para ver más detalles del error.
              </p>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
