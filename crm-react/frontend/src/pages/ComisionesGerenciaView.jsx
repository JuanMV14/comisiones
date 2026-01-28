import React, { useState, useEffect } from 'react'
import { TrendingUp, DollarSign, FileText, BarChart3, Loader2, AlertCircle, Calendar, CheckCircle, Clock, ChevronDown, ChevronUp, Eye } from 'lucide-react'
import { getComisionesMensuales, getFacturasPorMes } from '../api/analytics'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts'

const ComisionesGerenciaView = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [mesExpandido, setMesExpandido] = useState(null)
  const [facturasMes, setFacturasMes] = useState({})
  const [cargandoFacturas, setCargandoFacturas] = useState({})

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      setError(null)
      const resultado = await getComisionesMensuales()
      setData(resultado)
    } catch (err) {
      console.error('Error cargando comisiones mensuales:', err)
      setError(`Error al cargar los datos: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(val || 0)
  }

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'N/A') return 'N/A'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('es-CO', { year: 'numeric', month: '2-digit', day: '2-digit' })
    } catch {
      return dateStr
    }
  }

  const toggleMes = async (mes) => {
    if (mesExpandido === mes) {
      setMesExpandido(null)
    } else {
      setMesExpandido(mes)
      if (!facturasMes[mes]) {
        setCargandoFacturas({ ...cargandoFacturas, [mes]: true })
        try {
          const resultado = await getFacturasPorMes(mes)
          setFacturasMes({ ...facturasMes, [mes]: resultado.facturas || [] })
        } catch (err) {
          console.error('Error cargando facturas:', err)
          setFacturasMes({ ...facturasMes, [mes]: [] })
        } finally {
          setCargandoFacturas({ ...cargandoFacturas, [mes]: false })
        }
      }
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando tus comisiones...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md">
          <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-4" />
          <p className="text-red-400 mb-2">⚠️ Error</p>
          <p className="text-slate-300 text-sm">{error}</p>
          <button 
            onClick={cargarDatos} 
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Reintentar
          </button>
        </div>
      </div>
    )
  }

  const resumen = data?.resumen || {}
  const comisionesMensuales = data?.comisiones_mensuales || []

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Mis Comisiones</h2>
          <p className="text-sm text-slate-400">Tus comisiones mes tras mes</p>
        </div>
      </div>

      {/* KPIs Principales */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          icon={CheckCircle}
          title="Comisiones Pagadas"
          value={resumen.total_comisiones_pagadas || 0}
          subtitle={`${resumen.num_facturas_pagadas || 0} facturas pagadas`}
          color="bg-emerald-500/10 text-emerald-400"
          isCurrency
        />
        <MetricCard
          icon={Clock}
          title="Comisiones Pendientes"
          value={resumen.total_comisiones_pendientes || 0}
          subtitle={`${resumen.num_facturas_pendientes || 0} facturas pendientes`}
          color="bg-amber-500/10 text-amber-400"
          isCurrency
        />
        <MetricCard
          icon={TrendingUp}
          title="Total Comisiones"
          value={(resumen.total_comisiones_pagadas || 0) + (resumen.total_comisiones_pendientes || 0)}
          subtitle="Pagadas + Pendientes"
          color="bg-blue-500/10 text-blue-400"
          isCurrency
        />
      </div>

      {/* Gráfico de Comisiones Mes a Mes */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Comisiones Mes a Mes
        </h3>
        {comisionesMensuales.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={comisionesMensuales}>
              <defs>
                <linearGradient id="colorComisiones" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="mes" 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF' }}
              />
              <YAxis 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF' }}
                tickFormatter={(value) => `$${(value / 1000000).toFixed(0)}M`}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: '#1E293B', 
                  border: '1px solid #334155',
                  borderRadius: '8px',
                  color: '#F1F5F9'
                }}
                formatter={(value, name) => {
                  if (name === 'comisiones') {
                    return [formatCurrency(value), 'Comisiones']
                  }
                  return [value, name]
                }}
                labelFormatter={(label) => `Mes: ${label}`}
              />
              <Legend />
              <Area 
                type="monotone" 
                dataKey="comisiones" 
                stroke="#10B981" 
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#colorComisiones)"
                name="Comisiones Pagadas"
              />
            </AreaChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-96 flex items-center justify-center bg-slate-900/50 rounded-lg">
            <p className="text-slate-500">No hay comisiones registradas aún</p>
          </div>
        )}
      </div>

      {/* Tabla de Comisiones Mensuales */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <Calendar className="w-5 h-5 text-purple-400" />
          Detalle Mensual
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Mes</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Comisiones</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Facturas</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {comisionesMensuales.length > 0 ? (
                comisionesMensuales.map((item, idx) => {
                  const mes = item.mes || 'N/A'
                  const estaExpandido = mesExpandido === mes
                  const facturas = facturasMes[mes] || []
                  const cargando = cargandoFacturas[mes]
                  
                  return (
                    <React.Fragment key={idx}>
                      <tr className="hover:bg-slate-700/30 transition-colors cursor-pointer" onClick={() => toggleMes(mes)}>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            {estaExpandido ? (
                              <ChevronUp className="w-4 h-4 text-slate-400" />
                            ) : (
                              <ChevronDown className="w-4 h-4 text-slate-400" />
                            )}
                            <p className="font-semibold text-white text-sm">{mes || 'N/A'}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <p className="text-sm font-semibold text-emerald-400">
                            {formatCurrency(item.comisiones || 0)}
                          </p>
                        </td>
                        <td className="px-4 py-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <p className="text-sm text-slate-300">{item.num_facturas || 0}</p>
                            <Eye className="w-4 h-4 text-slate-400" />
                          </div>
                        </td>
                      </tr>
                      {estaExpandido && (
                        <tr>
                          <td colSpan="3" className="px-4 py-4 bg-slate-900/50">
                            {cargando ? (
                              <div className="flex items-center justify-center py-4">
                                <Loader2 className="w-5 h-5 animate-spin text-blue-500 mr-2" />
                                <p className="text-slate-400">Cargando facturas...</p>
                              </div>
                            ) : facturas.length > 0 ? (
                              <div className="space-y-2">
                                <p className="text-xs font-semibold text-slate-400 uppercase mb-3">
                                  Facturas que componen las comisiones de {mes}
                                </p>
                                <div className="overflow-x-auto">
                                  <table className="w-full text-sm">
                                    <thead className="bg-slate-800/50 border-b border-slate-700">
                                      <tr>
                                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">Factura</th>
                                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">Cliente</th>
                                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">Fecha Factura</th>
                                        <th className="px-3 py-2 text-left text-xs font-semibold text-slate-400">Fecha Pago</th>
                                        <th className="px-3 py-2 text-right text-xs font-semibold text-slate-400">Días Pago</th>
                                        <th className="px-3 py-2 text-right text-xs font-semibold text-slate-400">Valor Neto</th>
                                        <th className="px-3 py-2 text-right text-xs font-semibold text-slate-400">Comisión</th>
                                        <th className="px-3 py-2 text-center text-xs font-semibold text-slate-400">Estado</th>
                                      </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-700/30">
                                      {facturas.map((factura, fIdx) => (
                                        <tr key={fIdx} className="hover:bg-slate-800/50">
                                          <td className="px-3 py-2">
                                            <p className="font-semibold text-white text-xs">{factura.factura || 'N/A'}</p>
                                          </td>
                                          <td className="px-3 py-2">
                                            <p className="text-slate-300 text-xs">{factura.cliente || 'N/A'}</p>
                                          </td>
                                          <td className="px-3 py-2">
                                            <p className="text-slate-300 text-xs">{formatDate(factura.fecha_factura)}</p>
                                          </td>
                                          <td className="px-3 py-2">
                                            <p className="text-slate-300 text-xs">{formatDate(factura.fecha_pago_real)}</p>
                                          </td>
                                          <td className="px-3 py-2 text-right">
                                            <p className={`text-xs ${factura.dias_pago_real > 80 ? 'text-red-400' : 'text-slate-300'}`}>
                                              {factura.dias_pago_real !== null && factura.dias_pago_real !== undefined ? factura.dias_pago_real : 'N/A'}
                                            </p>
                                          </td>
                                          <td className="px-3 py-2 text-right">
                                            <p className="text-slate-300 text-xs">{formatCurrency(factura.valor_neto_final || 0)}</p>
                                          </td>
                                          <td className="px-3 py-2 text-right">
                                            <p className={`text-xs font-semibold ${factura.comision_perdida ? 'text-red-400' : 'text-emerald-400'}`}>
                                              {formatCurrency(factura.comision || 0)}
                                            </p>
                                          </td>
                                          <td className="px-3 py-2 text-center">
                                            {factura.comision_perdida ? (
                                              <span className="text-xs px-2 py-1 bg-red-500/20 text-red-400 rounded">
                                                Perdida
                                              </span>
                                            ) : (
                                              <span className="text-xs px-2 py-1 bg-emerald-500/20 text-emerald-400 rounded">
                                                Válida
                                              </span>
                                            )}
                                          </td>
                                        </tr>
                                      ))}
                                    </tbody>
                                    <tfoot className="bg-slate-800/70 border-t border-slate-700">
                                      <tr>
                                        <td colSpan="5" className="px-3 py-2 text-right">
                                          <p className="text-xs font-semibold text-slate-300">Total:</p>
                                        </td>
                                        <td className="px-3 py-2 text-right">
                                          <p className="text-xs font-semibold text-slate-300">
                                            {formatCurrency(facturas.reduce((sum, f) => sum + (f.valor_neto_final || 0), 0))}
                                          </p>
                                        </td>
                                        <td className="px-3 py-2 text-right">
                                          <p className="text-xs font-semibold text-emerald-400">
                                            {formatCurrency(facturas.reduce((sum, f) => sum + (f.comision || 0), 0))}
                                          </p>
                                        </td>
                                        <td></td>
                                      </tr>
                                    </tfoot>
                                  </table>
                                </div>
                              </div>
                            ) : (
                              <div className="text-center py-4">
                                <p className="text-slate-500 text-sm">No se encontraron facturas para este mes</p>
                              </div>
                            )}
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  )
                })
              ) : (
                <tr>
                  <td colSpan="3" className="px-4 py-8 text-center">
                    <p className="text-slate-500">No hay comisiones registradas</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Facturas con Problemas (sin fecha de pago) */}
      {data?.facturas_sin_fecha_pago && data.facturas_sin_fecha_pago.length > 0 && (
        <div className="bg-amber-500/10 rounded-xl p-6 border border-amber-500/20">
          <h3 className="text-lg font-semibold text-amber-400 mb-4 flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            Facturas Pagadas Sin Fecha de Pago
          </h3>
          <p className="text-sm text-amber-300 mb-4">
            Estas facturas están marcadas como pagadas pero no tienen fecha de pago. Necesitas agregar la fecha de pago para que aparezcan en el mes correcto.
          </p>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Factura</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Pedido</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Fecha Factura</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Comisión</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {data.facturas_sin_fecha_pago.map((factura, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{factura.factura || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{factura.cliente || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{factura.pedido || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{factura.fecha_factura || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm font-semibold text-amber-400">
                        {formatCurrency(factura.comision || 0)}
                      </p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

const MetricCard = ({ icon: Icon, title, value, subtitle, color, isCurrency = false, isPercentage = false }) => {
  const formatValue = (val) => {
    if (isPercentage) {
      return `${val.toFixed(2)}%`
    }
    if (isCurrency) {
      return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(val)
    }
    return val.toLocaleString('es-CO')
  }

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
      <div className="flex items-center justify-between mb-3">
        <div className={`p-2 rounded-lg ${color}`}>
          <Icon className="w-5 h-5" />
        </div>
      </div>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">{formatValue(value)}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  )
}

export default ComisionesGerenciaView
