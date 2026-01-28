import React, { useState, useEffect } from 'react'
import { Save, Loader2, Calculator, DollarSign, Calendar, FileText, User, MapPin, Truck, Percent } from 'lucide-react'
import { getClientes } from '../api/clientes'
import { crearVenta } from '../api/ventas'

const NuevaVentaView = () => {
  const [clientes, setClientes] = useState([])
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [comisionCalculada, setComisionCalculada] = useState(null)
  const [clienteSeleccionado, setClienteSeleccionado] = useState(null)
  const [formData, setFormData] = useState({
    pedido: '',
    cliente: '',
    factura: '',
    fecha_factura: new Date().toISOString().split('T')[0],
    valor_total: 0,
    descuento_adicional: 0,
    ciudad_destino: 'Resto',
    recogida_local: false,
    valor_flete: 0,
    referencia: ''
  })

  useEffect(() => {
    loadClientes()
  }, [])

  useEffect(() => {
    calcularComision()
  }, [
    formData.valor_total,
    formData.valor_flete,
    formData.descuento_adicional,
    clienteSeleccionado
  ])

  // Cargar datos del cliente cuando se selecciona
  useEffect(() => {
    if (formData.cliente) {
      const cliente = clientes.find(c => c.nombre === formData.cliente)
      if (cliente) {
        setClienteSeleccionado(cliente)
        // Actualizar ciudad destino con la ciudad del cliente si existe
        // Solo actualizar si la ciudad del cliente es válida y diferente de 'N/A'
        const ciudadCliente = cliente.ciudad
        if (ciudadCliente && 
            ciudadCliente !== 'N/A' && 
            ciudadCliente !== 'Resto' &&
            ciudadCliente.trim() !== '' &&
            ciudadCliente.trim().toLowerCase() !== 'n/a') {
          setFormData(prev => ({
            ...prev,
            ciudad_destino: ciudadCliente.trim()
          }))
        }
      } else {
        setClienteSeleccionado(null)
      }
    } else {
      setClienteSeleccionado(null)
    }
  }, [formData.cliente, clientes])

  const loadClientes = async () => {
    try {
      const data = await getClientes()
      setClientes(data)
    } catch (error) {
      console.error('Error cargando clientes:', error)
    }
  }

  const calcularComision = () => {
    if (formData.valor_total <= 0) {
      setComisionCalculada(null)
      return
    }

    // Obtener datos del cliente seleccionado
    const cliente_propio = clienteSeleccionado?.cliente_propio !== undefined 
      ? clienteSeleccionado.cliente_propio 
      : true // Por defecto es propio
    const descuento_predeterminado = clienteSeleccionado?.descuento_predeterminado || 0
    const plazo_pago = clienteSeleccionado?.plazo_pago || 30
    const condicion_especial = plazo_pago > 45 // Si el plazo es mayor a 45 días, es condición especial

    // Calcular valor neto
    const valor_productos_con_iva = formData.valor_total - formData.valor_flete
    const valor_neto = valor_productos_con_iva / 1.19
    const iva = valor_productos_con_iva - valor_neto

    // Calcular base de comisión
    // Si hay descuento predeterminado del cliente, se considera como descuento a pie de factura
    // El descuento predeterminado (15% base) NO reduce la comisión, solo afecta la base
    const tiene_descuento_predeterminado = descuento_predeterminado > 0
    let base = tiene_descuento_predeterminado ? valor_neto : valor_neto * 0.85

    // Determinar porcentaje
    // IMPORTANTE: Solo el descuento ADICIONAL (superior al base) reduce la comisión
    // El descuento predeterminado del 15% NO reduce la comisión
    const tiene_descuento_adicional = formData.descuento_adicional > 0
    // NO incluir descuento_predeterminado aquí - solo afecta la base, no el porcentaje
    let porcentaje = 0
    if (cliente_propio) {
      porcentaje = tiene_descuento_adicional ? 1.5 : 2.5
    } else {
      porcentaje = tiene_descuento_adicional ? 0.5 : 1.0
    }

    const comision = base * (porcentaje / 100)

    setComisionCalculada({
      valor_neto,
      iva,
      base_comision: base,
      comision,
      porcentaje,
      cliente_propio,
      condicion_especial
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!formData.pedido || !formData.cliente || formData.valor_total <= 0) {
      alert('Por favor completa todos los campos requeridos')
      return
    }

    try {
      setSaving(true)
      
      // Obtener datos del cliente para la venta
      const cliente_propio = clienteSeleccionado?.cliente_propio !== undefined 
        ? clienteSeleccionado.cliente_propio 
        : true
      const descuento_predeterminado = clienteSeleccionado?.descuento_predeterminado || 0
      const plazo_pago = clienteSeleccionado?.plazo_pago || 30
      const condicion_especial = plazo_pago > 45
      const descuento_pie_factura = descuento_predeterminado > 0

      const ventaData = {
        ...formData,
        fecha_factura: new Date(formData.fecha_factura).toISOString(),
        cliente_propio: cliente_propio,
        descuento_pie_factura: descuento_pie_factura,
        condicion_especial: condicion_especial
      }

      const resultado = await crearVenta(ventaData)
      
      alert(`✅ Venta creada exitosamente!\nFactura: ${resultado.factura}\nComisión: $${resultado.comision.toLocaleString('es-CO')}`)
      
      // Resetear formulario
      setFormData({
        pedido: '',
        cliente: '',
        factura: '',
        fecha_factura: new Date().toISOString().split('T')[0],
        valor_total: 0,
        descuento_adicional: 0,
        ciudad_destino: 'Resto',
        recogida_local: false,
        valor_flete: 0,
        referencia: ''
      })
      setClienteSeleccionado(null)
      setComisionCalculada(null)
    } catch (error) {
      console.error('Error creando venta:', error)
      alert('Error al crear la venta: ' + (error.response?.data?.detail || error.message))
    } finally {
      setSaving(false)
    }
  }

  const formatCurrency = (val) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0
    }).format(val)
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Nueva Venta</h2>
        <p className="text-sm text-slate-400">Registra una venta rápidamente</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-400" />
            Información de la Venta
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Número de Pedido *
              </label>
              <input
                type="text"
                value={formData.pedido}
                onChange={(e) => setFormData({ ...formData, pedido: e.target.value })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Número de Factura
              </label>
              <input
                type="text"
                value={formData.factura}
                onChange={(e) => setFormData({ ...formData, factura: e.target.value })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Se genera automáticamente si se deja vacío"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Fecha de Factura *
              </label>
              <input
                type="date"
                value={formData.fecha_factura}
                onChange={(e) => setFormData({ ...formData, fecha_factura: e.target.value })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Cliente *
              </label>
              <select
                value={formData.cliente}
                onChange={(e) => setFormData({ ...formData, cliente: e.target.value })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              >
                <option value="">Selecciona un cliente</option>
                {clientes.map((cliente) => (
                  <option key={cliente.id || cliente.nombre} value={cliente.nombre}>
                    {cliente.nombre}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Referencia / Producto
              </label>
              <input
                type="text"
                value={formData.referencia}
                onChange={(e) => setFormData({ ...formData, referencia: e.target.value })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Código o nombre del producto"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Ciudad Destino
              </label>
              <input
                type="text"
                value={formData.ciudad_destino}
                onChange={(e) => setFormData({ ...formData, ciudad_destino: e.target.value })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Ciudad de destino"
                list="ciudades-comunes"
              />
              <datalist id="ciudades-comunes">
                <option value="Resto">Resto</option>
                <option value="Medellín">Medellín</option>
                <option value="Bogotá">Bogotá</option>
                <option value="Cali">Cali</option>
                <option value="Barranquilla">Barranquilla</option>
                <option value="Cartagena">Cartagena</option>
                <option value="Bucaramanga">Bucaramanga</option>
                <option value="Pereira">Pereira</option>
                <option value="Santa Marta">Santa Marta</option>
                <option value="Manizales">Manizales</option>
                <option value="Armenia">Armenia</option>
                <option value="Villavicencio">Villavicencio</option>
                <option value="Ibagué">Ibagué</option>
                <option value="Pasto">Pasto</option>
              </datalist>
            </div>
          </div>
        </div>

        <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-emerald-400" />
            Valores y Descuentos
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Valor Total (con IVA) *
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.valor_total}
                onChange={(e) => setFormData({ ...formData, valor_total: parseFloat(e.target.value) || 0 })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Valor Flete
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.valor_flete}
                onChange={(e) => setFormData({ ...formData, valor_flete: parseFloat(e.target.value) || 0 })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Descuento Adicional (%)
              </label>
              <input
                type="number"
                step="0.01"
                value={formData.descuento_adicional}
                onChange={(e) => setFormData({ ...formData, descuento_adicional: parseFloat(e.target.value) || 0 })}
                className="w-full px-4 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {/* Información del Cliente Seleccionado */}
          {clienteSeleccionado && (
            <div className="mt-4 p-4 bg-slate-900/50 rounded-lg border border-slate-700/50">
              <h4 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
                <User className="w-4 h-4" />
                Información del Cliente
              </h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block mb-1">Tipo:</span>
                  <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                    clienteSeleccionado.cliente_propio 
                      ? 'bg-blue-500/20 text-blue-400' 
                      : 'bg-slate-700/50 text-slate-400'
                  }`}>
                    {clienteSeleccionado.cliente_propio ? 'Cliente Propio' : 'Cliente Externo'}
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-1">Descuento Base:</span>
                  <span className="text-white font-medium">
                    {clienteSeleccionado.descuento_predeterminado || 0}%
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-1">Plazo de Pago:</span>
                  <span className="text-white font-medium">
                    {clienteSeleccionado.plazo_pago || 30} días
                  </span>
                </div>
                <div>
                  <span className="text-slate-400 block mb-1">Condición:</span>
                  <span className={`inline-flex px-2 py-1 rounded text-xs font-medium ${
                    (clienteSeleccionado.plazo_pago || 30) > 45
                      ? 'bg-amber-500/20 text-amber-400' 
                      : 'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {(clienteSeleccionado.plazo_pago || 30) > 45 ? 'Especial' : 'Normal'}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Solo mantener Recogida Local */}
          <div className="mt-4">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={formData.recogida_local}
                onChange={(e) => setFormData({ ...formData, recogida_local: e.target.checked })}
                className="w-4 h-4 rounded border-slate-700 bg-slate-900 text-blue-500 focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-sm text-slate-300">Recogida local</span>
            </label>
          </div>
        </div>

        {comisionCalculada && (
          <div className="bg-gradient-to-br from-emerald-500/10 to-blue-500/10 rounded-xl p-6 border border-emerald-500/20">
            <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
              <Calculator className="w-5 h-5 text-emerald-400" />
              Cálculo de Comisión
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Valor Neto</p>
                <p className="text-lg font-bold text-white">{formatCurrency(comisionCalculada.valor_neto)}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Base Comisión</p>
                <p className="text-lg font-bold text-white">{formatCurrency(comisionCalculada.base_comision)}</p>
              </div>
              <div className="bg-slate-900/50 rounded-lg p-4">
                <p className="text-xs text-slate-400 mb-1">Comisión ({comisionCalculada.porcentaje}%)</p>
                <p className="text-xl font-bold text-emerald-400">{formatCurrency(comisionCalculada.comision)}</p>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-center justify-end gap-3">
          <button
            type="submit"
            disabled={saving || !formData.pedido || !formData.cliente || formData.valor_total <= 0}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {saving ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Guardando...
              </>
            ) : (
              <>
                <Save className="w-5 h-5" />
                Guardar Venta
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}

export default NuevaVentaView
