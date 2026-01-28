import React, { useState, useEffect } from 'react'
import { ShoppingCart, DollarSign, Users, Package, TrendingUp, Loader2, AlertCircle, BarChart3, Calendar } from 'lucide-react'
import { getAnalisisCompras } from '../api/analytics'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

const MetricCard = ({ icon: Icon, title, value, subtitle, color, isCurrency = false, isPercentage = false, trend = null }) => {
  const formatValue = (val) => {
    if (isCurrency) {
      return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(val || 0)
    }
    if (isPercentage) {
      return `${(val || 0).toFixed(2)}%`
    }
    return new Intl.NumberFormat('es-CO').format(val || 0)
  }

  return (
    <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
      <div className="flex items-center justify-between mb-2">
        <Icon className={`w-5 h-5 ${color}`} />
        {trend !== null && (
          <div className={`flex items-center gap-1 ${trend >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingUp className="w-4 h-4 rotate-180" />}
            <span className="text-xs font-semibold">{Math.abs(trend).toFixed(1)}%</span>
          </div>
        )}
      </div>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className={`text-2xl font-bold ${color.includes('text-') ? '' : 'text-white'}`}>
        {formatValue(value)}
      </p>
      {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
    </div>
  )
}

const AnalisisComprasView = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [periodo, setPeriodo] = useState('12')

  useEffect(() => {
    cargarDatos()
  }, [periodo])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      setError(null)
      const resultado = await getAnalisisCompras(periodo)
      setData(resultado)
    } catch (err) {
      console.error('Error cargando análisis de compras:', err)
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

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando análisis de compras...</p>
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

  const kpis = data?.kpis || {}
  const tendencias = data?.tendencias || {}
  const crecimiento = tendencias.crecimiento_mensual || 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Análisis Compras</h2>
          <p className="text-sm text-slate-400">Análisis detallado de patrones de compra de clientes</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={periodo}
            onChange={(e) => setPeriodo(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="3">Últimos 3 meses</option>
            <option value="6">Últimos 6 meses</option>
            <option value="12">Últimos 12 meses</option>
            <option value="24">Últimos 24 meses</option>
          </select>
        </div>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
        <MetricCard
          icon={ShoppingCart}
          title="Total Compras"
          value={kpis.total_compras || 0}
          subtitle="Registros de compra"
          color="bg-blue-500/10 text-blue-400"
        />
        <MetricCard
          icon={DollarSign}
          title="Valor Total"
          value={kpis.valor_total || 0}
          subtitle="Suma de todas las compras"
          color="bg-emerald-500/10 text-emerald-400"
          isCurrency
        />
        <MetricCard
          icon={TrendingUp}
          title="Promedio por Compra"
          value={kpis.promedio_compra || 0}
          subtitle="Ticket promedio"
          color="bg-purple-500/10 text-purple-400"
          isCurrency
        />
        <MetricCard
          icon={Users}
          title="Clientes Activos"
          value={kpis.clientes_activos || 0}
          subtitle="Clientes con compras"
          color="bg-orange-500/10 text-orange-400"
        />
        <MetricCard
          icon={Package}
          title="Referencias Únicas"
          value={kpis.referencias_unicas || 0}
          subtitle="Productos diferentes"
          color="bg-pink-500/10 text-pink-400"
        />
      </div>

      {/* Gráfico de Tendencias */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Evolución de Compras Mensuales</h3>
          <div className="flex items-center gap-2">
            <TrendingUp className={`w-4 h-4 ${crecimiento >= 0 ? 'text-emerald-400' : 'text-red-400'}`} />
            <span className={`text-sm font-semibold ${crecimiento >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
              {crecimiento >= 0 ? '+' : ''}{crecimiento.toFixed(2)}%
            </span>
          </div>
        </div>
        {tendencias.compras_mensuales && tendencias.compras_mensuales.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={tendencias.compras_mensuales}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis 
                dataKey="mes" 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis 
                stroke="#9CA3AF"
                tick={{ fill: '#9CA3AF', fontSize: 12 }}
                tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1E293B', border: '1px solid #334155', borderRadius: '8px' }}
                formatter={(value, name) => {
                  if (name === 'valor_total') return [formatCurrency(value), 'Valor Total']
                  if (name === 'num_compras') return [value, 'Número de Compras']
                  if (name === 'clientes_activos') return [value, 'Clientes Activos']
                  return [value, name]
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="valor_total" 
                stroke="#3B82F6" 
                strokeWidth={2}
                name="Valor Total"
                dot={{ fill: '#3B82F6', r: 4 }}
              />
              <Line 
                type="monotone" 
                dataKey="num_compras" 
                stroke="#10B981" 
                strokeWidth={2}
                name="Número de Compras"
                dot={{ fill: '#10B981', r: 4 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-12">
            <p className="text-slate-500">No hay datos para mostrar</p>
          </div>
        )}
      </div>

      {/* Top Clientes y Top Referencias */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Clientes */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700/50">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Users className="w-5 h-5 text-blue-400" />
              Top 20 Clientes por Valor
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Valor Total</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Compras</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Última Compra</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {data?.top_clientes && data.top_clientes.length > 0 ? (
                  data.top_clientes.map((cliente, idx) => (
                    <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-xs text-slate-400">#{idx + 1}</span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-white text-sm">{cliente.nombre || cliente.nit || 'N/A'}</p>
                        {cliente.ciudad && (
                          <p className="text-xs text-slate-500">{cliente.ciudad}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm font-semibold text-white">{formatCurrency(cliente.valor_total || 0)}</p>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm text-slate-300">{cliente.num_compras || 0}</p>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm text-slate-300">{formatDate(cliente.ultima_compra)}</p>
                        {cliente.dias_desde_compra !== null && (
                          <p className="text-xs text-slate-500">{cliente.dias_desde_compra} días</p>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center">
                      <p className="text-slate-500">No hay datos disponibles</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Referencias */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700/50">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Package className="w-5 h-5 text-emerald-400" />
              Top 20 Referencias por Valor
            </h3>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">#</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Código</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Detalle</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Valor Total</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Cantidad</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Clientes</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {data?.top_referencias && data.top_referencias.length > 0 ? (
                  data.top_referencias.map((ref, idx) => (
                    <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                      <td className="px-4 py-3">
                        <span className="text-xs text-slate-400">#{idx + 1}</span>
                      </td>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-white text-sm">{ref.codigo || 'N/A'}</p>
                      </td>
                      <td className="px-4 py-3">
                        <p className="text-sm text-slate-300">{ref.detalle || 'N/A'}</p>
                        {ref.marca && (
                          <p className="text-xs text-slate-500">{ref.marca}</p>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm font-semibold text-white">{formatCurrency(ref.valor_total || 0)}</p>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm text-slate-300">{ref.cantidad_total || 0}</p>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm text-slate-300">{ref.clientes_unicos || 0}</p>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="6" className="px-4 py-8 text-center">
                      <p className="text-slate-500">No hay datos disponibles</p>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Análisis de Frecuencia */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="p-4 border-b border-slate-700/50">
          <h3 className="text-lg font-semibold text-white flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            Análisis de Frecuencia de Compras
          </h3>
          <p className="text-sm text-slate-400 mt-1">Clientes ordenados por valor total con frecuencia de compra mensual</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">#</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Valor Total</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Total Compras</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Frecuencia Mensual</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Primera Compra</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Última Compra</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {data?.frecuencia_compras && data.frecuencia_compras.length > 0 ? (
                data.frecuencia_compras.map((cliente, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <span className="text-xs text-slate-400">#{idx + 1}</span>
                    </td>
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{cliente.nombre || cliente.nit || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm font-semibold text-white">{formatCurrency(cliente.valor_total || 0)}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm text-slate-300">{cliente.num_compras || 0}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className={`text-sm font-semibold ${
                        (cliente.frecuencia_mensual || 0) >= 4 ? 'text-emerald-400' :
                        (cliente.frecuencia_mensual || 0) >= 2 ? 'text-yellow-400' : 'text-slate-300'
                      }`}>
                        {(cliente.frecuencia_mensual || 0).toFixed(2)} compras/mes
                      </p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm text-slate-300">{formatDate(cliente.primera_compra)}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm text-slate-300">{formatDate(cliente.ultima_compra)}</p>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center">
                    <p className="text-slate-500">No hay datos disponibles</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

export default AnalisisComprasView
