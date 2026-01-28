import React, { useState, useEffect } from 'react'
import { MapPin, TrendingUp, Users, DollarSign, BarChart3, Loader2, AlertCircle } from 'lucide-react'
import { getAnalisisGeografico } from '../api/analytics'
import Plot from 'react-plotly.js'

const AnalisisGeograficoView = () => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [periodo, setPeriodo] = useState('historico')

  useEffect(() => {
    cargarDatos()
  }, [periodo])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      setError(null)
      const resultado = await getAnalisisGeografico(periodo)
      setData(resultado)
    } catch (err) {
      console.error('Error cargando análisis geográfico:', err)
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
          <p className="text-slate-400">Cargando análisis geográfico...</p>
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

  const distribucion = data?.distribucion
  const ranking = data?.ranking || []
  const segmentacion = data?.segmentacion

  // Preparar datos para el mapa
  const prepararDatosMapa = () => {
    if (!distribucion?.datos_mapa || distribucion.datos_mapa.length === 0) {
      return null
    }

    const datos = distribucion.datos_mapa
    
    return {
      lat: datos.map(d => d.lat),
      lon: datos.map(d => d.lon),
      text: datos.map(d => 
        `${d.ciudad}<br>` +
        `Clientes: ${d.num_clientes}<br>` +
        `Total Compras: $${(d.total_compras || 0).toLocaleString('es-CO')}<br>` +
        `Cupo Total: $${(d.cupo_total || 0).toLocaleString('es-CO')}<br>` +
        `Cupo Utilizado: $${(d.cupo_utilizado || 0).toLocaleString('es-CO')}`
      ),
      size: datos.map(d => Math.max(10, Math.min(50, (d.total_compras || 0) / 100000))),
      color: datos.map(d => d.num_clientes || 0),
      ciudades: datos.map(d => d.ciudad)
    }
  }

  const datosMapa = prepararDatosMapa()

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Análisis Geográfico</h2>
          <p className="text-sm text-slate-400">Distribución geográfica de clientes y ventas</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            value={periodo} 
            onChange={(e) => setPeriodo(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="historico">Histórico</option>
            <option value="mes_actual">Mes Actual</option>
          </select>
        </div>
      </div>

      {/* Métricas Resumen */}
      {distribucion && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <MetricCard
            icon={MapPin}
            title="Ciudades"
            value={distribucion.total_ciudades || 0}
            subtitle={`${distribucion.ciudades_con_coordenadas || 0} con coordenadas`}
            color="bg-blue-500/10 text-blue-400"
          />
          <MetricCard
            icon={Users}
            title="Total Clientes"
            value={distribucion.total_clientes || 0}
            subtitle="Clientes activos"
            color="bg-purple-500/10 text-purple-400"
          />
          <MetricCard
            icon={DollarSign}
            title="Total Compras"
            value={distribucion.datos_mapa?.reduce((sum, d) => sum + (d.total_compras || 0), 0) || 0}
            subtitle="Valor total"
            color="bg-emerald-500/10 text-emerald-400"
            isCurrency
          />
          <MetricCard
            icon={TrendingUp}
            title="Cupo Total"
            value={distribucion.datos_mapa?.reduce((sum, d) => sum + (d.cupo_total || 0), 0) || 0}
            subtitle="Cupo aprobado"
            color="bg-orange-500/10 text-orange-400"
            isCurrency
          />
        </div>
      )}

      {/* Mapa de Colombia */}
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
          <MapPin className="w-5 h-5 text-blue-400" />
          Mapa de Distribución Geográfica
        </h3>
        
        {datosMapa ? (
          <Plot
            data={[
              {
                type: 'scattermapbox',
                mode: 'markers',
                lat: datosMapa.lat,
                lon: datosMapa.lon,
                text: datosMapa.text,
                hovertemplate: '<b>%{text}</b><extra></extra>',
                marker: {
                  size: datosMapa.size,
                  color: datosMapa.color,
                  colorscale: 'Viridis',
                  showscale: true,
                  colorbar: {
                    title: 'Número de Clientes',
                    titleside: 'right'
                  },
                  sizemode: 'diameter',
                  sizeref: 2,
                  sizemin: 10
                }
              }
            ]}
            layout={{
              mapbox: {
                style: 'open-street-map',
                center: { lat: 4.6, lon: -74.0 },
                zoom: 5
              },
              margin: { l: 0, r: 0, t: 0, b: 0 },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              height: 600
            }}
            config={{
              displayModeBar: true,
              displaylogo: false,
              responsive: true
            }}
            style={{ width: '100%', height: '600px' }}
          />
        ) : (
          <div className="h-96 flex items-center justify-center bg-slate-900/50 rounded-lg">
            <p className="text-slate-500">No hay datos geográficos disponibles</p>
          </div>
        )}
      </div>

      {/* Tablas de Análisis */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Ranking de Ciudades */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            Ranking de Ciudades
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ciudad</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Clientes</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Compras</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {distribucion?.por_ciudad?.slice(0, 15).map((ciudad, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{ciudad.ciudad}</p>
                      <p className="text-xs text-slate-400">{ciudad.departamento || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{ciudad.num_clientes || 0}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm font-semibold text-white">
                        ${(ciudad.total_compras || 0).toLocaleString('es-CO')}
                      </p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Top Clientes por Ciudad */}
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Users className="w-5 h-5 text-emerald-400" />
            Top Clientes
          </h3>
          <div className="overflow-x-auto max-h-96 overflow-y-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700 sticky top-0">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ciudad</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Compras</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {ranking.slice(0, 20).map((cliente, idx) => (
                  <tr key={idx} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{cliente.nombre || cliente.nit_cliente || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{cliente.ciudad || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm font-semibold text-white">
                        ${(cliente.total_compras || 0).toLocaleString('es-CO')}
                      </p>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Segmentación */}
      {segmentacion && !segmentacion.error && (
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-orange-400" />
            Segmentación por Presupuesto
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {segmentacion.resumen_segmentos?.map((seg, idx) => (
              <div key={idx} className="bg-slate-700/30 rounded-lg p-4 border border-slate-700/50">
                <p className="text-sm font-semibold text-white mb-2">{seg.segmento}</p>
                <p className="text-xs text-slate-400 mb-1">Clientes: {seg.num_clientes || 0}</p>
                <p className="text-xs text-slate-400 mb-1">
                  Compras: ${(seg.total_compras || 0).toLocaleString('es-CO')}
                </p>
                <p className="text-xs text-slate-400">
                  Cupo: ${(seg.cupo_total || 0).toLocaleString('es-CO')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

const MetricCard = ({ icon: Icon, title, value, subtitle, color, isCurrency = false }) => {
  const formatValue = (val) => {
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

export default AnalisisGeograficoView
