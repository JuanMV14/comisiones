import React, { useState, useEffect } from 'react'
import { FileText, Search, Calendar, DollarSign, TrendingUp, Loader2, Eye, Filter, Download, Edit, CheckCircle, Upload, X, Save, FileImage } from 'lucide-react'
import { getFacturas, actualizarFactura, marcarFacturaPagado, subirComprobantePago, obtenerComprobantePago } from '../api/facturas'
import { getMesesDisponibles } from '../api/dashboard'

const ComisionesView = () => {
  const [facturas, setFacturas] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [mesSeleccionado, setMesSeleccionado] = useState(null)
  const [mesesDisponibles, setMesesDisponibles] = useState([])
  const [facturaSeleccionada, setFacturaSeleccionada] = useState(null)
  const [mostrarDetalle, setMostrarDetalle] = useState(false)
  const [mostrarEditar, setMostrarEditar] = useState(false)
  const [mostrarMarcarPagado, setMostrarMarcarPagado] = useState(false)
  const [mostrarSubirComprobante, setMostrarSubirComprobante] = useState(false)
  const [editando, setEditando] = useState(false)
  const [formData, setFormData] = useState({})
  const [archivoComprobante, setArchivoComprobante] = useState(null)
  const [fechaPago, setFechaPago] = useState(new Date().toISOString().split('T')[0])
  const [mostrarComprobante, setMostrarComprobante] = useState(false)
  const [comprobanteData, setComprobanteData] = useState(null)
  const [cargandoComprobante, setCargandoComprobante] = useState(false)

  useEffect(() => {
    const cargarMeses = async () => {
      try {
        const mesesData = await getMesesDisponibles()
        if (mesesData && mesesData.meses && mesesData.meses.length > 0) {
          setMesesDisponibles(mesesData.meses)
          setMesSeleccionado(mesesData.meses[0].valor) // Mes más reciente por defecto
        }
      } catch (err) {
        console.error('Error cargando meses:', err)
      }
    }
    cargarMeses()
  }, [])

  useEffect(() => {
    // Cargar facturas siempre, incluso cuando mesSeleccionado es null (Ver Todo)
    cargarFacturas()
  }, [mesSeleccionado, searchTerm])

  const cargarFacturas = async () => {
    try {
      setLoading(true)
      setError(null)
      // Si mesSeleccionado es null, pasar null para obtener todas las facturas
      const data = await getFacturas(mesSeleccionado || null, searchTerm || null, false)
      setFacturas(data.facturas || [])
    } catch (err) {
      console.error('Error cargando facturas:', err)
      setError(`Error al cargar las facturas: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(val)
  }

  const formatDate = (dateStr) => {
    if (!dateStr || dateStr === 'N/A') return 'N/A'
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('es-CO', { year: 'numeric', month: 'short', day: 'numeric' })
    } catch {
      return dateStr
    }
  }

  const getEstadoColor = (estado) => {
    switch (estado) {
      case 'Pagado':
        return 'bg-emerald-500/20 text-emerald-400'
      case 'Vencido':
        return 'bg-red-500/20 text-red-400'
      default:
        return 'bg-amber-500/20 text-amber-400'
    }
  }

  const facturasFiltradas = facturas.filter(factura =>
    factura.cliente.toLowerCase().includes(searchTerm.toLowerCase()) ||
    factura.factura.toLowerCase().includes(searchTerm.toLowerCase()) ||
    factura.pedido.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totales = {
    // Usar valor_neto_final (sin IVA, después de descuentos y devoluciones) si está disponible
    // Si no, usar valor_neto_ajustado, y si tampoco, usar valor_neto
    valor: facturasFiltradas.reduce((sum, f) => {
      if (f.valor_neto_final !== undefined) {
        return sum + (f.valor_neto_final || 0)
      } else if (f.valor_neto_ajustado !== undefined) {
        return sum + (f.valor_neto_ajustado || 0)
      } else {
        return sum + (f.valor_neto || 0)
      }
    }, 0),
    comisiones: facturasFiltradas.reduce((sum, f) => sum + (f.comision || 0), 0),
    cantidad: facturasFiltradas.length
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando facturas...</p>
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
            onClick={cargarFacturas}
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Facturas</h2>
          <p className="text-sm text-slate-400">Gestión y consulta de tus facturas</p>
        </div>
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
              <option value="">Cargando meses...</option>
            )}
          </select>
        </div>
      </div>

      {/* Métricas Resumen */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-blue-500/10 rounded-lg">
              <FileText className="w-5 h-5 text-blue-400" />
            </div>
          </div>
          <p className="text-sm text-slate-400 mb-1">Total Facturas</p>
          <p className="text-2xl font-bold text-white">{totales.cantidad}</p>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-emerald-500/10 rounded-lg">
              <DollarSign className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
          <p className="text-sm text-slate-400 mb-1">Valor Total</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(totales.valor)}</p>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
          <div className="flex items-center justify-between mb-2">
            <div className="p-2 bg-purple-500/10 rounded-lg">
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
          </div>
          <p className="text-sm text-slate-400 mb-1">Total Comisiones</p>
          <p className="text-2xl font-bold text-white">{formatCurrency(totales.comisiones)}</p>
        </div>
      </div>

      {/* Búsqueda y Filtros */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
        <div className="flex items-center gap-3">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Buscar por cliente, factura o pedido..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
      </div>

      {/* Tabla de Facturas */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Factura</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Fecha</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Valor</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Comisión</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {facturasFiltradas.length > 0 ? (
                facturasFiltradas.map((factura) => (
                  <tr key={factura.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-4">
                      <div>
                        <p className="font-semibold text-white text-sm">{factura.factura}</p>
                        <p className="text-xs text-slate-400">Pedido: {factura.pedido}</p>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-sm text-slate-300">{factura.cliente}</p>
                      {factura.ciudad_destino && factura.ciudad_destino !== 'N/A' && (
                        <p className="text-xs text-slate-500">{factura.ciudad_destino}</p>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-sm text-slate-300">{formatDate(factura.fecha_factura)}</p>
                      {factura.fecha_pago && (
                        <p className="text-xs text-slate-500">Pagado: {formatDate(factura.fecha_pago)}</p>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      {/* Mostrar valor_neto_final (sin IVA, después de descuentos y devoluciones) si está disponible */}
                      {factura.valor_neto_final !== undefined ? (
                        <>
                          <p className="text-sm font-semibold text-white">{formatCurrency(factura.valor_neto_final)}</p>
                          <p className="text-xs text-slate-400">Sin IVA, después de descuentos</p>
                        </>
                      ) : factura.valor_neto_ajustado !== undefined ? (
                        <>
                          <p className="text-sm font-semibold text-white">{formatCurrency(factura.valor_neto_ajustado)}</p>
                          <p className="text-xs text-slate-400">Sin IVA, después de descuentos</p>
                        </>
                      ) : (
                        <>
                          <p className="text-sm font-semibold text-white">{formatCurrency(factura.valor_neto || 0)}</p>
                          <p className="text-xs text-slate-400">Neto: {formatCurrency(factura.valor_neto || 0)}</p>
                        </>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-sm font-semibold text-emerald-400">{formatCurrency(factura.comision)}</p>
                      <p className="text-xs text-slate-400">{factura.porcentaje}%</p>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${getEstadoColor(factura.estado)}`}>
                        {factura.estado}
                      </span>
                      {factura.dias_pago !== null && (
                        <p className="text-xs text-slate-500 mt-1">{factura.dias_pago} días</p>
                      )}
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            setFacturaSeleccionada(factura)
                            setMostrarDetalle(true)
                          }}
                          className="p-1.5 text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
                          title="Ver detalle"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            setFacturaSeleccionada(factura)
                            // Convertir fecha de pago si existe
                            let fechaPagoFormato = null
                            if (factura.fecha_pago) {
                              fechaPagoFormato = factura.fecha_pago.split('T')[0]
                            } else if (factura.fecha_pago_real) {
                              fechaPagoFormato = factura.fecha_pago_real.split('T')[0]
                            }
                            
                            setFormData({
                              pedido: factura.pedido,
                              factura: factura.factura,
                              cliente: factura.cliente,
                              fecha_factura: factura.fecha_factura,
                              fecha_pago_real: fechaPagoFormato,
                              valor_total: factura.valor,
                              valor_flete: factura.valor_flete || 0,
                              descuento_adicional: factura.descuento_adicional || 0,
                              ciudad_destino: factura.ciudad_destino,
                              referencia: factura.referencia
                            })
                            setMostrarEditar(true)
                          }}
                          className="p-1.5 text-amber-400 hover:bg-amber-500/10 rounded transition-colors"
                          title="Editar factura"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        {factura.pagado && (
                          <button
                            onClick={async () => {
                              try {
                                setCargandoComprobante(true)
                                setFacturaSeleccionada(factura)
                                const comprobante = await obtenerComprobantePago(factura.id)
                                setComprobanteData(comprobante)
                                setMostrarComprobante(true)
                              } catch (error) {
                                if (error.response?.status === 404) {
                                  alert('Esta factura no tiene comprobante de pago subido')
                                } else {
                                  alert(`Error al cargar comprobante: ${error.response?.data?.detail || error.message}`)
                                }
                              } finally {
                                setCargandoComprobante(false)
                              }
                            }}
                            className="p-1.5 text-indigo-400 hover:bg-indigo-500/10 rounded transition-colors"
                            title="Ver comprobante de pago"
                          >
                            <FileImage className="w-4 h-4" />
                          </button>
                        )}
                        {!factura.pagado && (
                          <>
                            <button
                              onClick={() => {
                                setFacturaSeleccionada(factura)
                                setFechaPago(new Date().toISOString().split('T')[0])
                                setMostrarMarcarPagado(true)
                              }}
                              className="p-1.5 text-emerald-400 hover:bg-emerald-500/10 rounded transition-colors"
                              title="Marcar como pagado"
                            >
                              <CheckCircle className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => {
                                setFacturaSeleccionada(factura)
                                setFechaPago(new Date().toISOString().split('T')[0])
                                setArchivoComprobante(null)
                                setMostrarSubirComprobante(true)
                              }}
                              className="p-1.5 text-purple-400 hover:bg-purple-500/10 rounded transition-colors"
                              title="Subir comprobante"
                            >
                              <Upload className="w-4 h-4" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" className="px-4 py-8 text-center">
                    <p className="text-slate-500">
                      {mesSeleccionado === null 
                        ? 'No se encontraron facturas' 
                        : 'No se encontraron facturas para este mes'}
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal de Detalle de Factura */}
      {mostrarDetalle && facturaSeleccionada && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">Detalle de Factura</h3>
              <button
                onClick={() => {
                  setMostrarDetalle(false)
                  setFacturaSeleccionada(null)
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                ✕
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-xs text-slate-400 mb-1">Número de Factura</p>
                  <p className="text-lg font-bold text-white">{facturaSeleccionada.factura}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Pedido</p>
                  <p className="text-lg font-semibold text-white">{facturaSeleccionada.pedido}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Cliente</p>
                  <p className="text-sm font-medium text-white">{facturaSeleccionada.cliente}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Fecha de Factura</p>
                  <p className="text-sm text-white">{formatDate(facturaSeleccionada.fecha_factura)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Ciudad Destino</p>
                  <p className="text-sm text-white">{facturaSeleccionada.ciudad_destino || 'N/A'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-400 mb-1">Referencia</p>
                  <p className="text-sm text-white">{facturaSeleccionada.referencia || 'N/A'}</p>
                </div>
              </div>

              <div className="border-t border-slate-700 pt-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Valores</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Valor Total</p>
                    <p className="text-lg font-bold text-white">{formatCurrency(facturaSeleccionada.valor)}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Valor Neto</p>
                    <p className="text-lg font-semibold text-white">{formatCurrency(facturaSeleccionada.valor_neto)}</p>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-700 pt-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Comisión</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Porcentaje</p>
                    <p className="text-lg font-semibold text-white">{facturaSeleccionada.porcentaje}%</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Comisión Calculada</p>
                    <p className="text-lg font-bold text-emerald-400">{formatCurrency(facturaSeleccionada.comision)}</p>
                  </div>
                </div>
              </div>

              <div className="border-t border-slate-700 pt-4">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Estado</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs text-slate-400 mb-1">Estado</p>
                    <span className={`inline-flex px-3 py-1 rounded text-sm font-medium ${getEstadoColor(facturaSeleccionada.estado)}`}>
                      {facturaSeleccionada.estado}
                    </span>
                  </div>
                  {facturaSeleccionada.dias_pago !== null && (
                    <div>
                      <p className="text-xs text-slate-400 mb-1">Días de Pago</p>
                      <p className="text-sm font-semibold text-white">{facturaSeleccionada.dias_pago} días</p>
                    </div>
                  )}
                  {facturaSeleccionada.fecha_pago && (
                    <div>
                      <p className="text-xs text-slate-400 mb-1">Fecha de Pago</p>
                      <p className="text-sm text-white">{formatDate(facturaSeleccionada.fecha_pago)}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Editar Factura */}
      {mostrarEditar && facturaSeleccionada && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">Editar Factura</h3>
              <button
                onClick={() => {
                  setMostrarEditar(false)
                  setFacturaSeleccionada(null)
                  setFormData({})
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Pedido</label>
                  <input
                    type="text"
                    value={formData.pedido || ''}
                    onChange={(e) => setFormData({ ...formData, pedido: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Factura</label>
                  <input
                    type="text"
                    value={formData.factura || ''}
                    onChange={(e) => setFormData({ ...formData, factura: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Cliente</label>
                  <input
                    type="text"
                    value={formData.cliente || ''}
                    onChange={(e) => setFormData({ ...formData, cliente: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Fecha Factura</label>
                  <input
                    type="date"
                    value={formData.fecha_factura ? formData.fecha_factura.split('T')[0] : ''}
                    onChange={(e) => setFormData({ ...formData, fecha_factura: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Fecha de Pago {facturaSeleccionada?.pagado && <span className="text-xs text-emerald-400">(Pagada)</span>}
                  </label>
                  <input
                    type="date"
                    value={formData.fecha_pago_real ? formData.fecha_pago_real.split('T')[0] : (facturaSeleccionada?.fecha_pago ? facturaSeleccionada.fecha_pago.split('T')[0] : '')}
                    onChange={(e) => setFormData({ ...formData, fecha_pago_real: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="DD/MM/YYYY o YYYY-MM-DD"
                  />
                  {facturaSeleccionada?.pagado && !formData.fecha_pago_real && !facturaSeleccionada?.fecha_pago && (
                    <p className="text-xs text-amber-400 mt-1">⚠️ Esta factura está marcada como pagada pero no tiene fecha de pago</p>
                  )}
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Valor Total</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.valor_total || 0}
                    onChange={(e) => setFormData({ ...formData, valor_total: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Valor Flete</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.valor_flete || 0}
                    onChange={(e) => setFormData({ ...formData, valor_flete: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Descuento Adicional (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.descuento_adicional || 0}
                    onChange={(e) => setFormData({ ...formData, descuento_adicional: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Ciudad Destino</label>
                  <input
                    type="text"
                    value={formData.ciudad_destino || ''}
                    onChange={(e) => setFormData({ ...formData, ciudad_destino: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-slate-300 mb-2">Referencia</label>
                  <input
                    type="text"
                    value={formData.referencia || ''}
                    onChange={(e) => setFormData({ ...formData, referencia: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-slate-800 border-t border-slate-700 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setMostrarEditar(false)
                  setFacturaSeleccionada(null)
                  setFormData({})
                }}
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                disabled={editando}
              >
                Cancelar
              </button>
              <button
                onClick={async () => {
                  try {
                    setEditando(true)
                    await actualizarFactura(facturaSeleccionada.id, formData)
                    alert('✅ Factura actualizada correctamente')
                    setMostrarEditar(false)
                    setFacturaSeleccionada(null)
                    setFormData({})
                    await cargarFacturas()
                  } catch (error) {
                    alert(`Error al actualizar factura: ${error.response?.data?.detail || error.message}`)
                  } finally {
                    setEditando(false)
                  }
                }}
                disabled={editando}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {editando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Guardar Cambios
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Marcar como Pagado */}
      {mostrarMarcarPagado && facturaSeleccionada && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">Marcar como Pagado</h3>
              <button
                onClick={() => {
                  setMostrarMarcarPagado(false)
                  setFacturaSeleccionada(null)
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-slate-300 mb-2">
                  Factura: <span className="font-semibold text-white">{facturaSeleccionada.factura}</span>
                </p>
                <p className="text-sm text-slate-300 mb-4">
                  Cliente: <span className="font-semibold text-white">{facturaSeleccionada.cliente}</span>
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Fecha de Pago</label>
                <input
                  type="date"
                  value={fechaPago}
                  onChange={(e) => setFechaPago(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            <div className="px-6 py-4 border-t border-slate-700 flex justify-end gap-3">
              <button
                onClick={() => {
                  setMostrarMarcarPagado(false)
                  setFacturaSeleccionada(null)
                }}
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                disabled={editando}
              >
                Cancelar
              </button>
              <button
                onClick={async () => {
                  try {
                    setEditando(true)
                    await marcarFacturaPagado(facturaSeleccionada.id, fechaPago)
                    alert('✅ Factura marcada como pagada')
                    setMostrarMarcarPagado(false)
                    setFacturaSeleccionada(null)
                    await cargarFacturas()
                  } catch (error) {
                    alert(`Error al marcar factura: ${error.response?.data?.detail || error.message}`)
                  } finally {
                    setEditando(false)
                  }
                }}
                disabled={editando}
                className="px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {editando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Marcar como Pagado
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Subir Comprobante */}
      {mostrarSubirComprobante && facturaSeleccionada && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
            <div className="px-6 py-4 border-b border-slate-700 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">Subir Comprobante de Pago</h3>
              <button
                onClick={() => {
                  setMostrarSubirComprobante(false)
                  setFacturaSeleccionada(null)
                  setArchivoComprobante(null)
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <p className="text-sm text-slate-300 mb-2">
                  Factura: <span className="font-semibold text-white">{facturaSeleccionada.factura}</span>
                </p>
                <p className="text-sm text-slate-300 mb-4">
                  Cliente: <span className="font-semibold text-white">{facturaSeleccionada.cliente}</span>
                </p>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Fecha de Pago</label>
                <input
                  type="date"
                  value={fechaPago}
                  onChange={(e) => setFechaPago(e.target.value)}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Comprobante de Pago</label>
                <input
                  type="file"
                  accept="image/*,.pdf"
                  onChange={(e) => setArchivoComprobante(e.target.files[0])}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-500 file:text-white hover:file:bg-blue-600"
                />
                {archivoComprobante && (
                  <p className="text-xs text-slate-400 mt-2">
                    Archivo seleccionado: {archivoComprobante.name} ({(archivoComprobante.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>
            </div>
            <div className="px-6 py-4 border-t border-slate-700 flex justify-end gap-3">
              <button
                onClick={() => {
                  setMostrarSubirComprobante(false)
                  setFacturaSeleccionada(null)
                  setArchivoComprobante(null)
                }}
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                disabled={editando}
              >
                Cancelar
              </button>
              <button
                onClick={async () => {
                  if (!archivoComprobante) {
                    alert('Por favor selecciona un archivo')
                    return
                  }
                  try {
                    setEditando(true)
                    await subirComprobantePago(facturaSeleccionada.id, archivoComprobante, fechaPago)
                    alert('✅ Comprobante subido y factura marcada como pagada')
                    setMostrarSubirComprobante(false)
                    setFacturaSeleccionada(null)
                    setArchivoComprobante(null)
                    await cargarFacturas()
                  } catch (error) {
                    alert(`Error al subir comprobante: ${error.response?.data?.detail || error.message}`)
                  } finally {
                    setEditando(false)
                  }
                }}
                disabled={editando || !archivoComprobante}
                className="px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {editando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Subiendo...
                  </>
                ) : (
                  <>
                    <Upload className="w-4 h-4" />
                    Subir Comprobante
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal de Ver Comprobante */}
      {mostrarComprobante && comprobanteData && facturaSeleccionada && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold text-white">Comprobante de Pago</h3>
                <p className="text-sm text-slate-400 mt-1">
                  Factura: {facturaSeleccionada.factura} - {facturaSeleccionada.cliente}
                </p>
              </div>
              <button
                onClick={() => {
                  setMostrarComprobante(false)
                  setComprobanteData(null)
                  setFacturaSeleccionada(null)
                }}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6">
              {cargandoComprobante ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <p className="text-sm text-slate-400">Archivo: {comprobanteData.nombre}</p>
                      <p className="text-xs text-slate-500">
                        Tipo: {comprobanteData.tipo} • Tamaño: {(comprobanteData.tamaño / 1024).toFixed(2)} KB
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        // Crear enlace de descarga
                        const byteCharacters = atob(comprobanteData.comprobante)
                        const byteNumbers = new Array(byteCharacters.length)
                        for (let i = 0; i < byteCharacters.length; i++) {
                          byteNumbers[i] = byteCharacters.charCodeAt(i)
                        }
                        const byteArray = new Uint8Array(byteNumbers)
                        const blob = new Blob([byteArray], { type: comprobanteData.tipo })
                        const url = URL.createObjectURL(blob)
                        const link = document.createElement('a')
                        link.href = url
                        link.download = comprobanteData.nombre
                        document.body.appendChild(link)
                        link.click()
                        document.body.removeChild(link)
                        URL.revokeObjectURL(url)
                      }}
                      className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                      <Download className="w-4 h-4" />
                      Descargar
                    </button>
                  </div>

                  {comprobanteData.tipo.startsWith('image/') ? (
                    <div className="bg-slate-900 rounded-lg p-4 flex items-center justify-center">
                      <img
                        src={`data:${comprobanteData.tipo};base64,${comprobanteData.comprobante}`}
                        alt="Comprobante de pago"
                        className="max-w-full max-h-[70vh] rounded-lg"
                      />
                    </div>
                  ) : comprobanteData.tipo === 'application/pdf' ? (
                    <div className="bg-slate-900 rounded-lg p-4">
                      <iframe
                        src={`data:${comprobanteData.tipo};base64,${comprobanteData.comprobante}`}
                        className="w-full h-[70vh] rounded-lg"
                        title="Comprobante de pago PDF"
                      />
                    </div>
                  ) : (
                    <div className="bg-slate-900 rounded-lg p-8 text-center">
                      <FileImage className="w-16 h-16 text-slate-400 mx-auto mb-4" />
                      <p className="text-slate-300 mb-2">Tipo de archivo no soportado para vista previa</p>
                      <p className="text-sm text-slate-500">Tipo: {comprobanteData.tipo}</p>
                      <button
                        onClick={() => {
                          const byteCharacters = atob(comprobanteData.comprobante)
                          const byteNumbers = new Array(byteCharacters.length)
                          for (let i = 0; i < byteCharacters.length; i++) {
                            byteNumbers[i] = byteCharacters.charCodeAt(i)
                          }
                          const byteArray = new Uint8Array(byteNumbers)
                          const blob = new Blob([byteArray], { type: comprobanteData.tipo })
                          const url = URL.createObjectURL(blob)
                          const link = document.createElement('a')
                          link.href = url
                          link.download = comprobanteData.nombre
                          document.body.appendChild(link)
                          link.click()
                          document.body.removeChild(link)
                          URL.revokeObjectURL(url)
                        }}
                        className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors inline-flex items-center gap-2"
                      >
                        <Download className="w-4 h-4" />
                        Descargar Archivo
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default ComisionesView
