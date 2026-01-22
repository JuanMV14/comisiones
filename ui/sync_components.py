import streamlit as st
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime
from database.sync_manager import SyncManager
from utils.formatting import format_currency


class SyncUI:
    """Interfaz para sincronización de compras y facturas"""
    
    def __init__(self, sync_manager: SyncManager):
        self.sync_manager = sync_manager
    
    def render_sincronizacion(self):
        """Renderiza la interfaz de sincronización"""
        st.header("🔄 Sincronización de Compras y Facturas")
        st.markdown("---")
        st.info("💡 **Sincroniza las compras de clientes B2B con las facturas/comisiones existentes**")
        
        # Botón para analizar
        if st.button("🔍 Analizar Sincronización", type="primary", use_container_width=True):
            with st.spinner("Analizando datos..."):
                analisis = self.sync_manager.analizar_sincronizacion()
            
            if "error" in analisis:
                st.error(f"❌ {analisis['error']}")
            else:
                st.session_state['analisis_sincronizacion'] = analisis
                st.success("✅ Análisis completado")
        
        # Mostrar resultados del análisis
        if 'analisis_sincronizacion' in st.session_state:
            analisis = st.session_state['analisis_sincronizacion']
            self._mostrar_resultados_analisis(analisis)
    
    def _mostrar_resultados_analisis(self, analisis: Dict[str, Any]):
        """Muestra los resultados del análisis de sincronización"""
        st.markdown("---")
        st.subheader("📊 Resumen del Análisis")
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Compras", analisis['total_compras'])
        with col2:
            st.metric("Total Facturas", analisis['total_facturas'])
        with col3:
            st.metric("Coincidencias Automáticas", analisis['coincidencias_automaticas'], 
                     delta=f"{analisis['coincidencias_automaticas']/analisis['total_compras']*100:.1f}%")
        with col4:
            st.metric("Sin Coincidencia", analisis['sin_coincidencia'])
        
        st.markdown("---")
        
        # Tabs para diferentes tipos de coincidencias
        tab1, tab2, tab3 = st.tabs([
            f"✅ Automáticas ({analisis['coincidencias_automaticas']})",
            f"⚠️ Posibles ({analisis['coincidencias_posibles']})",
            f"❌ Sin Coincidencia ({analisis['sin_coincidencia']})"
        ])
        
        with tab1:
            self._mostrar_coincidencias_automaticas(analisis['detalle_automaticas'])
        
        with tab2:
            self._mostrar_coincidencias_posibles(analisis['detalle_posibles'])
        
        with tab3:
            self._mostrar_sin_coincidencia(analisis['detalle_sin_coincidencia'])
    
    def _mostrar_coincidencias_automaticas(self, coincidencias: List[Dict]):
        """Muestra coincidencias automáticas"""
        if not coincidencias:
            st.info("No hay coincidencias automáticas")
            return
        
        st.success(f"✅ Se encontraron {len(coincidencias)} coincidencias automáticas con alta confianza")
        
        # Botón para sincronizar todas
        st.info("💡 Al sincronizar, se vincularán TODOS los productos de cada compra a su factura correspondiente")
        if st.button("🔄 Sincronizar Todas Automáticamente", type="primary", use_container_width=True):
            with st.spinner("Sincronizando compras con facturas y vinculando productos..."):
                resultado = self.sync_manager.sincronizar_automaticas(coincidencias)
            
            if "error" in resultado:
                st.error(f"❌ {resultado['error']}")
            else:
                facturas_sync = resultado.get('facturas_sincronizadas', resultado.get('sincronizadas', 0))
                productos_vinc = resultado.get('productos_vinculados', 0)
                st.success(f"✅ {facturas_sync} facturas sincronizadas con {productos_vinc} productos vinculados")
                if resultado.get('errores', 0) > 0:
                    st.warning(f"⚠️ {resultado['errores']} errores durante la sincronización")
                st.cache_data.clear()
                # Limpiar análisis para refrescar
                if 'analisis_sincronizacion' in st.session_state:
                    del st.session_state['analisis_sincronizacion']
                st.rerun()
        
        # Botón para sincronizar TODAS las compras sin análisis previo
        st.markdown("---")
        if st.button("🚀 Sincronizar TODAS las Compras Automáticamente", use_container_width=True, help="Busca y sincroniza automáticamente todas las compras que puedan relacionarse con facturas"):
            with st.spinner("Analizando y sincronizando todas las compras..."):
                resultado = self.sync_manager.sincronizar_todas_automaticas()
            
            if "error" in resultado:
                st.error(f"❌ Error: {resultado['error']}")
            else:
                facturas_sync = resultado.get('facturas_sincronizadas', 0)
                productos_vinc = resultado.get('productos_vinculados', 0)
                if facturas_sync > 0:
                    st.success(f"✅ {facturas_sync} facturas sincronizadas con {productos_vinc} productos vinculados")
                else:
                    st.info(resultado.get('mensaje', 'Sincronización completada'))
                st.cache_data.clear()
                # Limpiar análisis para refrescar
                if 'analisis_sincronizacion' in st.session_state:
                    del st.session_state['analisis_sincronizacion']
                st.rerun()
        
        st.markdown("---")
        
        # Mostrar detalles
        for i, coincidencia in enumerate(coincidencias[:10], 1):  # Primeras 10
            compra = coincidencia['compra']
            factura = coincidencia['factura']
            
            with st.container(border=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📦 Compra")
                    st.write(f"**Cliente:** {compra.get('nit_cliente', 'N/A')}")
                    st.write(f"**Documento:** {compra.get('num_documento', 'N/A')}")
                    st.write(f"**Fecha:** {pd.to_datetime(compra.get('fecha')).strftime('%d/%m/%Y')}")
                    st.write(f"**Total:** {format_currency(compra.get('total', 0))}")
                
                with col2:
                    st.markdown("#### 🧾 Factura")
                    st.write(f"**Cliente:** {factura.get('cliente', 'N/A')}")
                    st.write(f"**Factura:** {factura.get('factura', 'N/A')}")
                    st.write(f"**Fecha:** {pd.to_datetime(factura.get('fecha_factura')).strftime('%d/%m/%Y') if factura.get('fecha_factura') else 'N/A'}")
                    st.write(f"**Valor:** {format_currency(factura.get('valor', 0))}")
                
                st.progress(coincidencia['score'], text=f"Confianza: {coincidencia['score']*100:.1f}%")
    
    def _mostrar_coincidencias_posibles(self, coincidencias: List[Dict]):
        """Muestra coincidencias posibles que requieren revisión"""
        if not coincidencias:
            st.info("No hay coincidencias posibles")
            return
        
        st.warning(f"⚠️ Se encontraron {len(coincidencias)} coincidencias posibles que requieren revisión manual")
        
        st.markdown("---")
        
        for i, coincidencia in enumerate(coincidencias[:10], 1):
            compra = coincidencia['compra']
            factura = coincidencia['factura']
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown("#### 📦 Compra")
                    st.write(f"**Cliente:** {compra.get('nit_cliente', 'N/A')}")
                    st.write(f"**Documento:** {compra.get('num_documento', 'N/A')}")
                    st.write(f"**Fecha:** {pd.to_datetime(compra.get('fecha')).strftime('%d/%m/%Y')}")
                    st.write(f"**Total:** {format_currency(compra.get('total', 0))}")
                
                with col2:
                    st.markdown("#### 🧾 Factura Sugerida")
                    st.write(f"**Cliente:** {factura.get('cliente', 'N/A')}")
                    st.write(f"**Factura:** {factura.get('factura', 'N/A')}")
                    st.write(f"**Fecha:** {pd.to_datetime(factura.get('fecha_factura')).strftime('%d/%m/%Y') if factura.get('fecha_factura') else 'N/A'}")
                    st.write(f"**Valor:** {format_currency(factura.get('valor', 0))}")
                
                with col3:
                    st.progress(coincidencia['score'], text=f"{coincidencia['score']*100:.1f}%")
                    if st.button("✅ Vincular", key=f"vincular_{i}"):
                        # Aquí necesitaríamos obtener el ID real de la compra
                        st.info("Funcionalidad de vinculación manual en desarrollo")
    
    def _mostrar_sin_coincidencia(self, sin_coincidencia: List[Dict]):
        """Muestra compras sin coincidencia"""
        if not sin_coincidencia:
            st.info("✅ Todas las compras tienen coincidencia")
            return
        
        st.error(f"❌ {len(sin_coincidencia)} compras sin coincidencia encontrada")
        st.info("💡 Estas compras pueden ser nuevas o no tener factura asociada en el sistema")
        
        st.markdown("---")
        
        for i, item in enumerate(sin_coincidencia[:10], 1):
            compra = item['compra']
            
            with st.container(border=True):
                st.markdown(f"#### Compra #{i}")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Cliente:** {compra.get('nit_cliente', 'N/A')}")
                    st.write(f"**Documento:** {compra.get('num_documento', 'N/A')}")
                    st.write(f"**Fecha:** {pd.to_datetime(compra.get('fecha')).strftime('%d/%m/%Y')}")
                
                with col2:
                    st.write(f"**Total:** {format_currency(compra.get('total', 0))}")
                    st.write(f"**Cantidad Items:** {compra.get('cantidad', 0)}")
                
                if item.get('facturas_candidatas'):
                    with st.expander("Ver facturas candidatas"):
                        for factura in item['facturas_candidatas'][:3]:
                            st.write(f"- {factura.get('cliente')} | Factura: {factura.get('factura')} | Valor: {format_currency(factura.get('valor', 0))}")
