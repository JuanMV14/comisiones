import React, { useState, useEffect } from 'react'
import { Search, Mail, Eye, MapPin, X, Save, Loader2, Trash2, AlertTriangle } from 'lucide-react'
import { getClientes, crearCliente, actualizarCliente, eliminarCliente } from '../api/clientes'

const ClientesView = () => {
  const [clientes, setClientes] = useState([])
  const [searchTerm, setSearchTerm] = useState('')
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingCliente, setEditingCliente] = useState(null)
  const [saving, setSaving] = useState(false)
  const [clienteAEliminar, setClienteAEliminar] = useState(null)
  const [mostrarConfirmacion, setMostrarConfirmacion] = useState(false)
  const [formData, setFormData] = useState({
    nombre: '',
    nit: '',
    contacto: '',
    email: '',
    telefono: '',
    ciudad: '',
    direccion: '',
    cupo_total: 0,
    plazo_pago: 30,
    descuento_predeterminado: 0,
    cliente_propio: true
  })

  useEffect(() => {
    loadClientes()
  }, [])

  const loadClientes = async () => {
    try {
      setLoading(true)
      const data = await getClientes()
      setClientes(data)
    } catch (error) {
      console.error('Error loading clientes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleNuevoCliente = () => {
    setEditingCliente(null)
    setFormData({
      nombre: '',
      nit: '',
      contacto: '',
      email: '',
      telefono: '',
      ciudad: '',
      direccion: '',
      cupo_total: 0,
      plazo_pago: 30,
      descuento_predeterminado: 0,
      cliente_propio: true
    })
    setShowModal(true)
  }

  const handleEditarCliente = (cliente) => {
    setEditingCliente(cliente)
    setFormData({
      nombre: cliente.nombre || '',
      nit: cliente.nit || '',
      contacto: cliente.contacto || cliente.nombre || '',
      email: cliente.email || '',
      telefono: cliente.telefono || '',
      ciudad: cliente.ciudad || '',
      direccion: cliente.direccion || '',
      cupo_total: cliente.credito || cliente.cupo_total || 0,
      plazo_pago: cliente.plazo_pago || 30,
      descuento_predeterminado: cliente.descuento_predeterminado || 0,
      cliente_propio: cliente.cliente_propio !== undefined ? cliente.cliente_propio : true
    })
    setShowModal(true)
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      
      if (editingCliente && editingCliente.id) {
        // Actualizar cliente existente
        await actualizarCliente(editingCliente.id, formData)
      } else {
        // Crear nuevo cliente
        await crearCliente(formData)
      }
      
      setShowModal(false)
      await loadClientes()
    } catch (error) {
      console.error('Error guardando cliente:', error)
      alert('Error al guardar el cliente: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  const handleEliminarClick = (cliente) => {
    setClienteAEliminar(cliente)
    setMostrarConfirmacion(true)
  }

  const handleConfirmarEliminar = async () => {
    if (!clienteAEliminar) return

    try {
      setSaving(true)
      const resultado = await eliminarCliente(clienteAEliminar.id)
      
      setMostrarConfirmacion(false)
      setClienteAEliminar(null)
      
      // Mostrar mensaje apropiado según el resultado
      if (resultado.success) {
        if (resultado.cliente) {
          alert('Cliente eliminado correctamente (marcado como inactivo)')
        } else {
          alert(resultado.mensaje || 'El cliente no existe en clientes_b2b. Solo está en el historial de comisiones.')
        }
        await loadClientes()
      } else {
        alert(resultado.mensaje || 'No se pudo eliminar el cliente')
      }
    } catch (error) {
      console.error('Error eliminando cliente:', error)
      const errorMessage = error.response?.data?.detail || error.message
      alert(`Error al eliminar el cliente: ${errorMessage}`)
    } finally {
      setSaving(false)
    }
  }

  const handleCancelarEliminar = () => {
    setMostrarConfirmacion(false)
    setClienteAEliminar(null)
  }

  const filteredClientes = clientes.filter(cliente =>
    cliente.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
    cliente.contacto?.toLowerCase().includes(searchTerm.toLowerCase())
  )

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(val)
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Clientes</h2>
          <p className="text-sm text-slate-400">Gestiona tus clientes comerciales</p>
        </div>
        <button 
          onClick={handleNuevoCliente}
          className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          Nuevo Cliente
        </button>
      </div>

      {/* Buscador */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
        <input
          type="text"
          placeholder="Buscar clientes por nombre o contacto..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-slate-500"
        />
      </div>

      {/* Tabla de Clientes */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ciudad</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Crédito</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Estado</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {loading ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-slate-400">
                    Cargando clientes...
                  </td>
                </tr>
              ) : filteredClientes.length === 0 ? (
                <tr>
                  <td colSpan="5" className="px-4 py-8 text-center text-slate-400">
                    No se encontraron clientes
                  </td>
                </tr>
              ) : (
                filteredClientes.map((cliente) => (
                  <tr key={cliente.id} className="hover:bg-slate-700/30 transition-colors">
                    <td className="px-4 py-4">
                      <div>
                        <p className="font-semibold text-white text-sm">{cliente.nombre}</p>
                        <p className="text-xs text-slate-400">{cliente.contacto}</p>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-slate-400" />
                        <span className="text-sm text-slate-300">{cliente.ciudad || 'N/A'}</span>
                      </div>
                    </td>
                    <td className="px-4 py-4">
                      <p className="text-sm font-semibold text-white">
                        {cliente.credito ? formatCurrency(cliente.credito) : 'N/A'}
                      </p>
                    </td>
                    <td className="px-4 py-4">
                      <span className={`inline-flex px-2 py-1 rounded text-xs ${
                        cliente.estado === 'activo' 
                          ? 'bg-emerald-500/10 text-emerald-400' 
                          : 'bg-red-500/10 text-red-400'
                      }`}>
                        {cliente.estado || 'activo'}
                      </span>
                    </td>
                    <td className="px-4 py-4">
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => handleEditarCliente(cliente)}
                          className="p-1.5 text-blue-400 hover:bg-blue-500/10 rounded transition-colors"
                          title="Editar cliente"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleEliminarClick(cliente)}
                          className="p-1.5 text-red-400 hover:bg-red-500/10 rounded transition-colors"
                          title="Eliminar cliente"
                          disabled={saving}
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

      {/* Modal de Crear/Editar Cliente */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-slate-800 border-b border-slate-700 px-6 py-4 flex items-center justify-between">
              <h3 className="text-xl font-bold text-white">
                {editingCliente ? 'Editar Cliente' : 'Nuevo Cliente'}
              </h3>
              <button
                onClick={() => setShowModal(false)}
                className="text-slate-400 hover:text-white transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Nombre *
                  </label>
                  <input
                    type="text"
                    value={formData.nombre}
                    onChange={(e) => setFormData({ ...formData, nombre: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    NIT
                  </label>
                  <input
                    type="text"
                    value={formData.nit}
                    onChange={(e) => setFormData({ ...formData, nit: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Contacto
                  </label>
                  <input
                    type="text"
                    value={formData.contacto}
                    onChange={(e) => setFormData({ ...formData, contacto: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Teléfono
                  </label>
                  <input
                    type="text"
                    value={formData.telefono}
                    onChange={(e) => setFormData({ ...formData, telefono: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Ciudad
                  </label>
                  <input
                    type="text"
                    value={formData.ciudad}
                    onChange={(e) => setFormData({ ...formData, ciudad: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="md:col-span-2">
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Dirección
                  </label>
                  <input
                    type="text"
                    value={formData.direccion}
                    onChange={(e) => setFormData({ ...formData, direccion: e.target.value })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Cupo Total (COP)
                  </label>
                  <input
                    type="number"
                    value={formData.cupo_total}
                    onChange={(e) => setFormData({ ...formData, cupo_total: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Plazo de Pago (días)
                  </label>
                  <input
                    type="number"
                    value={formData.plazo_pago}
                    onChange={(e) => setFormData({ ...formData, plazo_pago: parseInt(e.target.value) || 30 })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-2">
                    Descuento Predeterminado (%)
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.descuento_predeterminado}
                    onChange={(e) => setFormData({ ...formData, descuento_predeterminado: parseFloat(e.target.value) || 0 })}
                    className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* Opciones adicionales */}
              <div className="mt-4 pt-4 border-t border-slate-700">
                <h4 className="text-sm font-semibold text-slate-300 mb-3">Configuración del Cliente</h4>
                <div className="space-y-3">
                  <label className="flex items-center gap-3 cursor-pointer group">
                    <input
                      type="checkbox"
                      checked={formData.cliente_propio}
                      onChange={(e) => setFormData({ ...formData, cliente_propio: e.target.checked })}
                      className="w-5 h-5 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-2 focus:ring-blue-500 cursor-pointer"
                    />
                    <div className="flex-1">
                      <span className="text-sm font-medium text-white group-hover:text-blue-400 transition-colors">
                        Cliente Propio
                      </span>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {formData.cliente_propio 
                          ? 'Este cliente genera comisiones completas (2.5% sin descuento, 1.5% con descuento)'
                          : 'Este cliente genera comisiones reducidas (1.0% sin descuento, 0.5% con descuento)'}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      formData.cliente_propio 
                        ? 'bg-blue-500/20 text-blue-400' 
                        : 'bg-slate-700/50 text-slate-400'
                    }`}>
                      {formData.cliente_propio ? 'Propio' : 'Externo'}
                    </span>
                  </label>
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-slate-800 border-t border-slate-700 px-6 py-4 flex items-center justify-end gap-3">
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 text-slate-300 hover:text-white transition-colors"
                disabled={saving}
              >
                Cancelar
              </button>
              <button
                onClick={handleSave}
                disabled={saving || !formData.nombre}
                className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {saving ? (
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

      {/* Modal de Confirmación de Eliminación */}
      {mostrarConfirmacion && clienteAEliminar && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-slate-800 rounded-xl border border-red-500/50 w-full max-w-md">
            <div className="p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 bg-red-500/10 rounded-lg">
                  <AlertTriangle className="w-6 h-6 text-red-400" />
                </div>
                <h3 className="text-xl font-bold text-white">Confirmar Eliminación</h3>
              </div>
              <p className="text-slate-300 mb-2">
                ¿Estás seguro de que deseas eliminar el cliente?
              </p>
              <p className="text-slate-400 text-sm mb-6">
                <strong className="text-white">{clienteAEliminar.nombre}</strong>
                <br />
                <span className="text-xs">El cliente será marcado como inactivo (soft delete)</span>
              </p>
              <div className="flex items-center justify-end gap-3">
                <button
                  onClick={handleCancelarEliminar}
                  disabled={saving}
                  className="px-4 py-2 text-slate-300 hover:text-white transition-colors disabled:opacity-50"
                >
                  Cancelar
                </button>
                <button
                  onClick={handleConfirmarEliminar}
                  disabled={saving}
                  className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {saving ? (
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

export default ClientesView
