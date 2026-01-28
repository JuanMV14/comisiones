import React, { useState } from 'react'
import { MapPin, TrendingUp, Users, Package, X } from 'lucide-react'

const MapaColombiaInteractivo = ({ datos, referenciaSeleccionada, onReferenciaChange, onCiudadClick, ciudadSeleccionada }) => {
  const [hoveredCiudad, setHoveredCiudad] = useState(null)

  if (!datos || !datos.ciudades || datos.ciudades.length === 0) {
    return (
      <div className="w-full h-full flex items-center justify-center bg-slate-950 rounded-lg p-8">
        <div className="text-center">
          <MapPin className="w-12 h-12 text-slate-600 mx-auto mb-4" />
          <p className="text-slate-500 mb-2">No hay datos geográficos disponibles</p>
        </div>
      </div>
    )
  }

  const ciudades = datos.ciudades || []
  const ventasMax = Math.max(...ciudades.map(c => c.total_ventas || 0), 1)

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(val)
  }

  // Coordenadas aproximadas de ciudades principales de Colombia (para posicionamiento en el mapa)
  const coordenadasCiudades = {
    'Bogotá': { x: 50, y: 30 },
    'Bogota': { x: 50, y: 30 },
    'Medellín': { x: 45, y: 40 },
    'Medellin': { x: 45, y: 40 },
    'Cali': { x: 40, y: 55 },
    'Barranquilla': { x: 55, y: 20 },
    'Cartagena': { x: 60, y: 15 },
    'Bucaramanga': { x: 50, y: 35 },
    'Pereira': { x: 42, y: 48 },
    'Santa Marta': { x: 58, y: 18 },
    'Manizales': { x: 42, y: 42 },
    'Armenia': { x: 40, y: 50 },
    'Villavicencio': { x: 52, y: 40 },
    'Valledupar': { x: 55, y: 25 },
    'Montería': { x: 50, y: 30 },
    'Sincelejo': { x: 52, y: 28 },
    'Ibagué': { x: 45, y: 45 },
    'Pasto': { x: 35, y: 65 },
    'Neiva': { x: 45, y: 50 },
    'Bello': { x: 45, y: 40 },
    'Itagüí': { x: 45, y: 40 },
    'Itagui': { x: 45, y: 40 },
    'Corozal': { x: 55, y: 28 },
    'Buenaventura': { x: 38, y: 58 },
    'Resto': { x: 50, y: 50 }
  }

  // Obtener coordenadas de una ciudad
  const getCoordenadas = (ciudad) => {
    return coordenadasCiudades[ciudad] || { x: 50, y: 50 }
  }

  // Calcular tamaño del marcador basado en ventas
  const getTamañoMarcador = (ventas) => {
    if (ventasMax === 0) return 20
    const porcentaje = (ventas / ventasMax) * 100
    return Math.max(15, Math.min(50, 15 + (porcentaje * 0.35)))
  }

  // Obtener color basado en ventas
  const getColorMarcador = (ventas) => {
    if (ventas === 0) return '#64748b' // Gris para sin ventas
    const porcentaje = (ventas / ventasMax) * 100
    if (porcentaje >= 70) return '#3b82f6' // Azul fuerte
    if (porcentaje >= 30) return '#60a5fa' // Azul medio
    return '#93c5fd' // Azul claro
  }

  return (
    <div className="w-full h-full bg-slate-950 rounded-lg p-6 relative">
      {/* Selector de Referencia */}
      {datos.referencias_disponibles && datos.referencias_disponibles.length > 0 && (
        <div className="mb-4 p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
          <div className="flex items-center gap-3">
            <Package className="w-5 h-5 text-orange-400" />
            <label className="text-sm font-semibold text-slate-300">Filtrar por Referencia:</label>
            <select
              value={referenciaSeleccionada || ''}
              onChange={(e) => onReferenciaChange(e.target.value || null)}
              className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">Todas las referencias</option>
              {datos.referencias_disponibles.map((ref, idx) => (
                <option key={idx} value={ref}>{ref}</option>
              ))}
            </select>
            {referenciaSeleccionada && (
              <button
                onClick={() => onReferenciaChange(null)}
                className="p-2 text-slate-400 hover:text-white transition-colors"
                title="Limpiar filtro"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
          {referenciaSeleccionada && (
            <p className="text-xs text-slate-400 mt-2">
              Mostrando ciudades donde se compra la referencia: <span className="text-orange-400 font-semibold">{referenciaSeleccionada}</span>
            </p>
          )}
        </div>
      )}

      {/* Mapa SVG de Colombia */}
      <div className="relative bg-slate-900/30 rounded-lg border border-slate-800 overflow-hidden" style={{ minHeight: '500px' }}>
        <svg viewBox="0 0 100 100" className="w-full h-full" preserveAspectRatio="xMidYMid meet">
          {/* Contorno simplificado de Colombia */}
          <path
            d="M 20 10 L 35 8 L 50 12 L 65 10 L 80 15 L 85 25 L 82 40 L 75 55 L 70 70 L 60 80 L 45 85 L 30 82 L 15 75 L 8 60 L 10 40 L 12 25 Z"
            fill="none"
            stroke="#334155"
            strokeWidth="0.5"
            opacity="0.3"
          />
          
          {/* Marcadores de ciudades */}
          {ciudades.map((ciudad, idx) => {
            const coords = getCoordenadas(ciudad.ciudad)
            const tamaño = getTamañoMarcador(ciudad.total_ventas)
            const color = getColorMarcador(ciudad.total_ventas)
            const isSelected = ciudadSeleccionada === ciudad.ciudad
            const isHovered = hoveredCiudad === ciudad.ciudad

            return (
              <g key={idx}>
                {/* Círculo del marcador */}
                <circle
                  cx={coords.x}
                  cy={coords.y}
                  r={isHovered || isSelected ? tamaño + 3 : tamaño}
                  fill={color}
                  stroke={isSelected ? '#fbbf24' : isHovered ? '#ffffff' : '#1e293b'}
                  strokeWidth={isSelected ? 2 : isHovered ? 1.5 : 1}
                  opacity={isHovered || isSelected ? 1 : 0.8}
                  className="cursor-pointer transition-all"
                  onClick={() => onCiudadClick && onCiudadClick(ciudad.ciudad)}
                  onMouseEnter={() => setHoveredCiudad(ciudad.ciudad)}
                  onMouseLeave={() => setHoveredCiudad(null)}
                />
                {/* Texto con número o inicial */}
                <text
                  x={coords.x}
                  y={coords.y + tamaño * 0.3}
                  textAnchor="middle"
                  fill="white"
                  fontSize={tamaño * 0.4}
                  fontWeight="bold"
                  className="pointer-events-none"
                >
                  {idx + 1}
                </text>
                {/* Etiqueta de ciudad (solo si está hover o seleccionada) */}
                {(isHovered || isSelected) && (
                  <text
                    x={coords.x}
                    y={coords.y - tamaño - 5}
                    textAnchor="middle"
                    fill="white"
                    fontSize="3"
                    fontWeight="bold"
                    className="pointer-events-none"
                  >
                    {ciudad.ciudad}
                  </text>
                )}
              </g>
            )
          })}
        </svg>

        {/* Tooltip flotante */}
        {hoveredCiudad && (() => {
          const ciudad = ciudades.find(c => c.ciudad === hoveredCiudad)
          if (!ciudad) return null
          return (
            <div className="absolute bg-slate-800 border border-slate-700 rounded-lg p-4 shadow-xl z-10 pointer-events-none"
                 style={{ 
                   left: `${getCoordenadas(ciudad.ciudad).x}%`, 
                   top: `${getCoordenadas(ciudad.ciudad).y - 15}%`,
                   transform: 'translate(-50%, -100%)',
                   minWidth: '200px'
                 }}>
              <h4 className="font-bold text-white text-sm mb-2 flex items-center gap-2">
                <MapPin className="w-4 h-4 text-blue-400" />
                {ciudad.ciudad}
              </h4>
              <div className="space-y-1 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">💰 Ventas:</span>
                  <span className="text-white font-semibold">{formatCurrency(ciudad.total_ventas || 0)}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400">🧑 Clientes:</span>
                  <span className="text-white">{ciudad.num_clientes || 0}</span>
                </div>
                {ciudad.top_cliente && (
                  <div className="mt-2 pt-2 border-t border-slate-700">
                    <p className="text-slate-400 text-xs mb-1">👑 Cliente Top:</p>
                    <p className="text-white font-semibold text-xs">{ciudad.top_cliente.nombre || ciudad.top_cliente.nit}</p>
                    <p className="text-slate-300 text-xs">{formatCurrency(ciudad.top_cliente.total_ventas || 0)}</p>
                  </div>
                )}
                {ciudad.top_referencia && !referenciaSeleccionada && (
                  <div className="mt-2 pt-2 border-t border-slate-700">
                    <p className="text-slate-400 text-xs mb-1">📦 Ref. Top:</p>
                    <p className="text-white font-semibold text-xs">{ciudad.top_referencia.codigo}</p>
                    <p className="text-slate-300 text-xs">{formatCurrency(ciudad.top_referencia.total_ventas || 0)}</p>
                  </div>
                )}
              </div>
            </div>
          )
        })()}
      </div>

      {/* Leyenda */}
      <div className="mt-4 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
        <p className="text-xs font-semibold text-slate-400 mb-2 uppercase">Leyenda</p>
        <div className="flex items-center gap-4 text-xs flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-600 border border-blue-500"></div>
            <span className="text-slate-300">Alto volumen</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-400 border border-blue-400"></div>
            <span className="text-slate-300">Medio volumen</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-blue-300 border border-blue-300"></div>
            <span className="text-slate-300">Bajo volumen</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-slate-500 border border-slate-500"></div>
            <span className="text-slate-300">Sin ventas</span>
          </div>
          <div className="ml-auto text-slate-500">
            Tamaño = Ventas • Color = Volumen
          </div>
        </div>
      </div>

      {/* Resumen */}
      <div className="mt-4 pt-4 border-t border-slate-700/50">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>Total: {ciudades.length} ciudades</span>
          <span>Ventas totales: {formatCurrency(ciudades.reduce((sum, c) => sum + (c.total_ventas || 0), 0))}</span>
        </div>
      </div>
    </div>
  )
}

export default MapaColombiaInteractivo
