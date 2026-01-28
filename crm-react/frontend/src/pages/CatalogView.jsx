import React, { useState, useEffect } from 'react'
import { Package, Search, Plus, Edit2, Trash2, Filter, X, Loader2, AlertCircle, CheckCircle, TrendingUp } from 'lucide-react'
import { getProductos, crearProducto, actualizarProducto, eliminarProducto, getResumenCatalogo } from '../api/catalogo'

const CatalogView = () => {
  const [productos, setProductos] = useState([])
  const [resumen, setResumen] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  
  // Filtros y búsqueda
  const [busqueda, setBusqueda] = useState('')
  const [filtroActivo, setFiltroActivo] = useState(null) // null = todos, true = activos, false = inactivos
  const [filtroLinea, setFiltroLinea] = useState('')
  const [filtroMarca, setFiltroMarca] = useState('')
  
  // Modales
  const [mostrarCrear, setMostrarCrear] = useState(false)
  const [mostrarEditar, setMostrarEditar] = useState(false)
  const [productoSeleccionado, setProductoSeleccionado] = useState(null)
  
  // Formulario
  const [formData, setFormData] = useState({
    cod_ur: '',
    referencia: '',
    descripcion: '',
    precio: '',
    marca: '',
    linea: '',
    equivalencia: '',
    detalle_descuento: '',
    activo: true
  })

  useEffect(() => {
    cargarDatos()
  }, [])

  useEffect(() => {
    cargarProductos()
  }, [busqueda, filtroActivo, filtroLinea, filtroMarca])

  const cargarDatos = async () => {
    try {
      setLoading(true)
      const [productosData, resumenData] = await Promise.all([
        getProductos({ limit: 0, offset: 0 }), // Cargar todos los productos
        getResumenCatalogo()
      ])
      setProductos(productosData.productos || [])
      setResumen(resumenData)
      console.log(`✅ Cargados ${productosData.productos?.length || 0} productos de ${productosData.total || 0} totales`)
    } catch (err) {
      console.error('Error cargando datos:', err)
      setError(`Error al cargar los datos: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const cargarProductos = async () => {
    try {
      setLoading(true)
      const params = {
        limit: 0, // 0 = sin límite, cargar todos
        offset: 0
      }
      
      if (busqueda) params.busqueda = busqueda
      if (filtroActivo !== null) params.activo = filtroActivo
      if (filtroLinea) params.linea = filtroLinea
      if (filtroMarca) params.marca = filtroMarca
      
      const resultado = await getProductos(params)
      setProductos(resultado.productos || [])
      console.log(`✅ Cargados ${resultado.productos?.length || 0} productos de ${resultado.total || 0} totales`)
    } catch (err) {
      console.error('Error cargando productos:', err)
      setError(`Error al cargar productos: ${err.message}`)
    } finally {
      setLoading(false)
    }
  }

  const handleCrear = async (e) => {
    e.preventDefault()
    try {
      await crearProducto(formData)
      setMostrarCrear(false)
      resetForm()
      cargarDatos()
    } catch (err) {
      alert(`Error creando producto: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleEditar = async (e) => {
    e.preventDefault()
    try {
      await actualizarProducto(productoSeleccionado.id, formData)
      setMostrarEditar(false)
      setProductoSeleccionado(null)
      resetForm()
      cargarDatos()
    } catch (err) {
      alert(`Error actualizando producto: ${err.response?.data?.detail || err.message}`)
    }
  }

  const handleEliminar = async (productoId) => {
    if (!confirm('¿Estás seguro de que deseas desactivar este producto?')) {
      return
    }
    
    try {
      await eliminarProducto(productoId)
      cargarDatos()
    } catch (err) {
      alert(`Error desactivando producto: ${err.response?.data?.detail || err.message}`)
    }
  }

  const abrirEditar = (producto) => {
    setProductoSeleccionado(producto)
    setFormData({
      cod_ur: producto.cod_ur || '',
      referencia: producto.referencia || '',
      descripcion: producto.descripcion || '',
      precio: producto.precio || '',
      marca: producto.marca || '',
      linea: producto.linea || '',
      equivalencia: producto.equivalencia || '',
      detalle_descuento: producto.detalle_descuento || '',
      activo: producto.activo !== undefined ? producto.activo : true
    })
    setMostrarEditar(true)
  }

  const resetForm = () => {
    setFormData({
      cod_ur: '',
      referencia: '',
      descripcion: '',
      precio: '',
      marca: '',
      linea: '',
      equivalencia: '',
      detalle_descuento: '',
      activo: true
    })
  }

  const limpiarFiltros = () => {
    setBusqueda('')
    setFiltroActivo(null)
    setFiltroLinea('')
    setFiltroMarca('')
  }

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(val || 0)
  }

  if (loading && productos.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-slate-400">Cargando catálogo...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Catálogo</h2>
          <p className="text-sm text-slate-400">Gestión de productos y catálogo</p>
        </div>
        <button
          onClick={() => {
            resetForm()
            setMostrarCrear(true)
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Nuevo Producto
        </button>
      </div>

      {/* KPIs */}
      {resumen && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <Package className="w-5 h-5 text-blue-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Total Productos</p>
            <p className="text-2xl font-bold text-white">{resumen.total_productos || 0}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Activos</p>
            <p className="text-2xl font-bold text-white">{resumen.productos_activos || 0}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <X className="w-5 h-5 text-red-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Inactivos</p>
            <p className="text-2xl font-bold text-white">{resumen.productos_inactivos || 0}</p>
          </div>
          <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="w-5 h-5 text-purple-400" />
            </div>
            <p className="text-sm text-slate-400 mb-1">Líneas</p>
            <p className="text-2xl font-bold text-white">{resumen.lineas?.length || 0}</p>
          </div>
        </div>
      )}

      {/* Filtros y Búsqueda */}
      <div className="bg-slate-800/50 rounded-xl p-4 border border-slate-700/50">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Buscar por código, descripción, categoría o marca..."
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
            value={filtroLinea}
            onChange={(e) => setFiltroLinea(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas las líneas</option>
            {resumen?.lineas?.map((linea) => (
              <option key={linea} value={linea}>{linea}</option>
            ))}
          </select>
          <select
            value={filtroMarca}
            onChange={(e) => setFiltroMarca(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Todas las marcas</option>
            {resumen?.marcas?.map((marca) => (
              <option key={marca} value={marca}>{marca}</option>
            ))}
          </select>
        </div>
        {(busqueda || filtroActivo !== null || filtroLinea || filtroMarca) && (
          <button
            onClick={limpiarFiltros}
            className="mt-3 flex items-center gap-2 text-sm text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
            Limpiar filtros
          </button>
        )}
      </div>

      {/* Tabla de Productos */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Código UR</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Referencia</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Descripción</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Línea</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Marca</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-400 uppercase">Precio</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">Estado</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-400 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {productos.length > 0 ? (
                productos.map((producto) => (
                  <tr key={producto.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-semibold text-white text-sm">{producto.cod_ur || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{producto.referencia || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{producto.descripcion || 'N/A'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{producto.linea || '-'}</p>
                    </td>
                    <td className="px-4 py-3">
                      <p className="text-sm text-slate-300">{producto.marca || '-'}</p>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <p className="text-sm font-semibold text-white">{formatCurrency(producto.precio || 0)}</p>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                        producto.activo 
                          ? 'bg-emerald-500/20 text-emerald-400' 
                          : 'bg-red-500/20 text-red-400'
                      }`}>
                        {producto.activo ? 'Activo' : 'Inactivo'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          onClick={() => abrirEditar(producto)}
                          className="p-2 text-blue-400 hover:bg-blue-500/20 rounded-lg transition-colors"
                          title="Editar"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEliminar(producto.id)}
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
                  <td colSpan="8" className="px-4 py-8 text-center">
                    <p className="text-slate-500">No se encontraron productos</p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal Crear Producto */}
      {mostrarCrear && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4">Nuevo Producto</h3>
            <form onSubmit={handleCrear} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Código UR *</label>
                <input
                  type="text"
                  required
                  value={formData.cod_ur}
                  onChange={(e) => setFormData({ ...formData, cod_ur: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Código único del producto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Referencia *</label>
                <input
                  type="text"
                  required
                  value={formData.referencia}
                  onChange={(e) => setFormData({ ...formData, referencia: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Referencia del producto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Descripción *</label>
                <input
                  type="text"
                  required
                  value={formData.descripcion}
                  onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Descripción del producto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Precio *</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0"
                  value={formData.precio}
                  onChange={(e) => setFormData({ ...formData, precio: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="0.00"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Línea</label>
                <input
                  type="text"
                  value={formData.linea}
                  onChange={(e) => setFormData({ ...formData, linea: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Línea del producto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Marca</label>
                <input
                  type="text"
                  value={formData.marca}
                  onChange={(e) => setFormData({ ...formData, marca: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Marca del producto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Equivalencia</label>
                <input
                  type="text"
                  value={formData.equivalencia}
                  onChange={(e) => setFormData({ ...formData, equivalencia: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Equivalencia del producto"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Detalle Descuento</label>
                <input
                  type="text"
                  value={formData.detalle_descuento}
                  onChange={(e) => setFormData({ ...formData, detalle_descuento: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Detalle de descuento"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.activo}
                  onChange={(e) => setFormData({ ...formData, activo: e.target.checked })}
                  className="w-4 h-4 text-blue-500 bg-slate-900 border-slate-700 rounded focus:ring-blue-500"
                />
                <label className="text-sm text-slate-300">Producto activo</label>
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

      {/* Modal Editar Producto */}
      {mostrarEditar && productoSeleccionado && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-md border border-slate-700">
            <h3 className="text-xl font-bold text-white mb-4">Editar Producto</h3>
            <form onSubmit={handleEditar} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Código UR *</label>
                <input
                  type="text"
                  required
                  value={formData.cod_ur}
                  onChange={(e) => setFormData({ ...formData, cod_ur: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Referencia *</label>
                <input
                  type="text"
                  required
                  value={formData.referencia}
                  onChange={(e) => setFormData({ ...formData, referencia: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Descripción *</label>
                <input
                  type="text"
                  required
                  value={formData.descripcion}
                  onChange={(e) => setFormData({ ...formData, descripcion: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Precio *</label>
                <input
                  type="number"
                  required
                  step="0.01"
                  min="0"
                  value={formData.precio}
                  onChange={(e) => setFormData({ ...formData, precio: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Línea</label>
                <input
                  type="text"
                  value={formData.linea}
                  onChange={(e) => setFormData({ ...formData, linea: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Marca</label>
                <input
                  type="text"
                  value={formData.marca}
                  onChange={(e) => setFormData({ ...formData, marca: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Equivalencia</label>
                <input
                  type="text"
                  value={formData.equivalencia}
                  onChange={(e) => setFormData({ ...formData, equivalencia: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Detalle Descuento</label>
                <input
                  type="text"
                  value={formData.detalle_descuento}
                  onChange={(e) => setFormData({ ...formData, detalle_descuento: e.target.value })}
                  className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={formData.activo}
                  onChange={(e) => setFormData({ ...formData, activo: e.target.checked })}
                  className="w-4 h-4 text-blue-500 bg-slate-900 border-slate-700 rounded focus:ring-blue-500"
                />
                <label className="text-sm text-slate-300">Producto activo</label>
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
                    setProductoSeleccionado(null)
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
    </div>
  )
}

export default CatalogView
