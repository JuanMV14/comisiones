import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  Home, 
  Users, 
  TrendingUp, 
  DollarSign, 
  Package, 
  MessageSquare, 
  Settings,
  BarChart3,
  MapPin,
  FileText,
  ArrowLeftRight,
  Download,
  UserCog
} from 'lucide-react'

const Sidebar = () => {
  const location = useLocation()

  const opcionesVendedor = [
    { icon: Home, label: 'Panel del Vendedor', path: '/panel-vendedor', key: 'panel-vendedor' },
    { icon: Users, label: 'Clientes', path: '/clientes', key: 'clientes' },
    { icon: TrendingUp, label: 'Nueva Venta', path: '/nueva-venta', key: 'nueva-venta' },
    { icon: Package, label: 'Catálogo', path: '/catalogo', key: 'catalogo' },
    { icon: MessageSquare, label: 'Mensajería', path: '/mensajeria', key: 'mensajeria', badge: 2 },
    { icon: FileText, label: 'Facturas', path: '/facturas', key: 'facturas' }
  ]

  const opcionesGerencia = [
    { icon: BarChart3, label: 'Dashboard Ejecutivo', path: '/dashboard-ejecutivo', key: 'dashboard-ejecutivo' },
    { icon: MapPin, label: 'Análisis Geográfico', path: '/analisis-geografico', key: 'analisis-geografico' },
    { icon: TrendingUp, label: 'Análisis Comercial', path: '/analisis-comercial', key: 'analisis-comercial' },
    { icon: DollarSign, label: 'Comisiones', path: '/comisiones', key: 'comisiones' },
    { icon: UserCog, label: 'Gestión Clientes B2B', path: '/gestion-clientes-b2b', key: 'gestion-clientes-b2b' },
    { icon: Package, label: 'Análisis Compras', path: '/analisis-compras', key: 'analisis-compras' },
    { icon: ArrowLeftRight, label: 'Devoluciones', path: '/devoluciones', key: 'devoluciones' },
    { icon: Download, label: 'Importaciones y Stock', path: '/importaciones-stock', key: 'importaciones-stock' },
    { icon: FileText, label: 'Reportes', path: '/reportes', key: 'reportes' }
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen">
      <div className="p-6 border-b border-slate-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
            <Package className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-white font-bold text-lg">CRM</h2>
            <p className="text-xs text-slate-400">Sistema de Gestión</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-4 mt-2">NAVEGACIÓN</p>
        
        {opcionesVendedor.map((item) => {
          const Icon = item.icon
          const active = isActive(item.path)
          return (
            <Link
              key={item.key}
              to={item.path}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                active
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium flex-1 text-left">{item.label}</span>
              {item.badge && (
                <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">{item.badge}</span>
              )}
            </Link>
          )
        })}

        <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-4 mt-8">ADMINISTRACIÓN</p>
        
        {opcionesGerencia.map((item) => {
          const Icon = item.icon
          const active = isActive(item.path)
          return (
            <Link
              key={item.key}
              to={item.path}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                active
                  ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                  : 'text-slate-400 hover:bg-slate-800 hover:text-white'
              }`}
            >
              <Icon className="w-5 h-5" />
              <span className="text-sm font-medium flex-1 text-left">{item.label}</span>
            </Link>
          )
        })}
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button className="w-full flex items-center gap-3 px-4 py-3 text-slate-400 hover:bg-slate-800 hover:text-white rounded-lg transition-all">
          <Settings className="w-5 h-5" />
          <span className="text-sm font-medium">Configuración</span>
        </button>
      </div>
    </div>
  )
}

export default Sidebar
