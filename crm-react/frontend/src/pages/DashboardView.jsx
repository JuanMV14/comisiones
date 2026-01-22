import React, { useState, useEffect } from 'react'
import { TrendingUp, DollarSign, Users, Package, ArrowUpRight, MapPin, Loader2 } from 'lucide-react'
import { getDashboardMetrics, getSalesChart, getColombiaMap } from '../api/dashboard'
import { getMetricsDirecto } from '../utils/supabaseClient'

const DashboardView = () => {
  const [metrics, setMetrics] = useState({
    totalVentas: 0,
    comisiones: 0,
    clientesActivos: 0,
    pedidosMes: 0
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      // Intentar backend primero, si falla usar Supabase directo
      try {
        const data = await getDashboardMetrics()
        setMetrics(data)
      } catch (backendError) {
        console.warn('Backend no disponible, usando conexión directa a Supabase:', backendError)
        // Si el backend falla, usar Supabase directo
        const data = await getMetricsDirecto()
        setMetrics({
          totalVentas: data.totalVentas || 0,
          comisiones: data.comisiones || 0,
          clientesActivos: data.clientesActivos || 0,
          pedidosMes: data.pedidosMes || 0
        })
      }
    } catch (error) {
      console.error('Error loading dashboard:', error)
      setError('Error al cargar los datos. Verifica la consola para más detalles.')
    } finally {
      setLoading(false)
    }
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
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md">
          <p className="text-red-400 mb-2">⚠️ Error</p>
          <p className="text-slate-300 text-sm">{error}</p>
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
        <div className="flex items-center gap-3">
          <select className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm">
            <option>Noviembre</option>
            <option>Octubre</option>
          </select>
        </div>
      </div>

      {/* Métricas Principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <MetricCard
          title="Total Ventas"
          value={metrics.totalVentas}
          icon={DollarSign}
          trend="+12.5%"
          trendUp={true}
        />
        <MetricCard
          title="Comisiones"
          value={metrics.comisiones}
          icon={TrendingUp}
          trend="+8.2%"
          trendUp={true}
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

      {/* Mapa de Colombia y Gráficos */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Mapa de Clientes - Colombia</h3>
          <div className="relative h-80 bg-slate-900/50 rounded-lg overflow-hidden">
            {/* Aquí irá el mapa de Colombia con Plotly */}
            <MapaColombia />
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Ventas Mensuales</h3>
          </div>
          {/* Aquí irá el gráfico de ventas mensuales */}
          <SalesChartComponent />
        </div>
      </div>

      {/* Productos y Alertas */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Productos Más Vendidos</h3>
          <ProductosTopList />
        </div>

        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4">Alertas del Día</h3>
          <AlertasList />
        </div>
      </div>
    </div>
  )
}

const MetricCard = ({ title, value, icon: Icon, trend, trendUp }) => {
  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(val)
  }

  return (
    <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
      <div className="flex items-center justify-between mb-4">
        <div className="p-2 bg-blue-500/10 rounded-lg">
          <Icon className="w-5 h-5 text-blue-400" />
        </div>
        <span className={`text-xs flex items-center gap-1 ${trendUp ? 'text-emerald-400' : 'text-red-400'}`}>
          <ArrowUpRight className="w-3 h-3" /> {trend}
        </span>
      </div>
      <p className="text-sm text-slate-400 mb-1">{title}</p>
      <p className="text-2xl font-bold text-white">
        {typeof value === 'number' && value > 1000 ? formatCurrency(value) : value}
      </p>
    </div>
  )
}

const MapaColombia = () => {
  return (
    <div className="absolute inset-0 flex items-center justify-center">
      <p className="text-slate-500">Mapa de Colombia con marcadores de ciudades - Integrar Plotly</p>
    </div>
  )
}

const SalesChartComponent = () => {
  return (
    <div className="h-64 flex items-center justify-center">
      <p className="text-slate-500">Gráfico de ventas mensuales - Integrar Recharts</p>
    </div>
  )
}

const ProductosTopList = () => {
  return (
    <div className="space-y-3">
      <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
        <p className="text-sm font-medium text-white">Disco Freno Brembo</p>
        <p className="text-xs text-slate-400">45 unidades vendidas</p>
      </div>
      <div className="p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
        <p className="text-sm font-medium text-white">Kit Embrague Valeo</p>
        <p className="text-xs text-slate-400">23 unidades vendidas</p>
      </div>
    </div>
  )
}

const AlertasList = () => {
  return (
    <div className="space-y-3">
      <div className="p-3 bg-red-500/10 border border-red-500/20 rounded-lg">
        <p className="text-sm font-medium text-white">Factura #874152 vence en 3 días</p>
        <p className="text-xs text-slate-400">AUTOFRANCO</p>
      </div>
      <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
        <p className="text-sm font-medium text-white">Cliente inactivo 35 días</p>
        <p className="text-xs text-slate-400">Andrade S.A.</p>
      </div>
    </div>
  )
}

export default DashboardView
