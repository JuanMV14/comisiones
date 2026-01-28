import React, { useState, useEffect } from 'react'
import { TrendingUp, DollarSign, Users, Package, BarChart3, Loader2, AlertCircle, ArrowUpRight, ArrowDownRight } from 'lucide-react'
import { getAnalisisComercial } from '../api/analytics'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const ReferenciaRow = ({ producto, idx }) => {
  const [expanded, setExpanded] = useState(false)
  
  return (
    <>
      <tr className="hover:bg-slate-700/30 transition-colors cursor-pointer" onClick={() => setExpanded(!expanded)}>
        <td className="px-4 py-3">
          <span className="text-xs text-slate-400">#{idx + 1}</span>
        </td>
        <td className="px-4 py-3">
          <p className="font-semibold text-white text-sm">{producto.referencia || 'N/A'}</p>
        </td>
        <td className="px-4 py-3">
          <p className="text-sm font-semibold text-white">
            ${(producto.total_ventas || 0).toLocaleString('es-CO')}
          </p>
        </td>
        <td className="px-4 py-3">
          <p className="text-sm text-slate-300">{producto.cantidad_vendida || 0}</p>
        </td>
        <td className="px-4 py-3">
          <p className="text-sm text-slate-300">{producto.num_clientes || 0}</p>
        </td>
      </tr>
      {expanded && producto.top_clientes && producto.top_clientes.length > 0 && (
        <tr>
          <td colSpan={5} className="px-4 py-3 bg-slate-900/50">
            <div className="ml-4">
              <p className="text-xs font-semibold text-slate-400 mb-2">Top Clientes que compran esta referencia:</p>
              <div className="space-y-1">
                {producto.top_clientes.map((cliente, cIdx) => (
                  <div key={cIdx} className="flex items-center justify-between text-xs">
                    <span className="text-slate-300">{cliente.nombre || cliente.nit}</span>
                    <div className="flex items-center gap-4">
                      <span className="text-slate-400">Cant: {cliente.cantidad || 0}</span>
                      <span className="text-emerald-400 font-semibold">
                        ${(cliente.total_comprado || 0).toLocaleString('es-CO')}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  )
}

const AnalisisComercialView = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    cargarDatos()
  }, [])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      setError(null)
      const resultado = await getAnalisisComercial()
      setData(resultado)
    } catch (err) {
      console.error('Error cargando análisis comercial:', err)
      setError(`Error al cargar los datos: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando análisis comercial...</p>
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

  const tendencias = data?.tendencias || {}
  const crecimiento = tendencias.crecimiento_mensual || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Análisis Comercial</h2>
          <p className="text-sm text-slate-400">Análisis de ventas, productos y tendencias comerciales</p>
        </div>
      </div>

      {/* Métricas de Tendencias */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          icon={DollarSign}
          title="Ventas Mes Actual"
          value={tendencias.ventas_mes_actual || 0}
          subtitle="Facturación del mes"
          color="bg-blue-500/10 text-blue-400"
          isCurrency
        />
        <MetricCard
          icon={TrendingUp}
          title="Crecimiento Mensual"
          value={crecimiento}
          subtitle={crecimiento >= 0 ? "Aumento" : "Disminución"}
          color={crecimiento >= 0 ? "bg-emerald-500/10 text-emerald-400" : "bg-red-500/10 text-red-400"}
          isPercentage
          trend={crecimiento}
        />
        <MetricCard
          icon={DollarSign}
          title="Ventas Mes Anterior"
          value={tendencias.ventas_mes_anterior || 0}
          subtitle="Comparación"
          color="bg-purple-500/10 text-purple-400"
          isCurrency
        />
      </div>

      {/* Gráfico de Ventas Mensuales */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-blue-400" />
          Ventas Mensuales (Últimos 12 Meses)
        </h3>
        {data?.ventas_mensuales && data.ventas_mensuales.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={data.ventas_mensuales}>
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
                formatter={(value) => `$${value.toLocaleString('es-CO')}`}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="total_ventas" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Ventas"
                dot={{ fill: '#3B82F6' }}
              />
              <Line 
                type="monotone" 
                dataKey="total_comisiones" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Comisiones"
                dot={{ fill: '#10B981' }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-96 flex items-center justify-center bg-slate-900/50 rounded-lg">
            <p className="text-slate-500">No hay datos de ventas mensuales disponibles</p>
          </div>
        )}
      </div>

      {/* Top Clientes y Productos */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Clientes */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-purple-400" />
            Top 20 Clientes
          </h3>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ventas</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Facturas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {data?.top_clientes?.slice(0, 20).map((cliente, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <span className="text-xs text-slate-400">#{idx + 1}</span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{cliente.cliente || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm font-semibold text-white">
                        ${(cliente.total_ventas || 0).toLocaleString('es-CO')}
                      </p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{cliente.num_facturas || 0}</p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Productos/Referencias */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Package className="w-5 h-5 text-orange-400" />
            Top 20 Referencias
          </h3>
          {data?.top_productos && data.top_productos.length > 0 ? (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead className="bg-slate-900/50 border-b border-slate-700 sticky top-0">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">#</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Referencia</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ventas</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cantidad</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Clientes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-700/50">
                  {data.top_productos.slice(0, 20).map((producto, idx) => (
                    <ReferenciaRow key={idx} producto={producto} idx={idx} />
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center">
              <p className="text-slate-500">No hay datos de referencias disponibles</p>
            </div>
          )}
        </div>
      </div>

      {/* Gráfico de Barras - Top Clientes */}
      {data?.top_clientes && data.top_clientes.length > 0 && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-emerald-400" />
            Top 10 Clientes por Ventas
          </h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={data.top_clientes.slice(0, 10)}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="cliente" 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={100}
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
                formatter={(value) => `$${value.toLocaleString('es-CO')}`}
              />
              <Bar dataKey="total_ventas" fill="#3B82F6" radius={[8, 8, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

const MetricCard = ({ icon: Icon, title, value, subtitle, color, isCurrency = false, isPercentage = false, trend = null }) => {
  const formatValue = (val) => {
    if (isPercentage) {
      return `${val >= 0 ? '+' : ''}${val.toFixed(2)}%`
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
        {trend !== null && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend >= 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
          </div>
        )}
      </div>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">{formatValue(value)}</p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  )
}

export default AnalisisComercialView
