import React, { useState } from 'react'
import { MapPin, TrendingUp, TrendingDown, Minus } from 'lucide-react'

const MapaColombiaCroquis = ({ datos, onCiudadClick, ciudadSeleccionada }) => {
  const [hoveredCiudad, setHoveredCiudad] = useState(null)

  // Manejar diferentes formatos de datos
  let ciudadesConDatos = []
  if (datos) {
    if (Array.isArray(datos.datos_mapa)) {
      ciudadesConDatos = datos.datos_mapa
    } else if (Array.isArray(datos)) {
      ciudadesConDatos = datos
    } else if (datos.distribucion?.datos_mapa) {
      ciudadesConDatos = datos.distribucion.datos_mapa
    } else if (datos.por_ciudad) {
      ciudadesConDatos = datos.por_ciudad
    }
  }

  // Calcular estadísticas para normalizar
  const ventasMax = ciudadesConDatos.length > 0 
    ? Math.max(...ciudadesConDatos.map(c => c.total_compras || 0), 1)
    : 1
  const ventasPromedio = ciudadesConDatos.length > 0
    ? ciudadesConDatos.reduce((sum, c) => sum + (c.total_compras || 0), 0) / ciudadesConDatos.length
    : 0

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(val)
  }

  // Determinar nivel de cumplimiento basado en ventas vs promedio
  const getNivelCumplimiento = (ventas) => {
    if (ventas >= ventasPromedio * 1.5) return 'alto' // 150% del promedio
    if (ventas >= ventasPromedio * 0.7) return 'medio' // 70% del promedio
    return 'bajo' // Menos del 70%
  }

  // Obtener color según nivel de cumplimiento
  const getColorCumplimiento = (nivel) => {
    switch (nivel) {
      case 'alto':
        return {
          bg: 'bg-blue-600',
          border: 'border-blue-500',
          text: 'text-blue-400',
          light: 'bg-blue-500/20'
        }
      case 'medio':
        return {
          bg: 'bg-blue-400',
          border: 'border-blue-400',
          text: 'text-blue-300',
          light: 'bg-blue-400/20'
        }
      default:
        return {
          bg: 'bg-slate-500',
          border: 'border-slate-500',
          text: 'text-slate-400',
          light: 'bg-slate-500/20'
        }
    }
  }

  // Ordenar ciudades por ventas (mayor a menor)
  const ciudadesOrdenadas = [...ciudadesConDatos].sort((a, b) => (b.total_compras || 0) - (a.total_compras || 0))

  if (ciudadesConDatos.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-950 rounded-lg p-8">
        <div className="text-center">
          <MapPin className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 mb-2">No hay datos geográficos disponibles</p>
          <p className="text-slate-600 text-sm">Verifica que haya datos en la base de datos</p>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full h-full bg-slate-950 rounded-lg p-6">
      {/* Leyenda mejorada */}
      <div className="mb-4 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
        <p className="text-xs font-semibold text-slate-400 mb-2 uppercase">Leyenda</p>
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-600 border border-blue-500"></div>
            <span className="text-slate-300">Alto cumplimiento</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-400 border border-blue-400"></div>
            <span className="text-slate-300">Medio cumplimiento</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-slate-500 border border-slate-500"></div>
            <span className="text-slate-300">Bajo cumplimiento</span>
          </div>
          <div className="ml-auto text-slate-500">
            Tamaño = Ventas • Color = Cumplimiento
          </div>
        </div>
      </div>

      {/* Grid de ciudades - Visualización clara */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 max-h-[500px] overflow-y-auto">
        {ciudadesOrdenadas.map((ciudad, index) => {
          const ventas = ciudad.total_compras || 0
          const clientes = ciudad.num_clientes || 0
          const nivel = getNivelCumplimiento(ventas)
          const color = getColorCumplimiento(nivel)
          const isSelected = ciudadSeleccionada === ciudad.ciudad
          const isHovered = hoveredCiudad === ciudad.ciudad

          // Tamaño del indicador basado en ventas (normalizado)
          // Evitar división por cero
          const tamañoIndicador = ventasMax > 0
            ? Math.max(8, Math.min(40, (ventas / ventasMax) * 40))
            : 8

          return (
            <div
              key={index}
              onClick={() => onCiudadClick && onCiudadClick(ciudad.ciudad)}
              onMouseEnter={() => setHoveredCiudad(ciudad.ciudad)}
              onMouseLeave={() => setHoveredCiudad(null)}
              className={`
                relative p-4 rounded-lg border-2 cursor-pointer transition-all
                ${isSelected 
                  ? `${color.border} ${color.light} shadow-lg scale-105` 
                  : isHovered
                  ? 'border-slate-600 bg-slate-800/50 scale-102'
                  : 'border-slate-700 bg-slate-800/30 hover:border-slate-600'
                }
              `}
            >
              {/* Indicador de tamaño (círculo) */}
              <div className="flex items-center gap-3 mb-3">
                <div 
                  className={`${color.bg} rounded-full border-2 ${color.border} flex items-center justify-center transition-all`}
                  style={{ 
                    width: `${tamañoIndicador}px`, 
                    height: `${tamañoIndicador}px`,
                    minWidth: '32px',
                    minHeight: '32px'
                  }}
                >
                  <MapPin className="w-4 h-4 text-white" />
                </div>
                <div className="flex-1">
                  <h4 className="font-bold text-white text-sm">{ciudad.ciudad}</h4>
                  {ciudad.departamento && (
                    <p className="text-xs text-slate-400">{ciudad.departamento}</p>
                  )}
                </div>
              </div>

              {/* Métricas */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">💰 Ventas</span>
                  <span className="text-sm font-semibold text-white">{formatCurrency(ventas)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">🧑 Clientes</span>
                  <span className="text-sm text-slate-300">{clientes}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">📊 Nivel</span>
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${color.light} ${color.text} capitalize`}>
                    {nivel}
                  </span>
                </div>
              </div>

              {/* Badge de selección */}
              {isSelected && (
                <div className="absolute top-2 right-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse"></div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Resumen al final */}
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Total: {ciudadesConDatos.length} ciudades</span>
          <span>Ventas totales: {formatCurrency(ciudadesConDatos.reduce((sum, c) => sum + (c.total_compras || 0), 0))}</span>
        </div>
      </div>
    </div>
  )
}

export default MapaColombiaCroquis
