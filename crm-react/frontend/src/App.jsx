import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import Layout from './components/Layout'
import CRMCorporativo from './components/CRMCorporativo'
import DashboardView from './pages/DashboardView'
import ClientesView from './pages/ClientesView'
import NuevaVentaView from './pages/NuevaVentaView'
import CatalogView from './pages/CatalogView'
import MensajesView from './pages/MensajesView'
import ComisionesView from './pages/ComisionesView'
import DashboardEjecutivoView from './pages/DashboardEjecutivoView'
import AnalisisGeograficoView from './pages/AnalisisGeograficoView'
import AnalisisComercialView from './pages/AnalisisComercialView'
import ComisionesGerenciaView from './pages/ComisionesGerenciaView'
import GestionClientesB2BView from './pages/GestionClientesB2BView'
import AnalisisComprasView from './pages/AnalisisComprasView'
import DevolucionesView from './pages/DevolucionesView'
import ImportacionesStockView from './pages/ImportacionesStockView'
import ReportesView from './pages/ReportesView'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <Routes>
          {/* Ruta principal con el nuevo componente CRM */}
          <Route path="/crm" element={<CRMCorporativo />} />
          
          {/* Rutas con Layout (Sidebar) */}
          <Route path="/" element={<Layout />}>
            {/* ZONA 1: ASISTENTE PARA VENDEDORES */}
            <Route index element={<DashboardView />} />
            <Route path="panel-vendedor" element={<DashboardView />} />
            <Route path="clientes" element={<ClientesView />} />
            <Route path="nueva-venta" element={<NuevaVentaView />} />
            <Route path="catalogo" element={<CatalogView />} />
            <Route path="mensajeria" element={<MensajesView />} />
            <Route path="facturas" element={<ComisionesView />} />
            
            {/* ZONA 2: PANEL ESTRATÉGICO PARA GERENCIA */}
            <Route path="dashboard-ejecutivo" element={<DashboardEjecutivoView />} />
            <Route path="analisis-geografico" element={<AnalisisGeograficoView />} />
            <Route path="analisis-comercial" element={<AnalisisComercialView />} />
            <Route path="comisiones" element={<ComisionesGerenciaView />} />
            <Route path="gestion-clientes-b2b" element={<GestionClientesB2BView />} />
            <Route path="analisis-compras" element={<AnalisisComprasView />} />
            <Route path="devoluciones" element={<DevolucionesView />} />
            <Route path="importaciones-stock" element={<ImportacionesStockView />} />
            <Route path="reportes" element={<ReportesView />} />
          </Route>
        </Routes>
      </Router>
    </ErrorBoundary>
  )
}

export default App
