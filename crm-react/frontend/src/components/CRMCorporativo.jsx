import React, { useState, useMemo, useEffect } from 'react';
import { Users, TrendingUp, DollarSign, Search, Plus, Mail, Phone, Eye, BarChart3, Package, ShoppingCart, FileText, Bell, ArrowUpRight, ArrowDownRight, Loader2 } from 'lucide-react';
import { getClientes } from '../api/clientes';
import { getDashboardMetrics } from '../api/dashboard';
import { getClientesDirecto, getMetricsDirecto } from '../utils/supabaseClient';

const CRMCorporativo = () => {
  const [activeTab, setActiveTab] = useState('panel');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('todos');
  const [selectedClient, setSelectedClient] = useState(null);
  
  // Estados para datos
  const [clientes, setClientes] = useState([]);
  const [estadisticas, setEstadisticas] = useState({
    ventasTotal: 0,
    clientesActivos: 0,
    comisionEstimada: 0,
    facturasCobrar: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cargar datos del backend
  useEffect(() => {
    const cargarDatos = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Intentar cargar desde el backend primero, si falla usar Supabase directo
        let clientesData = [];
        let metricsData = {
          totalVentas: 0,
          comisiones: 0,
          clientesActivos: 0,
          pedidosMes: 0
        };
        
        try {
          // Intentar backend primero
          const [backendClientes, backendMetrics] = await Promise.all([
            getClientes(),
            getDashboardMetrics()
          ]);
          clientesData = backendClientes;
          metricsData = backendMetrics;
        } catch (backendError) {
          console.warn('Backend no disponible, usando conexión directa a Supabase:', backendError);
          // Si el backend falla, usar Supabase directo
          const [supabaseClientes, supabaseMetrics] = await Promise.all([
            getClientesDirecto(),
            getMetricsDirecto()
          ]);
          clientesData = supabaseClientes;
          metricsData = supabaseMetrics;
        }

        // Mapear clientes del backend al formato esperado
        const clientesMapeados = clientesData.map((cliente, index) => ({
          id: cliente.id || index + 1,
          nombre: cliente.nombre || 'Sin nombre',
          contacto: cliente.contacto || cliente.nombre || 'Sin contacto',
          email: cliente.email || '',
          telefono: cliente.telefono || '',
          ciudad: cliente.ciudad || 'N/A',
          credito: cliente.credito || 0,
          creditoUsado: cliente.creditoUsado || 0,
          ultimaCompra: cliente.ultimaCompra || 'N/A',
          ventas: cliente.ventas || 0,
          estado: cliente.estado || 'activo',
          promedioPago: cliente.promedioPago || 0
        }));

        setClientes(clientesMapeados);
        
        // Actualizar estadísticas
        setEstadisticas({
          ventasTotal: metricsData.totalVentas || 0,
          clientesActivos: metricsData.clientesActivos || clientesMapeados.filter(c => c.estado === 'activo').length,
          comisionEstimada: metricsData.comisiones || 0,
          facturasCobrar: 0 // TODO: Implementar cuando esté disponible en la API
        });
      } catch (err) {
        console.error('Error cargando datos:', err);
        setError('Error al cargar los datos. Por favor, verifica que el backend esté funcionando.');
      } finally {
        setLoading(false);
      }
    };

    cargarDatos();
  }, []);

  // Datos de ejemplo para gráficos (hasta que la API los proporcione)
  const ventasMensuales = [
    { mes: 'Ene', ventas: 3300000, comisiones: 320000 },
    { mes: 'Feb', ventas: 4200000, comisiones: 380000 },
    { mes: 'Mar', ventas: 3800000, comisiones: 350000 },
    { mes: 'Abr', ventas: 4100000, comisiones: 390000 },
    { mes: 'May', ventas: 5200000, comisiones: 410000 },
    { mes: 'Jun', ventas: 4500000, comisiones: 395000 },
  ];

  const clientesFiltrados = useMemo(() => {
    return clientes.filter(cliente => {
      const matchSearch = cliente.nombre.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         cliente.contacto.toLowerCase().includes(searchTerm.toLowerCase());
      const matchFilter = filterStatus === 'todos' || cliente.estado === filterStatus;
      return matchSearch && matchFilter;
    });
  }, [clientes, searchTerm, filterStatus]);

  const StatCard = ({ icon: Icon, title, value, subtitle, trend, color }) => (
    <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-5 border border-slate-700/50 hover:border-slate-600/50 transition-all">
      <div className="flex items-start justify-between mb-3">
        <div className={`p-2.5 rounded-lg ${color}`}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        {trend && (
          <div className={`flex items-center gap-1 text-xs font-medium ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {trend > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
            {Math.abs(trend)}%
          </div>
        )}
      </div>
      <div>
        <p className="text-2xl font-bold text-white mb-1">{value}</p>
        <p className="text-xs text-slate-400">{title}</p>
        {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
      </div>
    </div>
  );

  const PanelVendedor = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-slate-400">Cargando datos...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md">
            <p className="text-red-400 mb-2">⚠️ Error</p>
            <p className="text-slate-300 text-sm">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      );
    }

    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Panel del Vendedor</h2>
          <p className="text-sm text-slate-400">Resumen rápido de tu gestión comercial</p>
        </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={DollarSign} title="Ventas del Mes" value={`$${(estadisticas.ventasTotal / 1000000).toFixed(1)}M`} subtitle="Facturación del mes" trend={8.5} color="bg-gradient-to-br from-blue-500 to-blue-600" />
        <StatCard icon={TrendingUp} title="Comisión Estimada" value={`$${(estadisticas.comisionEstimada / 1000).toFixed(0)}K`} subtitle="Este mes" trend={12.3} color="bg-gradient-to-br from-emerald-500 to-emerald-600" />
        <StatCard icon={Users} title="Clientes Activos" value={estadisticas.clientesActivos} subtitle={`${clientes.length} clientes totales`} color="bg-gradient-to-br from-purple-500 to-purple-600" />
        <StatCard icon={FileText} title="Facturas por Cobrar" value={`$${(estadisticas.facturasCobrar / 1000000).toFixed(1)}M`} subtitle={estadisticas.facturasCobrar > 0 ? "Facturas pendientes" : "Sin facturas pendientes"} trend={estadisticas.facturasCobrar > 0 ? -3.2 : null} color="bg-gradient-to-br from-orange-500 to-orange-600" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-center justify-between mb-5">
            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
              <Bell className="w-5 h-5 text-amber-400" />
              Alertas Inteligentes
            </h3>
          </div>
          <div className="space-y-3">
            <div className="p-4 rounded-lg border bg-red-500/5 border-red-500/20">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-red-500/20">
                  <Users className="w-4 h-4 text-red-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white mb-1">Clientes que Dejaron de Comprar</p>
                  <p className="text-xs text-slate-400 leading-relaxed">Sebastián Quintero terminó 35 días, llamar mayor a 25 días</p>
                </div>
              </div>
            </div>
            <div className="p-4 rounded-lg border bg-amber-500/5 border-amber-500/20">
              <div className="flex items-start gap-3">
                <div className="p-2 rounded-lg bg-amber-500/20">
                  <FileText className="w-4 h-4 text-amber-400" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-white mb-1">Facturas Próximas a Vencer</p>
                  <p className="text-xs text-slate-400 leading-relaxed">Factura #56789 vence en 3 días - $1,495,000</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-5">Clientes Clave</h3>
          <div className="space-y-4">
            {clientes.slice(0, 3).map((cliente) => (
              <div key={cliente.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-700/30 hover:bg-slate-700/50 transition-colors">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white font-semibold text-sm">
                    {cliente.contacto.split(' ').map(n => n[0]).join('')}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white">{cliente.contacto}</p>
                    <p className="text-xs text-slate-400">{cliente.nombre}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-semibold text-white">${(cliente.ventas / 1000000).toFixed(1)}M</p>
                  <p className="text-xs text-slate-400">{cliente.ultimaCompra}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-6">Ventas Últimos 6 Meses</h3>
          <div className="h-48 flex items-end justify-between gap-2">
            {ventasMensuales.map((data, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full bg-slate-700/30 rounded-t-lg overflow-hidden relative" style={{ height: '160px' }}>
                  <div className="absolute bottom-0 w-full bg-gradient-to-t from-blue-500 to-blue-400 rounded-t-lg transition-all duration-500" style={{ height: `${(data.ventas / 5500000) * 100}%` }} />
                </div>
                <span className="text-xs text-slate-400 font-medium">{data.mes}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700/50">
          <h3 className="text-lg font-semibold text-white mb-6">Comisiones por Mes</h3>
          <div className="h-48 flex items-end justify-between gap-2">
            {ventasMensuales.map((data, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                <div className="w-full bg-slate-700/30 rounded-t-lg overflow-hidden relative" style={{ height: '160px' }}>
                  <div className="absolute bottom-0 w-full bg-gradient-to-t from-emerald-500 to-emerald-400 rounded-t-lg transition-all duration-500" style={{ height: `${(data.comisiones / 450000) * 100}%` }} />
                </div>
                <span className="text-xs text-slate-400 font-medium">{data.mes}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
    );
  };

  const ClientesView = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-4" />
            <p className="text-slate-400">Cargando clientes...</p>
          </div>
        </div>
      );
    }

    if (error) {
      return (
        <div className="flex items-center justify-center h-96">
          <div className="text-center bg-red-500/10 border border-red-500/20 rounded-lg p-6 max-w-md">
            <p className="text-red-400 mb-2">⚠️ Error</p>
            <p className="text-slate-300 text-sm">{error}</p>
            <button 
              onClick={() => window.location.reload()} 
              className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
            >
              Reintentar
            </button>
          </div>
        </div>
      );
    }

    return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-white mb-1">Clientes</h2>
        <p className="text-sm text-slate-400">Gestiona y analiza a tus clientes comerciales</p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3">
        <div className="flex gap-2">
          <button onClick={() => setFilterStatus('todos')} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filterStatus === 'todos' ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'}`}>
            👥 Todos
          </button>
          <button onClick={() => setFilterStatus('inactivo')} className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${filterStatus === 'inactivo' ? 'bg-blue-500 text-white' : 'bg-slate-800 text-slate-400 hover:text-white border border-slate-700'}`}>
            ⏸️ Inactivos
          </button>
        </div>
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input type="text" placeholder="Buscar cliente" value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-slate-500" />
          </div>
        </div>
      </div>

      <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl border border-slate-700/50 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-900/50 border-b border-slate-700">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Cliente</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Ciudad</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Crédito</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Uso</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Últ. Compra</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-400 uppercase">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700/50">
              {clientesFiltrados.map((cliente) => (
                <tr key={cliente.id} className="hover:bg-slate-700/30 transition-colors">
                  <td className="px-4 py-4">
                    <div>
                      <p className="font-semibold text-white text-sm">{cliente.nombre}</p>
                      <p className="text-xs text-slate-400">{cliente.contacto}</p>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <span className="text-sm text-slate-300">{cliente.ciudad}</span>
                  </td>
                  <td className="px-4 py-4">
                    <p className="text-sm font-semibold text-white">
                      {cliente.credito > 0 ? `$${(cliente.credito / 1000000).toFixed(0)}M` : 'N/A'}
                    </p>
                  </td>
                  <td className="px-4 py-4">
                    {cliente.credito > 0 ? (
                      <div className="flex items-center gap-2">
                        <div className="flex-1 max-w-24 bg-slate-700 rounded-full h-2">
                          <div className={`h-2 rounded-full ${cliente.creditoUsado > 80 ? 'bg-red-500' : cliente.creditoUsado > 60 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${Math.min(cliente.creditoUsado, 100)}%` }} />
                        </div>
                        <span className={`text-xs font-semibold ${cliente.creditoUsado > 80 ? 'text-red-400' : cliente.creditoUsado > 60 ? 'text-amber-400' : 'text-emerald-400'}`}>{cliente.creditoUsado}%</span>
                      </div>
                    ) : (
                      <span className="text-xs text-slate-500">N/A</span>
                    )}
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-slate-300">{cliente.ultimaCompra}</span>
                      <span className={`w-2 h-2 rounded-full ${cliente.estado === 'inactivo' ? 'bg-red-500' : 'bg-emerald-500'}`}></span>
                    </div>
                  </td>
                  <td className="px-4 py-4">
                    <div className="flex items-center gap-2">
                      <button onClick={() => setSelectedClient(cliente)} className="p-1.5 text-blue-400 hover:bg-blue-500/10 rounded transition-colors">
                        <Eye className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 text-slate-400 hover:bg-slate-700 rounded transition-colors">
                        <Mail className="w-4 h-4" />
                      </button>
                      <button className="p-1.5 text-slate-400 hover:bg-slate-700 rounded transition-colors">
                        <Phone className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedClient && (
        <div className="bg-gradient-to-br from-slate-800 to-slate-900 rounded-xl p-6 border border-slate-700/50">
          <div className="flex items-start justify-between mb-6">
            <div>
              <h3 className="text-xl font-bold text-white">{selectedClient.nombre}</h3>
              <p className="text-sm text-slate-400">{selectedClient.contacto}</p>
            </div>
            <button onClick={() => setSelectedClient(null)} className="text-slate-400 hover:text-white">✕</button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="bg-slate-700/30 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Crédito Aprobado</p>
              <p className="text-xl font-bold text-white">
                {selectedClient.credito > 0 ? `$${(selectedClient.credito / 1000000).toFixed(0)}M` : 'N/A'}
              </p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Crédito Disponible</p>
              <p className="text-xl font-bold text-emerald-400">
                {selectedClient.credito > 0 ? `$${((selectedClient.credito * (100 - selectedClient.creditoUsado) / 100) / 1000000).toFixed(1)}M` : 'N/A'}
              </p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Porcentaje Usado</p>
              <p className="text-xl font-bold text-white">
                {selectedClient.credito > 0 ? `${selectedClient.creditoUsado}%` : 'N/A'}
              </p>
            </div>
            <div className="bg-slate-700/30 rounded-lg p-4">
              <p className="text-xs text-slate-400 mb-1">Estado</p>
              <p className={`text-sm font-semibold ${selectedClient.estado === 'activo' ? 'text-emerald-400' : 'text-red-400'}`}>
                {selectedClient.estado === 'activo' ? 'Activo ✓' : 'Inactivo'}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <header className="bg-slate-900/50 border-b border-slate-800 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-white">CRM</h1>
                <p className="text-xs text-slate-400">Sistema de Ventas</p>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                JP
              </div>
            </div>
          </div>
        </div>
      </header>

      <nav className="bg-slate-900/30 border-b border-slate-800 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex gap-1">
            <button onClick={() => setActiveTab('panel')} className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all font-medium text-sm ${activeTab === 'panel' ? 'border-blue-500 text-blue-400 bg-slate-800/50' : 'border-transparent text-slate-400 hover:text-slate-300'}`}>
              <BarChart3 className="w-4 h-4" />
              Panel
            </button>
            <button onClick={() => setActiveTab('clientes')} className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-all font-medium text-sm ${activeTab === 'clientes' ? 'border-blue-500 text-blue-400 bg-slate-800/50' : 'border-transparent text-slate-400 hover:text-slate-300'}`}>
              <Users className="w-4 h-4" />
              Clientes
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">
        {activeTab === 'panel' && <PanelVendedor />}
        {activeTab === 'clientes' && <ClientesView />}
      </main>
    </div>
  );
};

export default CRMCorporativo;
