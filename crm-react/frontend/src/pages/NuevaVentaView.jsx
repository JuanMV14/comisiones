import React from 'react'

const NuevaVentaView = () => {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Nueva Venta Simple</h2>
        <p className="text-sm text-slate-400">Registra una venta rápidamente</p>
      </div>
      <div className="bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
        <p className="text-slate-400">Vista de Nueva Venta - En desarrollo</p>
        <p className="text-sm text-slate-500 mt-2">
          Esta vista incluirá: selección de cliente, productos editables, descuentos por escala, 
          cálculo automático de comisiones, campos de fecha, pedido y factura.
        </p>
      </div>
    </div>
  )
}

export default NuevaVentaView
