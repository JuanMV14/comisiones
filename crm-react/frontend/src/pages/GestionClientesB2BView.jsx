import React, { useState, useEffect } from 'react'
import { Users, Search, Plus, Edit2, Trash2, Filter, X, Loader2, AlertCircle, CheckCircle, DollarSign, ShoppingCart, Calendar, MapPin, CreditCard, TrendingUp, Eye, Upload, FileSpreadsheet } from 'lucide-react'
import { getClientesB2B, getComprasCliente, getResumenClientesB2B, crearClienteB2B, actualizarClienteB2B, eliminarClienteB2B, cargarComprasExcel } from '../api/clientesB2B'

const GestionClientesB2BView = () => {
  const [clientes, setClientes] = useState([])
  const [resumen, setResumen] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Filtros y búsqueda
  const [busqueda, setBusqueda] = useState('')
  const [filtroActivo, setFiltroActivo] = useState(null)
  const [filtroCiudad, setFiltroCiudad] = useState('')
  
  // Modales
  const [mostrarCrear, setMostrarCrear] = useState(false)
  const [mostrarEditar, setMostrarEditar] = useState(false)
  const [mostrarDetalle, setMostrarDetalle] = useState(false)
  const [mostrarCargarExcel, setMostrarCargarExcel] = useState(false)
  const [clienteSeleccionado, setClienteSeleccionado] = useState(null)
  const [comprasCliente, setComprasCliente] = useState(null)
  const [loadingCompras, setLoadingCompras] = useState(false)
  const [archivoExcel, setArchivoExcel] = useState(null)
  const [nitClienteExcel, setNitClienteExcel] = useState('')
  const [loadingExcel, setLoadingExcel] = useState(false)
  const [resultadoExcel, setResultadoExcel] = useState(null)
  
  // Formulario
  const [formData, setFormData] = useState({
    nombre: '',
    nit: '',
    email: '',
    telefono: '',
    ciudad: '',
    direccion: '',
    cupo_total: '',
    plazo_pago: '30',
    descuento_predeterminado: '0',
    cliente_propio: true,
    vendedor: '',
    activo: true
  })

  useEffect(() => {
    cargarDatos()
  }, [])

  useEffect(() => {
    cargarClientes()
  }, [busqueda, filtroActivo, filtroCiudad])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      const [clientesData, resumenData] = await Promise.all([
        getClientesB2B({ limit: 0, offset: 0 }),
        getResumenClientesB2B()
      ])
      setClientes(clientesData.clientes || [])
      setResumen(resumenData)
      console.log(`✅ Cargados ${clientesData.clientes?.length || 0} clientes de ${clientesData.total || 0} totales`)
    } catch (err) {
      console.error('Error cargando datos:', err)
      setError(`Error al cargar los datos: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const cargarClientes = async () => {
    try {
      setLoading(true)
      const params = {
        limit: 0,
        offset: 0
      }
      
      if (busqueda) params.busqueda = busqueda
      if (filtroActivo !== null) params.activo = filtroActivo
      if (filtroCiudad) params.ciudad = filtroCiudad
      
      const resultado = await getClientesB2B(params)
      setClientes(resultado.clientes || [])
    } catch (err) {
      console.error('Error cargando clientes:', err)
      setError(`Error al cargar clientes: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const cargarComprasCliente = async (clienteId) => {
    try {
      setLoadingCompras(true)
      const resultado = await getComprasCliente(clienteId, { limit: 0, offset: 0 })
      setComprasCliente(resultado)
    } catch (err) {
      console.error('Error cargando compras:', err)
      alert(`Error al cargar compras: ${err.message}`)
    } finally {
      setLoadingCompras(false)
    }
  }

  const handleCrear = async (e) => {
    e.preventDefault()
    try {
      await crearClienteB2B(formData)
      setMostrarCrear(false)
      resetForm()
      cargarDatos()
    } catch (err) {
      alert(`Error creando cliente: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleEditar = async (e) => {
    e.preventDefault()
    try {
      await actualizarClienteB2B(clienteSeleccionado.id, formData)
      setMostrarEditar(false)
      setClienteSeleccionado(null)
      resetForm()
      cargarDatos()
    } catch (err) {
      alert(`Error actualizando cliente: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleEliminar = async (clienteId) => {
    if (!confirm('¿Estás seguro de que deseas desactivar este cliente?')) {
      return
    }
    
    try {
      await eliminarClienteB2B(clienteId)
      cargarDatos()
    } catch (err) {
      alert(`Error desactivando cliente: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleCargarExcel = async (e) => {
    e.preventDefault()
    if (!archivoExcel) {
      alert('Por favor selecciona un archivo Excel')
      return
    }

    try {
      setLoadingExcel(true)
      setResultadoExcel(null)
      
      console.log('📤 Cargando archivo Excel:', archivoExcel.name)
      console.log('📋 NIT Cliente:', nitClienteExcel || 'No especificado')
      
      const resultado = await cargarComprasExcel(archivoExcel, nitClienteExcel || null)
      
      console.log('✅ Resultado:', resultado)
      setResultadoExcel(resultado)
      
      if (resultado.success) {
        // Recargar datos después de cargar
        setTimeout(() => {
          cargarDatos()
          setMostrarCargarExcel(false)
          setArchivoExcel(null)
          setNitClienteExcel('')
          setResultadoExcel(null)
        }, 2000)
      }
    } catch (err) {
      console.error('❌ Error cargando archivo:', err)
      const errorMessage = err.response?.data?.detail || err.response?.data?.message || err.message || 'Error desconocido'
      alert(`Error cargando archivo: ${errorMessage}`)
      setResultadoExcel({
        success: false,
        error: errorMessage
      })
    } finally {
      setLoadingExcel(false)
    }
  }

  const abrirEditar = (cliente) => {
    setClienteSeleccionado(cliente)
    setFormData({
      nombre: cliente.nombre || '',
      nit: cliente.nit || '',
      email: cliente.email || '',
      telefono: cliente.telefono || '',
      ciudad: cliente.ciudad || '',
      direccion: cliente.direccion || '',
      cupo_total: cliente.cupo_total || '',
      plazo_pago: cliente.plazo_pago?.toString() || '30',
      descuento_predeterminado: cliente.descuento_predeterminado?.toString() || '0',
      cliente_propio: cliente.cliente_propio !== undefined ? cliente.cliente_propio : true,
      vendedor: cliente.vendedor || '',
      activo: cliente.activo !== undefined ? cliente.activo : true
    })
    setMostrarEditar(true)
  }

  const abrirDetalle = async (cliente) => {
    setClienteSeleccionado(cliente)
    setMostrarDetalle(true)
    await cargarComprasCliente(cliente.id)
  }

  const resetForm = () => {
    setFormData({
      nombre: '',
      nit: '',
      email: '',
      telefono: '',
      ciudad: '',
      direccion: '',
      cupo_total: '',
      plazo_pago: '30',
      descuento_predeterminado: '0',
      cliente_propio: true,
      vendedor: '',
      activo: true
    })
  }

  const limpiarFiltros = () => {
    setBusqueda('')
    setFiltroActivo(null)
    setFiltroCiudad('')
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

  if (loading && clientes.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando clientes B2B...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Gestión Clientes B2B</h2>
          <p className="text-sm text-slate-400">Administración de clientes y seguimiento de compras</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMostrarCargarExcel(true)}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Cargar Compras Excel
          </button>
          <button
            onClick={() => {
              resetForm()
              setMostrarCrear(true)
            }}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nuevo Cliente
          </button>
        </div>
      </div>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <Users className="w-5 h-5 text-blue-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Total Clientes</p>
            <p className="text-2xl font-bold text-white">{resumen.total_clientes || 0}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Activos</p>
            <p className="text-2xl font-bold text-white">{resumen.clientes_activos || 0}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <CreditCard className="w-5 h-5 text-purple-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Cupo Total</p>
            <p className="text-2xl font-bold text-white">{formatCurrency(resumen.total_cupo || 0)}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-orange-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Cupo Disponible</p>
            <p className="text-2xl font-bold text-white">{formatCurrency(resumen.cupo_disponible || 0)}</p>
          </div>
        </div>
      )}

      {/* Filtros y Búsqueda */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Buscar por nombre o NIT..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <select
            value={filtroActivo === null ? 'todos' : (filtroActivo ? 'activos' : 'inactivos')}
            onChange={(e) => {
              const valor = e.target.value
              setFiltroActivo(valor === 'todos' ? null : valor === 'activos')
            }}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="todos">Todos</option>
            <option value="activos">Activos</option>
            <option value="inactivos">Inactivos</option>
          </select>
          <select
            value={filtroCiudad}
            onChange={(e) => setFiltroCiudad(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas las ciudades</option>
            {resumen?.ciudades?.map((ciudad) => (
              <option key={ciudad} value={ciudad}>{ciudad}</option>
            ))}
          </select>
        </div>
        {(busqueda || filtroActivo !== null || filtroCiudad) && (
          <button
            onClick={limpiarFiltros}
            className="mt-3 flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Tabla de Clientes */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">NIT</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ciudad</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Cupo Total</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Cupo Utilizado</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Compras</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Última Compra</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">Estado</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {clientes.length > 0 ? (
                clientes.map((cliente) => (
                  <tr key={cliente.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{cliente.nombre || 'N/A'}</p>
                      {cliente.vendedor && (
                        <p className="text-xs text-slate-400">Vendedor: {cliente.vendedor}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{cliente.nit || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{cliente.ciudad || '-'}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm font-semibold text-white">{formatCurrency(cliente.cupo_total || 0)}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex flex-col items-end">
                        <p className={`text-sm font-semibold ${cliente.cupo_utilizado > cliente.cupo_total * 0.8 ? 'text-red-400' : 'text-slate-300'}`}>
                          {formatCurrency(cliente.cupo_utilizado || 0)}
                        </p>
                        <p className="text-xs text-slate-500">
                          {cliente.cupo_total > 0 ? `${((cliente.cupo_utilizado / cliente.cupo_total) * 100).toFixed(1)}%` : '0%'}
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex flex-col items-end">
                        <p className="text-sm font-semibold text-white">{cliente.total_compras || 0}</p>
                        {cliente.valor_total_compras > 0 && (
                          <p className="text-xs text-slate-400">{formatCurrency(cliente.valor_total_compras)}</p>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {cliente.ultima_compra ? (
                        <div className="flex flex-col items-end">
                          <p className="text-sm text-slate-300">{formatDate(cliente.ultima_compra)}</p>
                          {cliente.dias_desde_compra !== null && (
                            <p className="text-xs text-slate-500">{cliente.dias_desde_compra} días</p>
                          )}
                        </div>
                      ) : (
                        <p className="text-sm text-slate-500">Sin compras</p>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                        cliente.activo 
                          ? 'bg-emerald-500/20 text-emerald-400' 
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {cliente.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => abrirDetalle(cliente)}
                          className="p-2 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
                          title="Ver compras"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => abrirEditar(cliente)}
                          className="p-2 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEliminar(cliente.id)}
                          className="p-2 text-red-400 hover:bg-red-500/20 rounded-lg transition-colors"
                          title="Desactivar"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="9" className="px-4 py-8 text-center">
                    <p className="text-slate-500">No se encontraron clientes</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Crear Cliente */}
      {mostrarCrear && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-2xl border border-slate-700 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-4">Nuevo Cliente B2B</h3>
            <form onSubmit={handleCrear} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Nombre *</label>
                  <input
                    type="text"
                    required
                    value={formData.nombre}
                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">NIT *</label>
                  <input
                    type="text"
                    required
                    value={formData.nit}
                    onChange={(e) => setFormData({ ...formData, nit: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Teléfono</label>
                  <input
                    type="text"
                    value={formData.telefono}
                    onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Ciudad</label>
                  <input
                    type="text"
                    value={formData.ciudad}
                    onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Vendedor</label>
                  <input
                    type="text"
                    value={formData.vendedor}
                    onChange={(e) => setFormData({ ...formData, vendedor: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Cupo Total</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.cupo_total}
                    onChange={(e) => setFormData({ ...formData, cupo_total: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Plazo Pago (días)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.plazo_pago}
                    onChange={(e) => setFormData({ ...formData, plazo_pago: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Descuento Predeterminado (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={formData.descuento_predeterminado}
                    onChange={(e) => setFormData({ ...formData, descuento_predeterminado: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Dirección</label>
                <textarea
                  value={formData.direccion}
                  onChange={(e) => setFormData({ ...formData, direccion: e.target.value })}
                  rows="2"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.cliente_propio}
                  onChange={(e) => setFormData({ ...formData, cliente_propio: e.target.checked })}
                  className="w-4 h-4 text-blue-500 bg-slate-900 border-slate-700 rounded focus:ring-blue-500"
                />
                <label className="text-sm text-slate-300">Cliente propio</label>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Crear
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMostrarCrear(false)
                    resetForm()
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Editar Cliente */}
      {mostrarEditar && clienteSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-2xl border border-slate-700 max-h-[90vh] overflow-y-auto">
            <h3 className="text-xl font-bold text-white mb-4">Editar Cliente B2B</h3>
            <form onSubmit={handleEditar} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Nombre *</label>
                  <input
                    type="text"
                    required
                    value={formData.nombre}
                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">NIT *</label>
                  <input
                    type="text"
                    required
                    value={formData.nit}
                    onChange={(e) => setFormData({ ...formData, nit: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Email</label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Teléfono</label>
                  <input
                    type="text"
                    value={formData.telefono}
                    onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Ciudad</label>
                  <input
                    type="text"
                    value={formData.ciudad}
                    onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Vendedor</label>
                  <input
                    type="text"
                    value={formData.vendedor}
                    onChange={(e) => setFormData({ ...formData, vendedor: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Cupo Total</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.cupo_total}
                    onChange={(e) => setFormData({ ...formData, cupo_total: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Plazo Pago (días)</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.plazo_pago}
                    onChange={(e) => setFormData({ ...formData, plazo_pago: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">Descuento Predeterminado (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max="100"
                    value={formData.descuento_predeterminado}
                    onChange={(e) => setFormData({ ...formData, descuento_predeterminado: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Dirección</label>
                <textarea
                  value={formData.direccion}
                  onChange={(e) => setFormData({ ...formData, direccion: e.target.value })}
                  rows="2"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.cliente_propio}
                    onChange={(e) => setFormData({ ...formData, cliente_propio: e.target.checked })}
                    className="w-4 h-4 text-blue-500 bg-slate-900 border-slate-700 rounded focus:ring-blue-500"
                  />
                  <label className="text-sm text-slate-300">Cliente propio</label>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={formData.activo}
                    onChange={(e) => setFormData({ ...formData, activo: e.target.checked })}
                    className="w-4 h-4 text-blue-500 bg-slate-900 border-slate-700 rounded focus:ring-blue-500"
                  />
                  <label className="text-sm text-slate-300">Activo</label>
                </div>
              </div>
              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Guardar
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMostrarEditar(false)
                    setClienteSeleccionado(null)
                    resetForm()
                  }}
                  className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Modal Detalle Cliente - Compras */}
      {mostrarDetalle && clienteSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-6xl border border-slate-700 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-xl font-bold text-white">Historial de Compras</h3>
                <p className="text-sm text-slate-400">{clienteSeleccionado.nombre} - {clienteSeleccionado.nit}</p>
              </div>
              <button
                onClick={() => {
                  setMostrarDetalle(false)
                  setClienteSeleccionado(null)
                  setComprasCliente(null)
                }}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {loadingCompras ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-blue-500 mr-3" />
                <p className="text-slate-400">Cargando compras...</p>
              </div>
            ) : comprasCliente ? (
              <div className="space-y-6">
                {/* Resumen */}
                {comprasCliente.resumen && (
                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                      <p className="text-xs text-slate-400 mb-1">Total Compras</p>
                      <p className="text-2xl font-bold text-white">{comprasCliente.resumen.total_compras || 0}</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                      <p className="text-xs text-slate-400 mb-1">Devoluciones</p>
                      <p className="text-2xl font-bold text-red-400">{comprasCliente.resumen.total_devoluciones || 0}</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                      <p className="text-xs text-slate-400 mb-1">Valor Total</p>
                      <p className="text-2xl font-bold text-emerald-400">{formatCurrency(comprasCliente.resumen.valor_total || 0)}</p>
                    </div>
                    <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700/50">
                      <p className="text-xs text-slate-400 mb-1">Valor Neto</p>
                      <p className="text-2xl font-bold text-white">{formatCurrency(comprasCliente.resumen.valor_neto || 0)}</p>
                    </div>
                  </div>
                )}

                {/* Tabla de Compras */}
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead className="bg-slate-900/50 border-b border-slate-700">
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Fecha</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Documento</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Código</th>
                        <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Detalle</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Cantidad</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Valor Unit.</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Descuento</th>
                        <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Total</th>
                        <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">Tipo</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50">
                      {comprasCliente.compras && comprasCliente.compras.length > 0 ? (
                        (() => {
                          // Agrupar compras por documento/factura
                          const comprasPorFactura = {}
                          comprasCliente.compras.forEach((compra) => {
                            const doc = compra.num_documento || 'N/A'
                            if (!comprasPorFactura[doc]) {
                              comprasPorFactura[doc] = {
                                items: [],
                                fecha: compra.fecha
                              }
                            }
                            comprasPorFactura[doc].items.push(compra)
                          })
                          
                          // Renderizar agrupado por factura
                          return Object.entries(comprasPorFactura).map(([doc, facturaData]) => {
                            const items = facturaData.items
                            // Calcular total de factura sumando los items (solo compras, excluyendo devoluciones)
                            // Devolución: es_devolucion=True O total negativo
                            const totalFactura = items
                              .filter(item => {
                                const esDevolucion = item.es_devolucion || (parseFloat(item.total || 0) < 0)
                                return !esDevolucion
                              })
                              .reduce((sum, item) => sum + Math.abs(parseFloat(item.total || 0)), 0)
                            
                            return (
                              <React.Fragment key={doc}>
                                {items.map((compra, itemIdx) => (
                                  <tr 
                                    key={`${doc}-${itemIdx}`}
                                    className={`hover:bg-slate-700/30 transition-colors ${
                                      (compra.es_devolucion || (parseFloat(compra.total || 0) < 0)) ? 'bg-red-500/5' : ''
                                    }`}
                                  >
                                    {itemIdx === 0 && (
                                      <>
                                        <td className="px-4 py-3 border-r border-slate-700/50" rowSpan={items.length}>
                                          <p className="text-sm text-slate-300">{formatDate(compra.fecha)}</p>
                                        </td>
                                        <td className="px-4 py-3 border-r border-slate-700/50" rowSpan={items.length}>
                                          <div>
                                            <p className="text-sm font-semibold text-white">{compra.num_documento || 'N/A'}</p>
                                            {totalFactura > 0 && (
                                              <p className="text-xs text-emerald-400 mt-1 font-semibold">
                                                Total Factura: {formatCurrency(totalFactura)}
                                              </p>
                                            )}
                                          </div>
                                        </td>
                                      </>
                                    )}
                                    <td className="px-4 py-3">
                                      <p className="text-sm text-slate-300">{compra.cod_articulo || 'N/A'}</p>
                                    </td>
                                    <td className="px-4 py-3">
                                      <p className="text-sm text-slate-300">{compra.detalle || 'N/A'}</p>
                                      {compra.marca && (
                                        <p className="text-xs text-slate-500">{compra.marca}</p>
                                      )}
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <p className="text-sm text-slate-300">{compra.cantidad || 0}</p>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <p className="text-sm text-slate-300">{formatCurrency(compra.valor_unitario || 0)}</p>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      <p className="text-sm text-slate-300">{compra.descuento || 0}%</p>
                                    </td>
                                    <td className="px-4 py-3 text-right">
                                      {(() => {
                                        // Detectar devolución: es_devolucion=True O total negativo
                                        const esDevolucion = compra.es_devolucion || (parseFloat(compra.total || 0) < 0)
                                        const totalAbsoluto = Math.abs(parseFloat(compra.total || 0))
                                        return (
                                          <p className={`text-sm font-semibold ${esDevolucion ? 'text-red-400' : 'text-white'}`}>
                                            {esDevolucion ? '-' : ''}{formatCurrency(totalAbsoluto)}
                                          </p>
                                        )
                                      })()}
                                    </td>
                                    <td className="px-4 py-3 text-center">
                                      {(() => {
                                        // Detectar devolución: es_devolucion=True O total negativo
                                        const esDevolucion = compra.es_devolucion || (parseFloat(compra.total || 0) < 0)
                                        return (
                                          <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                                            esDevolucion 
                                              ? 'bg-red-500/20 text-red-400' 
                                              : 'bg-emerald-500/20 text-emerald-400'
                                          }`}>
                                            {esDevolucion ? 'Devolución' : 'Compra'}
                                          </span>
                                        )
                                      })()}
                                    </td>
                                  </tr>
                                ))}
                              </React.Fragment>
                            )
                          })
                        })()
                      ) : (
                        <tr>
                          <td colSpan="9" className="px-4 py-8 text-center">
                            <p className="text-slate-500">No hay compras registradas</p>
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <p className="text-slate-500">No se pudieron cargar las compras</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Modal Cargar Excel */}
      {mostrarCargarExcel && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-slate-700">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <FileSpreadsheet className="w-6 h-6 text-emerald-400" />
                  <h3 className="text-xl font-semibold text-white">Cargar Compras desde Excel</h3>
                </div>
                <button
                  onClick={() => {
                    setMostrarCargarExcel(false)
                    setArchivoExcel(null)
                    setNitClienteExcel('')
                    setResultadoExcel(null)
                  }}
                  className="text-slate-400 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            <form onSubmit={handleCargarExcel} className="p-6 space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Archivo Excel (.xlsx o .xls)
                </label>
                <div className="border-2 border-dashed border-slate-600 rounded-lg p-6 text-center hover:border-emerald-500 transition-colors">
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setArchivoExcel(e.target.files[0])}
                    className="hidden"
                    id="archivo-excel"
                  />
                  <label
                    htmlFor="archivo-excel"
                    className="cursor-pointer flex flex-col items-center gap-2"
                  >
                    <Upload className="w-8 h-8 text-slate-400" />
                    {archivoExcel ? (
                      <span className="text-emerald-400 font-semibold">{archivoExcel.name}</span>
                    ) : (
                      <>
                        <span className="text-slate-400">Haz clic para seleccionar archivo</span>
                        <span className="text-xs text-slate-500">Formatos: .xlsx, .xls</span>
                      </>
                    )}
                  </label>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  NIT del Cliente (Opcional)
                </label>
                <p className="text-xs text-slate-400 mb-2">
                  Si el Excel contiene múltiples clientes, déjalo vacío. Si el Excel tiene columna 'NIT_CLIENTE' o 'NIT', se detectará automáticamente.
                </p>
                <input
                  type="text"
                  value={nitClienteExcel}
                  onChange={(e) => setNitClienteExcel(e.target.value)}
                  placeholder="Ej: 901234567"
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="bg-slate-900/50 rounded-lg p-4 border border-slate-700">
                <p className="text-xs font-semibold text-slate-300 mb-2">Formato requerido del Excel:</p>
                <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside">
                  <li><strong>FUENTE:</strong> 'FE' para compras, 'DV' para devoluciones</li>
                  <li><strong>NUM_DCTO:</strong> Número de documento/factura</li>
                  <li><strong>FECHA:</strong> Fecha de la compra</li>
                  <li><strong>COD_ARTICULO:</strong> Código del artículo</li>
                  <li><strong>DETALLE:</strong> Descripción del producto</li>
                  <li><strong>CANTIDAD:</strong> Cantidad comprada</li>
                  <li><strong>valor_Unitario:</strong> Precio unitario</li>
                  <li><strong>dcto:</strong> Porcentaje de descuento</li>
                  <li><strong>Total:</strong> Total del item</li>
                  <li><strong>FAMILIA, Marca, SUBGRUPO, GRUPO:</strong> Categorías del producto</li>
                </ul>
              </div>

              {resultadoExcel && (
                <div className={`p-4 rounded-lg border ${
                  resultadoExcel.success 
                    ? 'bg-emerald-500/10 border-emerald-500/30' 
                    : 'bg-red-500/10 border-red-500/30'
                }`}>
                  {resultadoExcel.success ? (
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-emerald-400">
                        <CheckCircle className="w-5 h-5" />
                        <span className="font-semibold">Archivo procesado correctamente</span>
                      </div>
                      {resultadoExcel.cliente && (
                        <p className="text-sm text-slate-300">Cliente: {resultadoExcel.cliente}</p>
                      )}
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-slate-400">Compras nuevas:</p>
                          <p className="text-white font-semibold">{resultadoExcel.compras_nuevas || 0}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Compras actualizadas:</p>
                          <p className="text-white font-semibold">{resultadoExcel.compras_actualizadas || 0}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Devoluciones nuevas:</p>
                          <p className="text-white font-semibold">{resultadoExcel.devoluciones_nuevas || 0}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Devoluciones actualizadas:</p>
                          <p className="text-white font-semibold">{resultadoExcel.devoluciones_actualizadas || 0}</p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-400">
                      <AlertCircle className="w-5 h-5" />
                      <span>{resultadoExcel.error || 'Error procesando archivo'}</span>
                    </div>
                  )}
                </div>
              )}

              <div className="flex items-center gap-3 pt-4">
                <button
                  type="submit"
                  disabled={!archivoExcel || loadingExcel}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loadingExcel ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Procesando...
                    </>
                  ) : (
                    <>
                      <Upload className="w-4 h-4" />
                      Cargar Compras
                    </>
                  )}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setMostrarCargarExcel(false)
                    setArchivoExcel(null)
                    setNitClienteExcel('')
                    setResultadoExcel(null)
                  }}
                  className="px-4 py-3 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default GestionClientesB2BView
