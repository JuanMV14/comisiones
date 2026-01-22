import React from 'react'
import { MessageSquare, Mail, Search, Clock } from 'lucide-react'

const MensajesView = () => {
  const mensajes = [
    { id: 1, remitente: 'Victor Gómez', mensaje: 'Buenos días, ¿tienen disponibilidad del...', fecha: '11.05.2025', hora: '15:32', leido: false, avatar: 'VG' },
    { id: 2, remitente: 'Andrés Mejía', mensaje: 'Necesito cotización urgente para alternadores', fecha: '11.05.2025', hora: '14:20', leido: false, avatar: 'AM' },
    { id: 3, remitente: 'María González', mensaje: 'Gracias por el envío, todo llegó perfecto', fecha: '10.05.2025', hora: '16:45', leido: true, avatar: 'MG' }
  ]

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Mensajes</h2>
          <p className="text-sm text-slate-400">Comunicación con tus clientes</p>
        </div>
        <button className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2">
          <Mail className="w-4 h-4" />
          Nuevo mensaje
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 bg-slate-800/50 rounded-xl border border-slate-700/50 overflow-hidden">
          <div className="p-4 border-b border-slate-700">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Buscar mensajes..."
                className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-slate-500 text-sm"
              />
            </div>
          </div>
          <div className="divide-y divide-slate-700">
            {mensajes.map((msg) => (
              <div key={msg.id} className={`p-4 cursor-pointer transition-colors ${
                !msg.leido ? 'bg-blue-500/5 hover:bg-blue-500/10' : 'hover:bg-slate-700/30'
              }`}>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-sm flex-shrink-0">
                    {msg.avatar}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium text-white truncate">{msg.remitente}</p>
                      {!msg.leido && <div className="w-2 h-2 bg-blue-500 rounded-full"></div>}
                    </div>
                    <p className="text-xs text-slate-400 truncate mb-1">{msg.mensaje}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <Clock className="w-3 h-3" />
                      <span>{msg.hora}</span>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-800/50 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="text-center">
              <MessageSquare className="w-16 h-16 mx-auto mb-4 opacity-50" />
              <p className="text-lg">Selecciona un mensaje para ver la conversación</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default MensajesView
