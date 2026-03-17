import React, { useState, useEffect } from 'react'
import { TrendingUp, DollarSign, Users, Package, ArrowUpRight, Loader2, FileText, X, Target, Calendar, Plus, Edit2, Trash2, Save } from 'lucide-react'
import { getDashboardMetrics, getSalesChart, getClientesClave, getMesesDisponibles } from '../api/dashboard'
import { getMetricsDirecto } from '../utils/supabaseClient'
import { getPresupuestos, crearPresupuesto, actualizarPresupuesto, eliminarPresupuesto, getPresupuestosMarcas, crearPresupuestoMarca, actualizarPresupuestoMarca } from '../api/presupuestos'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

// Función de utilidad para formatear moneda (debe estar fuera del componente para que MetricCard pueda usarla)
const formatCurrency = (val) => {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0
  }).format(val || 0)
}

const DashboardView = () => {
  const [metrics, setMetrics] = useState({
    totalVentas: 0,
    comisiones: 0,
    clientesActivos: 0,
    pedidosMes: 0,
    metaVentas: 0,
    progresoMeta: 0,
    faltanteMeta: 0,
    facturasDetalle: []
  })
  const [mostrarDetalleFacturas, setMostrarDetalleFacturas] = useState(false)
  const [ventasMensuales, setVentasMensuales] = useState([])
  const [comisionesMensuales, setComisionesMensuales] = useState([])
  const [clientesClave, setClientesClave] = useState([])
  const [mesesDisponibles, setMesesDisponibles] = useState([])
  const [mesSeleccionado, setMesSeleccionado] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [userName, setUserName] = useState('Usuario') // Estado para el nombre del usuario
  const [mostrarPresupuestos, setMostrarPresupuestos] = useState(false)
  const [presupuestos, setPresupuestos] = useState([])
  const [loadingPresupuestos, setLoadingPresupuestos] = useState(false)
  const [presupuestoEditando, setPresupuestoEditando] = useState(null)
  const [formPresupuesto, setFormPresupuesto] = useState({
    mes: '',
    meta_ventas: '',
    meta_clientes_nuevos: ''
  })
  const [presupuestoMarcas, setPresupuestoMarcas] = useState(null)
  const [loadingPresupuestosMarcas, setLoadingPresupuestosMarcas] = useState(false)
  const [mostrarPresupuestosMarcas, setMostrarPresupuestosMarcas] = useState(false)
  const [formPresupuestoMarca, setFormPresupuestoMarca] = useState({
    meta_ventas: ''
  })

  useEffect(() => {
    // Obtener nombre del usuario desde localStorage o usar predeterminado
    const storedUser = localStorage.getItem('crm_user_name') || 'Usuario'
    setUserName(storedUser)
    
    // Cargar meses disponibles primero
    loadMesesDisponibles()
  }, [])

  // Recargar datos cuando cambie el mes seleccionado (incluye cuando es null para "Ver todo")
  useEffect(() => {
    loadDashboardData()
    if (mesSeleccionado) {
      cargarPresupuestosMarcas()
    }
  }, [mesSeleccionado])

  const loadMesesDisponibles = async () => {
    try {
      const mesesData = await getMesesDisponibles().catch(err => {
        console.warn('Error cargando meses:', err)
        return { meses: [] }
      })
      
      if (mesesData && mesesData.meses && mesesData.meses.length > 0) {
        setMesesDisponibles(mesesData.meses)
        // Seleccionar el mes actual por defecto (siempre el primero de la lista que es el más reciente)
        if (!mesSeleccionado) {
          // El backend ya ordena los meses de más reciente a más antiguo
          // y siempre incluye el mes actual, así que el primero es el mes actual
          setMesSeleccionado(mesesData.meses[0].valor)
        }
      }
    } catch (error) {
      console.error('Error cargando meses disponibles:', error)
    }
  }

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 Iniciando carga de datos del dashboard...')
      
      // Intentar backend primero, si falla usar Supabase directo
      let data = null
      let salesData = null
      let clientesData = null
      
      try {
        console.log('📡 Intentando conectar con backend...', mesSeleccionado ? `(Mes: ${mesSeleccionado})` : '')
        const [metricsData, salesChartData, clientesClaveData] = await Promise.all([
          getDashboardMetrics(mesSeleccionado),
          getSalesChart(),
          getClientesClave(mesSeleccionado)
        ])
        data = metricsData
        salesData = salesChartData
        clientesData = clientesClaveData
        
        console.log('✅ Datos cargados desde backend', { mes: mesSeleccionado, metrics: data })
      } catch (backendError) {
        console.warn('⚠️ Backend no disponible, usando conexión directa a Supabase:', backendError)
        data = await getMetricsDirecto()
        // Si falla el backend, no podemos obtener gráficos ni clientes clave
        salesData = { ventas_mensuales: [], comisiones_mensuales: [] }
        clientesData = { clientes_clave: [] }
      }
      
      if (data) {
        setMetrics({
          totalVentas: data.totalVentas || 0,
          comisiones: data.comisiones || 0,
          clientesActivos: data.clientesActivos || 0,
          pedidosMes: data.pedidosMes || 0,
          metaVentas: data.metaVentas || 0,
          progresoMeta: data.progresoMeta || 0,
          faltanteMeta: data.faltanteMeta || 0,
          facturasDetalle: data.facturasDetalle || []
        })
      }
      
      if (salesData) {
        setVentasMensuales(salesData.ventas_mensuales || [])
        setComisionesMensuales(salesData.comisiones_mensuales || [])
      }
      
      if (clientesData) {
        // Asegurar que clientes_clave sea un array
        const clientesArray = Array.isArray(clientesData) ? clientesData : (clientesData.clientes_clave || [])
        setClientesClave(clientesArray)
        console.log('✅ Clientes clave cargados:', clientesArray.length, 'para el mes:', mesSeleccionado)
      }
    } catch (error) {
      console.error('❌ Error loading dashboard:', error)
      setError(`Error al cargar los datos: ${error.message}. Abre la consola (F12) para más detalles.`)
    } finally {
      setLoading(false)
    }
  }

  // Función para obtener iniciales del nombre
  const getInitials = (name) => {
    if (!name || name === 'Usuario') return 'U'
    const palabras = name.trim().split(' ')
    if (palabras.length >= 2) {
      return (palabras[0][0] + palabras[1][0]).toUpperCase()
    }
    return name.substring(0, 2).toUpperCase()
  }


  const cargarPresupuestos = async () => {
    try {
      setLoadingPresupuestos(true)
      const data = await getPresupuestos()
      setPresupuestos(data.presupuestos || [])
    } catch (error) {
      console.error('Error cargando presupuestos:', error)
    } finally {
      setLoadingPresupuestos(false)
    }
  }

  const cargarPresupuestosMarcas = async () => {
    if (!mesSeleccionado) return
    
    try {
      setLoadingPresupuestosMarcas(true)
      const data = await getPresupuestosMarcas(mesSeleccionado)
      setPresupuestoMarcas(data)
    } catch (error) {
      console.error('Error cargando presupuestos por marca:', error)
      setPresupuestoMarcas(null)
    } finally {
      setLoadingPresupuestosMarcas(false)
    }
  }

  const handleGuardarPresupuestoMarca = async () => {
    if (!mesSeleccionado || !formPresupuestoMarca.meta_ventas) {
      alert('Por favor ingresa la meta de ventas')
      return
    }

    try {
      setLoadingPresupuestosMarcas(true)
      
      const data = {
        mes: mesSeleccionado,
        meta_ventas: parseFloat(formPresupuestoMarca.meta_ventas) || 0
      }

      if (presupuestoMarcas && presupuestoMarcas.meta_ventas_total > 0) {
        await actualizarPresupuestoMarca(mesSeleccionado, { meta_ventas: data.meta_ventas })
      } else {
        await crearPresupuestoMarca(data)
      }

      await cargarPresupuestosMarcas()
      setFormPresupuestoMarca({
        meta_ventas: ''
      })
    } catch (error) {
      console.error('Error guardando presupuesto por marca:', error)
      alert(error.response?.data?.detail || 'Error al guardar el presupuesto por marca')
    } finally {
      setLoadingPresupuestosMarcas(false)
    }
  }

  const handleAbrirPresupuestos = () => {
    setMostrarPresupuestos(true)
    cargarPresupuestos()
  }

  const handleNuevoPresupuesto = () => {
    const mesActual = new Date().toISOString().slice(0, 7) // YYYY-MM
    setPresupuestoEditando(null)
    setFormPresupuesto({
      mes: mesActual,
      meta_ventas: '',
      meta_clientes_nuevos: ''
    })
  }

  const handleEditarPresupuesto = (presupuesto) => {
    setPresupuestoEditando(presupuesto.mes)
    setFormPresupuesto({
      mes: presupuesto.mes,
      meta_ventas: presupuesto.meta_ventas || '',
      meta_clientes_nuevos: presupuesto.meta_clientes_nuevos || ''
    })
  }

  const handleGuardarPresupuesto = async () => {
    try {
      setLoadingPresupuestos(true)
      
      const data = {
        mes: formPresupuesto.mes,
        meta_ventas: parseFloat(formPresupuesto.meta_ventas) || 0,
        meta_clientes_nuevos: parseInt(formPresupuesto.meta_clientes_nuevos) || 0
      }

      if (presupuestoEditando) {
        await actualizarPresupuesto(presupuestoEditando, data)
      } else {
        await crearPresupuesto(data)
      }

      await cargarPresupuestos()
      setPresupuestoEditando(null)
      setFormPresupuesto({
        mes: '',
        meta_ventas: '',
        meta_clientes_nuevos: ''
      })
    } catch (error) {
      console.error('Error guardando presupuesto:', error)
      alert(error.response?.data?.detail || 'Error al guardar el presupuesto')
    } finally {
      setLoadingPresupuestos(false)
    }
  }

  const handleEliminarPresupuesto = async (mes) => {
    if (!confirm(`¿Estás seguro de eliminar el presupuesto de ${mes}?`)) {
      return
    }

    try {
      setLoadingPresupuestos(true)
      await eliminarPresupuesto(mes)
      await cargarPresupuestos()
    } catch (error) {
      console.error('Error eliminando presupuesto:', error)
      alert(error.response?.data?.detail || 'Error al eliminar el presupuesto')
    } finally {
      setLoadingPresupuestos(false)
    }
  }

  const formatearMes = (mes) => {
    if (!mes) return ''
    const [año, mesNum] = mes.split('-')
    const meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    return `${meses[parseInt(mesNum) - 1]} ${año}`
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando datos...</p>
        </div>
      </div>
    )
  }

  if (error) {
    const isProduction = window.location.hostname !== 'localhost' && !window.location.hostname.startsWith('127.0.0.1')
    const hasApiUrl = import.meta.env.VITE_API_URL
    
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md">
          <p className="text-red-400 mb-2">⚠️ Error</p>
          <p className="text-slate-300 text-sm mb-4">{error}</p>
          
          {isProduction && !hasApiUrl && (
            <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 mb-4 text-left">
              <p className="text-yellow-400 text-sm font-semibold mb-2">🔧 Configuración Requerida:</p>
              <p className="text-slate-300 text-xs mb-2">El backend no está configurado en producción.</p>
              <ol className="text-slate-300 text-xs list-decimal list-inside space-y-1">
                <li>Ve a Vercel Dashboard → Tu proyecto frontend</li>
                <li>Settings → Environment Variables</li>
                <li>Agrega: <code className="bg-slate-800 px-1 rounded">VITE_API_URL=https://tu-backend.vercel.app/api</code></li>
                <li>Redesplegar el frontend</li>
              </ol>
            </div>
          )}
          
          <button 
            onClick={loadDashboardData} 
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Panel del Vendedor</h2>
          <p className="text-sm text-slate-400">Resumen de tu actividad comercial</p>
        </div>
        <button
          onClick={handleAbrirPresupuestos}
          className="flex items-center gap-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors"
        >
          <Target className="w-4 h-4" />
          Gestionar Presupuestos
        </button>
        <div className="flex items-center gap-3">
          <select 
            value={mesSeleccionado === null ? 'todos' : (mesSeleccionado || '')}
            onChange={(e) => {
              const valor = e.target.value
              // Si selecciona "todos", establecer null para que no filtre por mes
              setMesSeleccionado(valor === 'todos' ? null : valor)
            }}
            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="todos">📊 Ver Todo</option>
            {mesesDisponibles.length > 0 ? (
              mesesDisponibles.map((mes) => (
                <option key={mes.valor} value={mes.valor}>
                  {mes.nombre}
                </option>
              ))
            ) : (
              <>
                <option value="">Cargando meses...</option>
                <option value="2024-11">Noviembre 2024</option>
                <option value="2024-10">Octubre 2024</option>
              </>
            )}
          </select>
        </div>
      </div>

      {/* Barra de Progreso de Meta */}
      {metrics.metaVentas > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Progreso de Meta de Ventas</h3>
              <p className="text-sm text-slate-400">
                {mesSeleccionado === null ? '📊 Ver Todo' : (mesesDisponibles.find(m => m.valor === mesSeleccionado)?.nombre || mesSeleccionado || 'Mes actual')}
              </p>
            </div>
            <div className="text-right">
              <p className="text-2xl font-bold text-white">{formatCurrency(metrics.totalVentas)}</p>
              <p className="text-sm text-slate-400">de {formatCurrency(metrics.metaVentas)}</p>
            </div>
          </div>
          
          {/* Barra de progreso */}
          <div className="mb-4">
            <div className="w-full bg-slate-700/50 rounded-full h-6 overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 flex items-center justify-center ${
                  metrics.progresoMeta >= 100
                    ? 'bg-emerald-500'
                    : metrics.progresoMeta >= 75
                    ? 'bg-blue-500'
                    : metrics.progresoMeta >= 50
                    ? 'bg-amber-500'
                    : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, Math.max(0, metrics.progresoMeta))}%` }}
              >
                {metrics.progresoMeta > 10 && (
                  <span className="text-xs font-semibold text-white">
                    {metrics.progresoMeta.toFixed(1)}%
                  </span>
                )}
              </div>
            </div>
            {metrics.progresoMeta < 10 && (
              <p className="text-xs text-slate-400 mt-1 text-center">
                {metrics.progresoMeta.toFixed(1)}% completado
              </p>
            )}
          </div>
          
          {/* Información adicional */}
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div className="bg-slate-900/50 rounded-lg p-3">
              <p className="text-xs text-slate-400 mb-1">Faltante</p>
              <p className="text-lg font-semibold text-amber-400">
                {formatCurrency(metrics.faltanteMeta)}
              </p>
            </div>
            <div className="bg-slate-900/50 rounded-lg p-3">
              <p className="text-xs text-slate-400 mb-1">Facturas del Mes</p>
              <p className="text-lg font-semibold text-white">
                {metrics.pedidosMes || metrics.facturasDetalle?.length || 0}
              </p>
            </div>
          </div>
          
          {/* Botón para ver detalle */}
          {metrics.facturasDetalle && metrics.facturasDetalle.length > 0 && (
            <div className="mt-4">
              <button
                onClick={() => setMostrarDetalleFacturas(!mostrarDetalleFacturas)}
                className="text-sm text-blue-400 hover:text-blue-300 flex items-center gap-2 transition-colors"
              >
                <FileText className="w-4 h-4" />
                {mostrarDetalleFacturas ? 'Ocultar' : 'Ver'} detalle de facturas ({metrics.facturasDetalle.length})
              </button>
            </div>
          )}
        </div>
      )}

      {/* Modal de Detalle de Facturas */}
      {mostrarDetalleFacturas && metrics.facturasDetalle && metrics.facturasDetalle.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">
              Detalle de Facturas - {formatCurrency(metrics.totalVentas)}
            </h3>
            <button
              onClick={() => setMostrarDetalleFacturas(false)}
              className="text-slate-400 hover:text-white transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50">
                <tr>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-400 uppercase">Cliente</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-400 uppercase">Fecha</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-400 uppercase">Factura</th>
                  <th className="px-4 py-2 text-right text-xs font-medium text-slate-400 uppercase">Valor</th>
                  <th className="px-4 py-2 text-left text-xs font-medium text-slate-400 uppercase">Tipo</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {metrics.facturasDetalle.map((factura, idx) => {
                  const esDevolucion = factura.valor_transaccion < 0
                  const mismoClienteAnterior = idx > 0 && metrics.facturasDetalle[idx - 1].cliente === factura.cliente
                  
                  return (
                    <tr 
                      key={`${factura.id}-${factura.tipo}-${idx}`} 
                      className={`hover:bg-slate-800/30 ${esDevolucion ? 'bg-red-500/5' : ''}`}
                    >
                      <td className="px-4 py-3 text-sm text-white">
                        {!mismoClienteAnterior && (
                          <div className="font-medium">{factura.cliente}</div>
                        )}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {factura.fecha_factura ? (() => {
                          try {
                            let date
                            const dateStr = factura.fecha_factura
                            if (dateStr.includes('-')) {
                              const parts = dateStr.split('T')[0].split('-')
                              if (parts.length === 3) {
                                date = new Date(parseInt(parts[0]), parseInt(parts[1]) - 1, parseInt(parts[2]))
                              } else {
                                date = new Date(dateStr)
                              }
                            } else {
                              date = new Date(dateStr)
                            }
                            if (isNaN(date.getTime())) return 'N/A'
                            return date.toLocaleDateString('es-CO', { 
                              year: 'numeric', 
                              month: '2-digit', 
                              day: '2-digit' 
                            })
                          } catch {
                            return 'N/A'
                          }
                        })() : 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-slate-300">
                        {factura.factura}
                        {factura.pedido && factura.pedido !== 'N/A' && (
                          <div className="text-xs text-slate-500">Pedido: {factura.pedido}</div>
                        )}
                      </td>
                      <td className={`px-4 py-3 text-sm text-right font-semibold ${
                        esDevolucion ? 'text-red-400' : 'text-emerald-400'
                      }`}>
                        {esDevolucion ? '-' : ''}{formatCurrency(Math.abs(factura.valor_transaccion))}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {esDevolucion ? (
                          <span className="inline-flex px-2 py-1 rounded text-xs font-medium bg-red-500/20 text-red-400">
                            Devolución
                          </span>
                        ) : (
                          <span className="inline-flex px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-400">
                            Venta
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
              <tfoot className="bg-slate-900/50">
                <tr>
                  <td colSpan="3" className="px-4 py-3 text-sm font-bold text-white text-right">
                    Total general:
                  </td>
                  <td className="px-4 py-3 text-sm font-bold text-emerald-400 text-right">
                    {formatCurrency(metrics.totalVentas)}
                  </td>
                  <td className="px-4 py-3"></td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Presupuesto por Marcas (EFFIX, MOTEK USA, KBS, TOYAMA) */}
      {mesSeleccionado && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-lg font-semibold text-white">Presupuesto por Marcas</h3>
              <p className="text-sm text-slate-400">
                {mesesDisponibles.find(m => m.valor === mesSeleccionado)?.nombre || mesSeleccionado} - EFFIX, MOTEK USA, KBS, TOYAMA
              </p>
            </div>
            <button
              onClick={() => setMostrarPresupuestosMarcas(!mostrarPresupuestosMarcas)}
              className="flex items-center gap-2 px-3 py-1.5 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors text-sm"
            >
              <Target className="w-4 h-4" />
              {mostrarPresupuestosMarcas ? 'Ocultar' : 'Gestionar'}
            </button>
          </div>

          {loadingPresupuestosMarcas ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-purple-500 mr-3" />
              <p className="text-slate-400">Cargando presupuesto por marca...</p>
            </div>
          ) : presupuestoMarcas ? (
            <div className="space-y-4">
              {/* Presupuesto Total */}
              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-sm font-semibold text-white">Presupuesto Total (4 Marcas)</h4>
                  {presupuestoMarcas.meta_ventas_total > 0 && (
                    <button
                      onClick={() => {
                        setFormPresupuestoMarca({
                          meta_ventas: presupuestoMarcas.meta_ventas_total.toString()
                        })
                      }}
                      className="p-1 text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
                      title="Editar presupuesto"
                    >
                      <Edit2 className="w-3 h-3" />
                    </button>
                  )}
                </div>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-sm text-slate-400">Meta Total:</span>
                    <span className="text-lg font-bold text-white">{formatCurrency(presupuestoMarcas.meta_ventas_total)}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-slate-400">Ventas Totales:</span>
                    <span className="text-lg font-bold text-emerald-400">{formatCurrency(presupuestoMarcas.ventas_totales_marcas)}</span>
                  </div>
                  {presupuestoMarcas.meta_ventas_total > 0 && (
                    <>
                      <div className="w-full bg-slate-700/50 rounded-full h-3 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 flex items-center justify-center ${
                            presupuestoMarcas.progreso_total >= 100
                              ? 'bg-emerald-500'
                              : presupuestoMarcas.progreso_total >= 75
                              ? 'bg-blue-500'
                              : presupuestoMarcas.progreso_total >= 50
                              ? 'bg-amber-500'
                              : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.min(100, Math.max(0, presupuestoMarcas.progreso_total))}%` }}
                        >
                          {presupuestoMarcas.progreso_total > 10 && (
                            <span className="text-xs font-semibold text-white">
                              {presupuestoMarcas.progreso_total.toFixed(1)}%
                            </span>
                          )}
                        </div>
                      </div>
                      {presupuestoMarcas.progreso_total < 10 && (
                        <p className="text-xs text-slate-400 text-center">
                          {presupuestoMarcas.progreso_total.toFixed(1)}% completado
                        </p>
                      )}
                      <div className="grid grid-cols-2 gap-4 mt-3">
                        <div>
                          <span className="text-xs text-slate-400">Progreso:</span>
                          <p className={`text-sm font-semibold ${presupuestoMarcas.progreso_total >= 100 ? 'text-emerald-400' : 'text-white'}`}>
                            {presupuestoMarcas.progreso_total.toFixed(1)}%
                          </p>
                        </div>
                        <div>
                          <span className="text-xs text-slate-400">Faltante:</span>
                          <p className="text-sm font-semibold text-amber-400">{formatCurrency(presupuestoMarcas.faltante_total)}</p>
                        </div>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Desglose por Marca */}
              {presupuestoMarcas.ventas_por_marca && (
                <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                  <h4 className="text-sm font-semibold text-white mb-3">Desglose por Marca</h4>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {presupuestoMarcas.marcas.map((marca) => {
                      const ventasMarca = presupuestoMarcas.ventas_por_marca[marca] || 0
                      const porcentajeDelTotal = presupuestoMarcas.ventas_totales_marcas > 0 
                        ? (ventasMarca / presupuestoMarcas.ventas_totales_marcas) * 100 
                        : 0
                      
                      return (
                        <div key={marca} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/30">
                          <p className="text-xs font-semibold text-slate-300 mb-2">{marca}</p>
                          <p className="text-sm font-bold text-emerald-400 mb-1">{formatCurrency(ventasMarca)}</p>
                          {presupuestoMarcas.ventas_totales_marcas > 0 && (
                            <p className="text-xs text-slate-400">{porcentajeDelTotal.toFixed(1)}% del total</p>
                          )}
                        </div>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-slate-400 text-sm">No hay presupuesto configurado para este mes</p>
            </div>
          )}

          {/* Formulario para editar presupuesto */}
          {mostrarPresupuestosMarcas && (
            <div className="mt-6 bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
              <h4 className="text-sm font-semibold text-white mb-4">Gestionar Presupuesto Total por Marcas</h4>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-2">
                    Meta de Ventas Total (COP) - EFFIX, MOTEK USA, KBS, TOYAMA
                  </label>
                  <input
                    type="number"
                    value={formPresupuestoMarca.meta_ventas}
                    onChange={(e) => setFormPresupuestoMarca({ ...formPresupuestoMarca, meta_ventas: e.target.value })}
                    placeholder={presupuestoMarcas?.meta_ventas_total?.toString() || "0"}
                    className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-purple-500"
                  />
                  <p className="text-xs text-slate-400 mt-1">
                    Este presupuesto es para las 4 marcas combinadas: EFFIX, MOTEK USA, KBS y TOYAMA
                  </p>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleGuardarPresupuestoMarca}
                    disabled={loadingPresupuestosMarcas || !formPresupuestoMarca.meta_ventas}
                    className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 text-sm"
                  >
                    <Save className="w-4 h-4" />
                    {presupuestoMarcas?.meta_ventas_total > 0 ? 'Actualizar' : 'Guardar'}
                  </button>
                  {presupuestoMarcas?.meta_ventas_total > 0 && (
                    <button
                      onClick={() => {
                        setFormPresupuestoMarca({ meta_ventas: '' })
                      }}
                      className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors text-sm"
                    >
                      Cancelar
                    </button>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Métricas Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Ventas del Mes"
          value={metrics.totalVentas}
          icon={DollarSign}
          trend="+12.5%"
          trendUp={true}
          subtitle="Facturación del mes"
        />
        <MetricCard
          title="Comisión Estimada"
          value={metrics.comisiones}
          icon={TrendingUp}
          trend="+8.2%"
          trendUp={true}
          subtitle="Este mes"
        />
        <MetricCard
          title="Clientes Activos"
          value={metrics.clientesActivos}
          icon={Users}
          trend="+5"
          trendUp={true}
        />
        <MetricCard
          title="Pedidos del Mes"
          value={metrics.pedidosMes}
          icon={Package}
          trend="+15%"
          trendUp={true}
        />
      </div>

      {/* Clientes Clave y Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Clientes Clave */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Clientes Clave</h3>
            <span className="text-xs text-slate-400">
              {mesSeleccionado 
                ? (mesesDisponibles.find(m => m.valor === mesSeleccionado)?.nombre_corto || mesSeleccionado)
                : 'Todos los meses'}
            </span>
          </div>
          <div className="space-y-4">
            {clientesClave.length > 0 ? (
              clientesClave.slice(0, 3).map((cliente, idx) => (
                <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
                      {cliente.iniciales || cliente.nombre?.substring(0, 2).toUpperCase() || 'N/A'}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-white">{cliente.cliente || cliente.nombre || 'Sin nombre'}</p>
                      <p className="text-xs text-slate-400">{cliente.ultima_compra || cliente.ultimaCompra || 'N/A'}</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-semibold text-white">
                      ${((cliente.total_ventas || cliente.ventas || 0) / 1000000).toFixed(1)}M
                    </p>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-slate-500 text-center py-8">
                {mesSeleccionado 
                  ? `No hay clientes clave para ${mesesDisponibles.find(m => m.valor === mesSeleccionado)?.nombre || mesSeleccionado}`
                  : 'No hay clientes clave disponibles'}
              </p>
            )}
          </div>
        </div>

        {/* Gráfico de Ventas Mensuales */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Ventas Últimos 6 Meses</h3>
          {ventasMensuales.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={ventasMensuales}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis 
                  dataKey="mes" 
                  stroke="#9CA3AF"
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                />
                <YAxis 
                  stroke="#9CA3AF"
                  tick={{ fill: '#9CA3AF', fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000000).toFixed(0)}M`}
                />
                <Tooltip 
                  contentStyle={{ 
                    backgroundColor: '#1E293B', 
                    border: '1px solid #334155',
                    borderRadius: '8px',
                    color: '#F1F5F9'
                  }}
                  formatter={(value) => `$${value.toLocaleString('es-CO')}`}
                />
                <Bar dataKey="ventas" fill="#3B82F6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-48 flex items-center justify-center">
              <p className="text-slate-500">No hay datos de ventas disponibles</p>
            </div>
          )}
        </div>
      </div>

      {/* Gráfico de Comisiones */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-semibold text-white mb-4">Comisiones por Mes</h3>
        {comisionesMensuales.length > 0 ? (
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={comisionesMensuales}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="mes" 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
              />
              <YAxis 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E293B', 
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#F1F5F9'
                }}
                formatter={(value) => `$${value.toLocaleString('es-CO')}`}
              />
              <Bar dataKey="comisiones" fill="#10B981" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-48 flex items-center justify-center">
            <p className="text-slate-500">No hay datos de comisiones disponibles</p>
          </div>
        )}
      </div>

      {/* Modal de Presupuestos */}
      {mostrarPresupuestos && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Target className="w-6 h-6 text-purple-400" />
                  <h3 className="text-xl font-semibold text-white">Gestión de Presupuestos Mensuales</h3>
                </div>
                <button
                  onClick={() => {
                    setMostrarPresupuestos(false)
                    setPresupuestoEditando(null)
                    setFormPresupuesto({
                      mes: '',
                      meta_ventas: '',
                      meta_clientes_nuevos: ''
                    })
                  }}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <div className="p-6 space-y-6">
              {/* Formulario de Presupuesto */}
              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                <div className="flex items-center justify-between mb-4">
                  <h4 className="text-lg font-semibold text-white">
                    {presupuestoEditando ? 'Editar Presupuesto' : 'Nuevo Presupuesto'}
                  </h4>
                  {!presupuestoEditando && (
                    <button
                      onClick={handleNuevoPresupuesto}
                      className="flex items-center gap-2 px-3 py-1.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors text-sm"
                    >
                      <Plus className="w-4 h-4" />
                      Nuevo
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Mes (YYYY-MM)
                    </label>
                    <input
                      type="month"
                      value={formPresupuesto.mes}
                      onChange={(e) => setFormPresupuesto({ ...formPresupuesto, mes: e.target.value })}
                      disabled={!!presupuestoEditando}
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Meta de Ventas (COP)
                    </label>
                    <input
                      type="number"
                      value={formPresupuesto.meta_ventas}
                      onChange={(e) => setFormPresupuesto({ ...formPresupuesto, meta_ventas: e.target.value })}
                      placeholder="0"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Meta de Clientes con Ventas
                    </label>
                    <input
                      type="number"
                      value={formPresupuesto.meta_clientes_nuevos}
                      onChange={(e) => setFormPresupuesto({ ...formPresupuesto, meta_clientes_nuevos: e.target.value })}
                      placeholder="0"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  {/* Campo de Meta de Comisiones comentado porque no existe en la BD
                  <div>
                    <label className="block text-sm font-semibold text-slate-300 mb-2">
                      Meta de Comisiones (COP)
                    </label>
                    <input
                      type="number"
                      value={formPresupuesto.meta_comisiones}
                      onChange={(e) => setFormPresupuesto({ ...formPresupuesto, meta_comisiones: e.target.value })}
                      placeholder="0"
                      className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                    />
                  </div>
                  */}
                </div>

                {formPresupuesto.mes && (
                  <div className="mt-4 flex gap-3">
                    <button
                      onClick={handleGuardarPresupuesto}
                      disabled={loadingPresupuestos || !formPresupuesto.mes}
                      className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50"
                    >
                      <Save className="w-4 h-4" />
                      {presupuestoEditando ? 'Actualizar' : 'Guardar'}
                    </button>
                    {presupuestoEditando && (
                      <button
                        onClick={() => {
                          setPresupuestoEditando(null)
                          setFormPresupuesto({
                            mes: '',
                            meta_ventas: '',
                            meta_clientes_nuevos: ''
                          })
                        }}
                        className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                      >
                        Cancelar
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Lista de Presupuestos */}
              <div>
                <h4 className="text-lg font-semibold text-white mb-4">Presupuestos Registrados</h4>
                {loadingPresupuestos ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-500 mr-3" />
                    <p className="text-slate-400">Cargando presupuestos...</p>
                  </div>
                ) : presupuestos.length === 0 ? (
                  <div className="text-center py-8 bg-slate-900/50 rounded-lg border border-slate-700/50">
                    <Calendar className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                    <p className="text-slate-400">No hay presupuestos registrados</p>
                    <p className="text-xs text-slate-500 mt-2">Crea uno nuevo usando el formulario de arriba</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {presupuestos.map((presupuesto) => (
                      <div
                        key={presupuesto.mes}
                        className={`bg-slate-900/50 rounded-lg p-4 border ${
                          presupuestoEditando === presupuesto.mes
                            ? 'border-purple-500/50 bg-purple-500/10'
                            : 'border-slate-700/50'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <Calendar className="w-5 h-5 text-purple-400" />
                              <h5 className="text-lg font-semibold text-white">
                                {formatearMes(presupuesto.mes)}
                              </h5>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                              <div>
                                <p className="text-xs text-slate-400 mb-1">Meta de Ventas</p>
                                <p className="text-sm font-semibold text-emerald-400">
                                  {formatCurrency(presupuesto.meta_ventas || 0)}
                                </p>
                              </div>
                              <div>
                                <p className="text-xs text-slate-400 mb-1">Meta de Clientes con Ventas</p>
                                <p className="text-sm font-semibold text-blue-400">
                                  {presupuesto.meta_clientes_nuevos || 0}
                                </p>
                              </div>
                              {/* Campo de Meta de Comisiones comentado porque no existe en la BD
                              <div>
                                <p className="text-xs text-slate-400 mb-1">Meta de Comisiones</p>
                                <p className="text-sm font-semibold text-purple-400">
                                  {formatCurrency(presupuesto.meta_comisiones || 0)}
                                </p>
                              </div>
                              */}
                            </div>
                          </div>
                          <div className="flex items-center gap-2 ml-4">
                            <button
                              onClick={() => handleEditarPresupuesto(presupuesto)}
                              className="p-2 text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                              title="Editar"
                            >
                              <Edit2 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => handleEliminarPresupuesto(presupuesto.mes)}
                              className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                              title="Eliminar"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

const MetricCard = ({ title, value, icon: Icon, trend, trendUp, subtitle }) => {

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-blue-500/10 rounded-lg">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
        {trend && (
          <span className={`text-xs flex items-center gap-1 ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
            <ArrowUpRight className="w-3 h-3" /> {trend}
          </span>
        )}
      </div>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">
        {typeof value === 'number' && value > 1000 ? formatCurrency(value) : value}
      </p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  )
}

// Exportar función para obtener iniciales (para usar en otros componentes)
export const getUserInitials = (name) => {
  if (!name || name === 'Usuario') return 'U'
  const palabras = name.trim().split(' ')
  if (palabras.length >= 2) {
    return (palabras[0][0] + palabras[1][0]).toUpperCase()
  }
  return name.substring(0, 2).toUpperCase()
}

export default DashboardView
