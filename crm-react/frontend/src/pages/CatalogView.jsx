import React, { useState, useEffect } from 'react'
import { Package, Search, Plus, Edit2, Trash2, Filter, X, Loader2, AlertCircle, CheckCircle, TrendingUp, Upload } from 'lucide-react'
import { getProductos, crearProducto, actualizarProducto, eliminarProducto, getResumenCatalogo, actualizarCatalogoDesdeExcel } from '../api/catalogo'

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
  const [mostrarSubirArchivo, setMostrarSubirArchivo] = useState(false)
  const [productoSeleccionado, setProductoSeleccionado] = useState(null)
  const [archivoSeleccionado, setArchivoSeleccionado] = useState(null)
  const [subiendoArchivo, setSubiendoArchivo] = useState(false)
  const [resultadoSubida, setResultadoSubida] = useState(null)
  
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

  const handleSubirArchivo = async (e) => {
    e.preventDefault()
    if (!archivoSeleccionado) {
      alert('Por favor selecciona un archivo Excel')
      return
    }

    try {
      setSubiendoArchivo(true)
      setResultadoSubida(null)
      
      console.log('📤 Subiendo archivo:', archivoSeleccionado.name)
      
      const resultado = await actualizarCatalogoDesdeExcel(archivoSeleccionado)
      
      console.log('✅ Archivo procesado:', resultado)
      setResultadoSubida(resultado)
      
      // Recargar datos después de 2 segundos si fue exitoso
      if (!resultado.error) {
        setTimeout(() => {
          cargarDatos()
          setMostrarSubirArchivo(false)
          setArchivoSeleccionado(null)
          setResultadoSubida(null)
        }, 2000)
      }
      
    } catch (err) {
      console.error('❌ Error subiendo archivo:', err)
      console.error('Error completo:', {
        message: err.message,
        response: err.response,
        status: err.response?.status,
        data: err.response?.data
      })
      
      let mensajeError = 'Error desconocido al subir el archivo'
      
      if (err.response) {
        // Error del servidor
        if (err.response.status === 404) {
          mensajeError = 'Endpoint no encontrado. Verifica que el backend esté corriendo y la ruta sea correcta.'
        } else if (err.response.status === 413) {
          mensajeError = 'El archivo es demasiado grande. Intenta con un archivo más pequeño.'
        } else {
          mensajeError = err.response.data?.detail || err.response.data?.message || `Error del servidor: ${err.response.status} ${err.response.statusText}`
        }
      } else if (err.request) {
        // Error de red
        mensajeError = 'No se pudo conectar al servidor. Verifica que el backend esté corriendo y la URL esté configurada correctamente.'
      } else {
        mensajeError = err.message || mensajeError
      }
      
      setResultadoSubida({
        error: mensajeError
      })
    } finally {
      setSubiendoArchivo(false)
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
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              setMostrarSubirArchivo(true)
              setResultadoSubida(null)
              setArchivoSeleccionado(null)
            }}
            className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Actualizar Catálogo
          </button>
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

      {/* Modal Subir Archivo Excel */}
      {mostrarSubirArchivo && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 overflow-y-auto p-4">
          <div className="bg-slate-800 rounded-xl p-6 w-full max-w-4xl border border-slate-700 my-8">
            <h3 className="text-xl font-bold text-white mb-4">Actualizar Catálogo desde Excel</h3>
            
            {resultadoSubida && (
              <div className={`mb-4 p-4 rounded-lg ${
                resultadoSubida.error 
                  ? 'bg-red-500/10 border border-red-500/20' 
                  : 'bg-emerald-500/10 border border-emerald-500/20'
              }`}>
                {resultadoSubida.error ? (
                  <div>
                    <p className="text-red-400 font-semibold mb-2">❌ Error</p>
                    <p className="text-red-300 text-sm">{resultadoSubida.error}</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    <div>
                      <p className="text-emerald-400 font-semibold mb-3">✅ Actualización completada</p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                        <div>
                          <p className="text-slate-400">Total productos</p>
                          <p className="text-white font-semibold text-lg">{resultadoSubida.total_productos || 0}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Productos nuevos</p>
                          <p className="text-emerald-400 font-semibold text-lg">{resultadoSubida.productos_nuevos || 0}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Productos actualizados</p>
                          <p className="text-blue-400 font-semibold text-lg">{resultadoSubida.productos_actualizados || 0}</p>
                        </div>
                        <div>
                          <p className="text-slate-400">Productos agotados</p>
                          <p className="text-red-400 font-semibold text-lg">{resultadoSubida.productos_agotados || resultadoSubida.productos_desactivados || 0}</p>
                        </div>
                      </div>
                    </div>

                    {/* Lista de Productos Nuevos */}
                    {resultadoSubida.productos_nuevos_detalle && resultadoSubida.productos_nuevos_detalle.length > 0 && (
                      <div className="mt-4 border-t border-slate-700 pt-4">
                        <h4 className="text-emerald-400 font-semibold mb-2 flex items-center gap-2">
                          <CheckCircle className="w-5 h-5" />
                          Productos Nuevos ({resultadoSubida.productos_nuevos_detalle.length})
                        </h4>
                        <div className="max-h-48 overflow-y-auto space-y-2">
                          {resultadoSubida.productos_nuevos_detalle.map((producto, idx) => (
                            <div key={idx} className="bg-slate-900/50 rounded-lg p-3 text-sm">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="text-white font-semibold">{producto.cod_ur}</p>
                                  <p className="text-slate-300">{producto.descripcion || producto.referencia}</p>
                                  <div className="flex gap-3 mt-1 text-xs text-slate-400">
                                    {producto.marca && <span>Marca: {producto.marca}</span>}
                                    {producto.linea && <span>Línea: {producto.linea}</span>}
                                    {producto.precio > 0 && <span>Precio: {formatCurrency(producto.precio)}</span>}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Lista de Productos Agotados */}
                    {resultadoSubida.productos_agotados_detalle && resultadoSubida.productos_agotados_detalle.length > 0 && (
                      <div className="mt-4 border-t border-slate-700 pt-4">
                        <h4 className="text-red-400 font-semibold mb-2 flex items-center gap-2">
                          <AlertCircle className="w-5 h-5" />
                          Productos Agotados ({resultadoSubida.productos_agotados_detalle.length})
                        </h4>
                        <div className="max-h-48 overflow-y-auto space-y-2">
                          {resultadoSubida.productos_agotados_detalle.map((producto, idx) => (
                            <div key={idx} className="bg-red-500/10 border border-red-500/20 rounded-lg p-3 text-sm">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <p className="text-red-300 font-semibold">{producto.cod_ur}</p>
                                  <p className="text-slate-300">{producto.descripcion || producto.referencia}</p>
                                  <div className="flex gap-3 mt-1 text-xs text-slate-400">
                                    {producto.marca && <span>Marca: {producto.marca}</span>}
                                    {producto.linea && <span>Línea: {producto.linea}</span>}
                                    {producto.precio > 0 && <span>Precio: {formatCurrency(producto.precio)}</span>}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

            {!resultadoSubida && (
              <form onSubmit={handleSubirArchivo} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Selecciona archivo Excel (.xlsx, .xls)
                  </label>
                  <input
                    type="file"
                    accept=".xlsx,.xls"
                    onChange={(e) => setArchivoSeleccionado(e.target.files[0])}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    disabled={subiendoArchivo}
                  />
                  <p className="text-xs text-slate-400 mt-2">
                    El archivo debe contener las columnas: Cod_UR, Referencia, Descripcion, Precio, Marca, Linea, Equivalencia, DetalleDescuento
                  </p>
                </div>
                
                <div className="flex gap-3 pt-4">
                  <button
                    type="submit"
                    disabled={!archivoSeleccionado || subiendoArchivo}
                    className="flex-1 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {subiendoArchivo ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Procesando...
                      </>
                    ) : (
                      <>
                        <Upload className="w-4 h-4" />
                        Subir y Actualizar
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setMostrarSubirArchivo(false)
                      setArchivoSeleccionado(null)
                      setResultadoSubida(null)
                    }}
                    disabled={subiendoArchivo}
                    className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50"
                  >
                    Cancelar
                  </button>
                </div>
              </form>
            )}

            {resultadoSubida && !resultadoSubida.error && (
              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setMostrarSubirArchivo(false)
                    setArchivoSeleccionado(null)
                    setResultadoSubida(null)
                  }}
                  className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Cerrar
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default CatalogView
