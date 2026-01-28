import React, { useState, useEffect } from 'react'
import { ArrowLeftRight, Search, Calendar, DollarSign, Loader2, Eye, Edit, Trash2, Plus, X, Save, FileText, AlertCircle } from 'lucide-react'
import { getDevoluciones, getDevolucionesComprasClientes, getFacturasDisponibles, crearDevolucion, actualizarDevolucion, eliminarDevolucion } from '../api/devoluciones'
import { getMesesDisponibles } from '../api/dashboard'

const DevolucionesView = () => {
  const [devoluciones, setDevoluciones] = useState([])
  const [devolucionesCompras, setDevolucionesCompras] = useState([])
  const [resumenPorMes, setResumenPorMes] = useState({})
  const [resumenPorCliente, setResumenPorCliente] = useState({})
  const [mostrarComprasClientes, setMostrarComprasClientes] = useState(true) // Por defecto mostrar desde compras_clientes
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [searchTerm, setSearchTerm] = useState('')
  const [mesSeleccionado, setMesSeleccionado] = useState(null)
  const [mesesDisponibles, setMesesDisponibles] = useState([])
  const [mostrarNueva, setMostrarNueva] = useState(false)
  const [mostrarEditar, setMostrarEditar] = useState(false)
  const [mostrarEliminar, setMostrarEliminar] = useState(false)
  const [devolucionSeleccionada, setDevolucionSeleccionada] = useState(null)
  const [facturasDisponibles, setFacturasDisponibles] = useState([])
  const [guardando, setGuardando] = useState(false)
  const [formData, setFormData] = useState({
    factura_id: '',
    valor_devuelto: 0,
    fecha_devolucion: new Date().toISOString().split('T')[0],
    motivo: '',
    afecta_comision: true
  })

  useEffect(() => {
    const cargarMeses = async () => {
      try {
        const mesesData = await getMesesDisponibles()
        if (mesesData && mesesData.meses && mesesData.meses.length > 0) {
          setMesesDisponibles(mesesData.meses)
          setMesSeleccionado(mesesData.meses[0].valor)
        }
      } catch (err) {
        console.error('Error cargando meses:', err)
      }
    }
    cargarMeses()
  }, [])

  useEffect(() => {
    if (mesSeleccionado || mostrarComprasClientes) {
      cargarDevoluciones()
    }
  }, [mesSeleccionado, searchTerm, mostrarComprasClientes])

  const cargarDevoluciones = async () => {
    try {
      setLoading(true)
      setError(null)
      
      if (mostrarComprasClientes) {
        // Cargar desde compras_clientes
        const data = await getDevolucionesComprasClientes(mesSeleccionado || null, searchTerm || null)
        setDevolucionesCompras(data.devoluciones || [])
        setResumenPorMes(data.resumen_por_mes || {})
        setResumenPorCliente(data.resumen_por_cliente || {})
        setDevoluciones([]) // Limpiar devoluciones tradicionales
      } else {
        // Cargar desde tabla devoluciones tradicional
        const data = await getDevoluciones(null, searchTerm || null, mesSeleccionado, null)
        setDevoluciones(data.devoluciones || [])
        setDevolucionesCompras([]) // Limpiar devoluciones de compras_clientes
        setResumenPorMes({})
        setResumenPorCliente({})
      }
    } catch (err) {
      console.error('Error cargando devoluciones:', err)
      setError(`Error al cargar las devoluciones: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const cargarFacturasDisponibles = async () => {
    try {
      const facturas = await getFacturasDisponibles()
      setFacturasDisponibles(facturas || [])
    } catch (err) {
      console.error('Error cargando facturas:', err)
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

  const handleNuevaDevolucion = () => {
    setFormData({
      factura_id: '',
      valor_devuelto: 0,
      fecha_devolucion: new Date().toISOString().split('T')[0],
      motivo: '',
      afecta_comision: true
    })
    setDevolucionSeleccionada(null)
    cargarFacturasDisponibles()
    setMostrarNueva(true)
  }

  const handleEditarDevolucion = (devolucion) => {
    setDevolucionSeleccionada(devolucion)
    setFormData({
      factura_id: devolucion.factura_id,
      valor_devuelto: devolucion.valor_devuelto,
      fecha_devolucion: devolucion.fecha_devolucion || new Date().toISOString().split('T')[0],
      motivo: devolucion.motivo || '',
      afecta_comision: devolucion.afecta_comision
    })
    cargarFacturasDisponibles()
    setMostrarEditar(true)
  }

  const handleEliminarDevolucion = (devolucion) => {
    setDevolucionSeleccionada(devolucion)
    setMostrarEliminar(true)
  }

  const handleGuardar = async () => {
    try {
      setGuardando(true)
      
      if (!formData.factura_id || formData.valor_devuelto <= 0) {
        alert('Por favor completa todos los campos requeridos')
        return
      }

      if (mostrarNueva) {
        await crearDevolucion(formData)
        alert('✅ Devolución creada exitosamente')
      } else {
        await actualizarDevolucion(devolucionSeleccionada.id, formData)
        alert('✅ Devolución actualizada exitosamente')
      }

      setMostrarNueva(false)
      setMostrarEditar(false)
      cargarDevoluciones()
    } catch (err) {
      console.error('Error guardando devolución:', err)
      alert('Error al guardar la devolución: ' + (err.response?.data?.detail || err.message))
    } finally {
      setGuardando(false)
    }
  }

  const handleEliminar = async () => {
    try {
      setGuardando(true)
      await eliminarDevolucion(devolucionSeleccionada.id)
      alert('✅ Devolución eliminada exitosamente')
      setMostrarEliminar(false)
      cargarDevoluciones()
    } catch (err) {
      console.error('Error eliminando devolución:', err)
      alert('Error al eliminar la devolución: ' + (err.response?.data?.detail || err.message))
    } finally {
      setGuardando(false)
    }
  }

  const devolucionesFiltradas = devoluciones.filter(devolucion =>
    devolucion.factura?.cliente?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    devolucion.factura?.factura?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    devolucion.factura?.pedido?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    devolucion.motivo?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const totales = {
    valor: devolucionesFiltradas.reduce((sum, d) => sum + (d.valor_devuelto || 0), 0),
    cantidad: devolucionesFiltradas.length
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando devoluciones...</p>
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
            onClick={cargarDevoluciones}
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
          <h2 className="text-2xl font-bold text-white mb-1">Devoluciones</h2>
          <p className="text-sm text-slate-400">Gestión de devoluciones de facturas</p>
        </div>
        <button
          onClick={handleNuevaDevolucion}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Nueva Devolución
        </button>
      </div>

      {/* Métricas */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">Total Devoluciones</p>
              <p className="text-2xl font-bold text-white">{totales.cantidad}</p>
            </div>
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <ArrowLeftRight className="w-6 h-6 text-blue-400" />
            </div>
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">Valor Total Devuelto</p>
              <p className="text-2xl font-bold text-white">{formatCurrency(totales.valor)}</p>
            </div>
            <div className="w-12 h-12 bg-emerald-500/20 rounded-lg flex items-center justify-center">
              <DollarSign className="w-6 h-6 text-emerald-400" />
            </div>
          </div>
        </div>
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-400 mb-1">Mes Seleccionado</p>
              <p className="text-lg font-semibold text-white">
                {mesesDisponibles.find(m => m.valor === mesSeleccionado)?.nombre || 'N/A'}
              </p>
            </div>
            <div className="w-12 h-12 bg-amber-500/20 rounded-lg flex items-center justify-center">
              <Calendar className="w-6 h-6 text-amber-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Filtros */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
              <input
                type="text"
                placeholder="Buscar por cliente, factura, pedido o motivo..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="md:w-64">
            <select
              value={mesSeleccionado || ''}
              onChange={(e) => setMesSeleccionado(e.target.value)}
              className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
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
      </div>

      {/* Tabla */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Factura</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Cliente</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Fecha</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Valor Devuelto</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Motivo</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-slate-400 uppercase tracking-wider">Afecta Comisión</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-slate-400 uppercase tracking-wider">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {devolucionesFiltradas.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center text-slate-400">
                    No hay devoluciones registradas
                  </td>
                </tr>
              ) : (
                devolucionesFiltradas.map((devolucion) => (
                  <tr key={devolucion.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-white">{devolucion.factura?.factura || 'N/A'}</div>
                      <div className="text-xs text-slate-400">Pedido: {devolucion.factura?.pedido || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-white">{devolucion.factura?.cliente || 'N/A'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-slate-300">{formatDate(devolucion.fecha_devolucion)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-emerald-400">{formatCurrency(devolucion.valor_devuelto)}</div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-slate-300 max-w-xs truncate">{devolucion.motivo || 'Sin motivo'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                        devolucion.afecta_comision
                          ? 'bg-amber-500/20 text-amber-400'
                          : 'bg-slate-700/50 text-slate-400'
                      }`}>
                        {devolucion.afecta_comision ? 'Sí' : 'No'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEditarDevolucion(devolucion)}
                          className="p-2 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEliminarDevolucion(devolucion)}
                          className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                          title="Eliminar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Nueva/Editar Devolución */}
      {(mostrarNueva || mostrarEditar) && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white">
                  {mostrarNueva ? 'Nueva Devolución' : 'Editar Devolución'}
                </h3>
                <button
                  onClick={() => {
                    setMostrarNueva(false)
                    setMostrarEditar(false)
                  }}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Factura *
                </label>
                <select
                  value={formData.factura_id}
                  onChange={(e) => setFormData({ ...formData, factura_id: e.target.value })}
                  disabled={mostrarEditar}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
                  required
                >
                  <option value="">Selecciona una factura</option>
                  {facturasDisponibles.map((factura) => (
                    <option key={factura.id} value={factura.id}>
                      {factura.factura} - {factura.cliente} - {formatCurrency(factura.valor)}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Valor Devuelto (con IVA) *
                </label>
                <input
                  type="number"
                  step="0.01"
                  value={formData.valor_devuelto}
                  onChange={(e) => setFormData({ ...formData, valor_devuelto: parseFloat(e.target.value) || 0 })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Fecha de Devolución *
                </label>
                <input
                  type="date"
                  value={formData.fecha_devolucion}
                  onChange={(e) => setFormData({ ...formData, fecha_devolucion: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Motivo
                </label>
                <textarea
                  value={formData.motivo}
                  onChange={(e) => setFormData({ ...formData, motivo: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Motivo de la devolución..."
                />
              </div>
              <div>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={formData.afecta_comision}
                    onChange={(e) => setFormData({ ...formData, afecta_comision: e.target.checked })}
                    className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-sm text-slate-300">Afecta el cálculo de comisión</span>
                </label>
              </div>
            </div>
            <div className="p-6 border-t border-slate-700 flex items-center justify-end gap-3">
              <button
                onClick={() => {
                  setMostrarNueva(false)
                  setMostrarEditar(false)
                }}
                className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
              >
                Cancelar
              </button>
              <button
                onClick={handleGuardar}
                disabled={guardando}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {guardando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Guardando...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4" />
                    Guardar
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal Eliminar */}
      {mostrarEliminar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 max-w-md w-full">
            <div className="p-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-12 h-12 bg-red-500/20 rounded-lg flex items-center justify-center">
                  <AlertCircle className="w-6 h-6 text-red-400" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-white">Eliminar Devolución</h3>
                  <p className="text-sm text-slate-400">Esta acción no se puede deshacer</p>
                </div>
              </div>
              <p className="text-slate-300 mb-6">
                ¿Estás seguro de que deseas eliminar la devolución de la factura{' '}
                <span className="font-semibold text-white">{devolucionSeleccionada?.factura?.factura}</span>?
              </p>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={() => setMostrarEliminar(false)}
                  className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleEliminar}
                  disabled={guardando}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {guardando ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Eliminando...
                    </>
                  ) : (
                    <>
                      <Trash2 className="w-4 h-4" />
                      Eliminar
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default DevolucionesView
