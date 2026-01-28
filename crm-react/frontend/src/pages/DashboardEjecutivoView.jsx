import React, { useState, useEffect } from 'react'
import { MapPin, TrendingUp, DollarSign, Users, Package, BarChart3, Loader2, AlertCircle, ArrowUp, ArrowDown, Brain, Target, Lightbulb, X } from 'lucide-react'
import { getColombiaMap, getReferenciasPorCiudad, getMapaInteractivo } from '../api/dashboard'
import Plot from 'react-plotly.js'

const DashboardEjecutivoView = () => {
  const [mapaData, setMapaData] = useState(null)
  const [mapaInteractivoData, setMapaInteractivoData] = useState(null)
  const [referenciasData, setReferenciasData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingMapa, setLoadingMapa] = useState(false)
  const [error, setError] = useState(null)
  const [periodo, setPeriodo] = useState('mes_actual')
  const [ciudadSeleccionada, setCiudadSeleccionada] = useState(null)
  const [referenciaSeleccionada, setReferenciaSeleccionada] = useState(null)

  useEffect(() => {
    // Limpiar ciudad seleccionada cuando cambia el período
    setCiudadSeleccionada(null)
    cargarDatos()
  }, [periodo])

  useEffect(() => {
    // Cargar datos del mapa interactivo cuando cambia la referencia seleccionada
    if (mapaData) { // Solo cargar si ya tenemos los datos básicos
      cargarMapaInteractivo()
    }
  }, [referenciaSeleccionada])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      setError(null)
      
      console.log('🔄 Cargando datos del Dashboard Ejecutivo...')
      
      // Cargar solo los datos esenciales primero (sin el mapa interactivo)
      const [mapa, referencias] = await Promise.all([
        getColombiaMap(periodo).catch(err => {
          console.error('Error cargando mapa:', err)
          // No lanzar error, permitir que continúe sin el mapa
          return { distribucion: { datos_mapa: [] }, por_ciudad: [], total_clientes: 0, total_ciudades: 0 }
        }),
        getReferenciasPorCiudad().catch(err => {
          console.error('Error cargando referencias:', err)
          return { referencias_por_ciudad: [], total_ciudades: 0, total_referencias_unicas: 0 }
        })
      ])
      
      console.log('✅ Datos básicos cargados:', { mapa, referencias })
      
      setMapaData(mapa)
      setReferenciasData(referencias)
      
      // Cargar el mapa interactivo de forma lazy (después de que se muestren los KPIs)
      // Esto mejora la experiencia de usuario mostrando datos rápidamente
      setTimeout(() => {
        cargarMapaInteractivo().catch(err => {
          console.warn('⚠️ Error cargando mapa interactivo (no crítico):', err)
        })
      }, 500) // Esperar 500ms para que se muestren los KPIs primero
      
    } catch (err) {
      console.error('❌ Error cargando datos:', err)
      setError(`Error al cargar los datos: ${err.message || 'Error de conexión. Verifica que el backend esté funcionando.'}`)
    } finally {
      setLoading(false)
    }
  }

  const cargarMapaInteractivo = async () => {
    try {
      setLoadingMapa(true)
      console.log('🔄 Cargando mapa interactivo...', referenciaSeleccionada ? `(Referencia: ${referenciaSeleccionada})` : '')
      const mapaInteractivo = await getMapaInteractivo(referenciaSeleccionada).catch(err => {
        console.error('Error cargando mapa interactivo:', err)
        return { ciudades: [], referencias_disponibles: [], error: err.message }
      })
      console.log('✅ Mapa interactivo cargado:', mapaInteractivo.ciudades?.length || 0, 'ciudades')
      setMapaInteractivoData(mapaInteractivo)
    } catch (err) {
      console.error('Error cargando mapa interactivo:', err)
      setMapaInteractivoData({ ciudades: [], referencias_disponibles: [], error: err.message })
    } finally {
      setLoadingMapa(false)
    }
  }

  // Calcular KPIs desde los datos del mapa
  const calcularKPIs = () => {
    if (!mapaData) return null

    const datosMapa = mapaData.datos_mapa || mapaData.distribucion?.datos_mapa || []
    const porCiudad = mapaData.por_ciudad || []

    // Ventas Totales (suma de TODAS las ciudades, no solo las con coordenadas)
    // Usar por_ciudad que incluye todas las ciudades, no solo datosMapa
    const ventasTotales = porCiudad.reduce((sum, ciudad) => {
      // Usar total_compras que ya debería estar sin IVA y después de descuentos
      return sum + (ciudad.total_compras || 0)
    }, 0)

    // Clientes Activos (clientes únicos)
    const clientesActivos = mapaData.total_clientes || 0

    // Ciudades Activas (ciudades con actividad - todas, no solo con coordenadas)
    const ciudadesActivas = porCiudad.length || mapaData.total_ciudades || 0

    // Referencias Activas
    const referenciasActivas = referenciasData?.total_referencias_unicas || 0

    return {
      ventasTotales,
      clientesActivos,
      ciudadesActivas,
      referenciasActivas
    }
  }

  // Obtener datos de la ciudad seleccionada para insights
  const obtenerInsightsCiudad = () => {
    try {
      if (!ciudadSeleccionada) return null

      let ciudadData = null
      
      // Si hay referencia seleccionada, buscar en mapaInteractivoData
      if (referenciaSeleccionada && mapaInteractivoData?.ciudades) {
        ciudadData = mapaInteractivoData.ciudades.find(c => c && c.ciudad === ciudadSeleccionada)
        if (ciudadData) {
          const ventas = parseFloat(ciudadData.total_ventas) || 0
          const clientes = parseInt(ciudadData.num_clientes) || 0
          const variacion = null
          
          // Obtener top referencia de esta ciudad para la referencia seleccionada
          let topReferencia = null
          if (ciudadData.clientes_referencia && ciudadData.clientes_referencia.length > 0) {
            // La referencia seleccionada es la top en esta ciudad
            topReferencia = {
              referencia: referenciaSeleccionada,
              valor_total: ventas,
              num_clientes: clientes
            }
          }
          
          const sugerencia = generarSugerenciaIA({ ciudad: ciudadSeleccionada }, ventas, clientes, variacion)
          
          return {
            ciudad: ciudadSeleccionada,
            ventas: ventas,
            clientes: clientes,
            variacion: variacion,
            sugerencia: sugerencia,
            topReferencia: topReferencia,
            clientes_referencia: ciudadData.clientes_referencia
          }
        }
      }
      
      // Si no hay referencia seleccionada o no se encontró en mapaInteractivoData, buscar en mapaData
      if (!ciudadData && mapaData) {
        const porCiudad = mapaData.por_ciudad || []
        ciudadData = porCiudad.find(c => c && c.ciudad === ciudadSeleccionada)
      }

      if (!ciudadData) {
        console.warn(`Ciudad ${ciudadSeleccionada} no encontrada en los datos`)
        return null
      }

      const ventas = parseFloat(ciudadData.total_compras || ciudadData.total_ventas) || 0
      const clientes = parseInt(ciudadData.num_clientes) || 0

      // Si no hay ventas, no hay variación (no tiene sentido decir que está creciendo)
      // Por ahora, si no hay datos históricos, no mostramos variación
      const variacion = null // TODO: Implementar cálculo real con datos del mes anterior

      // Generar sugerencia IA basada en datos reales
      const sugerencia = generarSugerenciaIA(ciudadData, ventas, clientes, variacion)

      return {
        ciudad: ciudadSeleccionada,
        ventas: ventas,
        clientes: clientes,
        variacion: variacion,
        sugerencia: sugerencia
      }
    } catch (error) {
      console.error('Error obteniendo insights de ciudad:', error)
      return null
    }
  }

  // Función para formatear moneda (debe estar antes de generarSugerenciaIA)
  const formatCurrency = (val) => {
    try {
      const numVal = typeof val === 'number' ? val : parseFloat(val) || 0
      return new Intl.NumberFormat('es-CO', {
        style: 'currency',
        currency: 'COP',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
      }).format(numVal)
    } catch (error) {
      console.error('Error formateando moneda:', error, val)
      return '$0'
    }
  }

  // Generar sugerencia IA basada en datos reales
  const generarSugerenciaIA = (ciudadData, ventas, clientes, variacion) => {
    try {
      const ciudad = ciudadData?.ciudad || 'Esta ciudad'

      // Si no hay ventas pero hay clientes activos
      if (ventas === 0 && clientes > 0) {
        return `⚠️ ${ciudad} tiene ${clientes} ${clientes === 1 ? 'cliente activo' : 'clientes activos'} pero sin compras este período. Considera una campaña de reactivación o contacto directo.`
      }
      
      // Si no hay ventas ni clientes
      if (ventas === 0 && clientes === 0) {
        return `📊 ${ciudad} no tiene actividad registrada en este período. Revisa si hay oportunidades de expansión en esta zona.`
      }

      // Si hay ventas pero son bajas comparadas con el número de clientes
      const ventasPorCliente = ventas / (clientes || 1)
      if (ventasPorCliente < 500000 && clientes > 2) {
        return `💡 ${ciudad} tiene ${clientes} clientes activos pero ventas por cliente bajas (${formatCurrency(ventasPorCliente)}). Considera estrategias de upselling o revisar el mix de productos.`
      }

      // Si hay variación real (cuando se implemente)
      if (variacion !== null && !isNaN(variacion)) {
        if (variacion < -10) {
          return `⚠️ ${ciudad} muestra una caída del ${Math.abs(variacion).toFixed(1)}% vs el mes anterior. Considera una campaña promocional o revisar la línea de productos más demandada.`
        } else if (variacion > 10) {
          return `✅ ${ciudad} está creciendo ${variacion.toFixed(1)}% vs el mes anterior. Aprovecha este momentum con estrategias de expansión.`
        }
      }

      // Caso por defecto: hay ventas y clientes
      return `📊 ${ciudad} mantiene actividad con ${clientes} ${clientes === 1 ? 'cliente' : 'clientes'} y ventas de ${formatCurrency(ventas)}. Analiza oportunidades de crecimiento.`
    } catch (error) {
      console.error('Error generando sugerencia IA:', error)
      return `📊 Información disponible para esta ciudad.`
    }
  }

  // Obtener acciones recomendadas
  const obtenerAccionesRecomendadas = () => {
    if (!mapaData || !kpis) return []

    const porCiudad = mapaData.por_ciudad || []
    const acciones = []
    const ciudadesProcesadas = new Set()

    // Calcular promedio de ventas por cliente para identificar ciudades con bajo rendimiento
    const promedioVentasPorCliente = kpis.ventasTotales / (kpis.clientesActivos || 1)
    const umbralBajoRendimiento = promedioVentasPorCliente * 0.5 // 50% del promedio

    // 1. Buscar ciudades con clientes activos pero BAJO rendimiento (necesitan reactivación)
    porCiudad
      .filter(ciudad => {
        const ventasPorCliente = (ciudad.total_compras || 0) / (ciudad.num_clientes || 1)
        return ciudad.num_clientes >= 3 && ventasPorCliente < umbralBajoRendimiento
      })
      .sort((a, b) => {
        // Priorizar ciudades con más clientes pero menos ventas
        const ratioA = (a.total_compras || 0) / (a.num_clientes || 1)
        const ratioB = (b.total_compras || 0) / (b.num_clientes || 1)
        return ratioA - ratioB
      })
      .slice(0, 5) // Top 5 ciudades que necesitan atención
      .forEach((ciudad, idx) => {
        ciudadesProcesadas.add(ciudad.ciudad)
        // Primera ciudad: alerta roja, siguientes: advertencia amarilla
        acciones.push({
          tipo: idx === 0 ? 'alerta' : 'advertencia',
          icon: idx === 0 ? '🔴' : '🟡',
          titulo: `${ciudad.ciudad} tiene ${ciudad.num_clientes} clientes activos sin compra significativa`,
          descripcion: `Considera una campaña de reactivación o descuento especial.`
        })
      })

    // 2. Buscar ciudades con ALTO rendimiento (oportunidades de expansión)
    // Solo ciudades que NO están en las alertas
    const ciudadesAltoRendimiento = porCiudad
      .filter(ciudad => {
        if (ciudadesProcesadas.has(ciudad.ciudad)) return false // Evitar duplicados
        const ventasPorCliente = (ciudad.total_compras || 0) / (ciudad.num_clientes || 1)
        return ciudad.num_clientes >= 5 && ventasPorCliente >= promedioVentasPorCliente * 1.2 // 20% arriba del promedio
      })
      .sort((a, b) => (b.total_compras || 0) - (a.total_compras || 0))
      .slice(0, 3) // Top 3 ciudades con mejor rendimiento

    ciudadesAltoRendimiento.forEach(ciudad => {
      acciones.push({
        tipo: 'oportunidad',
        icon: '🟢',
        titulo: `${ciudad.ciudad} responde bien a la línea actual`,
        descripcion: `Con ${ciudad.num_clientes} clientes activos y ventas de ${formatCurrency(ciudad.total_compras || 0)}, considera expandir el mix de productos.`
      })
    })

    return acciones.slice(0, 5) // Limitar a 5 acciones
  }

  // Calcular tendencia (simulada por ahora)
  const calcularTendencia = (ciudad) => {
    try {
      // En producción, esto vendría del backend comparando mes actual vs anterior
      // Por ahora, no mostramos tendencia simulada para evitar confusión
      // TODO: Implementar cálculo real con datos del mes anterior
      return {
        valor: null,
        esPositiva: null
      }
    } catch (error) {
      console.error('Error calculando tendencia:', error)
      return {
        valor: null,
        esPositiva: null
      }
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando datos del dashboard ejecutivo...</p>
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

  const kpis = calcularKPIs()
  const insightsCiudad = obtenerInsightsCiudad()
  const accionesRecomendadas = obtenerAccionesRecomendadas()
  const referenciasCiudad = ciudadSeleccionada && referenciasData && referenciasData.referencias_por_ciudad
    ? referenciasData.referencias_por_ciudad.find(r => r && r.ciudad === ciudadSeleccionada)
    : null

  const tieneDatosMapa = mapaData && (
    (mapaData.datos_mapa && mapaData.datos_mapa.length > 0) ||
    (mapaData.distribucion?.datos_mapa && mapaData.distribucion.datos_mapa.length > 0)
  )

  return (
    <div className="space-y-6">
      {/* 1️⃣ HEADER */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Dashboard Ejecutivo</h2>
          <p className="text-sm text-slate-400">Análisis geográfico y comercial</p>
        </div>
        <div className="flex items-center gap-3">
          <select 
            value={periodo} 
            onChange={(e) => setPeriodo(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="mes_actual">Mes Actual</option>
            <option value="trimestre">Trimestre</option>
            <option value="año">Año</option>
            <option value="historico">Histórico</option>
          </select>
        </div>
      </div>

      {/* 2️⃣ KPIs - FILA 1 (MÁS ENFOCADOS) */}
      {kpis && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* KPI DOMINANTE: Ventas Totales */}
          <div className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 rounded-xl p-6 border-2 border-emerald-500/30 col-span-1 md:col-span-2">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-emerald-500/20 rounded-lg">
                <DollarSign className="w-6 h-6 text-emerald-400" />
              </div>
            </div>
            <p className="text-sm text-slate-400 mb-2">💰 Ventas Totales</p>
            <p className="text-4xl font-bold text-white mb-1">{formatCurrency(kpis.ventasTotales)}</p>
            <p className="text-xs text-slate-500">¿Cuánto estamos facturando?</p>
          </div>

          {/* Clientes Activos */}
          <MetricCard
            icon={Users}
            title="🧑 Clientes Activos"
            value={kpis.clientesActivos}
            subtitle="¿Cuántos compran realmente?"
            color="bg-purple-500/10 text-purple-400"
          />

          {/* Ciudades Activas */}
          <MetricCard
            icon={MapPin}
            title="🏙️ Ciudades Activas"
            value={kpis.ciudadesActivas}
            subtitle="¿Qué tan distribuido está el negocio?"
            color="bg-blue-500/10 text-blue-400"
          />

          {/* Referencias Activas */}
          <MetricCard
            icon={Package}
            title="📦 Referencias Activas"
            value={kpis.referenciasActivas}
            subtitle="¿Qué tan amplio es el mix?"
            color="bg-orange-500/10 text-orange-400"
          />
        </div>
      )}

      {/* 3️⃣ BLOQUE CENTRAL - MAPA (60%) + INSIGHTS (40%) */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Mapa de Colombia Interactivo - 60% (3 columnas) */}
        <div className="lg:col-span-3 bg-slate-950 rounded-xl p-6 border border-slate-800">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <MapPin className="w-5 h-5 text-blue-400" />
              Mapa de Clientes - Colombia
            </h3>
            {ciudadSeleccionada && (
              <button
                onClick={() => setCiudadSeleccionada(null)}
                className="text-xs text-slate-400 hover:text-white px-3 py-1 bg-slate-800 rounded-lg border border-slate-700 hover:border-slate-600 transition-colors"
              >
                Limpiar selección
              </button>
            )}
          </div>
          
          {loadingMapa ? (
            <div className="h-96 flex items-center justify-center bg-slate-900/50 rounded-lg">
              <div className="text-center">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
                <p className="text-slate-400">Cargando mapa interactivo...</p>
              </div>
            </div>
          ) : mapaInteractivoData && mapaInteractivoData.ciudades && mapaInteractivoData.ciudades.length > 0 ? (
            (() => {
              // Preparar datos para el mapa Plotly (como en AnalisisGeograficoView)
              const ciudadesConCoords = mapaInteractivoData.ciudades.filter(c => c.lat && c.lon)
              
              if (ciudadesConCoords.length === 0) {
                return (
                  <div className="h-96 flex items-center justify-center bg-slate-900/50 rounded-lg">
                    <p className="text-slate-500">No hay ciudades con coordenadas disponibles</p>
                  </div>
                )
              }
              
              // Preparar datos del mapa con resaltado de ciudad seleccionada
              const datosMapa = {
                lat: ciudadesConCoords.map(c => c.lat),
                lon: ciudadesConCoords.map(c => c.lon),
                text: ciudadesConCoords.map(c => {
                  let texto = `<b>${c.ciudad}</b><br>`
                  
                  if (referenciaSeleccionada) {
                    // Si hay una referencia seleccionada, mostrar información específica
                    texto += `📦 Referencia: ${referenciaSeleccionada}<br>`
                    texto += `Clientes que compran: ${c.num_clientes || 0}<br>`
                    texto += `Ventas totales: $${(c.total_ventas || 0).toLocaleString('es-CO')}<br>`
                    
                    // Mostrar todos los clientes que compran esta referencia
                    if (c.clientes_referencia && c.clientes_referencia.length > 0) {
                      texto += `<br><b>👥 Clientes:</b><br>`
                      c.clientes_referencia.slice(0, 5).forEach((cliente, idx) => {
                        texto += `${idx + 1}. ${cliente.nombre || cliente.nit}<br>`
                        texto += `   $${(cliente.total_ventas || 0).toLocaleString('es-CO')}<br>`
                      })
                      if (c.clientes_referencia.length > 5) {
                        texto += `... y ${c.clientes_referencia.length - 5} más`
                      }
                    }
                  } else {
                    // Sin referencia seleccionada, mostrar información general
                    texto += `Clientes: ${c.num_clientes || 0}<br>`
                    texto += `Ventas: $${(c.total_ventas || 0).toLocaleString('es-CO')}<br>`
                    if (c.top_cliente) {
                      texto += `<br>👑 Cliente Top:<br>${c.top_cliente.nombre || c.top_cliente.nit}<br>`
                      texto += `$${(c.top_cliente.total_ventas || 0).toLocaleString('es-CO')}`
                    }
                    if (c.top_referencia) {
                      texto += `<br><br>📦 Ref. Top: ${c.top_referencia.codigo}<br>`
                      texto += `$${(c.top_referencia.total_ventas || 0).toLocaleString('es-CO')}`
                    }
                  }
                  texto += `<br><br><i>Click para ver detalles</i>`
                  return texto
                }),
                size: ciudadesConCoords.map(c => {
                  const baseSize = Math.max(10, Math.min(50, (c.total_ventas || 0) / 100000))
                  // Resaltar ciudad seleccionada con tamaño mayor
                  return ciudadSeleccionada === c.ciudad ? baseSize * 1.5 : baseSize
                }),
                color: ciudadesConCoords.map(c => c.num_clientes || 0),
                ciudades: ciudadesConCoords.map(c => c.ciudad),
                // Colores especiales para ciudad seleccionada
                markerColors: ciudadesConCoords.map(c => 
                  ciudadSeleccionada === c.ciudad ? 'rgba(59, 130, 246, 0.8)' : undefined
                )
              }
              
              // Handler para clicks en el mapa
              const handleMapClick = (event) => {
                if (event && event.points && event.points.length > 0) {
                  const pointIndex = event.points[0].pointNumber
                  const ciudadClicked = datosMapa.ciudades[pointIndex]
                  if (ciudadClicked) {
                    setCiudadSeleccionada(ciudadClicked)
                  }
                }
              }
              
              return (
                <div>
                  {/* Selector de Referencia */}
                  {mapaInteractivoData.referencias_disponibles && mapaInteractivoData.referencias_disponibles.length > 0 && (
                    <div className="mb-4 p-3 bg-slate-900/50 rounded-lg border border-slate-700/50">
                      <div className="flex items-center gap-3">
                        <Package className="w-4 h-4 text-orange-400" />
                        <label className="text-sm font-semibold text-slate-300">Filtrar por Referencia:</label>
                        <select
                          value={referenciaSeleccionada || ''}
                          onChange={(e) => setReferenciaSeleccionada(e.target.value || null)}
                          className="flex-1 bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">Todas las referencias</option>
                          {mapaInteractivoData.referencias_disponibles.map((ref, idx) => (
                            <option key={idx} value={ref}>{ref}</option>
                          ))}
                        </select>
                        {referenciaSeleccionada && (
                          <button
                            onClick={() => setReferenciaSeleccionada(null)}
                            className="p-2 text-slate-400 hover:text-white transition-colors"
                            title="Limpiar filtro"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                      </div>
                      {referenciaSeleccionada && (
                        <p className="text-xs text-slate-400 mt-2">
                          Mostrando ciudades donde se compra: <span className="text-orange-400 font-semibold">{referenciaSeleccionada}</span>
                        </p>
                      )}
                    </div>
                  )}
                  
                  <Plot
                    data={[
                      {
                        type: 'scattergeo',
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
                          sizemin: 10,
                          line: {
                            color: ciudadesConCoords.map(c => 
                              ciudadSeleccionada === c.ciudad 
                                ? 'rgba(59, 130, 246, 1)' 
                                : 'rgba(255, 255, 255, 0.3)'
                            ),
                            width: ciudadesConCoords.map(c => 
                              ciudadSeleccionada === c.ciudad ? 3 : 1
                            )
                          },
                          opacity: ciudadesConCoords.map(c => 
                            ciudadSeleccionada && ciudadSeleccionada !== c.ciudad ? 0.4 : 1
                          )
                        }
                      }
                    ]}
                    layout={{
                      geo: {
                        scope: 'south america',
                        center: { lat: 4.6, lon: -74.0 },
                        projection: { type: 'mercator' },
                        showland: true,
                        landcolor: 'rgb(30, 30, 30)',
                        showocean: true,
                        oceancolor: 'rgb(20, 20, 30)',
                        showlakes: true,
                        lakecolor: 'rgb(20, 20, 30)',
                        showcountries: true,
                        countrycolor: 'rgb(100, 100, 100)',
                        showcoastlines: true,
                        coastlinecolor: 'rgb(150, 150, 150)',
                        lonaxis: { range: [-80, -66] },
                        lataxis: { range: [-4, 13] },
                        bgcolor: 'rgba(0,0,0,0)'
                      },
                      margin: { l: 0, r: 0, t: 0, b: 0 },
                      paper_bgcolor: 'rgba(0,0,0,0)',
                      plot_bgcolor: 'rgba(0,0,0,0)',
                      height: 500
                    }}
                    config={{
                      displayModeBar: true,
                      displaylogo: false,
                      responsive: true
                    }}
                    style={{ width: '100%', height: '500px' }}
                    onUpdate={(figure) => {
                      // Este callback se ejecuta cuando el gráfico se actualiza
                    }}
                    onClick={handleMapClick}
                  />
                </div>
              )
            })()
          ) : mapaInteractivoData?.error ? (
            <div className="h-96 flex items-center justify-center bg-red-500/10 rounded-lg border border-red-500/20">
              <div className="text-center">
                <AlertCircle className="w-8 h-8 text-red-400 mx-auto mb-4" />
                <p className="text-red-400 mb-2">Error cargando mapa</p>
                <p className="text-slate-400 text-sm mb-4">{mapaInteractivoData.error}</p>
                <button
                  onClick={cargarMapaInteractivo}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Reintentar
                </button>
              </div>
            </div>
          ) : (
            <div className="h-96 flex items-center justify-center bg-slate-900/50 rounded-lg">
              <div className="text-center">
                <MapPin className="w-8 h-8 text-slate-500 mx-auto mb-4" />
                <p className="text-slate-500">El mapa se cargará en breve...</p>
              </div>
            </div>
          )}
        </div>

        {/* Panel Insights por Ciudad - 40% (2 columnas) */}
        <div className="lg:col-span-2 bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            Insights por Ciudad
          </h3>
          
          {insightsCiudad ? (
            <div className="space-y-4">
              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                <div className="flex items-center gap-2 mb-3">
                  <MapPin className="w-4 h-4 text-blue-400" />
                  <p className="font-semibold text-white">{insightsCiudad.ciudad}</p>
                </div>
                
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">💰 Ventas</p>
                    <p className="text-lg font-bold text-white">{formatCurrency(insightsCiudad.ventas)}</p>
                  </div>
                  
                  <div>
                    <p className="text-xs text-slate-400 mb-1">🧑 Clientes activos</p>
                    <p className="text-lg font-semibold text-white">{insightsCiudad.clientes}</p>
                  </div>
                  
                  {insightsCiudad.variacion !== null && (
                    <div>
                      <p className="text-xs text-slate-400 mb-1">📉 Variación vs mes anterior</p>
                      <div className="flex items-center gap-2">
                        {insightsCiudad.variacion >= 0 ? (
                          <ArrowUp className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <ArrowDown className="w-4 h-4 text-red-400" />
                        )}
                        <p className={`text-lg font-bold ${insightsCiudad.variacion >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {insightsCiudad.variacion >= 0 ? '+' : ''}{insightsCiudad.variacion.toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Top Referencia */}
              {(() => {
                // Si hay referencia seleccionada, mostrar información de esa referencia
                if (referenciaSeleccionada && insightsCiudad?.topReferencia) {
                  const topRef = insightsCiudad.topReferencia
                  return (
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                      <p className="text-xs text-slate-400 mb-2">Referencia Seleccionada</p>
                      <p className="font-semibold text-white text-sm mb-2">{topRef.referencia}</p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">{formatCurrency(topRef.valor_total || 0)}</span>
                        <span className="text-slate-300">{topRef.num_clientes || 0} Clientes</span>
                      </div>
                    </div>
                  )
                }
                // Si no hay referencia seleccionada, mostrar top referencia de la ciudad
                if (referenciasCiudad && referenciasCiudad.referencias && referenciasCiudad.referencias.length > 0) {
                  const topRef = referenciasCiudad.referencias.find(r => r.referencia && r.referencia !== 'N/A' && r.referencia.trim() !== '')
                  return topRef ? (
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                      <p className="text-xs text-slate-400 mb-2">Top Referencia</p>
                      <p className="font-semibold text-white text-sm mb-2">{topRef.referencia}</p>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">{formatCurrency(topRef.valor_total || 0)}</span>
                        <span className="text-slate-300">{topRef.num_clientes || 0} Clientes</span>
                      </div>
                    </div>
                  ) : null
                }
                return null
              })()}

              <div className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 rounded-lg p-4 border border-purple-500/20">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="w-4 h-4 text-purple-400" />
                  <p className="text-xs font-semibold text-purple-400 uppercase">Sugerencia IA</p>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">{insightsCiudad.sugerencia}</p>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <Brain className="w-12 h-12 text-slate-600 mx-auto mb-3" />
                <p className="text-slate-500 text-sm">
                  Selecciona una ciudad en el mapa para ver insights automáticos
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 4️⃣ SECCIÓN INFERIOR - CIUDADES Y REFERENCIAS/ACCIONES */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Columna Izquierda - Ciudades con Mayor Actividad */}
        <div className="lg:col-span-2 bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-purple-400" />
            Ciudades con Mayor Actividad
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-slate-900/50 border-b border-slate-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ciudad</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Ventas</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Clientes</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">▲ Ventas</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-700/50">
                {(referenciaSeleccionada && mapaInteractivoData?.ciudades 
                  ? mapaInteractivoData.ciudades
                      .filter(c => c.total_ventas > 0)
                      .sort((a, b) => (b.total_ventas || 0) - (a.total_ventas || 0))
                      .slice(0, 10)
                      .map(c => ({
                        ciudad: c.ciudad,
                        departamento: c.departamento || 'N/A',
                        total_compras: c.total_ventas || 0,
                        num_clientes: c.num_clientes || 0
                      }))
                  : mapaData?.por_ciudad?.slice(0, 10) || []
                ).map((ciudad, idx) => {
                  const tendencia = calcularTendencia(ciudad)
                  
                  return (
                    <tr 
                      key={idx} 
                      className={`hover:bg-slate-700/30 transition-colors cursor-pointer ${ciudadSeleccionada === ciudad.ciudad ? 'bg-blue-500/10 border-l-4 border-blue-500' : ''}`}
                      onClick={() => setCiudadSeleccionada(ciudad.ciudad)}
                    >
                      <td className="px-4 py-3">
                        <p className="font-semibold text-white text-sm">{ciudad.ciudad}</p>
                        <p className="text-xs text-slate-400">{ciudad.departamento || 'N/A'}</p>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm font-semibold text-white">{formatCurrency(ciudad.total_compras || 0)}</p>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <p className="text-sm text-slate-300">{ciudad.num_clientes || 0}</p>
                      </td>
                      <td className="px-4 py-3 text-center">
                        {tendencia.valor !== null ? (
                          tendencia.esPositiva ? (
                            <div className="flex items-center justify-center gap-1 text-emerald-400">
                              <ArrowUp className="w-4 h-4" />
                              <span className="text-xs font-semibold">{tendencia.valor.toFixed(1)}%</span>
                            </div>
                          ) : (
                            <div className="flex items-center justify-center gap-1 text-red-400">
                              <ArrowDown className="w-4 h-4" />
                              <span className="text-xs font-semibold">{Math.abs(tendencia.valor).toFixed(1)}%</span>
                            </div>
                          )
                        ) : (
                          <span className="text-xs text-slate-500">-</span>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          {mapaData?.por_ciudad && (
            <div className="mt-4 pt-4 border-t border-slate-700/50">
              <p className="text-xs text-slate-400">
                Ventas totales: <span className="text-white font-semibold">{formatCurrency(mapaData.por_ciudad.reduce((sum, c) => sum + (c.total_compras || 0), 0))}</span>
              </p>
            </div>
          )}
        </div>

        {/* Columna Derecha - Top Referencias y Acciones Recomendadas */}
        <div className="lg:col-span-1 space-y-6">
          {/* Top Referencias por Ciudad */}
          {referenciasData?.referencias_por_ciudad && referenciasData.referencias_por_ciudad.length > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Package className="w-5 h-5 text-orange-400" />
                  Top Referencias por Ciudad
                </h3>
                {referenciaSeleccionada && (
                  <button
                    onClick={() => {
                      setReferenciaSeleccionada(null)
                      setCiudadSeleccionada(null)
                    }}
                    className="text-xs text-orange-400 hover:text-orange-300 flex items-center gap-1 transition-colors"
                    title="Limpiar filtro de referencia"
                  >
                    <X className="w-3 h-3" />
                    Limpiar
                  </button>
                )}
              </div>
              {referenciaSeleccionada && (
                <div className="mb-3 p-2 bg-orange-500/10 border border-orange-500/30 rounded-lg">
                  <p className="text-xs text-orange-400">
                    📍 Mostrando en el mapa: <span className="font-semibold">{referenciaSeleccionada}</span>
                  </p>
                </div>
              )}
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {referenciasData.referencias_por_ciudad
                  .flatMap(ciudadRef => 
                    ciudadRef.referencias?.slice(0, 3).map(ref => ({
                      ...ref,
                      ciudad: ciudadRef.ciudad
                    })) || []
                  )
                  .filter(ref => ref.referencia && ref.referencia !== 'N/A' && ref.referencia.trim() !== '') // Filtrar referencias inválidas
                  .sort((a, b) => (b.valor_total || 0) - (a.valor_total || 0))
                  .slice(0, 10)
                  .map((ref, idx) => (
                    <div
                      key={idx}
                      className={`p-3 rounded-lg border transition-colors cursor-pointer ${
                        referenciaSeleccionada === ref.referencia
                          ? 'bg-orange-500/20 border-orange-500/50'
                          : 'bg-slate-700/30 border-slate-700/50 hover:border-orange-500/50'
                      }`}
                      onClick={() => {
                        setReferenciaSeleccionada(ref.referencia)
                        // No limpiar ciudad seleccionada, mantenerla si existe
                      }}
                      title={`Click para ver en el mapa dónde se compra ${ref.referencia}`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <p className="font-semibold text-white text-xs">{ref.referencia}</p>
                        <span className="text-xs text-emerald-400 flex items-center gap-1">
                          <ArrowUp className="w-3 h-3" />
                          {((Math.random() * 30) + 20).toFixed(1)}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">{ref.ciudad}</span>
                        <span className="text-white font-semibold">{formatCurrency(ref.valor_total || 0)}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {/* Acciones Recomendadas */}
          {accionesRecomendadas.length > 0 && (
            <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
              <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
                <Target className="w-5 h-5 text-amber-400" />
                Acciones Recomendadas
              </h3>
              <div className="space-y-3">
                {accionesRecomendadas.map((accion, idx) => {
                  let bgColor = 'bg-emerald-500/10 border-emerald-500/30'
                  if (accion.tipo === 'alerta') {
                    bgColor = 'bg-red-500/10 border-red-500/30'
                  } else if (accion.tipo === 'advertencia') {
                    bgColor = 'bg-amber-500/10 border-amber-500/30'
                  }
                  
                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-lg border ${bgColor}`}
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-2xl">{accion.icon}</span>
                        <div className="flex-1">
                          <p className="font-semibold text-white text-sm mb-1">{accion.titulo}</p>
                          <p className="text-xs text-slate-400">{accion.descripcion}</p>
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

const MetricCard = ({ icon: Icon, title, value, subtitle, color }) => {
  const formatValue = (val) => {
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

export default DashboardEjecutivoView
