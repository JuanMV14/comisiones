import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any

from database.queries import DatabaseManager
from ui.components import UIComponents
from ui.executive_components import ExecutiveComponents
from ui.notification_components import NotificationUI
from ui.kanban_components import KanbanUI
from ui.ml_components import MLComponentsUI
from ui.guides_components import GuidesComponentsUI
from business.guides_analyzer import GuidesAnalyzer
from business.calculations import ComisionCalculator, MetricsCalculator
from business.ai_recommendations import AIRecommendations
from business.invoice_radication import InvoiceRadicationSystem
from business.executive_dashboard import ExecutiveDashboard
from business.notification_system import NotificationSystem
from business.invoice_alerts import InvoiceAlertsSystem
from business.sales_pipeline import SalesPipeline
from business.ml_analytics import MLAnalytics
from business.client_product_recommendations import ClientProductRecommendations
from ui.client_recommendations_components import ClientRecommendationsUI
from database.catalog_manager import CatalogManager
from ui.catalog_store_components import CatalogStoreUI
from database.client_purchases_manager import ClientPurchasesManager
from ui.client_analytics_components import ClientAnalyticsUI
from business.client_analytics import ClientAnalytics
from utils.formatting import format_currency
from utils.streamlit_helpers import safe_rerun
from utils.discount_parser import DiscountParser

class TabRenderer:
    """Renderizador de todas las pestañas de la aplicación"""
    
    def __init__(self, db_manager: DatabaseManager, ui_components: UIComponents):
        self.db_manager = db_manager
        self.ui_components = ui_components
        self.comision_calc = ComisionCalculator()
        self.metrics_calc = MetricsCalculator()
        self.ai_recommendations = AIRecommendations(db_manager)
        self.invoice_radication = InvoiceRadicationSystem(db_manager)
        self.executive_dashboard = ExecutiveDashboard(db_manager)
        self.notification_system = NotificationSystem(db_manager)
        self.notification_ui = NotificationUI(self.notification_system)
        self.invoice_alerts = InvoiceAlertsSystem(db_manager)
        self.sales_pipeline = SalesPipeline(db_manager)
        self.kanban_ui = KanbanUI(self.sales_pipeline)
        self.ml_analytics = MLAnalytics(db_manager)
        self.ml_ui = MLComponentsUI(self.ml_analytics)
        self.client_recommendations = ClientProductRecommendations(db_manager)
        self.catalog_manager = CatalogManager(db_manager.supabase)
        self.client_recommendations_ui = ClientRecommendationsUI(self.client_recommendations, self.catalog_manager)
        self.catalog_store_ui = CatalogStoreUI(self.catalog_manager)
        
        # Limpiar flags de procesamiento al inicio
        self._clear_processing_flags()
    
    def _clear_processing_flags(self):
        """Limpia los flags de procesamiento para evitar bloqueos"""
        if "_processing_action" in st.session_state:
            st.session_state["_processing_action"] = False
    
    # ========================
    # TAB PANEL DEL VENDEDOR (NUEVO)
    # ========================
    
    def render_panel_vendedor(self):
        """Panel consolidado del día a día para vendedores - Diseño EXACTO como imágenes"""
        # Obtener datos
        df = self.db_manager.cargar_datos()
        
        # Calcular métricas del mes
        mes_actual = pd.Timestamp.now().strftime('%Y-%m')
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
        df['mes_factura'] = df['fecha_factura'].dt.strftime('%Y-%m')
        df_mes = df[(df['mes_factura'] == mes_actual) & (df.get('cliente_propio', False) == True)].copy()
        
        facturacion_mes = df_mes['valor'].sum() if not df_mes.empty else 0
        comisiones_mes = df_mes['comision'].sum() if not df_mes.empty else 0
        
        # Obtener clientes activos
        try:
            from database.client_purchases_manager import ClientPurchasesManager
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select(
                "nit, nombre, activo"
            ).eq("activo", True).execute()
            clientes_activos = len(clientes_b2b_response.data) if clientes_b2b_response.data else 0
        except:
            clientes_activos = 0
        
        # Pedidos del mes
        pedidos_mes = len(df_mes) if not df_mes.empty else 0
        
        # HEADER SUPERIOR - 4 métricas grandes como en el diseño
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-card-large">
                <div class="metric-label-large">Facturación del Mes</div>
                <div class="metric-value-large">{}</div>
            </div>
            """.format(format_currency(facturacion_mes)), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-card-large">
                <div class="metric-label-large">Comisiones Estimadas</div>
                <div class="metric-value-large">{}</div>
            </div>
            """.format(format_currency(comisiones_mes)), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-card-large">
                <div class="metric-label-large">Clientes Activos</div>
                <div class="metric-value-large">{}</div>
            </div>
            """.format(clientes_activos), unsafe_allow_html=True)
        
        with col4:
            st.markdown("""
            <div class="metric-card-large">
                <div class="metric-label-large">Pedidos del Mes</div>
                <div class="metric-value-large">{}</div>
            </div>
            """.format(pedidos_mes), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # MAPA DE COLOMBIA - Centrado y prominente
        with st.container(border=True):
            st.markdown("### Mapa de Clientes - Colombia")
            try:
                from business.client_analytics import ClientAnalytics
                client_analytics = ClientAnalytics(self.db_manager.supabase)
                distribucion = client_analytics.distribucion_geografica(periodo="historico")
                
                if "error" not in distribucion and distribucion.get('datos_mapa'):
                    import plotly.express as px
                    df_mapa = pd.DataFrame(distribucion['datos_mapa'])
                    
                    # Mapa de Colombia con estilo dark
                    fig = px.scatter_mapbox(
                        df_mapa,
                        lat='lat',
                        lon='lon',
                        size='total_compras',
                        color='num_clientes',
                        hover_name='ciudad',
                        hover_data={
                            'num_clientes': True,
                            'total_compras': ':,.0f',
                            'departamento': True,
                        },
                        zoom=5,
                        height=500,
                        color_continuous_scale='Viridis',
                        size_max=50,
                        labels={'num_clientes': 'Clientes', 'total_compras': 'Compras'}
                    )
                    
                    # Estilo dark para el mapa - usar carto-dark o open-street-map con tema oscuro
                    try:
                        fig.update_layout(
                            mapbox_style="carto-darkmatter",
                            paper_bgcolor='#020617',
                            plot_bgcolor='#020617',
                            font=dict(color='#E2E8F0'),
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                    except:
                        # Fallback a open-street-map si carto-darkmatter no está disponible
                        fig.update_layout(
                            mapbox_style="open-street-map",
                            paper_bgcolor='#020617',
                            plot_bgcolor='#020617',
                            font=dict(color='#E2E8F0'),
                            margin=dict(l=0, r=0, t=0, b=0)
                        )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("Cargando datos geográficos...")
            except Exception as e:
                st.warning(f"Error al cargar mapa: {str(e)}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # GRÁFICOS Y TABLAS - Layout de 2 columnas
        col1, col2 = st.columns(2)
        
        with col1:
            with st.container(border=True):
                st.markdown("### Ventas Mensuales")
                # Gráfico de ventas mensuales
                try:
                    df_ventas_mensuales = df.groupby(df['fecha_factura'].dt.to_period('M')).agg({
                        'valor': 'sum'
                    }).reset_index()
                    df_ventas_mensuales['fecha_factura'] = df_ventas_mensuales['fecha_factura'].astype(str)
                    df_ventas_mensuales = df_ventas_mensuales.tail(12)  # Últimos 12 meses
                    
                    import plotly.graph_objects as go
                    fig_ventas = go.Figure()
                    fig_ventas.add_trace(go.Scatter(
                        x=df_ventas_mensuales['fecha_factura'],
                        y=df_ventas_mensuales['valor'],
                        mode='lines+markers',
                        name='Ventas',
                        line=dict(color='#2563EB', width=3),
                        marker=dict(size=8, color='#60A5FA')
                    ))
                    fig_ventas.update_layout(
                        paper_bgcolor='#020617',
                        plot_bgcolor='#020617',
                        font=dict(color='#E2E8F0'),
                        height=300,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                    )
                    st.plotly_chart(fig_ventas, use_container_width=True)
                except Exception as e:
                    st.info("Cargando datos de ventas...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("### Ventas en Curso")
                self._render_ventas_en_curso(df)
        
        with col2:
            with st.container(border=True):
                st.markdown("### Comisiones Mensuales")
                # Gráfico de comisiones mensuales
                try:
                    df_comisiones_mensuales = df.groupby(df['fecha_factura'].dt.to_period('M')).agg({
                        'comision': 'sum'
                    }).reset_index()
                    df_comisiones_mensuales['fecha_factura'] = df_comisiones_mensuales['fecha_factura'].astype(str)
                    df_comisiones_mensuales = df_comisiones_mensuales.tail(12)  # Últimos 12 meses
                    
                    import plotly.graph_objects as go
                    fig_comisiones = go.Figure()
                    fig_comisiones.add_trace(go.Scatter(
                        x=df_comisiones_mensuales['fecha_factura'],
                        y=df_comisiones_mensuales['comision'],
                        mode='lines+markers',
                        name='Comisiones',
                        line=dict(color='#06B6D4', width=3),
                        marker=dict(size=8, color='#67E8F9')
                    ))
                    fig_comisiones.update_layout(
                        paper_bgcolor='#020617',
                        plot_bgcolor='#020617',
                        font=dict(color='#E2E8F0'),
                        height=300,
                        margin=dict(l=0, r=0, t=0, b=0),
                        xaxis=dict(showgrid=False),
                        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
                    )
                    st.plotly_chart(fig_comisiones, use_container_width=True)
                except Exception as e:
                    st.info("Cargando datos de comisiones...")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            with st.container(border=True):
                st.markdown("### Mejores Clientes")
                self._render_mejores_clientes_tabla(df)
    
    def _render_presupuesto_marcas_compacto(self, df: pd.DataFrame):
        """Versión compacta de presupuesto por marca para dashboard"""
        try:
            meta_actual = self.db_manager.obtener_meta_mes_actual()
            presupuesto_total = meta_actual.get('meta_ventas', 0)
            
            mes_actual = pd.Timestamp.now().strftime('%Y-%m')
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            df['mes_factura'] = df['fecha_factura'].dt.strftime('%Y-%m')
            
            df_mes = df[
                (df['mes_factura'] == mes_actual) &
                (df.get('cliente_propio', False) == True)
            ].copy()
            
            if df_mes.empty:
                st.info("No hay ventas este mes")
                return
            
            if 'valor_neto' not in df_mes.columns or df_mes['valor_neto'].isna().all():
                df_mes['valor_neto'] = df_mes['valor'] / 1.19
            
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                facturas_mes = df_mes['factura'].unique().tolist()
                compras_response = clientes_manager.supabase.table("compras_clientes").select(
                    "factura_id, marca, total, es_devolucion"
                ).eq("es_devolucion", False).in_("factura_id", [int(f) for f in facturas_mes if str(f).isdigit()]).execute()
                df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            except:
                df_compras = pd.DataFrame()
            
            ventas_totales = df_mes['valor_neto'].sum()
            
            if not df_compras.empty:
                ventas_marca = df_compras.groupby('marca').agg({'total': 'sum'}).reset_index()
                ventas_marca.columns = ['Marca', 'Total Vendido']
                ventas_marca = ventas_marca.sort_values('Total Vendido', ascending=False)
                ventas_marca['Marca'] = ventas_marca['Marca'].str.upper().str.strip()
                ventas_marca['% del Presupuesto'] = (ventas_marca['Total Vendido'] / presupuesto_total * 100).round(2)
                ventas_marca['% de Ventas'] = (ventas_marca['Total Vendido'] / ventas_totales * 100).round(2)
                
                # Mostrar top 5 marcas
                for idx, row in ventas_marca.head(5).iterrows():
                    st.markdown(f"**{row['Marca']}**")
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.progress(min(row['% del Presupuesto'] / 100, 1.0))
                        st.caption(f"{format_currency(row['Total Vendido'])} - {row['% del Presupuesto']:.1f}% del presupuesto")
                    with col2:
                        st.caption(f"{row['% de Ventas']:.1f}% ventas")
            else:
                st.info("Cargando datos de marcas...")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _render_alertas_dia_vendedor_compacto(self, df: pd.DataFrame):
        """Versión compacta de alertas para dashboard"""
        if df.empty:
            st.info("Sin datos")
            return
        
        hoy = pd.Timestamp.now()
        facturas_pendientes = df[df['pagado'] == False].copy()
        
        if not facturas_pendientes.empty:
            facturas_pendientes['fecha_pago_max'] = pd.to_datetime(facturas_pendientes['fecha_pago_max'])
            facturas_vencidas = facturas_pendientes[facturas_pendientes['fecha_pago_max'] < hoy]
            
            if not facturas_vencidas.empty:
                st.warning(f"⚠️ {len(facturas_vencidas)} facturas vencidas")
            else:
                st.success("✅ Sin facturas vencidas")
            
            dias_restantes = (facturas_pendientes['fecha_pago_max'] - hoy).dt.days
            proximas_vencer = facturas_pendientes[(dias_restantes >= 0) & (dias_restantes <= 5)]
            
            if not proximas_vencer.empty:
                st.info(f"📅 {len(proximas_vencer)} por vencer (5 días)")
        else:
            st.success("✅ Sin facturas pendientes")
    
    def _render_ventas_en_curso(self, df: pd.DataFrame):
        """Tabla de Ventas en Curso con clientes activos"""
        try:
            # Obtener clientes B2B con crédito activo
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select(
                "nit, nombre, cupo_total, cupo_utilizado, ciudad"
            ).eq("activo", True).execute()
            
            if not clientes_b2b_response.data:
                st.info("No hay clientes activos")
                return
            
            df_clientes_b2b = pd.DataFrame(clientes_b2b_response.data)
            
            # Obtener promedio de pago por cliente desde facturas
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'])
            df_pagadas = df[df['pagado'] == True].copy()
            
            if not df_pagadas.empty and 'fecha_pago_real' in df_pagadas.columns and 'fecha_factura' in df_pagadas.columns:
                df_pagadas['dias_pago'] = (df_pagadas['fecha_pago_real'] - df_pagadas['fecha_factura']).dt.days
                promedio_pago = df_pagadas.groupby('cliente')['dias_pago'].mean().reset_index()
                promedio_pago.columns = ['nombre', 'promedio_pago']
            else:
                promedio_pago = pd.DataFrame(columns=['nombre', 'promedio_pago'])
            
            # Combinar datos
            df_final = df_clientes_b2b.copy()
            if not promedio_pago.empty:
                df_final = df_final.merge(promedio_pago, on='nombre', how='left')
                df_final['promedio_pago'] = df_final['promedio_pago'].fillna(0).astype(int)
            else:
                df_final['promedio_pago'] = 0
            
            # Ordenar por cupo total
            df_final = df_final.sort_values('cupo_total', ascending=False).head(10)
            
            # Preparar datos para tabla
            df_display = pd.DataFrame({
                'Nombre': df_final['nombre'].tolist(),
                'Promedio Pago': [f"{int(p)} días" for p in df_final['promedio_pago']],
                'Crédito Activo': [format_currency(c) for c in df_final['cupo_total']]
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            
            st.caption(f"{len(df_final)} ventas activas")
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _render_mejores_clientes_tabla(self, df: pd.DataFrame):
        """Tabla de Mejores Clientes con ciudad y última actividad"""
        try:
            # Filtrar solo clientes propios
            if 'cliente_propio' in df.columns:
                df_propios = df[df['cliente_propio'] == True].copy()
                if not df_propios.empty:
                    clientes_validacion = df.groupby('cliente').agg({
                        'cliente_propio': lambda x: (x == True).sum(),
                        'cliente': 'count'
                    })
                    clientes_validacion.columns = ['facturas_propias', 'total_facturas']
                    clientes_validacion['pct_propio'] = (clientes_validacion['facturas_propias'] / clientes_validacion['total_facturas'] * 100).fillna(0)
                    clientes_validos = clientes_validacion[clientes_validacion['pct_propio'] >= 80].index.tolist()
                    df_propios = df_propios[df_propios['cliente'].isin(clientes_validos)].copy()
                df = df_propios
            
            if df.empty:
                st.info("No hay clientes propios")
                return
            
            # Calcular total por cliente
            clientes_stats = df.groupby('cliente').agg({
                'valor_neto': 'sum' if 'valor_neto' in df.columns else lambda x: df.loc[x.index, 'valor'].sum() / 1.19,
                'fecha_factura': 'max'
            }).reset_index()
            clientes_stats.columns = ['cliente', 'total', 'ultima_factura']
            clientes_stats = clientes_stats.sort_values('total', ascending=False).head(10)
            
            # Obtener ciudades desde clientes B2B
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("nit, nombre, ciudad").execute()
                df_clientes_b2b = pd.DataFrame(clientes_b2b_response.data) if clientes_b2b_response.data else pd.DataFrame()
                
                if not df_clientes_b2b.empty:
                    clientes_stats = clientes_stats.merge(df_clientes_b2b, left_on='cliente', right_on='nombre', how='left')
                    clientes_stats['ciudad'] = clientes_stats['ciudad'].fillna('N/A')
                else:
                    clientes_stats['ciudad'] = 'N/A'
            except:
                clientes_stats['ciudad'] = 'N/A'
            
            # Calcular días desde última actividad
            hoy = pd.Timestamp.now()
            clientes_stats['ultima_factura'] = pd.to_datetime(clientes_stats['ultima_factura'])
            clientes_stats['dias_ultima'] = (hoy - clientes_stats['ultima_factura']).dt.days
            
            # Preparar datos para tabla
            df_display = pd.DataFrame({
                'Nombre': clientes_stats['cliente'].tolist(),
                'Ciudad': clientes_stats['ciudad'].tolist(),
                'Última Actividad': [f"{int(d)} días" for d in clientes_stats['dias_ultima']]
            })
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def _render_productos_nuevos_importacion_compacto(self):
        """Versión compacta de productos nuevos"""
        try:
            df_catalogo = self.catalog_manager.cargar_catalogo()
            if df_catalogo.empty:
                st.info("Sin productos nuevos")
                return
            
            if 'fecha_actualizacion' in df_catalogo.columns:
                df_catalogo['fecha_actualizacion'] = pd.to_datetime(df_catalogo['fecha_actualizacion'])
                fecha_reciente = pd.Timestamp.now() - pd.Timedelta(days=30)
                productos_nuevos = df_catalogo[df_catalogo['fecha_actualizacion'] >= fecha_reciente].head(5)
            else:
                productos_nuevos = df_catalogo.head(5)
            
            if productos_nuevos.empty:
                st.info("Sin productos nuevos este mes")
            else:
                for idx, producto in productos_nuevos.iterrows():
                    nombre = producto.get('descripcion', producto.get('referencia', 'N/A'))
                    st.markdown(f"• {nombre[:40]}")
        except:
            st.info("Cargando productos...")
    
    def _render_presupuesto_marcas(self, df: pd.DataFrame):
        """Renderiza presupuesto general y desglose por marca"""
        try:
            # Obtener meta actual
            meta_actual = self.db_manager.obtener_meta_mes_actual()
            presupuesto_total = meta_actual.get('meta_ventas', 0)
            
            # Filtrar solo clientes propios del mes actual
            mes_actual = pd.Timestamp.now().strftime('%Y-%m')
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            df['mes_factura'] = df['fecha_factura'].dt.strftime('%Y-%m')
            
            df_mes = df[
                (df['mes_factura'] == mes_actual) &
                (df.get('cliente_propio', False) == True)
            ].copy()
            
            if df_mes.empty:
                st.info("No hay ventas de clientes propios este mes")
                return
            
            # Calcular valor neto si no existe
            if 'valor_neto' not in df_mes.columns or df_mes['valor_neto'].isna().all():
                df_mes['valor_neto'] = df_mes['valor'] / 1.19
            
            # Obtener compras para identificar marcas
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                facturas_mes = df_mes['factura'].unique().tolist()
                
                # Obtener compras relacionadas con estas facturas
                compras_response = clientes_manager.supabase.table("compras_clientes").select(
                    "factura_id, marca, total, es_devolucion"
                ).eq("es_devolucion", False).in_("factura_id", [int(f) for f in facturas_mes if str(f).isdigit()]).execute()
                
                df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            except:
                df_compras = pd.DataFrame()
            
            # Calcular presupuesto general
            ventas_totales = df_mes['valor_neto'].sum()
            porcentaje_presupuesto = (ventas_totales / presupuesto_total * 100) if presupuesto_total > 0 else 0
            
            # Mostrar presupuesto general
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Presupuesto Total", format_currency(presupuesto_total))
            with col2:
                st.metric("Ventas Actuales", format_currency(ventas_totales), delta=f"{porcentaje_presupuesto:.1f}% del presupuesto")
            with col3:
                faltante = max(0, presupuesto_total - ventas_totales)
                st.metric("Faltante", format_currency(faltante))
            
            st.markdown("---")
            
            # Presupuesto por marca
            if not df_compras.empty:
                # Agrupar por marca
                ventas_marca = df_compras.groupby('marca').agg({
                    'total': 'sum'
                }).reset_index()
                ventas_marca.columns = ['Marca', 'Total Vendido']
                ventas_marca = ventas_marca.sort_values('Total Vendido', ascending=False)
                
                # Normalizar nombres de marcas (CTR, EFFIX, etc.)
                ventas_marca['Marca'] = ventas_marca['Marca'].str.upper().str.strip()
                
                # Calcular porcentajes
                ventas_marca['% del Presupuesto Total'] = (ventas_marca['Total Vendido'] / presupuesto_total * 100).round(2)
                ventas_marca['% de Ventas del Mes'] = (ventas_marca['Total Vendido'] / ventas_totales * 100).round(2)
                
                st.markdown("### 📊 Ventas por Marca")
                
                # Mostrar tarjetas por marca
                cols = st.columns(min(len(ventas_marca), 4))
                for idx, row in ventas_marca.iterrows():
                    with cols[idx % len(cols)]:
                        with st.container(border=True):
                            st.markdown(f"**{row['Marca']}**")
                            st.metric("Total", format_currency(row['Total Vendido']))
                            st.caption(f"📊 {row['% del Presupuesto Total']:.1f}% del presupuesto total")
                            st.caption(f"📈 {row['% de Ventas del Mes']:.1f}% de las ventas del mes")
                
                # Tabla detallada
                st.markdown("---")
                st.markdown("### Detalle por Marca")
                ventas_display = ventas_marca.copy()
                ventas_display['Total Vendido'] = ventas_display['Total Vendido'].apply(format_currency)
                ventas_display['% del Presupuesto Total'] = ventas_display['% del Presupuesto Total'].apply(lambda x: f"{x:.2f}%")
                ventas_display['% de Ventas del Mes'] = ventas_display['% de Ventas del Mes'].apply(lambda x: f"{x:.2f}%")
                st.dataframe(
                    ventas_display.rename(columns={
                        'Marca': 'Marca',
                        'Total Vendido': 'Total Vendido',
                        '% del Presupuesto Total': '% del Presupuesto',
                        '% de Ventas del Mes': '% de Ventas del Mes'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                # Si no hay datos de compras, mostrar solo resumen general
                st.info("💡 No hay datos de compras detalladas para mostrar desglose por marca. Las ventas se muestran de forma consolidada.")
                
                # Intentar obtener marcas desde catálogo o facturas directas si hay algún campo de marca
                if 'marca' in df_mes.columns and df_mes['marca'].notna().any():
                    ventas_marca = df_mes.groupby('marca').agg({
                        'valor_neto': 'sum'
                    }).reset_index()
                    ventas_marca.columns = ['Marca', 'Total Vendido']
                    ventas_marca = ventas_marca.sort_values('Total Vendido', ascending=False)
                    
                    ventas_marca['% del Presupuesto Total'] = (ventas_marca['Total Vendido'] / presupuesto_total * 100).round(2)
                    ventas_marca['% de Ventas del Mes'] = (ventas_marca['Total Vendido'] / ventas_totales * 100).round(2)
                    
                    st.markdown("### 📊 Ventas por Marca (aproximado)")
                    ventas_display = ventas_marca.copy()
                    ventas_display['Total Vendido'] = ventas_display['Total Vendido'].apply(format_currency)
                    ventas_display['% del Presupuesto Total'] = ventas_display['% del Presupuesto Total'].apply(lambda x: f"{x:.2f}%")
                    ventas_display['% de Ventas del Mes'] = ventas_display['% de Ventas del Mes'].apply(lambda x: f"{x:.2f}%")
                    st.dataframe(ventas_display, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error calculando presupuesto: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    def _render_alertas_dia_vendedor(self, df: pd.DataFrame):
        """Renderiza alertas del día para vendedores"""
        if df.empty:
            st.info("No hay datos disponibles")
            return
        
        hoy = pd.Timestamp.now()
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Facturas vencidas
            facturas_pendientes = df[df['pagado'] == False].copy()
            if not facturas_pendientes.empty:
                facturas_pendientes['fecha_pago_max'] = pd.to_datetime(facturas_pendientes['fecha_pago_max'])
                facturas_vencidas = facturas_pendientes[facturas_pendientes['fecha_pago_max'] < hoy]
                num_vencidas = len(facturas_vencidas)
                valor_vencido = facturas_vencidas['valor'].sum() if not facturas_vencidas.empty else 0
                
                st.metric(
                    "Facturas Vencidas",
                    num_vencidas,
                    delta=f"{format_currency(valor_vencido)}",
                    delta_color="inverse"
                )
            else:
                st.metric("Facturas Vencidas", 0)
        
        with col2:
            # Próximas a vencer (5 días)
            if not facturas_pendientes.empty:
                facturas_pendientes['fecha_pago_max'] = pd.to_datetime(facturas_pendientes['fecha_pago_max'])
                dias_restantes = (facturas_pendientes['fecha_pago_max'] - hoy).dt.days
                proximas_vencer = facturas_pendientes[(dias_restantes >= 0) & (dias_restantes <= 5)]
                num_proximas = len(proximas_vencer)
                
                st.metric(
                    "Próximas a Vencer (5 días)",
                    num_proximas,
                    delta_color="normal"
                )
            else:
                st.metric("Próximas a Vencer (5 días)", 0)
        
        with col3:
            # Clientes inactivos (>60 días sin comprar)
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            ultima_compra_por_cliente = df.groupby('cliente')['fecha_factura'].max()
            dias_sin_comprar = (hoy - ultima_compra_por_cliente).dt.days
            clientes_inactivos = ultima_compra_por_cliente[dias_sin_comprar > 60]
            
            st.metric(
                "Clientes Inactivos (>60 días)",
                len(clientes_inactivos),
                help="Clientes que no han comprado en más de 60 días"
            )
        
        # Mostrar detalles de alertas críticas
        if not facturas_pendientes.empty:
            facturas_pendientes['fecha_pago_max'] = pd.to_datetime(facturas_pendientes['fecha_pago_max'])
            facturas_vencidas = facturas_pendientes[facturas_pendientes['fecha_pago_max'] < hoy]
            
            if not facturas_vencidas.empty:
                with st.expander(f"Ver {len(facturas_vencidas)} Facturas Vencidas", expanded=False):
                    for idx, factura in facturas_vencidas.head(10).iterrows():
                        dias_vencido = (hoy - factura['fecha_pago_max']).days
                        col1, col2, col3 = st.columns([3, 2, 1])
                        with col1:
                            st.write(f"**{factura.get('cliente', 'N/A')}** - {factura.get('factura', 'N/A')}")
                        with col2:
                            st.write(f"{format_currency(factura.get('valor', 0))} - Vencido hace {dias_vencido} días")
                        with col3:
                            if st.button("Enviar Recordatorio", key=f"reminder_{factura.get('id')}", use_container_width=True):
                                st.info("Funcionalidad de mensajería en desarrollo")
    
    def _render_mejores_clientes_vendedor(self, df: pd.DataFrame):
        """Renderiza los mejores clientes para vendedores (SOLO CLIENTES PROPIOS)"""
        if df.empty:
            st.info("No hay datos de clientes")
            return
        
        # FILTRAR SOLO CLIENTES PROPIOS - Validación más estricta
        if 'cliente_propio' in df.columns:
            # Primero filtrar solo facturas donde cliente_propio == True
            df_propios = df[df['cliente_propio'] == True].copy()
            
            # Validación adicional: verificar que el cliente tenga mayoría de facturas como propio
            if not df_propios.empty:
                # Agrupar por cliente y contar facturas propias vs totales
                clientes_validacion = df.groupby('cliente').agg({
                    'cliente_propio': lambda x: (x == True).sum(),  # Cuántas facturas como propio
                    'cliente': 'count'  # Total de facturas
                })
                clientes_validacion.columns = ['facturas_propias', 'total_facturas']
                clientes_validacion['pct_propio'] = (clientes_validacion['facturas_propias'] / clientes_validacion['total_facturas'] * 100).fillna(0)
                
                # Solo incluir clientes donde al menos el 80% de sus facturas son como cliente propio
                clientes_validos = clientes_validacion[clientes_validacion['pct_propio'] >= 80].index.tolist()
                
                # Filtrar df_propios para solo incluir clientes válidos
                df_propios = df_propios[df_propios['cliente'].isin(clientes_validos)].copy()
            
            df = df_propios
        
        if df.empty:
            st.info("No hay clientes propios registrados")
            return
        
        # Calcular métricas por cliente
        clientes_stats = df.groupby('cliente').agg({
            'valor_neto': ['sum', 'mean', 'count'],
            'comision': 'sum',
            'fecha_factura': 'max'
        }).round(0)
        
        clientes_stats.columns = ['Total Compras', 'Ticket Promedio', 'Num Compras', 'Total Comisiones', 'Ultima Compra']
        clientes_stats = clientes_stats.sort_values('Total Compras', ascending=False).head(10)
        
        # Calcular días desde última compra
        hoy = pd.Timestamp.now()
        clientes_stats['Ultima Compra'] = pd.to_datetime(clientes_stats['Ultima Compra'])
        clientes_stats['Dias Sin Comprar'] = (hoy - clientes_stats['Ultima Compra']).dt.days
        
        # Mostrar en cards
        cols = st.columns(5)
        for idx, (cliente, row) in enumerate(clientes_stats.iterrows()):
            col_idx = idx % 5
            with cols[col_idx]:
                with st.container(border=True):
                    st.markdown(f"**{cliente[:25]}...**" if len(cliente) > 25 else f"**{cliente}**")
                    st.metric("Total", format_currency(row['Total Compras']))
                    st.caption(f"{int(row['Num Compras'])} compras")
                    st.caption(f"Última: {int(row['Dias Sin Comprar'])} días")
    
    def _render_buscador_cliente_rapido(self):
        """Buscador rápido de clientes con vista consolidada"""
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Buscador
            termino_busqueda = st.text_input(
                "Buscar por NIT o Nombre",
                placeholder="Ej: 901234567 o DISTRIBUIDORA",
                key="buscador_cliente_rapido"
            )
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("Buscar", type="primary", use_container_width=True):
                if termino_busqueda:
                    st.session_state['cliente_buscado'] = termino_busqueda
                    st.rerun()
        
        # Mostrar resultado de búsqueda
        if 'cliente_buscado' in st.session_state and st.session_state['cliente_buscado']:
            termino = st.session_state['cliente_buscado']
            self._render_vista_cliente_consolidada(termino)
            
            if st.button("Limpiar Búsqueda", key="limpiar_busqueda"):
                del st.session_state['cliente_buscado']
                st.rerun()
    
    def _render_vista_cliente_consolidada(self, termino_busqueda: str):
        """Vista consolidada de un cliente específico"""
        # Buscar cliente en comisiones
        df = self.db_manager.cargar_datos()
        
        # Buscar por nombre o factura
        cliente_encontrado = None
        if not df.empty:
            # Buscar por nombre (búsqueda parcial)
            clientes_match = df[df['cliente'].str.contains(termino_busqueda, case=False, na=False)]
            if not clientes_match.empty:
                cliente_encontrado = clientes_match['cliente'].iloc[0]
        
        # Si no se encuentra en comisiones, buscar en clientes B2B
        if not cliente_encontrado:
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                # Buscar por NIT
                cliente_b2b = clientes_manager.obtener_cliente(termino_busqueda)
                if cliente_b2b:
                    cliente_encontrado = cliente_b2b.get('nombre')
            except:
                pass
        
        if not cliente_encontrado:
            st.warning(f"No se encontró cliente con: {termino_busqueda}")
            return
        
        # Obtener datos del cliente
        df_cliente = df[df['cliente'] == cliente_encontrado] if not df.empty else pd.DataFrame()
        
        # Obtener cliente B2B si existe
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            cliente_b2b = None
            # Buscar NIT en compras o facturas
            if not df_cliente.empty:
                # Intentar buscar por nombre
                todos_clientes = clientes_manager.supabase.table("clientes_b2b").select("*").execute()
                if todos_clientes.data:
                    for c in todos_clientes.data:
                        if c['nombre'].upper() == cliente_encontrado.upper():
                            cliente_b2b = c
                            break
        except:
            cliente_b2b = None
        
        # Mostrar vista consolidada
        st.markdown(f"### Cliente: {cliente_encontrado}")
        
        # Pestañas internas
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Resumen General",
            "Historial de Compras",
            "Productos Frecuentes",
            "Recomendaciones",
            "Facturas y Pagos"
        ])
        
        with tab1:
            self._render_resumen_cliente(cliente_encontrado, df_cliente, cliente_b2b)
        
        with tab2:
            self._render_historial_compras_cliente(df_cliente)
        
        with tab3:
            self._render_productos_frecuentes_cliente(cliente_encontrado)
        
        with tab4:
            self._render_recomendaciones_cliente(cliente_encontrado)
        
        with tab5:
            self._render_facturas_pagos_cliente(cliente_encontrado, df_cliente)
    
    def _render_resumen_cliente(self, cliente: str, df_cliente: pd.DataFrame, cliente_b2b: Dict = None):
        """Resumen ejecutivo del cliente"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Información Básica")
            if cliente_b2b:
                st.write(f"**NIT:** {cliente_b2b.get('nit', 'N/A')}")
                st.write(f"**Ciudad:** {cliente_b2b.get('ciudad', 'N/A')}")
                st.write(f"**Vendedor:** {cliente_b2b.get('vendedor', 'N/A')}")
            else:
                st.info("Cliente no registrado en sistema B2B")
        
        with col2:
            st.markdown("#### Crédito")
            if cliente_b2b:
                cupo_total = cliente_b2b.get('cupo_total', 0)
                
                # CALCULAR CUPO UTILIZADO DINÁMICAMENTE: Sumar facturas pendientes
                cupo_utilizado_calculado = 0
                if not df_cliente.empty:
                    facturas_pendientes = df_cliente[df_cliente['pagado'] == False]
                    if not facturas_pendientes.empty:
                        # Usar valor_neto si está disponible, sino calcular desde valor
                        if 'valor_neto' in facturas_pendientes.columns:
                            cupo_utilizado_calculado = facturas_pendientes['valor_neto'].sum()
                        else:
                            # Si solo hay valor, calcular valor_neto
                            cupo_utilizado_calculado = facturas_pendientes['valor'].sum() / 1.19
                
                # Usar el valor calculado dinámicamente
                cupo_utilizado = cupo_utilizado_calculado
                cupo_disponible = cupo_total - cupo_utilizado
                porcentaje_uso = (cupo_utilizado / cupo_total * 100) if cupo_total > 0 else 0
                
                st.metric("Cupo Total", format_currency(cupo_total))
                st.metric("Cupo Utilizado", format_currency(cupo_utilizado), f"{porcentaje_uso:.1f}%")
                st.metric("Cupo Disponible", format_currency(cupo_disponible))
                
                # Mostrar info si hay facturas pendientes
                if not df_cliente.empty:
                    facturas_pendientes = df_cliente[df_cliente['pagado'] == False]
                    if not facturas_pendientes.empty:
                        st.caption(f"📋 {len(facturas_pendientes)} factura(s) pendiente(s) afectando el cupo")
            else:
                st.info("Sin información de crédito")
        
        with col3:
            st.markdown("#### Comportamiento de Pago")
            if not df_cliente.empty:
                facturas_pagadas = df_cliente[df_cliente['pagado'] == True]
                if not facturas_pagadas.empty and 'dias_pago_real' in facturas_pagadas.columns:
                    promedio_dias = facturas_pagadas['dias_pago_real'].mean()
                    puntualidad = "Excelente" if promedio_dias <= 30 else "Buena" if promedio_dias <= 45 else "Regular"
                    st.metric("Promedio de Días", f"{promedio_dias:.0f} días")
                    st.metric("Puntualidad", puntualidad)
                else:
                    st.info("Sin pagos registrados")
            else:
                st.info("Sin datos")
        
        # Métricas generales
        st.markdown("---")
        col1, col2, col3, col4 = st.columns(4)
        
        if not df_cliente.empty:
            with col1:
                st.metric("Total Facturado", format_currency(df_cliente['valor'].sum()))
            with col2:
                st.metric("Ticket Promedio", format_currency(df_cliente['valor'].mean()))
            with col3:
                st.metric("Num. Facturas", len(df_cliente))
            with col4:
                ultima_compra = pd.to_datetime(df_cliente['fecha_factura']).max()
                dias_desde = (pd.Timestamp.now() - ultima_compra).days
                st.metric("Última Compra", f"{dias_desde} días")
        
        # Botones de acción rápida
        st.markdown("---")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Nueva Venta", type="primary", use_container_width=True):
                st.session_state['cliente_para_venta'] = cliente
                st.info("Ve a la pestaña 'Nueva Venta Simple' para crear la venta")
        with col2:
            if st.button("Enviar WhatsApp", use_container_width=True):
                st.info("Funcionalidad de WhatsApp en desarrollo")
        with col3:
            if st.button("Enviar Email", use_container_width=True):
                st.info("Funcionalidad de Email en desarrollo")
    
    def _render_historial_compras_cliente(self, df_cliente: pd.DataFrame):
        """Muestra historial de compras del cliente"""
        if df_cliente.empty:
            st.info("No hay historial de compras")
            return
        
        # Agrupar por factura
        facturas = df_cliente.groupby(['factura', 'fecha_factura', 'pagado', 'valor']).agg({
            'pedido': 'first',
            'comision': 'sum'
        }).reset_index()
        
        facturas = facturas.sort_values('fecha_factura', ascending=False)
        
        # Mostrar tabla
        st.dataframe(
            facturas[['factura', 'fecha_factura', 'valor', 'comision', 'pagado']],
            use_container_width=True,
            hide_index=True
        )
    
    def _render_productos_frecuentes_cliente(self, cliente: str):
        """Muestra productos frecuentes del cliente con navegación jerárquica en tarjetas"""
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            # Obtener NIT del cliente (búsqueda aproximada)
            todos_clientes = clientes_manager.supabase.table("clientes_b2b").select("*").execute()
            nit_cliente = None
            
            if todos_clientes.data:
                for c in todos_clientes.data:
                    if c['nombre'].upper() == cliente.upper():
                        nit_cliente = c['nit']
                        break
            
            if not nit_cliente:
                st.info("Cliente no encontrado en sistema B2B. No se pueden mostrar productos frecuentes.")
                return
            
            # Obtener compras del cliente directamente
            df_compras = clientes_manager.obtener_compras_cliente(nit_cliente, incluir_devoluciones=False)
            
            if df_compras.empty:
                st.info("No hay compras registradas para este cliente")
                return
            
            # Filtrar solo compras (FE)
            if 'fuente' in df_compras.columns:
                df_compras = df_compras[df_compras['fuente'].astype(str).str.upper() == 'FE'].copy()
            elif 'es_devolucion' in df_compras.columns:
                df_compras = df_compras[(df_compras['es_devolucion'] == False) | (df_compras['es_devolucion'].isna())].copy()
            
            if df_compras.empty:
                st.info("No hay compras para este cliente")
                return
            
            # Implementar navegación jerárquica
            nivel = st.session_state.get(f'productos_nivel_{cliente}', 'marcas')
            marca_seleccionada = st.session_state.get(f'productos_marca_{cliente}', None)
            grupo_seleccionado = st.session_state.get(f'productos_grupo_{cliente}', None)
            subgrupo_seleccionado = st.session_state.get(f'productos_subgrupo_{cliente}', None)
            
            # Botón para volver atrás
            if nivel != 'marcas':
                if st.button("← Volver", key=f"volver_productos_{cliente}"):
                    if nivel == 'grupos':
                        st.session_state[f'productos_nivel_{cliente}'] = 'marcas'
                        st.session_state[f'productos_marca_{cliente}'] = None
                    elif nivel == 'subgrupos':
                        st.session_state[f'productos_nivel_{cliente}'] = 'grupos'
                        st.session_state[f'productos_grupo_{cliente}'] = None
                    elif nivel == 'referencias':
                        st.session_state[f'productos_nivel_{cliente}'] = 'subgrupos'
                        st.session_state[f'productos_subgrupo_{cliente}'] = None
                    st.rerun()
            
            # Nivel 1: MARCAS
            if nivel == 'marcas':
                st.markdown("### Selecciona una Marca")
                self._render_tarjetas_marcas(df_compras, cliente)
            
            # Nivel 2: GRUPOS de la marca seleccionada
            elif nivel == 'grupos' and marca_seleccionada:
                st.markdown(f"### Grupos de la Marca: {marca_seleccionada}")
                df_marca = df_compras[df_compras['marca'].str.upper() == marca_seleccionada.upper()]
                self._render_tarjetas_grupos(df_marca, cliente, marca_seleccionada)
            
            # Nivel 3: SUBGRUPOS del grupo seleccionado
            elif nivel == 'subgrupos' and marca_seleccionada and grupo_seleccionado:
                st.markdown(f"### Subgrupos de {marca_seleccionada} > {grupo_seleccionado}")
                df_grupo = df_compras[
                    (df_compras['marca'].str.upper() == marca_seleccionada.upper()) &
                    (df_compras['grupo'].str.upper() == grupo_seleccionado.upper())
                ]
                self._render_tarjetas_subgrupos(df_grupo, cliente, marca_seleccionada, grupo_seleccionado)
            
            # Nivel 4: REFERENCIAS del subgrupo seleccionado
            elif nivel == 'referencias' and marca_seleccionada and grupo_seleccionado and subgrupo_seleccionado:
                st.markdown(f"### Referencias de {marca_seleccionada} > {grupo_seleccionado} > {subgrupo_seleccionado}")
                df_subgrupo = df_compras[
                    (df_compras['marca'].str.upper() == marca_seleccionada.upper()) &
                    (df_compras['grupo'].str.upper() == grupo_seleccionado.upper()) &
                    (df_compras['subgrupo'].str.upper() == subgrupo_seleccionado.upper())
                ]
                self._render_tarjetas_referencias(df_subgrupo)
        
        except Exception as e:
            st.error(f"Error obteniendo productos: {str(e)}")
    
    def _render_recomendaciones_cliente(self, cliente: str):
        """Muestra recomendaciones de productos para el cliente"""
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            
            # Buscar NIT
            todos_clientes = clientes_manager.supabase.table("clientes_b2b").select("*").execute()
            nit_cliente = None
            
            if todos_clientes.data:
                for c in todos_clientes.data:
                    if c['nombre'].upper() == cliente.upper():
                        nit_cliente = c['nit']
                        break
            
            if not nit_cliente:
                st.info("Cliente no encontrado. Las recomendaciones requieren que el cliente esté registrado en B2B.")
                return
            
            # Generar recomendaciones
            recomendaciones = clientes_manager.generar_recomendaciones(nit_cliente, self.catalog_manager)
            
            if "error" in recomendaciones:
                st.warning(recomendaciones['error'])
                return
            
            # Mostrar recomendaciones
            if recomendaciones.get('por_marca'):
                st.markdown("#### Recomendaciones por Marca Preferida")
                df_marca = pd.DataFrame(recomendaciones['por_marca'])
                st.dataframe(df_marca, use_container_width=True, hide_index=True)
            
            if recomendaciones.get('por_categoria'):
                st.markdown("---")
                st.markdown("#### Recomendaciones por Categoría")
                df_cat = pd.DataFrame(recomendaciones['por_categoria'])
                st.dataframe(df_cat, use_container_width=True, hide_index=True)
            
            if recomendaciones.get('complementarios'):
                st.markdown("---")
                st.markdown("#### Productos Complementarios")
                df_comp = pd.DataFrame(recomendaciones['complementarios'])
                st.dataframe(df_comp, use_container_width=True, hide_index=True)
            
            if not recomendaciones.get('por_marca') and not recomendaciones.get('por_categoria'):
                st.info("Generando recomendaciones... Esto puede tomar unos segundos.")
        
        except Exception as e:
            st.error(f"Error generando recomendaciones: {str(e)}")
    
    def _render_facturas_pagos_cliente(self, cliente: str, df_cliente: pd.DataFrame):
        """Muestra facturas pendientes y próximas a vencer del cliente"""
        if df_cliente.empty:
            st.info("No hay facturas para este cliente")
            return
        
        # Separar facturas
        hoy = pd.Timestamp.now()
        facturas_pendientes = df_cliente[df_cliente['pagado'] == False].copy()
        
        if not facturas_pendientes.empty:
            facturas_pendientes['fecha_pago_max'] = pd.to_datetime(facturas_pendientes['fecha_pago_max'])
            facturas_pendientes['dias_vencimiento'] = (facturas_pendientes['fecha_pago_max'] - hoy).dt.days
            
            # Vencidas
            vencidas = facturas_pendientes[facturas_pendientes['dias_vencimiento'] < 0]
            # Próximas a vencer
            proximas = facturas_pendientes[
                (facturas_pendientes['dias_vencimiento'] >= 0) & 
                (facturas_pendientes['dias_vencimiento'] <= 7)
            ]
            
            tab1, tab2 = st.tabs(["Vencidas", "Próximas a Vencer"])
            
            with tab1:
                if not vencidas.empty:
                    for _, factura in vencidas.iterrows():
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                            with col1:
                                st.write(f"**{factura.get('factura', 'N/A')}**")
                            with col2:
                                st.write(f"Valor: {format_currency(factura.get('valor', 0))}")
                            with col3:
                                dias_vencido = abs(factura['dias_vencimiento'])
                                st.write(f"Vencida hace {int(dias_vencido)} días")
                            with col4:
                                if st.button("Recordatorio", key=f"rem_{factura.get('id')}", use_container_width=True):
                                    st.info("Funcionalidad en desarrollo")
                else:
                    st.success("No hay facturas vencidas")
            
            with tab2:
                if not proximas.empty:
                    for _, factura in proximas.iterrows():
                        with st.container(border=True):
                            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
                            with col1:
                                st.write(f"**{factura.get('factura', 'N/A')}**")
                            with col2:
                                st.write(f"Valor: {format_currency(factura.get('valor', 0))}")
                            with col3:
                                st.write(f"Vence en {int(factura['dias_vencimiento'])} días")
                            with col4:
                                if st.button("Recordatorio", key=f"rem_prox_{factura.get('id')}", use_container_width=True):
                                    st.info("Funcionalidad en desarrollo")
                else:
                    st.info("No hay facturas próximas a vencer")
        else:
            st.success("Cliente al día con todos sus pagos")
    
    def _render_productos_nuevos_importacion(self):
        """Muestra productos nuevos detectados en importaciones"""
        st.info("Funcionalidad de detección de productos nuevos en desarrollo")
        st.write("Aquí se mostrarán los productos nuevos detectados cuando cargues un archivo de importación en la pestaña de Catálogo.")
    
    # ========================
    # FUNCIONES AUXILIARES PARA NAVEGACIÓN JERÁRQUICA DE PRODUCTOS
    # ========================
    
    def _render_tarjetas_marcas(self, df_compras: pd.DataFrame, cliente_key: str):
        """Renderiza tarjetas de marcas para navegación jerárquica"""
        if df_compras.empty:
            st.info("No hay datos de marcas")
            return
        
        # Agrupar por marca
        marcas_stats = df_compras.groupby('marca').agg({
            'total': 'sum',
            'cantidad': 'sum',
            'cod_articulo': 'nunique'
        }).reset_index()
        marcas_stats.columns = ['marca', 'total', 'cantidad', 'productos_diferentes']
        marcas_stats = marcas_stats.sort_values('total', ascending=False)
        
        # Mostrar en tarjetas (3 columnas)
        cols = st.columns(3)
        for idx, (_, row) in enumerate(marcas_stats.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                with st.container(border=True):
                    marca = row['marca'] if pd.notna(row['marca']) else 'Sin Marca'
                    st.markdown(f"### {marca[:30]}...**" if len(marca) > 30 else f"### {marca}**")
                    st.metric("Total", format_currency(row['total']))
                    st.caption(f"Cantidad: {int(row['cantidad'])} unidades")
                    st.caption(f"Productos: {int(row['productos_diferentes'])} diferentes")
                    
                    # Botón para ver grupos de esta marca
                    if st.button("Ver Grupos →", key=f"marca_{cliente_key}_{idx}", use_container_width=True):
                        st.session_state[f'productos_nivel_{cliente_key}'] = 'grupos'
                        st.session_state[f'productos_marca_{cliente_key}'] = row['marca']
                        st.rerun()
    
    def _render_tarjetas_grupos(self, df_compras: pd.DataFrame, cliente_key: str, marca: str):
        """Renderiza tarjetas de grupos para navegación jerárquica"""
        if df_compras.empty:
            st.info("No hay grupos para esta marca")
            return
        
        # Agrupar por grupo
        grupos_stats = df_compras.groupby('grupo').agg({
            'total': 'sum',
            'cantidad': 'sum',
            'cod_articulo': 'nunique'
        }).reset_index()
        grupos_stats.columns = ['grupo', 'total', 'cantidad', 'productos_diferentes']
        grupos_stats = grupos_stats.sort_values('total', ascending=False)
        
        # Mostrar en tarjetas (3 columnas)
        cols = st.columns(3)
        for idx, (_, row) in enumerate(grupos_stats.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                with st.container(border=True):
                    grupo = row['grupo'] if pd.notna(row['grupo']) else 'Sin Grupo'
                    st.markdown(f"### {grupo[:30]}...**" if len(grupo) > 30 else f"### {grupo}**")
                    st.metric("Total", format_currency(row['total']))
                    st.caption(f"Cantidad: {int(row['cantidad'])} unidades")
                    st.caption(f"Productos: {int(row['productos_diferentes'])} diferentes")
                    
                    # Botón para ver subgrupos de este grupo
                    if st.button("Ver Subgrupos →", key=f"grupo_{cliente_key}_{idx}", use_container_width=True):
                        st.session_state[f'productos_nivel_{cliente_key}'] = 'subgrupos'
                        st.session_state[f'productos_grupo_{cliente_key}'] = row['grupo']
                        st.rerun()
    
    def _render_tarjetas_subgrupos(self, df_compras: pd.DataFrame, cliente_key: str, marca: str, grupo: str):
        """Renderiza tarjetas de subgrupos para navegación jerárquica"""
        if df_compras.empty:
            st.info("No hay subgrupos para este grupo")
            return
        
        # Agrupar por subgrupo
        subgrupos_stats = df_compras.groupby('subgrupo').agg({
            'total': 'sum',
            'cantidad': 'sum',
            'cod_articulo': 'nunique'
        }).reset_index()
        subgrupos_stats.columns = ['subgrupo', 'total', 'cantidad', 'productos_diferentes']
        subgrupos_stats = subgrupos_stats.sort_values('total', ascending=False)
        
        # Mostrar en tarjetas (3 columnas)
        cols = st.columns(3)
        for idx, (_, row) in enumerate(subgrupos_stats.iterrows()):
            col_idx = idx % 3
            with cols[col_idx]:
                with st.container(border=True):
                    subgrupo = row['subgrupo'] if pd.notna(row['subgrupo']) else 'Sin Subgrupo'
                    st.markdown(f"### {subgrupo[:30]}...**" if len(subgrupo) > 30 else f"### {subgrupo}**")
                    st.metric("Total", format_currency(row['total']))
                    st.caption(f"Cantidad: {int(row['cantidad'])} unidades")
                    st.caption(f"Productos: {int(row['productos_diferentes'])} diferentes")
                    
                    # Botón para ver referencias de este subgrupo
                    if st.button("Ver Referencias →", key=f"subgrupo_{cliente_key}_{idx}", use_container_width=True):
                        st.session_state[f'productos_nivel_{cliente_key}'] = 'referencias'
                        st.session_state[f'productos_subgrupo_{cliente_key}'] = row['subgrupo']
                        st.rerun()
    
    def _render_tarjetas_referencias(self, df_compras: pd.DataFrame):
        """Renderiza tarjetas de referencias (último nivel)"""
        if df_compras.empty:
            st.info("No hay referencias para este subgrupo")
            return
        
        # Agrupar por referencia (cod_articulo y detalle)
        referencias_stats = df_compras.groupby(['cod_articulo', 'detalle']).agg({
            'total': 'sum',
            'cantidad': 'sum',
            'num_documento': 'count'
        }).reset_index()
        referencias_stats.columns = ['cod_articulo', 'detalle', 'total', 'cantidad', 'veces_comprado']
        referencias_stats = referencias_stats.sort_values('cantidad', ascending=False)
        
        # Mostrar en tabla o tarjetas
        st.dataframe(
            referencias_stats.rename(columns={
                'cod_articulo': 'Código',
                'detalle': 'Descripción',
                'total': 'Total',
                'cantidad': 'Cantidad',
                'veces_comprado': 'Veces Comprado'
            }),
            use_container_width=True,
            hide_index=True
        )
    
    # ========================
    # TAB CLIENTES - VISTA VENDEDOR (REORGANIZADO)
    # ========================
    
    def render_clientes_vendedor(self):
        """Renderiza la pestaña de clientes EXACTA como la imagen - Botones horizontales tipo tabs"""
        from ui.theme_manager import ThemeManager
        theme = ThemeManager.get_theme()
        
        # Inicializar estado de tabs
        if 'clientes_tab_activo' not in st.session_state:
            st.session_state['clientes_tab_activo'] = 'Todos'
        
        # Título y subtítulo - EXACTO como imagen
        st.markdown(
            f"""
            <div style='margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    color: {theme['text_primary']};
                    margin-bottom: 0.5rem;
                '>
                    Clientes
                </h1>
                <p style='color: {theme['text_secondary']}; font-size: 1rem; margin: 0;'>
                    Gestiona y analiza a tus clientes comerciales
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # BOTONES HORIZONTALES TIPO TABS - EXACTO como imagen
        col_tabs = st.columns([1, 1, 1, 3])
        
        with col_tabs[0]:
            if st.button("👥 Todos", use_container_width=True, 
                        type="primary" if st.session_state['clientes_tab_activo'] == 'Todos' else "secondary",
                        key="btn_todos"):
                st.session_state['clientes_tab_activo'] = 'Todos'
                st.rerun()
        
        with col_tabs[1]:
            if st.button("Inactivos", use_container_width=True,
                        type="primary" if st.session_state['clientes_tab_activo'] == 'Inactivos' else "secondary",
                        key="btn_inactivos"):
                st.session_state['clientes_tab_activo'] = 'Inactivos'
                st.rerun()
        
        with col_tabs[2]:
            if st.button("⚠️ Pronto a vencer", use_container_width=True,
                        type="primary" if st.session_state['clientes_tab_activo'] == 'Pronto a vencer' else "secondary",
                        key="btn_pronto_vencer"):
                st.session_state['clientes_tab_activo'] = 'Pronto a vencer'
                st.rerun()
        
        with col_tabs[3]:
            busqueda = st.text_input("🔍 Buscar cliente", placeholder="Buscar cliente", 
                                    key="buscar_cliente_vendedor", label_visibility="collapsed")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Obtener lista de clientes B2B
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            todos_clientes = clientes_manager.supabase.table("clientes_b2b").select("*").execute()
            df_clientes = pd.DataFrame(todos_clientes.data) if todos_clientes.data else pd.DataFrame()
            
            if not df_clientes.empty:
                # Aplicar filtro según tab activo
                tab_activo = st.session_state.get('clientes_tab_activo', 'Todos')
                if tab_activo == 'Inactivos':
                    df_clientes = df_clientes[df_clientes.get('activo', True) == False]
                elif tab_activo == 'Pronto a vencer':
                    # Filtrar clientes con facturas próximas a vencer (TODO: implementar lógica)
                    pass
                
                # Aplicar búsqueda
                if busqueda:
                    df_clientes = df_clientes[
                        (df_clientes['nit'].astype(str).str.contains(busqueda, case=False, na=False)) |
                        (df_clientes['nombre'].str.contains(busqueda, case=False, na=False))
                    ]
                
                # Mostrar tabla de clientes EXACTA como imagen
                if not df_clientes.empty:
                    # Preparar datos para mostrar
                    df_clientes['cupo_disponible'] = df_clientes['cupo_total'] - df_clientes['cupo_utilizado']
                    df_clientes['uso_cupo_pct'] = (df_clientes['cupo_utilizado'] / df_clientes['cupo_total'] * 100).fillna(0)
                    
                    # Inicializar cliente seleccionado
                    if 'cliente_seleccionado_idx' not in st.session_state:
                        st.session_state['cliente_seleccionado_idx'] = None
                    
                    # TABLA EN CONTAINER - EXACTO como imagen
                    with st.container(border=True):
                        # Header con título y buscador
                        col_header1, col_header2 = st.columns([1, 1])
                        with col_header1:
                            st.markdown("### Clientes")
                        with col_header2:
                            st.text_input("Buscar cliente", key="buscar_tabla_cliente", label_visibility="collapsed")
                        
                        # Mostrar tabla como filas individuales EXACTO como imagen
                        for idx, row in df_clientes.head(20).iterrows():
                            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 1, 1.5, 1, 1, 1, 0.5])
                            
                            with col1:
                                st.markdown(f"**{row['nombre']}**")
                            with col2:
                                st.markdown(row.get('ciudad', 'N/A'))
                            with col3:
                                st.markdown(format_currency(row.get('cupo_total', 0)))
                            with col4:
                                # Tags de uso con colores (amarillo si >50%, verde si <50%)
                                uso_pct = row.get('uso_cupo_pct', 0)
                                if uso_pct >= 50:
                                    st.markdown(f"<span style='background: #fef08a; color: #78350f; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>{uso_pct:.0f}%</span>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<span style='background: #86efac; color: #14532d; padding: 4px 10px; border-radius: 12px; font-size: 0.75rem; font-weight: 600;'>{uso_pct:.0f}%</span>", unsafe_allow_html=True)
                            with col5:
                                st.markdown("27 días")  # TODO: calcular desde facturas
                            with col6:
                                # Dots de color para última compra (simulado)
                                st.markdown("<span style='color: #22c55e;'>●</span> 2 días", unsafe_allow_html=True)
                            with col7:
                                if st.button("Ver", key=f"ver_cliente_{idx}", use_container_width=True):
                                    st.session_state['cliente_seleccionado_idx'] = idx
                                    st.session_state['cliente_seleccionado'] = row.to_dict()
                                    st.rerun()
                            
                            if idx < len(df_clientes.head(20)) - 1:
                                st.markdown("<hr style='margin: 0.5rem 0; border-color: rgba(255,255,255,0.1);'>", unsafe_allow_html=True)
                    
                    # Detalle del cliente seleccionado
                    if 'cliente_seleccionado' in st.session_state and st.session_state['cliente_seleccionado']:
                        st.markdown("<br>", unsafe_allow_html=True)
                        self._render_detalle_cliente_vendedor(st.session_state['cliente_seleccionado'], clientes_manager)
                else:
                    st.warning("No se encontraron clientes con los filtros aplicados")
            else:
                st.info("No hay clientes registrados en el sistema B2B")
        
        except Exception as e:
            st.error(f"Error cargando clientes: {str(e)}")
            import traceback
            st.code(traceback.format_exc())
    
    def _render_detalle_cliente_vendedor(self, cliente_data: Dict, clientes_manager: ClientPurchasesManager):
        """Renderiza el detalle completo de un cliente con pestañas internas - Estilo dark"""
        from ui.theme_manager import ThemeManager
        theme = ThemeManager.get_theme()
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Header del cliente en container
        with st.container(border=True):
            st.markdown(
                f"""
                <div style='margin-bottom: 1rem;'>
                    <h2 style='
                        font-size: 1.75rem;
                        font-weight: 700;
                        color: {theme['text_primary']};
                        margin: 0;
                    '>
                        {cliente_data['nombre']}
                    </h2>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Pestañas internas
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Compras",
            "Crédito",
            "Facturas",
            "Recomendaciones",
            "Historial",
            "Productos"
        ])
        
        nit_cliente = cliente_data['nit']
        
        with tab1:
            self._render_resumen_cliente_vendedor(cliente_data)
        
        with tab2:
            self._render_historial_compras_cliente_vendedor(nit_cliente, clientes_manager)
        
        with tab3:
            self._render_productos_frecuentes_cliente_vendedor(nit_cliente, clientes_manager)
        
        with tab4:
            self._render_recomendaciones_cliente_vendedor(nit_cliente, clientes_manager)
        
        with tab5:
            self._render_facturas_pagos_cliente_vendedor(nit_cliente)
        
        with tab6:
            self._render_credito_finanzas_cliente(cliente_data)
    
    def _render_resumen_cliente_vendedor(self, cliente_data: Dict):
        """Resumen general del cliente"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Información Básica")
            st.write(f"**NIT:** {cliente_data.get('nit', 'N/A')}")
            st.write(f"**Ciudad:** {cliente_data.get('ciudad', 'N/A')}")
            st.write(f"**Vendedor:** {cliente_data.get('vendedor', 'N/A')}")
            st.write(f"**Email:** {cliente_data.get('email', 'N/A')}")
            st.write(f"**Teléfono:** {cliente_data.get('telefono', 'N/A')}")
        
        with col2:
            st.markdown("#### Métricas de Compras")
            # Obtener análisis
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                analisis = clientes_manager.analizar_cliente(cliente_data['nit'])
                if "error" not in analisis:
                    resumen = analisis.get('resumen', {})
                    st.metric("Total Compras", format_currency(resumen.get('neto_compras', 0)))
                    st.metric("Ticket Promedio", format_currency(resumen.get('ticket_promedio', 0)))
                    st.metric("Transacciones", resumen.get('num_transacciones', 0))
                    st.metric("Días Sin Comprar", resumen.get('dias_sin_comprar', 0))
            except:
                st.info("Cargando métricas...")
        
        with col3:
            st.markdown("#### Acciones Rápidas")
            if st.button("Nueva Venta", type="primary", use_container_width=True):
                st.session_state['cliente_para_venta'] = cliente_data['nombre']
                st.success(f"Cliente {cliente_data['nombre']} seleccionado. Ve a 'Nueva Venta Simple'")
            
            if st.button("Enviar WhatsApp", use_container_width=True):
                st.info("Funcionalidad de WhatsApp en desarrollo")
            
            if st.button("Enviar Email", use_container_width=True):
                st.info("Funcionalidad de Email en desarrollo")
    
    def _render_historial_compras_cliente_vendedor(self, nit_cliente: str, clientes_manager: ClientPurchasesManager):
        """Historial detallado de compras"""
        compras = clientes_manager.obtener_compras_cliente(nit_cliente, incluir_devoluciones=False)
        
        if compras.empty:
            st.info("No hay historial de compras para este cliente")
            return
        
        # Agrupar por documento
        compras_por_doc = compras.groupby('num_documento').agg({
            'fecha': 'first',
            'total': 'sum',
            'cod_articulo': 'count'
        }).reset_index()
        
        compras_por_doc = compras_por_doc.sort_values('fecha', ascending=False)
        
        # Mostrar tabla
        st.dataframe(
            compras_por_doc.rename(columns={
                'num_documento': 'Documento',
                'fecha': 'Fecha',
                'total': 'Total',
                'cod_articulo': 'Productos'
            }),
            use_container_width=True,
            hide_index=True
        )
        
        # Ver detalle de un documento
        doc_seleccionado = st.selectbox(
            "Ver Detalle de Documento",
            options=["-- Selecciona --"] + compras_por_doc['num_documento'].tolist(),
            key="doc_detalle_vendedor"
        )
        
        if doc_seleccionado and doc_seleccionado != "-- Selecciona --":
            detalle_doc = compras[compras['num_documento'] == doc_seleccionado]
            st.dataframe(detalle_doc[['cod_articulo', 'detalle', 'cantidad', 'valor_unitario', 'total']], use_container_width=True, hide_index=True)
    
    def _render_productos_frecuentes_cliente_vendedor(self, nit_cliente: str, clientes_manager: ClientPurchasesManager):
        """Productos frecuentes con navegación jerárquica en tarjetas"""
        try:
            # Obtener compras del cliente directamente
            df_compras = clientes_manager.obtener_compras_cliente(nit_cliente, incluir_devoluciones=False)
            
            if df_compras.empty:
                st.info("No hay compras registradas para este cliente")
                return
            
            # Filtrar solo compras (FE)
            if 'fuente' in df_compras.columns:
                df_compras = df_compras[df_compras['fuente'].astype(str).str.upper() == 'FE'].copy()
            elif 'es_devolucion' in df_compras.columns:
                df_compras = df_compras[(df_compras['es_devolucion'] == False) | (df_compras['es_devolucion'].isna())].copy()
            
            if df_compras.empty:
                st.info("No hay compras para este cliente")
                return
            
            # Obtener nombre del cliente para la clave única
            cliente_b2b = clientes_manager.obtener_cliente(nit_cliente)
            nombre_cliente = cliente_b2b.get('nombre', nit_cliente) if cliente_b2b else nit_cliente
            
            # Implementar navegación jerárquica
            nivel = st.session_state.get(f'productos_nivel_{nit_cliente}', 'marcas')
            marca_seleccionada = st.session_state.get(f'productos_marca_{nit_cliente}', None)
            grupo_seleccionado = st.session_state.get(f'productos_grupo_{nit_cliente}', None)
            subgrupo_seleccionado = st.session_state.get(f'productos_subgrupo_{nit_cliente}', None)
            
            # Botón para volver atrás
            if nivel != 'marcas':
                if st.button("← Volver", key=f"volver_productos_{nit_cliente}"):
                    if nivel == 'grupos':
                        st.session_state[f'productos_nivel_{nit_cliente}'] = 'marcas'
                        st.session_state[f'productos_marca_{nit_cliente}'] = None
                    elif nivel == 'subgrupos':
                        st.session_state[f'productos_nivel_{nit_cliente}'] = 'grupos'
                        st.session_state[f'productos_grupo_{nit_cliente}'] = None
                    elif nivel == 'referencias':
                        st.session_state[f'productos_nivel_{nit_cliente}'] = 'subgrupos'
                        st.session_state[f'productos_subgrupo_{nit_cliente}'] = None
                    st.rerun()
            
            # Nivel 1: MARCAS
            if nivel == 'marcas':
                st.markdown("### Selecciona una Marca")
                self._render_tarjetas_marcas(df_compras, nit_cliente)
            
            # Nivel 2: GRUPOS de la marca seleccionada
            elif nivel == 'grupos' and marca_seleccionada:
                st.markdown(f"### Grupos de la Marca: {marca_seleccionada}")
                df_marca = df_compras[df_compras['marca'].str.upper() == marca_seleccionada.upper()]
                self._render_tarjetas_grupos(df_marca, nit_cliente, marca_seleccionada)
            
            # Nivel 3: SUBGRUPOS del grupo seleccionado
            elif nivel == 'subgrupos' and marca_seleccionada and grupo_seleccionado:
                st.markdown(f"### Subgrupos de {marca_seleccionada} > {grupo_seleccionado}")
                df_grupo = df_compras[
                    (df_compras['marca'].str.upper() == marca_seleccionada.upper()) &
                    (df_compras['grupo'].str.upper() == grupo_seleccionado.upper())
                ]
                self._render_tarjetas_subgrupos(df_grupo, nit_cliente, marca_seleccionada, grupo_seleccionado)
            
            # Nivel 4: REFERENCIAS del subgrupo seleccionado
            elif nivel == 'referencias' and marca_seleccionada and grupo_seleccionado and subgrupo_seleccionado:
                st.markdown(f"### Referencias de {marca_seleccionada} > {grupo_seleccionado} > {subgrupo_seleccionado}")
                df_subgrupo = df_compras[
                    (df_compras['marca'].str.upper() == marca_seleccionada.upper()) &
                    (df_compras['grupo'].str.upper() == grupo_seleccionado.upper()) &
                    (df_compras['subgrupo'].str.upper() == subgrupo_seleccionado.upper())
                ]
                self._render_tarjetas_referencias(df_subgrupo)
        
        except Exception as e:
            st.error(f"Error obteniendo productos: {str(e)}")
    
    def _render_recomendaciones_cliente_vendedor(self, nit_cliente: str, clientes_manager: ClientPurchasesManager):
        """Recomendaciones inteligentes de productos"""
        with st.spinner("Generando recomendaciones..."):
            recomendaciones = clientes_manager.generar_recomendaciones(nit_cliente, self.catalog_manager)
        
        if "error" in recomendaciones:
            st.warning(recomendaciones['error'])
            return
        
        # Mostrar recomendaciones por categoría
        if recomendaciones.get('por_marca'):
            st.markdown("#### Por Marca Preferida")
            df_marca = pd.DataFrame(recomendaciones['por_marca'])
            st.dataframe(df_marca, use_container_width=True, hide_index=True)
        
        if recomendaciones.get('por_categoria'):
            st.markdown("---")
            st.markdown("#### Por Categoría")
            df_cat = pd.DataFrame(recomendaciones['por_categoria'])
            st.dataframe(df_cat, use_container_width=True, hide_index=True)
        
        if recomendaciones.get('complementarios'):
            st.markdown("---")
            st.markdown("#### Productos Complementarios")
            df_comp = pd.DataFrame(recomendaciones['complementarios'])
            st.dataframe(df_comp, use_container_width=True, hide_index=True)
    
    def _render_facturas_pagos_cliente_vendedor(self, nit_cliente: str):
        """Facturas y pagos del cliente"""
        df = self.db_manager.cargar_datos()
        
        # Buscar cliente por NIT
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            cliente_b2b = clientes_manager.obtener_cliente(nit_cliente)
            if cliente_b2b:
                nombre_cliente = cliente_b2b['nombre']
                df_cliente = df[df['cliente'] == nombre_cliente] if not df.empty else pd.DataFrame()
            else:
                st.info("Cliente no encontrado en facturas")
                return
        except:
            st.error("Error buscando cliente")
            return
        
        if df_cliente.empty:
            st.info("No hay facturas para este cliente")
            return
        
        # Separar facturas
        hoy = pd.Timestamp.now()
        facturas_pendientes = df_cliente[df_cliente['pagado'] == False].copy()
        facturas_pagadas = df_cliente[df_cliente['pagado'] == True].copy()
        
        tab1, tab2, tab3 = st.tabs(["Pendientes", "Pagadas", "Todas"])
        
        with tab1:
            if not facturas_pendientes.empty:
                facturas_pendientes['fecha_pago_max'] = pd.to_datetime(facturas_pendientes['fecha_pago_max'])
                facturas_pendientes['dias_vencimiento'] = (facturas_pendientes['fecha_pago_max'] - hoy).dt.days
                
                st.dataframe(
                    facturas_pendientes[['factura', 'fecha_factura', 'valor', 'fecha_pago_max', 'dias_vencimiento']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.success("Cliente al día con todos sus pagos")
        
        with tab2:
            if not facturas_pagadas.empty:
                st.dataframe(
                    facturas_pagadas[['factura', 'fecha_factura', 'valor', 'fecha_pago_real', 'dias_pago_real']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("No hay facturas pagadas")
        
        with tab3:
            st.dataframe(
                df_cliente[['factura', 'fecha_factura', 'valor', 'pagado', 'fecha_pago_real']],
                use_container_width=True,
                hide_index=True
            )
    
    def _render_credito_finanzas_cliente(self, cliente_data: Dict):
        """Crédito y finanzas del cliente - Calcula cupo utilizado dinámicamente"""
        cupo_total = cliente_data.get('cupo_total', 0)
        
        # CALCULAR CUPO UTILIZADO DINÁMICAMENTE: Sumar facturas pendientes del cliente
        cupo_utilizado_calculado = 0
        
        try:
            # Obtener facturas del cliente
            df = self.db_manager.cargar_datos()
            if not df.empty:
                # Buscar cliente por nombre o NIT
                nombre_cliente = cliente_data.get('nombre', '')
                nit_cliente = cliente_data.get('nit', '')
                
                # Filtrar facturas del cliente
                if nombre_cliente:
                    df_cliente = df[df['cliente'] == nombre_cliente]
                elif nit_cliente:
                    # Buscar por NIT en clientes B2B
                    try:
                        clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                        cliente_b2b = clientes_manager.obtener_cliente(nit_cliente)
                        if cliente_b2b:
                            nombre_cliente = cliente_b2b.get('nombre', '')
                            df_cliente = df[df['cliente'] == nombre_cliente] if nombre_cliente else pd.DataFrame()
                        else:
                            df_cliente = pd.DataFrame()
                    except:
                        df_cliente = pd.DataFrame()
                else:
                    df_cliente = pd.DataFrame()
                
                # Sumar valor de facturas pendientes de pago
                if not df_cliente.empty:
                    facturas_pendientes = df_cliente[df_cliente['pagado'] == False]
                    if not facturas_pendientes.empty:
                        # Usar valor_neto si está disponible, sino usar valor
                        if 'valor_neto' in facturas_pendientes.columns:
                            cupo_utilizado_calculado = facturas_pendientes['valor_neto'].sum()
                        else:
                            # Si solo hay valor, calcular valor_neto
                            cupo_utilizado_calculado = facturas_pendientes['valor'].sum() / 1.19
        except Exception as e:
            # Si hay error, usar el valor de la BD como fallback
            cupo_utilizado_calculado = cliente_data.get('cupo_utilizado', 0)
        
        # Usar el valor calculado dinámicamente
        cupo_utilizado = cupo_utilizado_calculado
        cupo_disponible = cupo_total - cupo_utilizado
        porcentaje_uso = (cupo_utilizado / cupo_total * 100) if cupo_total > 0 else 0
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Cupo Total", format_currency(cupo_total))
            st.metric("Cupo Utilizado", format_currency(cupo_utilizado))
            st.metric("Cupo Disponible", format_currency(cupo_disponible))
            st.progress(porcentaje_uso / 100, text=f"Uso: {porcentaje_uso:.1f}%")
        
        with col2:
            st.metric("Plazo de Pago", f"{cliente_data.get('plazo_pago', 30)} días")
            st.metric("Descuento Predeterminado", f"{cliente_data.get('descuento_predeterminado', 0)}%")
            
            # Mostrar información adicional si hay facturas pendientes
            try:
                df = self.db_manager.cargar_datos()
                if not df.empty:
                    nombre_cliente = cliente_data.get('nombre', '')
                    if nombre_cliente:
                        df_cliente = df[df['cliente'] == nombre_cliente]
                        facturas_pendientes = df_cliente[df_cliente['pagado'] == False]
                        if not facturas_pendientes.empty:
                            st.info(f"📋 {len(facturas_pendientes)} factura(s) pendiente(s) afectando el cupo")
            except:
                pass
    
    # ========================
    # TAB MENSAJERÍA Y COMUNICACIÓN (MEJORAR)
    # ========================
    
    def render_mensajeria_comunicacion(self):
        """Renderiza la pestaña de mensajería y comunicación mejorada"""
        st.header("Mensajería y Comunicación")
        st.caption("Gestiona la comunicación con tus clientes")
        
        tab1, tab2, tab3 = st.tabs([
            "Recordatorios Automáticos",
            "Envíos Manuales",
            "Radicación de Facturas"
        ])
        
        with tab1:
            self._render_recordatorios_automaticos()
        
        with tab2:
            self._render_envios_manuales()
        
        with tab3:
            self._render_radicacion_facturas()
    
    def _render_recordatorios_automaticos(self):
        """Configuración y visualización de recordatorios automáticos"""
        st.markdown("### Recordatorios Automáticos")
        st.caption("Sistema de alertas y recordatorios automáticos para facturas")
        
        # Generar recordatorios
        with st.spinner("Generando recordatorios..."):
            recordatorios = self.invoice_alerts.generar_recordatorios_automaticos()
        
        if "error" in recordatorios:
            st.error(f"❌ Error: {recordatorios['error']}")
            return
        
        # Resumen
        resumen = recordatorios.get('resumen', {})
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Recordatorios", resumen.get('total_recordatorios', 0))
        with col2:
            st.metric("Primeros Recordatorios", resumen.get('primeros', 0), help="15 días antes")
        with col3:
            st.metric("Segundos Recordatorios", resumen.get('segundos', 0), help="5 días antes")
        with col4:
            st.metric("Recordatorios Finales", resumen.get('finales', 0), help="1 día antes")
        
        st.markdown("---")
        
        # Lista de recordatorios
        if recordatorios.get('recordatorios'):
            st.markdown("### Lista de Recordatorios")
            
            # Agrupar por tipo
            tipos = {
                'PRIMER_RECORDATORIO': '⏰ Primer Recordatorio (15 días antes)',
                'SEGUNDO_RECORDATORIO': '⚠️ Segundo Recordatorio (5 días antes)',
                'RECORDATORIO_FINAL': '🚨 Recordatorio Final (1 día antes)'
            }
            
            for tipo, titulo in tipos.items():
                recordatorios_tipo = [r for r in recordatorios['recordatorios'] if r['tipo'] == tipo]
                if recordatorios_tipo:
                    with st.expander(f"{titulo} ({len(recordatorios_tipo)})", expanded=(tipo == 'RECORDATORIO_FINAL')):
                        for recordatorio in recordatorios_tipo:
                            with st.container(border=True):
                                col1, col2, col3 = st.columns([3, 2, 1])
                                
                                with col1:
                                    st.markdown(f"**{recordatorio['cliente']}**")
                                    st.caption(f"Factura: {recordatorio['factura']} | Valor: {format_currency(recordatorio['valor'])}")
                                    st.caption(f"Vence: {recordatorio['fecha_vencimiento']}")
                                
                                with col2:
                                    st.caption(f"⏳ {recordatorio['dias_restantes']} días restantes")
                                
                                with col3:
                                    if st.button("Enviar", key=f"enviar_{recordatorio['factura']}_{tipo}", use_container_width=True):
                                        st.info("Funcionalidad de envío automático en desarrollo")
        else:
            st.success("✅ No hay recordatorios pendientes en este momento")
        
        st.markdown("---")
        
        # Configuración
        with st.expander("⚙️ Configuración de Recordatorios"):
            st.markdown("**Configuración actual:**")
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("- **Primer recordatorio:** 15 días antes del vencimiento")
                st.write("- **Segundo recordatorio:** 5 días antes del vencimiento")
                st.write("- **Recordatorio final:** 1 día antes del vencimiento")
            
            with col2:
                st.info("📝 La configuración de recordatorios es gestionada por el sistema. Para modificar los tiempos de recordatorio, contacta al administrador.")
    
    def _render_envios_manuales(self):
        """Envíos manuales de mensajes WhatsApp/Email"""
        st.markdown("### Enviar Mensaje Manual")
        st.caption("Envío de mensajes personalizados a clientes por WhatsApp o Email")
        
        # Selección de cliente
        df = self.db_manager.cargar_datos()
        if not df.empty:
            clientes = sorted(df['cliente'].unique().tolist())
        else:
            clientes = []
        
        # Obtener datos de clientes B2B para contacto
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            todos_clientes_b2b = clientes_manager.supabase.table("clientes_b2b").select("*").eq("activo", True).execute()
            df_clientes_b2b = pd.DataFrame(todos_clientes_b2b.data) if todos_clientes_b2b.data else pd.DataFrame()
        except:
            df_clientes_b2b = pd.DataFrame()
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            cliente_seleccionado = st.selectbox(
                "Seleccionar Cliente",
                options=["-- Selecciona un Cliente --"] + clientes,
                key="cliente_envio_manual"
            )
        
        with col2:
            canal = st.radio(
                "Canal de Envío",
                options=["📧 Email", "💬 WhatsApp", "📧💬 Ambos"],
                key="canal_envio_manual"
            )
        
        if cliente_seleccionado == "-- Selecciona un Cliente --":
            st.info("👆 Selecciona un cliente para continuar")
            return
        
        # Información del cliente
        cliente_info = None
        if not df_clientes_b2b.empty:
            cliente_encontrado = df_clientes_b2b[df_clientes_b2b['nombre'].str.contains(cliente_seleccionado, case=False, na=False)]
            if not cliente_encontrado.empty:
                cliente_info = cliente_encontrado.iloc[0].to_dict()
        
        if cliente_info:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"📧 Email: {cliente_info.get('email', 'No disponible')}")
            with col2:
                st.info(f"📱 Teléfono: {cliente_info.get('telefono', 'No disponible')}")
            with col3:
                st.info(f"🏙️ Ciudad: {cliente_info.get('ciudad', 'No disponible')}")
        
        st.markdown("---")
        
        # Tipo de mensaje y plantilla
        tipo_mensaje = st.selectbox(
            "Tipo de Mensaje",
            ["Factura Vencida", "Factura por Vencer", "Recordatorio de Pago", "Personalizado"],
            key="tipo_mensaje_manual"
        )
        
        # Obtener facturas del cliente si aplica
        factura_seleccionada = None
        if tipo_mensaje in ["Factura Vencida", "Factura por Vencer"]:
            df_cliente = df[df['cliente'] == cliente_seleccionado]
            if not df_cliente.empty:
                facturas_pendientes = df_cliente[df_cliente['pagado'] == False]
                if not facturas_pendientes.empty:
                    facturas_opciones = [
                        f"{row['factura']} - {format_currency(row['valor'])} - Vence: {row.get('fecha_pago_max', 'N/A')}"
                        for _, row in facturas_pendientes.iterrows()
                    ]
                    factura_seleccionada_str = st.selectbox(
                        "Seleccionar Factura",
                        options=["-- Selecciona una Factura --"] + facturas_opciones,
                        key="factura_seleccionada_manual"
                    )
                    
                    if factura_seleccionada_str != "-- Selecciona una Factura --":
                        factura_num = factura_seleccionada_str.split(" - ")[0]
                        factura_seleccionada = df_cliente[df_cliente['factura'] == factura_num].iloc[0].to_dict()
        
        # Mensaje
        mensaje_preview = ""
        
        if tipo_mensaje != "Personalizado" and factura_seleccionada:
            # Usar plantilla
            if tipo_mensaje == "Factura Vencida":
                template = self.notification_system.get_template_factura_vencida(factura_seleccionada)
                mensaje_preview = template.get('whatsapp_text', '')
            elif tipo_mensaje == "Factura por Vencer":
                dias = (pd.to_datetime(factura_seleccionada.get('fecha_pago_max')) - pd.Timestamp.now()).days
                template = self.notification_system.get_template_factura_por_vencer(factura_seleccionada, dias)
                mensaje_preview = template.get('whatsapp_text', '')
            else:
                mensaje_preview = f"Recordatorio de pago para {cliente_seleccionado}"
        else:
            mensaje_preview = st.text_area(
                "Mensaje",
                placeholder="Escribe tu mensaje aquí...",
                height=150,
                key="mensaje_manual_texto"
            )
        
        if mensaje_preview:
            st.markdown("### 📄 Vista Previa del Mensaje")
            st.text(mensaje_preview)
        
        st.markdown("---")
        
        # Botón de envío
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            enviar = st.button("📤 Enviar Mensaje", type="primary", use_container_width=True)
        
        with col2:
            previsualizar = st.button("👁️ Previsualizar", use_container_width=True)
        
        if enviar:
            if not cliente_info:
                st.error("❌ No se encontró información de contacto del cliente")
                return
            
            email_cliente = cliente_info.get('email', '')
            telefono_cliente = cliente_info.get('telefono', '')
            
            if not email_cliente and not telefono_cliente:
                st.error("❌ El cliente no tiene email ni teléfono registrado")
                return
            
            resultados = []
            
            # Enviar por canal seleccionado
            if "Email" in canal:
                if not email_cliente:
                    st.warning("⚠️ El cliente no tiene email registrado")
                else:
                    with st.spinner(f"Enviando email a {email_cliente}..."):
                        if tipo_mensaje in ["Factura Vencida", "Factura por Vencer"] and factura_seleccionada:
                            template = self.notification_system.get_template_factura_vencida(factura_seleccionada) if tipo_mensaje == "Factura Vencida" else self.notification_system.get_template_factura_por_vencer(factura_seleccionada, 5)
                            resultado = self.notification_system.send_email(
                                email_cliente,
                                template['email_subject'],
                                template['email_html']
                            )
                        else:
                            resultado = self.notification_system.send_email(
                                email_cliente,
                                f"Mensaje de {cliente_seleccionado}",
                                f"<p>{mensaje_preview}</p>"
                            )
                        resultados.append(("Email", resultado))
            
            if "WhatsApp" in canal:
                if not telefono_cliente:
                    st.warning("⚠️ El cliente no tiene teléfono registrado")
                else:
                    with st.spinner(f"Enviando WhatsApp a {telefono_cliente}..."):
                        if tipo_mensaje in ["Factura Vencida", "Factura por Vencer"] and factura_seleccionada:
                            template = self.notification_system.get_template_factura_vencida(factura_seleccionada) if tipo_mensaje == "Factura Vencida" else self.notification_system.get_template_factura_por_vencer(factura_seleccionada, 5)
                            mensaje_whatsapp = template.get('whatsapp_text', mensaje_preview)
                        else:
                            mensaje_whatsapp = mensaje_preview
                        
                        resultado = self.notification_system.send_whatsapp(telefono_cliente, mensaje_whatsapp)
                        resultados.append(("WhatsApp", resultado))
            
            # Mostrar resultados
            st.markdown("---")
            st.markdown("### Resultados del Envío")
            
            for canal_nombre, resultado in resultados:
                if resultado.get('success'):
                    st.success(f"✅ {canal_nombre}: {resultado.get('message', 'Enviado exitosamente')}")
                else:
                    st.error(f"❌ {canal_nombre}: {resultado.get('error', 'Error desconocido')}")
        
        if previsualizar:
            st.info("💡 La vista previa se muestra arriba. Configura los canales de comunicación (WhatsApp/Email) para enviar mensajes.")
    
    def _render_radicacion_facturas(self):
        """Radicación de facturas (usar función existente)"""
        self.render_radicacion_facturas()
    
    # ========================
    # TAB COMISIONES - VISTA VENDEDOR (SIMPLIFICAR)
    # ========================
    
    def render_comisiones_vendedor(self):
        """Vista simplificada de comisiones para vendedores con detalle por categoría"""
        st.header("Mis Comisiones")
        st.caption("Vista simplificada de tus comisiones")
        
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            st.info("No hay datos de comisiones")
            return
        
        # Resumen del mes - IMPORTANTE: Filtrar por mes de PAGO, no por mes de factura
        hoy = pd.Timestamp.now()
        mes_actual = hoy.strftime("%Y-%m")
        primer_dia_mes = hoy.replace(day=1).date()
        
        # Convertir fechas de pago a datetime
        df['fecha_pago_real'] = pd.to_datetime(df['fecha_pago_real'], errors='coerce')
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        
        # Filtrar facturas PAGADAS en el mes actual (por fecha_pago_real)
        facturas_pagadas_mes = df[
            (df['pagado'] == True) & 
            (df['fecha_pago_real'].notna()) &
            (df['fecha_pago_real'].dt.to_period('M') == mes_actual)
        ].copy()
        
        # Filtrar facturas PENDIENTES que se vencen este mes o ya están vencidas
        # Convertir fecha_pago_max a datetime
        df['fecha_pago_max'] = pd.to_datetime(df['fecha_pago_max'], errors='coerce')
        
        # Obtener rango del mes actual
        primer_dia_mes_dt = hoy.replace(day=1)
        ultimo_dia_mes = (primer_dia_mes_dt + pd.DateOffset(months=1) - pd.Timedelta(days=1)).date()
        hoy_date = hoy.date()
        
        # Filtrar facturas pendientes que:
        # 1. Están vencidas (fecha_pago_max < hoy) O
        # 2. Se vencen este mes (fecha_pago_max entre primer y último día del mes)
        facturas_pendientes = df[
            (df['pagado'] == False) &
            (df['fecha_pago_max'].notna()) &
            (
                (df['fecha_pago_max'].dt.date < hoy_date) |  # Ya vencidas
                (
                    (df['fecha_pago_max'].dt.date >= primer_dia_mes_dt.date()) &
                    (df['fecha_pago_max'].dt.date <= ultimo_dia_mes)
                )  # Se vencen este mes
            )
        ].copy()
        
        # Separar facturas pagadas por categoría
        facturas_ganadas = facturas_pagadas_mes[facturas_pagadas_mes.get('comision_perdida', False) == False].copy()
        facturas_perdidas = facturas_pagadas_mes[facturas_pagadas_mes.get('comision_perdida', False) == True].copy()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            comisiones_ganadas = facturas_ganadas['comision'].sum()
            num_ganadas = len(facturas_ganadas)
            st.metric("Comisiones Ganadas", format_currency(comisiones_ganadas), delta=f"{num_ganadas} facturas")
        
        with col2:
            comisiones_perdidas = facturas_perdidas['comision'].sum()
            num_perdidas = len(facturas_perdidas)
            st.metric("Comisiones Perdidas", format_currency(comisiones_perdidas), delta=f"{num_perdidas} facturas", delta_color="inverse")
        
        with col3:
            comisiones_pendientes = facturas_pendientes['comision'].sum()
            num_pendientes = len(facturas_pendientes)
            st.metric("Comisiones Pendientes", format_currency(comisiones_pendientes), delta=f"{num_pendientes} facturas")
        
        with col4:
            total_comisiones = comisiones_ganadas + comisiones_pendientes
            st.metric("Total Mes Actual", format_currency(total_comisiones))
        
        st.markdown("---")
        
        # Expandibles para ver detalle de cada categoría
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if not facturas_ganadas.empty:
                with st.expander(f"Ver {len(facturas_ganadas)} Facturas - Comisiones Ganadas ({format_currency(comisiones_ganadas)})", expanded=False):
                    df_ganadas_display = facturas_ganadas[['cliente', 'factura', 'fecha_factura', 'valor', 'comision']].copy()
                    df_ganadas_display['valor'] = df_ganadas_display['valor'].apply(format_currency)
                    df_ganadas_display['comision'] = df_ganadas_display['comision'].apply(format_currency)
                    st.dataframe(df_ganadas_display, use_container_width=True, hide_index=True)
        
        with col2:
            if not facturas_perdidas.empty:
                with st.expander(f"Ver {len(facturas_perdidas)} Facturas - Comisiones Perdidas ({format_currency(comisiones_perdidas)})", expanded=False):
                    df_perdidas_display = facturas_perdidas[['cliente', 'factura', 'fecha_factura', 'valor', 'comision']].copy()
                    df_perdidas_display['valor'] = df_perdidas_display['valor'].apply(format_currency)
                    df_perdidas_display['comision'] = df_perdidas_display['comision'].apply(format_currency)
                    st.dataframe(df_perdidas_display, use_container_width=True, hide_index=True)
        
        with col3:
            if not facturas_pendientes.empty:
                with st.expander(f"Ver {len(facturas_pendientes)} Facturas - Comisiones Pendientes ({format_currency(comisiones_pendientes)})", expanded=False):
                    df_pendientes_display = facturas_pendientes[['cliente', 'factura', 'fecha_factura', 'valor', 'comision']].copy()
                    df_pendientes_display['valor'] = df_pendientes_display['valor'].apply(format_currency)
                    df_pendientes_display['comision'] = df_pendientes_display['comision'].apply(format_currency)
                    st.dataframe(df_pendientes_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### Mis Facturas")
        
        # Combinar todas las facturas del mes (pagadas y pendientes) para la tabla general
        # Facturas pagadas este mes (aunque se facturaron antes)
        facturas_pagadas_mes_display = facturas_pagadas_mes[['cliente', 'factura', 'fecha_factura', 'valor', 'comision', 'pagado']].copy()
        
        # Facturas facturadas este mes pero pendientes
        facturas_pendientes_display = facturas_pendientes[['cliente', 'factura', 'fecha_factura', 'valor', 'comision', 'pagado']].copy()
        
        # Combinar ambas
        if not facturas_pagadas_mes_display.empty and not facturas_pendientes_display.empty:
            df_mes_display = pd.concat([facturas_pagadas_mes_display, facturas_pendientes_display], ignore_index=True)
        elif not facturas_pagadas_mes_display.empty:
            df_mes_display = facturas_pagadas_mes_display
        elif not facturas_pendientes_display.empty:
            df_mes_display = facturas_pendientes_display
        else:
            df_mes_display = pd.DataFrame(columns=['cliente', 'factura', 'fecha_factura', 'valor', 'comision', 'pagado'])
        
        if not df_mes_display.empty:
            df_mes_display['valor'] = df_mes_display['valor'].apply(format_currency)
            df_mes_display['comision'] = df_mes_display['comision'].apply(format_currency)
            df_mes_display = df_mes_display.sort_values('fecha_factura', ascending=False)
            
            st.dataframe(
                df_mes_display,
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay facturas para mostrar este mes")
    
    # ========================
    # TAB ANÁLISIS GEOGRÁFICO (NUEVO - Expandido)
    # ========================
    
    def render_analisis_geografico(self):
        """Análisis geográfico expandido"""
        st.header("Análisis Geográfico")
        st.caption("Análisis profundo de distribución geográfica de clientes y ventas")
        
        # Usar componente existente
        try:
            from business.client_analytics import ClientAnalytics
            client_analytics = ClientAnalytics(self.db_manager.supabase)
            analytics_ui = ClientAnalyticsUI(client_analytics)
            analytics_ui._render_mapa_geografico()
        except:
            st.info("Funcionalidad de análisis geográfico mejorada en desarrollo")
            st.write("Usa la pestaña 'Analytics Clientes' para ver el mapa básico")
    
    # ========================
    # TAB ANÁLISIS COMERCIAL AVANZADO (NUEVO)
    # ========================
    
    def render_analisis_comercial_avanzado(self):
        """Análisis comercial avanzado: referencias quietas, negociaciones"""
        st.header("Análisis Comercial Avanzado")
        st.caption("Referencias quietas, oportunidades de negociación y análisis de productos")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Referencias Quietas",
            "Análisis de Rotación",
            "Oportunidades de Negociación",
            "Segmentación de Clientes"
        ])
        
        with tab1:
            self._render_referencias_quietas()
        
        with tab2:
            self._render_analisis_rotacion()
        
        with tab3:
            self._render_oportunidades_negociacion()
        
        with tab4:
            self._render_segmentacion_clientes()
    
    def _render_referencias_quietas(self):
        """Productos sin rotación con clientes a contactar"""
        st.markdown("### Referencias Quietas (Sin Rotación)")
        st.caption("Productos sin ventas recientes y clientes que los compraron antes")
        
        # Configuración de días sin rotación
        col1, col2 = st.columns([1, 3])
        with col1:
            dias_sin_rotacion = st.selectbox(
                "Días sin Rotación",
                options=[60, 90, 120, 180],
                index=1,  # Default 90 días
                key="dias_quietas"
            )
        
        with st.spinner(f"Analizando productos sin rotación en los últimos {dias_sin_rotacion} días..."):
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                
                # Obtener todas las compras (no devoluciones)
                compras_response = clientes_manager.supabase.table("compras_clientes").select(
                    "cod_articulo, detalle, marca, grupo, subgrupo, nit_cliente, fecha, total, cantidad"
                ).eq("es_devolucion", False).execute()
                
                if not compras_response.data:
                    st.info("No hay datos de compras disponibles")
                    return
                
                df_compras = pd.DataFrame(compras_response.data)
                df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
                
                # Calcular última venta por producto
                fecha_limite = pd.Timestamp.now() - pd.Timedelta(days=dias_sin_rotacion)
                
                productos_stats = df_compras.groupby('cod_articulo').agg({
                    'fecha': 'max',
                    'nit_cliente': lambda x: list(x.unique()),
                    'total': ['sum', 'count'],
                    'detalle': 'first',
                    'marca': 'first',
                    'grupo': 'first',
                    'subgrupo': 'first'
                }).reset_index()
                
                productos_stats.columns = ['cod_articulo', 'ultima_venta', 'clientes_que_compraron', 'total_vendido', 'veces_vendido', 'detalle', 'marca', 'grupo', 'subgrupo']
                
                # Filtrar productos quietos (sin ventas en el período)
                productos_quietos = productos_stats[
                    (productos_stats['ultima_venta'] < fecha_limite) | 
                    (productos_stats['ultima_venta'].isna())
                ].copy()
                
                productos_quietos['dias_sin_venta'] = (pd.Timestamp.now() - productos_quietos['ultima_venta']).dt.days
                productos_quietos = productos_quietos.sort_values('dias_sin_venta', ascending=False)
                
                if productos_quietos.empty:
                    st.success(f"✅ No hay productos sin rotación en los últimos {dias_sin_rotacion} días")
                    return
                
                # Métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Productos Quietos", len(productos_quietos))
                with col2:
                    st.metric("Total Vendido Histórico", format_currency(productos_quietos['total_vendido'].sum()))
                with col3:
                    st.metric("Veces Vendido Total", int(productos_quietos['veces_vendido'].sum()))
                with col4:
                    st.metric("Clientes Únicos", productos_quietos['clientes_que_compraron'].apply(len).sum())
                
                st.markdown("---")
                
                # Tabla de productos quietos
                st.markdown(f"### Lista de Productos Quietos ({len(productos_quietos)} productos)")
                
                # Preparar datos para mostrar
                productos_display = productos_quietos.head(50).copy()  # Limitar a top 50
                productos_display['total_vendido'] = productos_display['total_vendido'].apply(format_currency)
                productos_display['num_clientes'] = productos_display['clientes_que_compraron'].apply(len)
                productos_display['ultima_venta'] = productos_display['ultima_venta'].dt.strftime('%Y-%m-%d')
                
                # Mostrar tabla
                st.dataframe(
                    productos_display[['cod_articulo', 'detalle', 'marca', 'grupo', 'ultima_venta', 'dias_sin_venta', 'num_clientes', 'veces_vendido', 'total_vendido']].rename(columns={
                        'cod_articulo': 'Código',
                        'detalle': 'Producto',
                        'marca': 'Marca',
                        'grupo': 'Grupo',
                        'ultima_venta': 'Última Venta',
                        'dias_sin_venta': 'Días Sin Venta',
                        'num_clientes': 'Clientes',
                        'veces_vendido': 'Veces Vendido',
                        'total_vendido': 'Total Histórico'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
                
                # Detalle de producto seleccionado
                st.markdown("---")
                productos_lista = productos_display['cod_articulo'].tolist()
                producto_seleccionado = st.selectbox(
                    "Ver Detalle de Producto y Clientes a Contactar",
                    options=["-- Selecciona un Producto --"] + productos_lista,
                    key="producto_quieto_detalle"
                )
                
                if producto_seleccionado != "-- Selecciona un Producto --":
                    producto_info = productos_quietos[productos_quietos['cod_articulo'] == producto_seleccionado].iloc[0]
                    
                    with st.container(border=True):
                        col1, col2 = st.columns([2, 1])
                        
                        with col1:
                            st.markdown(f"### {producto_info['detalle']}")
                            st.caption(f"**Código:** {producto_info['cod_articulo']} | **Marca:** {producto_info['marca']} | **Grupo:** {producto_info['grupo']}")
                            st.caption(f"**Última Venta:** {producto_info['ultima_venta'].strftime('%Y-%m-%d')} ({int(producto_info['dias_sin_venta'])} días atrás)")
                            st.caption(f"**Total Vendido Histórico:** {format_currency(producto_info['total_vendido'])} | **Veces Vendido:** {int(producto_info['veces_vendido'])}")
                        
                        with col2:
                            num_clientes = len(producto_info['clientes_que_compraron'])
                            st.metric("Clientes a Contactar", num_clientes)
                        
                        st.markdown("---")
                        st.markdown("### Clientes que Compraron Este Producto")
                        
                        # Obtener nombres de clientes
                        clientes_nits = producto_info['clientes_que_compraron']
                        if clientes_nits:
                            try:
                                clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select(
                                    "nit, nombre, ciudad, telefono, email"
                                ).in_("nit", clientes_nits).execute()
                                
                                if clientes_b2b_response.data:
                                    df_clientes = pd.DataFrame(clientes_b2b_response.data)
                                    st.dataframe(
                                        df_clientes[['nombre', 'nit', 'ciudad', 'telefono', 'email']],
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                    
                                    # Botón para exportar lista
                                    if st.button("📋 Copiar Lista de Clientes", use_container_width=True):
                                        lista_nombres = "\n".join(df_clientes['nombre'].tolist())
                                        st.code(lista_nombres, language=None)
                                        st.success("Lista copiada. Puedes copiarla desde el código de arriba.")
                                else:
                                    st.info("No se encontraron datos completos de los clientes")
                            except Exception as e:
                                st.warning(f"No se pudieron cargar los datos de clientes: {str(e)}")
                        else:
                            st.info("No hay clientes registrados para este producto")
                
            except Exception as e:
                st.error(f"Error analizando referencias quietas: {str(e)}")
                import traceback
                with st.expander("Detalles del error"):
                    st.code(traceback.format_exc())
    
    def _render_analisis_rotacion(self):
        """Análisis de rotación de productos"""
        st.markdown("### Análisis de Rotación de Productos")
        st.caption("Productos más y menos vendidos con tendencias por marca/grupo")
        
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            
            # Obtener todas las compras
            compras_response = clientes_manager.supabase.table("compras_clientes").select(
                "cod_articulo, detalle, marca, grupo, subgrupo, fecha, total, cantidad"
            ).eq("es_devolucion", False).execute()
            
            if not compras_response.data:
                st.info("No hay datos de compras disponibles")
                return
            
            df_compras = pd.DataFrame(compras_response.data)
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
            
            # Análisis por producto
            productos_rotacion = df_compras.groupby('cod_articulo').agg({
                'detalle': 'first',
                'marca': 'first',
                'grupo': 'first',
                'subgrupo': 'first',
                'total': ['sum', 'count'],
                'cantidad': 'sum',
                'fecha': ['min', 'max']
            }).reset_index()
            
            productos_rotacion.columns = ['cod_articulo', 'detalle', 'marca', 'grupo', 'subgrupo', 'total_vendido', 'veces_vendido', 'cantidad_total', 'primera_venta', 'ultima_venta']
            
            # Calcular días de análisis
            productos_rotacion['dias_activo'] = (productos_rotacion['ultima_venta'] - productos_rotacion['primera_venta']).dt.days
            productos_rotacion['rotacion_mensual'] = productos_rotacion['veces_vendido'] / ((productos_rotacion['dias_activo'] / 30).replace(0, 1))
            
            # Top 50 productos más vendidos
            st.markdown("### Top 50 Productos Más Vendidos")
            top_productos = productos_rotacion.nlargest(50, 'total_vendido')
            top_productos['total_vendido'] = top_productos['total_vendido'].apply(format_currency)
            
            st.dataframe(
                top_productos[['cod_articulo', 'detalle', 'marca', 'grupo', 'veces_vendido', 'cantidad_total', 'total_vendido', 'rotacion_mensual']].rename(columns={
                    'cod_articulo': 'Código',
                    'detalle': 'Producto',
                    'marca': 'Marca',
                    'grupo': 'Grupo',
                    'veces_vendido': 'Veces Vendido',
                    'cantidad_total': 'Cantidad Total',
                    'total_vendido': 'Total Vendido',
                    'rotacion_mensual': 'Rotación Mensual'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # Bottom 50 productos menos vendidos (con al menos 1 venta)
            st.markdown("### Bottom 50 Productos Menos Vendidos")
            bottom_productos = productos_rotacion[productos_rotacion['veces_vendido'] > 0].nsmallest(50, 'total_vendido')
            bottom_productos['total_vendido'] = bottom_productos['total_vendido'].apply(format_currency)
            
            st.dataframe(
                bottom_productos[['cod_articulo', 'detalle', 'marca', 'grupo', 'veces_vendido', 'cantidad_total', 'total_vendido', 'rotacion_mensual']].rename(columns={
                    'cod_articulo': 'Código',
                    'detalle': 'Producto',
                    'marca': 'Marca',
                    'grupo': 'Grupo',
                    'veces_vendido': 'Veces Vendido',
                    'cantidad_total': 'Cantidad Total',
                    'total_vendido': 'Total Vendido',
                    'rotacion_mensual': 'Rotación Mensual'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # Tendencias por marca
            st.markdown("### Rotación por Marca")
            rotacion_marca = df_compras.groupby('marca').agg({
                'total': 'sum',
                'cod_articulo': 'nunique',
                'cantidad': 'sum'
            }).reset_index()
            rotacion_marca.columns = ['marca', 'total_vendido', 'productos_unicos', 'cantidad_total']
            rotacion_marca = rotacion_marca.sort_values('total_vendido', ascending=False)
            rotacion_marca['total_vendido'] = rotacion_marca['total_vendido'].apply(format_currency)
            
            st.dataframe(
                rotacion_marca,
                use_container_width=True,
                hide_index=True
            )
            
            st.markdown("---")
            
            # Tendencias por grupo
            st.markdown("### Rotación por Grupo")
            rotacion_grupo = df_compras.groupby('grupo').agg({
                'total': 'sum',
                'cod_articulo': 'nunique',
                'cantidad': 'sum'
            }).reset_index()
            rotacion_grupo.columns = ['grupo', 'total_vendido', 'productos_unicos', 'cantidad_total']
            rotacion_grupo = rotacion_grupo.sort_values('total_vendido', ascending=False).head(20)
            rotacion_grupo['total_vendido'] = rotacion_grupo['total_vendido'].apply(format_currency)
            
            st.dataframe(
                rotacion_grupo,
                use_container_width=True,
                hide_index=True
            )
            
        except Exception as e:
            st.error(f"Error analizando rotación: {str(e)}")
    
    def _render_oportunidades_negociacion(self):
        """Clientes candidatos para negociaciones especiales"""
        st.markdown("### Oportunidades de Negociación")
        st.caption("Clientes candidatos para descuentos por volumen, negociaciones especiales o campañas promocionales")
        
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                st.info("No hay datos de facturas disponibles")
                return
            
            # Obtener clientes B2B
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("*").eq("activo", True).execute()
            df_clientes_b2b = pd.DataFrame(clientes_b2b_response.data) if clientes_b2b_response.data else pd.DataFrame()
            
            if df_clientes_b2b.empty:
                st.info("No hay clientes B2B registrados")
                return
            
            # Analizar cada cliente
            oportunidades = []
            
            for _, cliente_b2b in df_clientes_b2b.iterrows():
                nombre_cliente = cliente_b2b['nombre']
                nit_cliente = cliente_b2b['nit']
                
                # Filtrar facturas del cliente
                df_cliente = df[df['cliente'] == nombre_cliente]
                
                if df_cliente.empty:
                    continue
                
                # Calcular métricas
                total_facturado = df_cliente['valor'].sum()
                num_facturas = len(df_cliente)
                ticket_promedio = total_facturado / num_facturas if num_facturas > 0 else 0
                
                # Análisis de pagos
                facturas_pagadas = df_cliente[df_cliente['pagado'] == True]
                if not facturas_pagadas.empty:
                    dias_pago_promedio = facturas_pagadas['dias_pago_real'].mean() if 'dias_pago_real' in facturas_pagadas.columns else 30
                    puntualidad = len(facturas_pagadas[facturas_pagadas.get('dias_pago_real', 999) <= 30]) / len(facturas_pagadas) * 100
                else:
                    dias_pago_promedio = 30
                    puntualidad = 0
                
                # Frecuencia (facturas por mes)
                df_cliente['fecha_factura'] = pd.to_datetime(df_cliente['fecha_factura'])
                meses_activo = (df_cliente['fecha_factura'].max() - df_cliente['fecha_factura'].min()).days / 30
                frecuencia_mensual = num_facturas / meses_activo if meses_activo > 0 else 0
                
                # Calcular score de oportunidad
                score = 0
                razones = []
                
                if total_facturado > 10000000:  # Más de 10M
                    score += 30
                    razones.append("Alto volumen de compras")
                
                if puntualidad >= 80:
                    score += 25
                    razones.append("Excelente puntualidad de pago")
                elif puntualidad >= 60:
                    score += 15
                    razones.append("Buena puntualidad de pago")
                
                if frecuencia_mensual >= 2:
                    score += 25
                    razones.append("Frecuencia constante de compras")
                elif frecuencia_mensual >= 1:
                    score += 15
                    razones.append("Frecuencia regular")
                
                if ticket_promedio > 500000:
                    score += 20
                    razones.append("Ticket promedio alto")
                
                if score >= 50:
                    oportunidades.append({
                        'cliente': nombre_cliente,
                        'nit': nit_cliente,
                        'ciudad': cliente_b2b.get('ciudad', 'N/A'),
                        'total_facturado': total_facturado,
                        'num_facturas': num_facturas,
                        'ticket_promedio': ticket_promedio,
                        'frecuencia_mensual': frecuencia_mensual,
                        'puntualidad': puntualidad,
                        'score': score,
                        'razones': ", ".join(razones),
                        'cupo_total': cliente_b2b.get('cupo_total', 0)
                    })
            
            if not oportunidades:
                st.info("No se encontraron oportunidades de negociación con los criterios actuales")
                return
            
            # Ordenar por score
            df_oportunidades = pd.DataFrame(oportunidades)
            df_oportunidades = df_oportunidades.sort_values('score', ascending=False)
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Oportunidades Encontradas", len(df_oportunidades))
            with col2:
                st.metric("Total Facturado", format_currency(df_oportunidades['total_facturado'].sum()))
            with col3:
                st.metric("Score Promedio", f"{df_oportunidades['score'].mean():.1f}")
            
            st.markdown("---")
            
            # Tabla de oportunidades
            df_display = df_oportunidades.copy()
            df_display['total_facturado'] = df_display['total_facturado'].apply(format_currency)
            df_display['ticket_promedio'] = df_display['ticket_promedio'].apply(format_currency)
            df_display['cupo_total'] = df_display['cupo_total'].apply(format_currency)
            df_display['puntualidad'] = df_display['puntualidad'].apply(lambda x: f"{x:.1f}%")
            df_display['frecuencia_mensual'] = df_display['frecuencia_mensual'].apply(lambda x: f"{x:.2f}")
            
            st.dataframe(
                df_display[['cliente', 'ciudad', 'total_facturado', 'num_facturas', 'ticket_promedio', 'frecuencia_mensual', 'puntualidad', 'score', 'razones']].rename(columns={
                    'cliente': 'Cliente',
                    'ciudad': 'Ciudad',
                    'total_facturado': 'Total Facturado',
                    'num_facturas': 'Facturas',
                    'ticket_promedio': 'Ticket Promedio',
                    'frecuencia_mensual': 'Frecuencia/Mes',
                    'puntualidad': 'Puntualidad',
                    'score': 'Score',
                    'razones': 'Razones'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Filtros
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                tipo_oportunidad = st.selectbox(
                    "Tipo de Oportunidad",
                    ["Todas", "Descuentos por Volumen", "Negociaciones Especiales", "Campañas Promocionales"],
                    key="tipo_oportunidad"
                )
            
            with col2:
                score_minimo = st.slider("Score Mínimo", 0, 100, 50, key="score_minimo")
            
            # Filtrar según criterios
            df_filtrado = df_oportunidades[df_oportunidades['score'] >= score_minimo]
            
            if len(df_filtrado) != len(df_oportunidades):
                st.info(f"Mostrando {len(df_filtrado)} de {len(df_oportunidades)} oportunidades")
            
        except Exception as e:
            st.error(f"Error analizando oportunidades: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    def _render_segmentacion_clientes(self):
        """Segmentación de clientes: VIP, recurrentes, crecimiento, riesgo"""
        st.markdown("### Segmentación de Clientes")
        st.caption("Clasificación de clientes por valor, frecuencia y comportamiento")
        
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                st.info("No hay datos disponibles")
                return
            
            # Filtrar solo clientes propios
            df_propios = df[df.get('cliente_propio', False) == True].copy()
            
            if df_propios.empty:
                st.info("No hay clientes propios para segmentar")
                return
            
            # Calcular métricas por cliente
            clientes_stats = df_propios.groupby('cliente').agg({
                'valor': ['sum', 'mean', 'count'],
                'fecha_factura': ['min', 'max'],
                'pagado': lambda x: (x == True).sum() / len(x) * 100 if len(x) > 0 else 0
            }).reset_index()
            
            clientes_stats.columns = ['cliente', 'total_facturado', 'ticket_promedio', 'num_facturas', 'primera_compra', 'ultima_compra', 'tasa_pago']
            
            # Calcular días desde última compra
            hoy = pd.Timestamp.now()
            clientes_stats['ultima_compra'] = pd.to_datetime(clientes_stats['ultima_compra'])
            clientes_stats['dias_sin_comprar'] = (hoy - clientes_stats['ultima_compra']).dt.days
            
            # Calcular frecuencia mensual
            clientes_stats['primera_compra'] = pd.to_datetime(clientes_stats['primera_compra'])
            meses_activo = ((clientes_stats['ultima_compra'] - clientes_stats['primera_compra']).dt.days / 30).replace(0, 1)
            clientes_stats['frecuencia_mensual'] = clientes_stats['num_facturas'] / meses_activo
            
            # Segmentar clientes
            total_facturado_umbral = clientes_stats['total_facturado'].quantile(0.8)  # Top 20%
            
            segmentos = {
                'VIP': clientes_stats[clientes_stats['total_facturado'] >= total_facturado_umbral].copy(),
                'Recurrentes': clientes_stats[
                    (clientes_stats['frecuencia_mensual'] >= 1) & 
                    (clientes_stats['total_facturado'] < total_facturado_umbral)
                ].copy(),
                'En Crecimiento': clientes_stats[
                    (clientes_stats['num_facturas'] >= 3) &
                    (clientes_stats['frecuencia_mensual'] >= 0.5) &
                    (clientes_stats['total_facturado'] < total_facturado_umbral)
                ].copy(),
                'En Riesgo': clientes_stats[clientes_stats['dias_sin_comprar'] > 60].copy()
            }
            
            # Métricas por segmento
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("VIP (Top 20%)", len(segmentos['VIP']))
            with col2:
                st.metric("Recurrentes", len(segmentos['Recurrentes']))
            with col3:
                st.metric("En Crecimiento", len(segmentos['En Crecimiento']))
            with col4:
                st.metric("En Riesgo", len(segmentos['En Riesgo']))
            
            st.markdown("---")
            
            # Tabs por segmento
            tab1, tab2, tab3, tab4 = st.tabs(["VIP", "Recurrentes", "En Crecimiento", "En Riesgo"])
            
            for idx, (nombre_segmento, df_segmento) in enumerate(segmentos.items()):
                with [tab1, tab2, tab3, tab4][idx]:
                    if df_segmento.empty:
                        st.info(f"No hay clientes en el segmento '{nombre_segmento}'")
                    else:
                        df_display = df_segmento.copy()
                        df_display['total_facturado'] = df_display['total_facturado'].apply(format_currency)
                        df_display['ticket_promedio'] = df_display['ticket_promedio'].apply(format_currency)
                        df_display['ultima_compra'] = df_display['ultima_compra'].dt.strftime('%Y-%m-%d')
                        df_display['frecuencia_mensual'] = df_display['frecuencia_mensual'].apply(lambda x: f"{x:.2f}")
                        df_display['tasa_pago'] = df_display['tasa_pago'].apply(lambda x: f"{x:.1f}%")
                        
                        st.dataframe(
                            df_display[['cliente', 'total_facturado', 'num_facturas', 'ticket_promedio', 'frecuencia_mensual', 'ultima_compra', 'dias_sin_comprar', 'tasa_pago']].rename(columns={
                                'cliente': 'Cliente',
                                'total_facturado': 'Total Facturado',
                                'num_facturas': 'Facturas',
                                'ticket_promedio': 'Ticket Promedio',
                                'frecuencia_mensual': 'Frecuencia/Mes',
                                'ultima_compra': 'Última Compra',
                                'dias_sin_comprar': 'Días Sin Comprar',
                                'tasa_pago': 'Tasa Pago'
                            }),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Botón exportar
                        if st.button(f"📥 Exportar Lista {nombre_segmento}", key=f"export_{nombre_segmento}"):
                            lista_clientes = "\n".join(df_segmento['cliente'].tolist())
                            st.code(lista_clientes, language=None)
                            st.success("Lista copiada. Puedes copiarla desde el código de arriba.")
        
        except Exception as e:
            st.error(f"Error segmentando clientes: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    # ========================
    # TAB ANÁLISIS DE COMPRAS Y COMPORTAMIENTO (NUEVO)
    # ========================
    
    def render_analisis_compras_comportamiento(self):
        """Análisis profundo de patrones de compra"""
        st.header("Análisis de Compras y Comportamiento")
        st.caption("Análisis detallado de patrones de compra de clientes")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "Historial de Compras",
            "Productos por Cliente",
            "Clientes Inactivos",
            "Clientes por Producto"
        ])
        
        with tab1:
            self._render_analisis_historial_compras()
        
        with tab2:
            self._render_productos_por_cliente()
        
        with tab3:
            self._render_clientes_inactivos()
        
        with tab4:
            self._render_clientes_por_producto()
    
    def _render_analisis_historial_compras(self):
        """Análisis de historial de compras con tendencias"""
        st.markdown("### Análisis de Historial de Compras")
        st.caption("Tendencias por cliente, producto/marca y análisis estacional")
        
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                st.info("No hay datos de facturas disponibles")
                return
            
            # Obtener datos de compras
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            compras_response = clientes_manager.supabase.table("compras_clientes").select(
                "cod_articulo, detalle, marca, grupo, subgrupo, nit_cliente, fecha, total, cantidad, es_devolucion"
            ).eq("es_devolucion", False).execute()
            
            df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            
            if df_compras.empty:
                st.info("No hay datos de compras disponibles")
                return
            
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
            
            # Filtro de período
            col1, col2 = st.columns([1, 2])
            with col1:
                periodo = st.selectbox(
                    "Período de Análisis",
                    ["Últimos 3 meses", "Últimos 6 meses", "Últimos 12 meses", "Todo el historial"],
                    key="periodo_historial"
                )
            
            # Calcular fecha límite
            if periodo == "Últimos 3 meses":
                fecha_limite = pd.Timestamp.now() - pd.Timedelta(days=90)
            elif periodo == "Últimos 6 meses":
                fecha_limite = pd.Timestamp.now() - pd.Timedelta(days=180)
            elif periodo == "Últimos 12 meses":
                fecha_limite = pd.Timestamp.now() - pd.Timedelta(days=365)
            else:
                fecha_limite = None
            
            if fecha_limite:
                df_compras = df_compras[df_compras['fecha'] >= fecha_limite].copy()
            
            if df_compras.empty:
                st.info(f"No hay compras en el período seleccionado")
                return
            
            # Tendencias por Cliente
            st.markdown("---")
            st.markdown("### 📈 Tendencias por Cliente")
            
            # Obtener nombres de clientes
            try:
                clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("nit, nombre").execute()
                df_clientes_b2b = pd.DataFrame(clientes_b2b_response.data) if clientes_b2b_response.data else pd.DataFrame()
                
                if not df_clientes_b2b.empty:
                    df_compras = df_compras.merge(df_clientes_b2b, left_on='nit_cliente', right_on='nit', how='left')
                    df_compras['cliente_nombre'] = df_compras['nombre'].fillna(df_compras['nit_cliente'])
                else:
                    df_compras['cliente_nombre'] = df_compras['nit_cliente']
            except:
                df_compras['cliente_nombre'] = df_compras['nit_cliente']
            
            tendencias_cliente = df_compras.groupby(['cliente_nombre', df_compras['fecha'].dt.to_period('M')]).agg({
                'total': 'sum',
                'cantidad': 'sum'
            }).reset_index()
            tendencias_cliente.columns = ['cliente', 'mes', 'total', 'cantidad']
            tendencias_cliente['mes'] = tendencias_cliente['mes'].astype(str)
            
            # Top 10 clientes
            top_clientes = df_compras.groupby('cliente_nombre')['total'].sum().nlargest(10)
            
            st.dataframe(
                pd.DataFrame({
                    'Cliente': top_clientes.index,
                    'Total Compras': top_clientes.values
                }).reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
            
            # Tendencias por Producto/Marca
            st.markdown("---")
            st.markdown("### 📊 Tendencias por Marca")
            
            tendencias_marca = df_compras.groupby(['marca', df_compras['fecha'].dt.to_period('M')]).agg({
                'total': 'sum',
                'cod_articulo': 'nunique'
            }).reset_index()
            tendencias_marca.columns = ['marca', 'mes', 'total', 'productos_unicos']
            tendencias_marca['mes'] = tendencias_marca['mes'].astype(str)
            
            top_marcas = df_compras.groupby('marca')['total'].sum().nlargest(10)
            
            col1, col2 = st.columns(2)
            with col1:
                st.dataframe(
                    pd.DataFrame({
                        'Marca': top_marcas.index,
                        'Total Compras': top_marcas.values
                    }).reset_index(drop=True),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col2:
                # Análisis estacional (por mes del año)
                df_compras['mes_año'] = df_compras['fecha'].dt.month
                estacional = df_compras.groupby('mes_año')['total'].sum().reset_index()
                estacional.columns = ['Mes', 'Total']
                estacional['Mes'] = estacional['Mes'].map({
                    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                    7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
                })
                st.dataframe(estacional, use_container_width=True, hide_index=True)
        
        except Exception as e:
            st.error(f"Error analizando historial: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    def _render_productos_por_cliente(self):
        """Qué compra cada cliente segmentado por Marca/Grupo/Subgrupo/Referencia"""
        st.markdown("### Productos por Cliente")
        st.caption("Análisis detallado de qué compra cada cliente")
        
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            
            # Seleccionar cliente
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("nit, nombre").eq("activo", True).execute()
            df_clientes = pd.DataFrame(clientes_b2b_response.data) if clientes_b2b_response.data else pd.DataFrame()
            
            if df_clientes.empty:
                st.info("No hay clientes disponibles")
                return
            
            cliente_seleccionado = st.selectbox(
                "Seleccionar Cliente",
                options=["-- Selecciona un Cliente --"] + df_clientes['nombre'].tolist(),
                key="cliente_analisis_productos"
            )
            
            if cliente_seleccionado == "-- Selecciona un Cliente --":
                st.info("👆 Selecciona un cliente para ver su análisis de productos")
                return
            
            nit_cliente = df_clientes[df_clientes['nombre'] == cliente_seleccionado]['nit'].iloc[0]
            
            # Obtener compras del cliente
            df_compras = clientes_manager.obtener_compras_cliente(nit_cliente, incluir_devoluciones=False)
            
            if df_compras.empty:
                st.info(f"No hay compras registradas para {cliente_seleccionado}")
                return
            
            # Análisis por nivel jerárquico
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("#### Por Marca")
                marca_stats = df_compras.groupby('marca').agg({
                    'total': 'sum',
                    'cantidad': 'sum',
                    'cod_articulo': 'nunique'
                }).reset_index()
                marca_stats.columns = ['Marca', 'Total', 'Cantidad', 'Productos Únicos']
                marca_stats = marca_stats.sort_values('Total', ascending=False)
                marca_stats['Total'] = marca_stats['Total'].apply(format_currency)
                st.dataframe(marca_stats, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### Por Grupo")
                grupo_stats = df_compras.groupby('grupo').agg({
                    'total': 'sum',
                    'cantidad': 'sum',
                    'cod_articulo': 'nunique'
                }).reset_index()
                grupo_stats.columns = ['Grupo', 'Total', 'Cantidad', 'Productos Únicos']
                grupo_stats = grupo_stats.sort_values('Total', ascending=False).head(10)
                grupo_stats['Total'] = grupo_stats['Total'].apply(format_currency)
                st.dataframe(grupo_stats, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Detalle por referencia
            st.markdown("#### Top Referencias Compradas")
            referencia_stats = df_compras.groupby(['cod_articulo', 'detalle']).agg({
                'total': 'sum',
                'cantidad': 'sum',
                'fecha': ['min', 'max', 'count']
            }).reset_index()
            referencia_stats.columns = ['cod_articulo', 'detalle', 'total', 'cantidad', 'primera_compra', 'ultima_compra', 'veces_comprado']
            referencia_stats = referencia_stats.sort_values('total', ascending=False).head(20)
            referencia_stats['total'] = referencia_stats['total'].apply(format_currency)
            
            st.dataframe(
                referencia_stats[['cod_articulo', 'detalle', 'veces_comprado', 'cantidad', 'total', 'ultima_compra']].rename(columns={
                    'cod_articulo': 'Código',
                    'detalle': 'Producto',
                    'veces_comprado': 'Veces Comprado',
                    'cantidad': 'Cantidad Total',
                    'total': 'Total',
                    'ultima_compra': 'Última Compra'
                }),
                use_container_width=True,
                hide_index=True
            )
        
        except Exception as e:
            st.error(f"Error analizando productos por cliente: {str(e)}")
    
    def _render_clientes_inactivos(self):
        """Lista de clientes que han dejado de comprar"""
        st.markdown("### Clientes Inactivos")
        st.caption("Clientes que han dejado de comprar con sugerencias de contacto")
        
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                st.info("No hay datos disponibles")
                return
            
            # Filtrar solo clientes propios
            df_propios = df[df.get('cliente_propio', False) == True].copy()
            
            if df_propios.empty:
                st.info("No hay clientes propios para analizar")
                return
            
            # Configuración de días de inactividad
            dias_inactivo = st.slider(
                "Días sin comprar para considerar inactivo",
                min_value=30,
                max_value=180,
                value=60,
                step=30,
                key="dias_inactivo"
            )
            
            # Calcular días desde última compra por cliente
            hoy = pd.Timestamp.now()
            df_propios['fecha_factura'] = pd.to_datetime(df_propios['fecha_factura'])
            
            clientes_stats = df_propios.groupby('cliente').agg({
                'fecha_factura': 'max',
                'valor': ['sum', 'mean', 'count']
            }).reset_index()
            
            clientes_stats.columns = ['cliente', 'ultima_compra', 'total_facturado', 'ticket_promedio', 'num_facturas']
            clientes_stats['dias_sin_comprar'] = (hoy - clientes_stats['ultima_compra']).dt.days
            
            # Filtrar inactivos
            clientes_inactivos = clientes_stats[clientes_stats['dias_sin_comprar'] > dias_inactivo].copy()
            clientes_inactivos = clientes_inactivos.sort_values('dias_sin_comprar', ascending=False)
            
            if clientes_inactivos.empty:
                st.success(f"✅ No hay clientes inactivos (más de {dias_inactivo} días sin comprar)")
                return
            
            st.metric("Clientes Inactivos", len(clientes_inactivos))
            
            # Preparar datos para mostrar
            clientes_display = clientes_inactivos.copy()
            clientes_display['total_facturado'] = clientes_display['total_facturado'].apply(format_currency)
            clientes_display['ticket_promedio'] = clientes_display['ticket_promedio'].apply(format_currency)
            clientes_display['ultima_compra'] = clientes_display['ultima_compra'].dt.strftime('%Y-%m-%d')
            
            st.dataframe(
                clientes_display[['cliente', 'ultima_compra', 'dias_sin_comprar', 'num_facturas', 'total_facturado', 'ticket_promedio']].rename(columns={
                    'cliente': 'Cliente',
                    'ultima_compra': 'Última Compra',
                    'dias_sin_comprar': 'Días Sin Comprar',
                    'num_facturas': 'Facturas',
                    'total_facturado': 'Total Facturado',
                    'ticket_promedio': 'Ticket Promedio'
                }),
                use_container_width=True,
                hide_index=True
            )
            
            # Acción sugerida
            st.markdown("---")
            st.markdown("### 💡 Acción Sugerida")
            st.info(f"Se recomienda contactar a estos {len(clientes_inactivos)} clientes que llevan más de {dias_inactivo} días sin realizar compras.")
            
            if st.button("📋 Exportar Lista de Clientes Inactivos", use_container_width=True):
                lista_clientes = "\n".join(clientes_inactivos['cliente'].tolist())
                st.code(lista_clientes, language=None)
                st.success("Lista copiada. Puedes copiarla desde el código de arriba.")
        
        except Exception as e:
            st.error(f"Error analizando clientes inactivos: {str(e)}")
    
    def _render_clientes_por_producto(self):
        """Para cada producto: quiénes lo compran"""
        st.markdown("### Clientes por Producto")
        st.caption("Análisis de quiénes compran cada producto")
        
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            
            # Buscar producto
            busqueda_producto = st.text_input(
                "Buscar Producto (Código o Nombre)",
                placeholder="Ej: ABC123 o nombre del producto",
                key="busqueda_producto_cliente"
            )
            
            if not busqueda_producto:
                st.info("👆 Busca un producto para ver qué clientes lo compran")
                return
            
            # Obtener compras
            compras_response = clientes_manager.supabase.table("compras_clientes").select(
                "cod_articulo, detalle, marca, grupo, nit_cliente, fecha, total, cantidad, es_devolucion"
            ).eq("es_devolucion", False).execute()
            
            df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            
            if df_compras.empty:
                st.info("No hay datos de compras disponibles")
                return
            
            # Filtrar por búsqueda
            df_filtrado = df_compras[
                (df_compras['cod_articulo'].str.contains(busqueda_producto, case=False, na=False)) |
                (df_compras['detalle'].str.contains(busqueda_producto, case=False, na=False))
            ].copy()
            
            if df_filtrado.empty:
                st.warning(f"No se encontraron productos que coincidan con '{busqueda_producto}'")
                return
            
            # Agrupar por producto
            productos_encontrados = df_filtrado.groupby(['cod_articulo', 'detalle']).agg({
                'nit_cliente': lambda x: list(x.unique()),
                'total': 'sum',
                'cantidad': 'sum',
                'fecha': ['min', 'max', 'count']
            }).reset_index()
            
            productos_encontrados.columns = ['cod_articulo', 'detalle', 'clientes', 'total_vendido', 'cantidad_total', 'primera_venta', 'ultima_venta', 'veces_vendido']
            
            # Seleccionar producto específico si hay múltiples
            if len(productos_encontrados) > 1:
                producto_seleccionado_str = st.selectbox(
                    "Seleccionar Producto",
                    options=[f"{row['cod_articulo']} - {row['detalle']}" for _, row in productos_encontrados.iterrows()],
                    key="producto_especifico_cliente"
                )
                cod_producto = producto_seleccionado_str.split(" - ")[0]
                producto_info = productos_encontrados[productos_encontrados['cod_articulo'] == cod_producto].iloc[0]
            else:
                producto_info = productos_encontrados.iloc[0]
            
            # Mostrar información del producto
            with st.container(border=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Código", producto_info['cod_articulo'])
                with col2:
                    st.metric("Total Vendido", format_currency(producto_info['total_vendido']))
                with col3:
                    st.metric("Clientes Únicos", len(producto_info['clientes']))
                
                st.caption(f"**Producto:** {producto_info['detalle']}")
                st.caption(f"**Primera Venta:** {producto_info['primera_venta']} | **Última Venta:** {producto_info['ultima_venta']} | **Veces Vendido:** {int(producto_info['veces_vendido'])}")
            
            st.markdown("---")
            
            # Clientes que compraron este producto
            st.markdown("### Clientes que Compraron Este Producto")
            
            # Obtener nombres de clientes
            clientes_nits = producto_info['clientes']
            try:
                clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("nit, nombre, ciudad, telefono, email").in_("nit", list(clientes_nits)).execute()
                df_clientes = pd.DataFrame(clientes_b2b_response.data) if clientes_b2b_response.data else pd.DataFrame()
                
                if not df_clientes.empty:
                    # Agregar estadísticas de compra del producto
                    compras_producto = df_filtrado[df_filtrado['cod_articulo'] == producto_info['cod_articulo']]
                    stats_cliente = compras_producto.groupby('nit_cliente').agg({
                        'total': 'sum',
                        'cantidad': 'sum',
                        'fecha': ['min', 'max', 'count']
                    }).reset_index()
                    stats_cliente.columns = ['nit', 'total_comprado', 'cantidad_total', 'primera_compra', 'ultima_compra', 'veces_comprado']
                    
                    df_clientes = df_clientes.merge(stats_cliente, on='nit', how='left')
                    df_clientes['total_comprado'] = df_clientes['total_comprado'].apply(format_currency)
                    df_clientes['ultima_compra'] = pd.to_datetime(df_clientes['ultima_compra']).dt.strftime('%Y-%m-%d')
                    
                    st.dataframe(
                        df_clientes[['nombre', 'ciudad', 'total_comprado', 'cantidad_total', 'veces_comprado', 'ultima_compra']].rename(columns={
                            'nombre': 'Cliente',
                            'ciudad': 'Ciudad',
                            'total_comprado': 'Total Comprado',
                            'cantidad_total': 'Cantidad',
                            'veces_comprado': 'Veces Comprado',
                            'ultima_compra': 'Última Compra'
                        }),
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("No se encontraron datos completos de los clientes")
            except Exception as e:
                st.warning(f"Error cargando datos de clientes: {str(e)}")
        
        except Exception as e:
            st.error(f"Error analizando clientes por producto: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    # ========================
    # TAB IMPORTACIONES Y STOCK (NUEVO)
    # ========================
    
    def render_importaciones_stock(self):
        """Gestión de importaciones y detección de productos nuevos"""
        st.header("Importaciones y Stock")
        st.caption("Gestiona importaciones y detecta productos nuevos")
        
        tab1, tab2, tab3 = st.tabs([
            "Cargar Importación",
            "Productos Nuevos Detectados",
            "Actualización de Precios"
        ])
        
        with tab1:
            self._render_cargar_importacion()
        
        with tab2:
            self._render_productos_nuevos()
        
        with tab3:
            self._render_actualizacion_precios()
    
    def _render_cargar_importacion(self):
        """Cargar archivo Excel de importación"""
        st.markdown("### Cargar Importación")
        st.caption("Sube un archivo Excel con productos de importación para detectar productos nuevos")
        
        archivo_subido = st.file_uploader(
            "Seleccionar archivo Excel",
            type=['xlsx', 'xls'],
            key="archivo_importacion"
        )
        
        if archivo_subido:
            try:
                # Guardar temporalmente
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(archivo_subido.getvalue())
                    tmp_path = tmp_file.name
                
                if st.button("📤 Procesar Importación", type="primary", use_container_width=True):
                    with st.spinner("Procesando archivo de importación..."):
                        resultado = self.catalog_manager.cargar_catalogo_desde_excel(tmp_path)
                        
                        if "error" in resultado:
                            st.error(f"❌ {resultado['error']}")
                        else:
                            st.success("✅ Importación procesada exitosamente!")
                            
                            # Métricas
                            col1, col2, col3, col4 = st.columns(4)
                            with col1:
                                st.metric("Total Productos", resultado.get('total_productos', 0))
                            with col2:
                                st.metric("Productos Nuevos", resultado.get('productos_nuevos', 0), delta="Nuevos")
                            with col3:
                                st.metric("Productos Actualizados", resultado.get('productos_actualizados', 0), delta="Actualizados")
                            with col4:
                                st.metric("Productos Desactivados", resultado.get('productos_desactivados', 0), delta="Sin stock")
                            
                            # Detalles
                            if resultado.get('productos_nuevos', 0) > 0:
                                st.markdown("---")
                                st.markdown("### 🆕 Productos Nuevos Detectados")
                                if resultado.get('detalle_nuevos'):
                                    df_nuevos = pd.DataFrame(resultado['detalle_nuevos'])
                                    st.dataframe(df_nuevos, use_container_width=True, hide_index=True)
                            
                            # Limpiar cache y recargar
                            st.cache_data.clear()
                            st.rerun()
                    
                    # Limpiar archivo temporal
                    os.unlink(tmp_path)
            
            except Exception as e:
                st.error(f"Error procesando archivo: {str(e)}")
                import traceback
                with st.expander("Detalles del error"):
                    st.code(traceback.format_exc())
        
        st.markdown("---")
        st.markdown("### 📋 Formato Esperado del Excel")
        st.info("""
        El archivo Excel debe contener las siguientes columnas:
        - **Cod_UR**: Código único del producto
        - **Referencia**: Referencia del producto
        - **Descripcion**: Descripción del producto
        - **Marca**: Marca del producto
        - **Linea**: Línea del producto
        - **Precio**: Precio del producto
        - **Equivalencia**: (Opcional) Equivalencia del producto
        - **DetalleDescuento**: (Opcional) Detalle de descuento
        """)
    
    def _render_productos_nuevos(self):
        """Mostrar productos nuevos detectados con recomendaciones"""
        st.markdown("### Productos Nuevos Detectados")
        st.caption("Productos nuevos de la última importación con recomendaciones de clientes")
        
        try:
            # Cargar catálogo
            df_catalogo = self.catalog_manager.cargar_catalogo()
            
            if df_catalogo.empty:
                st.info("No hay productos en el catálogo. Carga una importación primero.")
                return
            
            # Filtrar productos nuevos (fecha de actualización reciente)
            if 'fecha_actualizacion' in df_catalogo.columns:
                df_catalogo['fecha_actualizacion'] = pd.to_datetime(df_catalogo['fecha_actualizacion'])
                fecha_reciente = pd.Timestamp.now() - pd.Timedelta(days=30)
                productos_nuevos = df_catalogo[df_catalogo['fecha_actualizacion'] >= fecha_reciente].copy()
            else:
                # Si no hay fecha, mostrar todos los productos activos
                productos_nuevos = df_catalogo[df_catalogo.get('activo', True) == True].head(50).copy()
                st.info("No se encontró fecha de actualización. Mostrando productos activos.")
            
            if productos_nuevos.empty:
                st.success("✅ No hay productos nuevos detectados en los últimos 30 días")
                return
            
            st.metric("Productos Nuevos", len(productos_nuevos))
            st.markdown("---")
            
            # Obtener compras para recomendaciones
            try:
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                compras_response = clientes_manager.supabase.table("compras_clientes").select(
                    "cod_articulo, marca, grupo, nit_cliente"
                ).eq("es_devolucion", False).execute()
                
                df_compras = pd.DataFrame(compras_response.data) if compras_response.data else pd.DataFrame()
            except:
                df_compras = pd.DataFrame()
            
            # Mostrar productos nuevos con recomendaciones
            for idx, producto in productos_nuevos.head(20).iterrows():
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.markdown(f"**{producto.get('descripcion', producto.get('referencia', 'N/A'))}**")
                        st.caption(f"Código: {producto.get('cod_ur', 'N/A')} | Marca: {producto.get('marca', 'N/A')} | Línea: {producto.get('linea', 'N/A')}")
                        if 'precio' in producto:
                            st.caption(f"Precio: {format_currency(producto['precio'])}")
                    
                    with col2:
                        # Buscar clientes que compran marcas similares
                        if not df_compras.empty and producto.get('marca'):
                            marca_producto = producto.get('marca', '').upper()
                            clientes_marca = df_compras[
                                df_compras['marca'].str.upper() == marca_producto
                            ]['nit_cliente'].unique()
                            
                            num_clientes = len(clientes_marca)
                            st.metric("Clientes Potenciales", num_clientes)
                            
                            if num_clientes > 0:
                                if st.button("👥 Ver Clientes", key=f"ver_clientes_{idx}"):
                                    st.session_state[f'mostrar_clientes_{idx}'] = True
                            
                            if st.session_state.get(f'mostrar_clientes_{idx}', False):
                                try:
                                    clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select(
                                        "nit, nombre, ciudad, telefono, email"
                                    ).in_("nit", list(clientes_marca[:20])).execute()
                                    
                                    if clientes_b2b_response.data:
                                        df_clientes = pd.DataFrame(clientes_b2b_response.data)
                                        st.dataframe(df_clientes[['nombre', 'ciudad', 'telefono']], use_container_width=True, hide_index=True)
                                except:
                                    st.info("No se pudieron cargar los datos de clientes")
                        else:
                            st.info("Sin datos")
            
            if len(productos_nuevos) > 20:
                st.info(f"Mostrando 20 de {len(productos_nuevos)} productos nuevos. Usa filtros para ver más.")
        
        except Exception as e:
            st.error(f"Error cargando productos nuevos: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    def _render_actualizacion_precios(self):
        """Mostrar productos con precios actualizados"""
        st.markdown("### Actualización de Precios")
        st.caption("Productos con cambios de precio en la última importación")
        
        st.info("💡 Esta funcionalidad mostrará productos con cambios de precio cuando se procese una nueva importación.")
        st.write("""
        **Funcionalidad en desarrollo:**
        - Comparativa precio anterior vs nuevo
        - Confirmar actualizaciones masivas
        - Historial de cambios de precio
        """)
    
    # ========================
    # TAB REPORTES Y EXPORTACIÓN (NUEVO)
    # ========================
    
    def render_reportes_exportacion(self):
        """Generar reportes y exportar datos"""
        st.header("Reportes y Exportación")
        st.caption("Genera reportes personalizados y exporta datos")
        
        tab1, tab2 = st.tabs([
            "Reportes Predefinidos",
            "Exportación de Datos"
        ])
        
        with tab1:
            self._render_reportes_predefinidos()
        
        with tab2:
            self._render_exportacion_datos()
    
    def _render_reportes_predefinidos(self):
        """Reportes predefinidos: ventas, comisiones, productos, clientes"""
        st.markdown("### Reportes Predefinidos")
        st.caption("Genera reportes automáticos con análisis clave del negocio")
        
        tipo_reporte = st.selectbox(
            "Seleccionar Tipo de Reporte",
            [
                "Ventas por Período",
                "Comisiones por Vendedor",
                "Productos Más Vendidos",
                "Clientes por Ciudad",
                "Análisis de Crédito"
            ],
            key="tipo_reporte"
        )
        
        # Configuración de período
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input(
                "Fecha Inicio",
                value=pd.Timestamp.now() - pd.Timedelta(days=30),
                key="fecha_inicio_reporte"
            )
        with col2:
            fecha_fin = st.date_input(
                "Fecha Fin",
                value=pd.Timestamp.now(),
                key="fecha_fin_reporte"
            )
        
        st.markdown("---")
        
        try:
            df = self.db_manager.cargar_datos()
            
            if df.empty:
                st.info("No hay datos disponibles para generar reportes")
                return
            
            # Filtrar por período
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
            df_periodo = df[
                (df['fecha_factura'].dt.date >= fecha_inicio) &
                (df['fecha_factura'].dt.date <= fecha_fin)
            ].copy()
            
            if df_periodo.empty:
                st.warning(f"No hay datos en el período seleccionado ({fecha_inicio} a {fecha_fin})")
                return
            
            # Generar reporte según tipo
            if tipo_reporte == "Ventas por Período":
                self._generar_reporte_ventas(df_periodo, fecha_inicio, fecha_fin)
            elif tipo_reporte == "Comisiones por Vendedor":
                self._generar_reporte_comisiones(df_periodo, fecha_inicio, fecha_fin)
            elif tipo_reporte == "Productos Más Vendidos":
                self._generar_reporte_productos(df_periodo, fecha_inicio, fecha_fin)
            elif tipo_reporte == "Clientes por Ciudad":
                self._generar_reporte_clientes_ciudad(df_periodo, fecha_inicio, fecha_fin)
            elif tipo_reporte == "Análisis de Crédito":
                self._generar_reporte_credito(df_periodo, fecha_inicio, fecha_fin)
        
        except Exception as e:
            st.error(f"Error generando reporte: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    def _generar_reporte_ventas(self, df: pd.DataFrame, fecha_inicio, fecha_fin):
        """Reporte de ventas por período"""
        st.markdown("### 📊 Reporte de Ventas por Período")
        
        # Agrupar por día
        df['fecha'] = df['fecha_factura'].dt.date
        ventas_diarias = df.groupby('fecha').agg({
            'valor': ['sum', 'count'],
            'comision': 'sum'
        }).reset_index()
        ventas_diarias.columns = ['Fecha', 'Total Ventas', 'Número Facturas', 'Total Comisiones']
        ventas_diarias = ventas_diarias.sort_values('Fecha')
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Ventas", format_currency(df['valor'].sum()))
        with col2:
            st.metric("Total Facturas", len(df))
        with col3:
            st.metric("Ticket Promedio", format_currency(df['valor'].mean()))
        with col4:
            st.metric("Total Comisiones", format_currency(df['comision'].sum()))
        
        st.markdown("---")
        
        # Gráfico de tendencia
        import plotly.express as px
        fig = px.line(
            ventas_diarias,
            x='Fecha',
            y='Total Ventas',
            title='Tendencia de Ventas Diarias',
            labels={'Total Ventas': 'Ventas ($)', 'Fecha': 'Fecha'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Detalle de Ventas")
        ventas_diarias['Total Ventas'] = ventas_diarias['Total Ventas'].apply(format_currency)
        ventas_diarias['Total Comisiones'] = ventas_diarias['Total Comisiones'].apply(format_currency)
        st.dataframe(ventas_diarias, use_container_width=True, hide_index=True)
        
        # Exportar
        self._boton_exportar_reporte(ventas_diarias, f"ventas_{fecha_inicio}_{fecha_fin}")
    
    def _generar_reporte_comisiones(self, df: pd.DataFrame, fecha_inicio, fecha_fin):
        """Reporte de comisiones por vendedor"""
        st.markdown("### 💰 Reporte de Comisiones por Vendedor")
        
        # Agrupar por vendedor
        if 'vendedor' not in df.columns:
            st.warning("No hay información de vendedor en los datos")
            return
        
        comisiones_vendedor = df.groupby('vendedor').agg({
            'valor': 'sum',
            'comision': 'sum',
            'factura': 'count'
        }).reset_index()
        comisiones_vendedor.columns = ['Vendedor', 'Total Ventas', 'Total Comisiones', 'Número Facturas']
        comisiones_vendedor = comisiones_vendedor.sort_values('Total Comisiones', ascending=False)
        comisiones_vendedor['% del Total'] = (comisiones_vendedor['Total Comisiones'] / comisiones_vendedor['Total Comisiones'].sum() * 100).round(2)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Comisiones", format_currency(df['comision'].sum()))
        with col2:
            st.metric("Vendedores Activos", len(comisiones_vendedor))
        with col3:
            st.metric("Comisión Promedio", format_currency(df['comision'].mean()))
        
        st.markdown("---")
        
        # Gráfico de barras
        import plotly.express as px
        fig = px.bar(
            comisiones_vendedor,
            x='Vendedor',
            y='Total Comisiones',
            title='Comisiones por Vendedor',
            labels={'Total Comisiones': 'Comisiones ($)', 'Vendedor': 'Vendedor'}
        )
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Detalle de Comisiones")
        comisiones_display = comisiones_vendedor.copy()
        comisiones_display['Total Ventas'] = comisiones_display['Total Ventas'].apply(format_currency)
        comisiones_display['Total Comisiones'] = comisiones_display['Total Comisiones'].apply(format_currency)
        comisiones_display['% del Total'] = comisiones_display['% del Total'].apply(lambda x: f"{x}%")
        st.dataframe(comisiones_display, use_container_width=True, hide_index=True)
        
        # Exportar
        self._boton_exportar_reporte(comisiones_vendedor, f"comisiones_vendedor_{fecha_inicio}_{fecha_fin}")
    
    def _generar_reporte_productos(self, df: pd.DataFrame, fecha_inicio, fecha_fin):
        """Reporte de productos más vendidos"""
        st.markdown("### 📦 Reporte de Productos Más Vendidos")
        
        # Obtener datos de compras
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            compras_response = clientes_manager.supabase.table("compras_clientes").select(
                "cod_articulo, detalle, marca, grupo, total, cantidad, fecha, es_devolucion"
            ).eq("es_devolucion", False).gte("fecha", fecha_inicio.isoformat()).lte("fecha", fecha_fin.isoformat()).execute()
            
            if not compras_response.data:
                st.info("No hay datos de compras en el período seleccionado")
                return
            
            df_compras = pd.DataFrame(compras_response.data)
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
            
            # Agrupar por producto
            productos_stats = df_compras.groupby(['cod_articulo', 'detalle', 'marca', 'grupo']).agg({
                'total': 'sum',
                'cantidad': 'sum',
                'fecha': 'count'
            }).reset_index()
            productos_stats.columns = ['Código', 'Producto', 'Marca', 'Grupo', 'Total Vendido', 'Cantidad Total', 'Veces Vendido']
            productos_stats = productos_stats.sort_values('Total Vendido', ascending=False).head(50)
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Productos Vendidos", len(productos_stats))
            with col2:
                st.metric("Total Vendido", format_currency(productos_stats['Total Vendido'].sum()))
            with col3:
                st.metric("Cantidad Total", int(productos_stats['Cantidad Total'].sum()))
            
            st.markdown("---")
            st.markdown("### Top 50 Productos")
            productos_display = productos_stats.copy()
            productos_display['Total Vendido'] = productos_display['Total Vendido'].apply(format_currency)
            st.dataframe(productos_display, use_container_width=True, hide_index=True)
            
            # Exportar
            self._boton_exportar_reporte(productos_stats, f"productos_vendidos_{fecha_inicio}_{fecha_fin}")
        
        except Exception as e:
            st.error(f"Error obteniendo datos de productos: {str(e)}")
    
    def _generar_reporte_clientes_ciudad(self, df: pd.DataFrame, fecha_inicio, fecha_fin):
        """Reporte de clientes por ciudad"""
        st.markdown("### 🌍 Reporte de Clientes por Ciudad")
        
        # Obtener información de ciudades desde clientes B2B
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("nit, nombre, ciudad").execute()
            
            if not clientes_b2b_response.data:
                st.info("No hay datos de clientes B2B disponibles")
                return
            
            df_clientes_b2b = pd.DataFrame(clientes_b2b_response.data)
            
            # Agrupar ventas por cliente
            ventas_cliente = df.groupby('cliente').agg({
                'valor': 'sum',
                'factura': 'count'
            }).reset_index()
            ventas_cliente.columns = ['cliente', 'total_ventas', 'num_facturas']
            
            # Unir con información de ciudades
            df_merge = ventas_cliente.merge(
                df_clientes_b2b,
                left_on='cliente',
                right_on='nombre',
                how='left'
            )
            
            # Agrupar por ciudad
            clientes_ciudad = df_merge.groupby('ciudad').agg({
                'total_ventas': 'sum',
                'num_facturas': 'sum',
                'cliente': 'nunique'
            }).reset_index()
            clientes_ciudad.columns = ['Ciudad', 'Total Ventas', 'Número Facturas', 'Clientes Únicos']
            clientes_ciudad = clientes_ciudad.sort_values('Total Ventas', ascending=False)
            clientes_ciudad['% del Total'] = (clientes_ciudad['Total Ventas'] / clientes_ciudad['Total Ventas'].sum() * 100).round(2)
            
            # Métricas
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Ciudades", len(clientes_ciudad))
            with col2:
                st.metric("Total Ventas", format_currency(clientes_ciudad['Total Ventas'].sum()))
            with col3:
                st.metric("Total Clientes", int(clientes_ciudad['Clientes Únicos'].sum()))
            
            st.markdown("---")
            
            # Gráfico
            import plotly.express as px
            fig = px.bar(
                clientes_ciudad.head(20),
                x='Ciudad',
                y='Total Ventas',
                title='Ventas por Ciudad (Top 20)',
                labels={'Total Ventas': 'Ventas ($)', 'Ciudad': 'Ciudad'}
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### Detalle por Ciudad")
            clientes_display = clientes_ciudad.copy()
            clientes_display['Total Ventas'] = clientes_display['Total Ventas'].apply(format_currency)
            clientes_display['% del Total'] = clientes_display['% del Total'].apply(lambda x: f"{x}%")
            st.dataframe(clientes_display, use_container_width=True, hide_index=True)
            
            # Exportar
            self._boton_exportar_reporte(clientes_ciudad, f"clientes_ciudad_{fecha_inicio}_{fecha_fin}")
        
        except Exception as e:
            st.error(f"Error generando reporte de ciudades: {str(e)}")
    
    def _generar_reporte_credito(self, df: pd.DataFrame, fecha_inicio, fecha_fin):
        """Reporte de análisis de crédito"""
        st.markdown("### 💳 Reporte de Análisis de Crédito")
        
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("*").eq("activo", True).execute()
            
            if not clientes_b2b_response.data:
                st.info("No hay clientes B2B activos disponibles")
                return
            
            df_clientes_b2b = pd.DataFrame(clientes_b2b_response.data)
            
            # Calcular uso de crédito para cada cliente
            analisis_credito = []
            for _, cliente in df_clientes_b2b.iterrows():
                nombre_cliente = cliente['nombre']
                nit_cliente = cliente['nit']
                
                # Obtener facturas pendientes del cliente
                df_cliente = df[df['cliente'] == nombre_cliente]
                facturas_pendientes = df_cliente[df_cliente['pagado'] == False]
                
                # Calcular cupo utilizado (suma de facturas pendientes)
                cupo_utilizado_calc = facturas_pendientes['valor_neto'].sum() if 'valor_neto' in facturas_pendientes.columns else facturas_pendientes['valor'].sum() / 1.19
                cupo_total = cliente.get('cupo_total', 0) or 0
                cupo_disponible = cupo_total - cupo_utilizado_calc
                porcentaje_uso = (cupo_utilizado_calc / cupo_total * 100) if cupo_total > 0 else 0
                
                analisis_credito.append({
                    'Cliente': nombre_cliente,
                    'NIT': nit_cliente,
                    'Ciudad': cliente.get('ciudad', 'N/A'),
                    'Cupo Total': cupo_total,
                    'Cupo Utilizado': cupo_utilizado_calc,
                    'Cupo Disponible': cupo_disponible,
                    '% Uso': porcentaje_uso,
                    'Facturas Pendientes': len(facturas_pendientes),
                    'Valor Pendiente': facturas_pendientes['valor'].sum() if not facturas_pendientes.empty else 0
                })
            
            df_analisis = pd.DataFrame(analisis_credito)
            df_analisis = df_analisis.sort_values('% Uso', ascending=False)
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Clientes", len(df_analisis))
            with col2:
                st.metric("Cupo Total Asignado", format_currency(df_analisis['Cupo Total'].sum()))
            with col3:
                st.metric("Cupo Utilizado", format_currency(df_analisis['Cupo Utilizado'].sum()))
            with col4:
                alto_riesgo = len(df_analisis[df_analisis['% Uso'] > 80])
                st.metric("Alto Riesgo (>80%)", alto_riesgo, delta=f"{alto_riesgo} clientes")
            
            st.markdown("---")
            
            # Clasificar por nivel de riesgo
            df_analisis['Nivel Riesgo'] = df_analisis['% Uso'].apply(
                lambda x: 'Alto' if x > 80 else ('Medio' if x > 50 else 'Bajo')
            )
            
            st.markdown("### Análisis por Nivel de Riesgo")
            riesgo_stats = df_analisis.groupby('Nivel Riesgo').agg({
                'Cliente': 'count',
                'Cupo Total': 'sum',
                'Cupo Utilizado': 'sum'
            }).reset_index()
            riesgo_stats.columns = ['Nivel Riesgo', 'Número Clientes', 'Cupo Total', 'Cupo Utilizado']
            riesgo_stats['Cupo Total'] = riesgo_stats['Cupo Total'].apply(format_currency)
            riesgo_stats['Cupo Utilizado'] = riesgo_stats['Cupo Utilizado'].apply(format_currency)
            st.dataframe(riesgo_stats, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("### Detalle de Clientes")
            df_display = df_analisis.copy()
            df_display['Cupo Total'] = df_display['Cupo Total'].apply(format_currency)
            df_display['Cupo Utilizado'] = df_display['Cupo Utilizado'].apply(format_currency)
            df_display['Cupo Disponible'] = df_display['Cupo Disponible'].apply(format_currency)
            df_display['Valor Pendiente'] = df_display['Valor Pendiente'].apply(format_currency)
            df_display['% Uso'] = df_display['% Uso'].apply(lambda x: f"{x:.2f}%")
            st.dataframe(df_display[['Cliente', 'Ciudad', 'Cupo Total', 'Cupo Utilizado', 'Cupo Disponible', '% Uso', 'Facturas Pendientes', 'Valor Pendiente', 'Nivel Riesgo']], use_container_width=True, hide_index=True)
            
            # Exportar
            self._boton_exportar_reporte(df_analisis, f"analisis_credito_{fecha_inicio}_{fecha_fin}")
        
        except Exception as e:
            st.error(f"Error generando reporte de crédito: {str(e)}")
            import traceback
            with st.expander("Detalles del error"):
                st.code(traceback.format_exc())
    
    def _render_exportacion_datos(self):
        """Exportación de datos con filtros y configuración de columnas"""
        st.markdown("### Exportación de Datos")
        st.caption("Exporta datos filtrados a Excel o CSV")
        
        tipo_dato = st.selectbox(
            "Tipo de Datos a Exportar",
            [
                "Facturas/Comisiones",
                "Clientes B2B",
                "Compras de Clientes",
                "Productos del Catálogo"
            ],
            key="tipo_dato_exportar"
        )
        
        st.markdown("---")
        
        try:
            if tipo_dato == "Facturas/Comisiones":
                self._exportar_facturas()
            elif tipo_dato == "Clientes B2B":
                self._exportar_clientes()
            elif tipo_dato == "Compras de Clientes":
                self._exportar_compras()
            elif tipo_dato == "Productos del Catálogo":
                self._exportar_catalogo()
        
        except Exception as e:
            st.error(f"Error en exportación: {str(e)}")
    
    def _exportar_facturas(self):
        """Exportar facturas con filtros"""
        st.markdown("#### Exportar Facturas/Comisiones")
        
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            st.info("No hay datos de facturas disponibles")
            return
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha Inicio", value=df['fecha_factura'].min().date(), key="export_fecha_inicio")
        with col2:
            fecha_fin = st.date_input("Fecha Fin", value=df['fecha_factura'].max().date(), key="export_fecha_fin")
        
        # Aplicar filtros
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
        df_filtrado = df[
            (df['fecha_factura'].dt.date >= fecha_inicio) &
            (df['fecha_factura'].dt.date <= fecha_fin)
        ].copy()
        
        # Seleccionar columnas
        columnas_disponibles = list(df_filtrado.columns)
        columnas_seleccionadas = st.multiselect(
            "Seleccionar Columnas",
            options=columnas_disponibles,
            default=['pedido', 'cliente', 'factura', 'fecha_factura', 'valor', 'comision', 'pagado', 'cliente_propio'],
            key="columnas_facturas"
        )
        
        if columnas_seleccionadas:
            df_export = df_filtrado[columnas_seleccionadas]
            
            st.markdown("---")
            st.info(f"✅ {len(df_export)} registros listos para exportar")
            st.dataframe(df_export.head(10), use_container_width=True, hide_index=True)
            
            # Botones de exportación
            col1, col2 = st.columns(2)
            with col1:
                csv = df_export.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 Exportar CSV",
                    data=csv,
                    file_name=f"facturas_{fecha_inicio}_{fecha_fin}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                # Exportar a Excel
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Facturas')
                output.seek(0)
                st.download_button(
                    "📊 Exportar Excel",
                    data=output.getvalue(),
                    file_name=f"facturas_{fecha_inicio}_{fecha_fin}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    
    def _exportar_clientes(self):
        """Exportar clientes B2B"""
        st.markdown("#### Exportar Clienters B2B")
        
        try:
            clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select("*").execute()
            
            if not clientes_b2b_response.data:
                st.info("No hay clientes B2B disponibles")
                return
            
            df_clientes = pd.DataFrame(clientes_b2b_response.data)
            
            # Filtro de activos
            solo_activos = st.checkbox("Solo Clientes Activos", value=True, key="solo_activos_export")
            if solo_activos:
                df_clientes = df_clientes[df_clientes.get('activo', True) == True]
            
            st.info(f"✅ {len(df_clientes)} clientes listos para exportar")
            st.dataframe(df_clientes.head(10), use_container_width=True, hide_index=True)
            
            # Botones de exportación
            col1, col2 = st.columns(2)
            with col1:
                csv = df_clientes.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    "📥 Exportar CSV",
                    data=csv,
                    file_name=f"clientes_b2b_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            with col2:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df_clientes.to_excel(writer, index=False, sheet_name='Clientes')
                output.seek(0)
                st.download_button(
                    "📊 Exportar Excel",
                    data=output.getvalue(),
                    file_name=f"clientes_b2b_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        
        except Exception as e:
            st.error(f"Error exportando clientes: {str(e)}")
    
    def _exportar_compras(self):
        """Exportar compras de clientes"""
        st.markdown("#### Exportar Compras de Clientes")
        st.info("Esta funcionalidad exportará todas las compras detalladas de clientes")
        # Implementación similar a _exportar_clientes
        st.write("Funcionalidad en desarrollo - próximamente disponible")
    
    def _exportar_catalogo(self):
        """Exportar catálogo de productos"""
        st.markdown("#### Exportar Catálogo de Productos")
        
        df_catalogo = self.catalog_manager.cargar_catalogo()
        
        if df_catalogo.empty:
            st.info("No hay productos en el catálogo")
            return
        
        st.info(f"✅ {len(df_catalogo)} productos listos para exportar")
        st.dataframe(df_catalogo.head(10), use_container_width=True, hide_index=True)
        
        # Botones de exportación
        col1, col2 = st.columns(2)
        with col1:
            csv = df_catalogo.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 Exportar CSV",
                data=csv,
                file_name=f"catalogo_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with col2:
            from io import BytesIO
            output = BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_catalogo.to_excel(writer, index=False, sheet_name='Catálogo')
            output.seek(0)
            st.download_button(
                "📊 Exportar Excel",
                data=output.getvalue(),
                file_name=f"catalogo_{pd.Timestamp.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    def _boton_exportar_reporte(self, df: pd.DataFrame, nombre_base: str):
        """Botón genérico para exportar reportes"""
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            csv = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📥 Exportar a CSV",
                data=csv,
                file_name=f"{nombre_base}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            try:
                from io import BytesIO
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Reporte')
                output.seek(0)
                st.download_button(
                    "📊 Exportar a Excel",
                    data=output.getvalue(),
                    file_name=f"{nombre_base}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except ImportError:
                st.info("Excel export requiere la librería 'openpyxl'. Instálala con: pip install openpyxl")
    
    # ========================
    # TAB DASHBOARD EJECUTIVO
    # ========================
    
    def render_executive_dashboard(self):
        """Renderiza el Dashboard Ejecutivo Profesional para Gerencia"""
        # Limpiar flags de procesamiento
        self._clear_processing_flags()
        
        try:
            from ui.theme_manager import ThemeManager
            
            theme = ThemeManager.get_theme()
            
            # Título personalizado - Mismo estilo que Panel del Vendedor
            st.markdown(
                f"""
                <div style='margin-bottom: 2rem;'>
                    <h1 style='
                        font-size: 2.5rem;
                        font-weight: 800;
                        color: {theme['text_primary']};
                        margin-bottom: 0.5rem;
                    '>
                        Dashboard Ejecutivo
                    </h1>
                    <p style='color: {theme['text_secondary']}; font-size: 1rem; margin: 0;'>
                        Vista Ejecutiva · KPIs · Tendencias · Análisis de Riesgo
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Obtener resumen ejecutivo
            with st.spinner("Cargando dashboard ejecutivo..."):
                summary = self.executive_dashboard.get_executive_summary()
            
            # ========== SECCIÓN 1: KPIs FINANCIEROS ==========
            st.markdown("---")
            ExecutiveComponents.render_executive_kpi_grid(
                {**summary['kpis_financieros'], **summary['proyecciones']}
            )
            
            # ========== SECCIÓN 2: KPIs OPERACIONALES ==========
            st.markdown("---")
            ExecutiveComponents.render_operational_kpis(summary['kpis_operacionales'])
            
            # ========== SECCIÓN 3: TENDENCIAS Y MIX DE CLIENTES ==========
            st.markdown("---")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### 📈 Tendencia Mensual (Últimos 6 Meses)")
                ExecutiveComponents.render_trend_chart(summary['tendencias']['monthly_trend'])
                
                tendencias = summary['tendencias']
                growth = tendencias.get('growth_rate', 0)
                context = tendencias.get('growth_context')
                context = tendencias.get('growth_context')
                if growth != 0:
                    mensaje = (
                        f"📈 Crecimiento de {growth:.1f}%" if growth > 0
                        else f"📉 Decrecimiento de {abs(growth):.1f}%"
                    )
                    referencia = context['descripcion_base'] if context else "el período anterior"
                    mensaje = f"{mensaje} respecto a {referencia}"
                    st.info(mensaje)
            
            with col2:
                st.markdown("### 🎯 Mix de Clientes")
                ExecutiveComponents.render_client_mix(summary['comparativas'])
            
            # Comparativo MTD y proyección a meta
            mtd_summary = summary['kpis_financieros'].get('mtd_summary', {})
            if mtd_summary:
                st.markdown("---")
                st.markdown("### 🔍 Comparativo MTD y Meta")

                ventas_actual = mtd_summary.get('ventas_actual', 0)
                ventas_base = mtd_summary.get('ventas_base', 0)
                ventas_change = mtd_summary.get('ventas_change', 0)
                facturas_emitidas_actual = mtd_summary.get('facturas_emitidas_actual', 0)
                facturas_emitidas_base = mtd_summary.get('facturas_emitidas_base', 0)
                facturas_emitidas_change = mtd_summary.get('facturas_emitidas_change', 0)
                ticket_venta_actual = mtd_summary.get('ticket_venta_actual', 0)
                ticket_venta_base = mtd_summary.get('ticket_venta_base', 0)
                ticket_venta_change = mtd_summary.get('ticket_venta_change', 0)
                ingresos_actual = mtd_summary.get('ingresos_actual', 0)
                ingresos_base = mtd_summary.get('ingresos_base', 0)
                ingresos_change = mtd_summary.get('ingresos_change', 0)
                facturas_cobradas_actual = mtd_summary.get('facturas_cobradas_actual', 0)
                facturas_cobradas_base = mtd_summary.get('facturas_cobradas_base', 0)
                facturas_cobradas_change = mtd_summary.get('facturas_cobradas_change', 0)
                ticket_cobrado_actual = mtd_summary.get('ticket_cobrado_actual', 0)
                ticket_cobrado_base = mtd_summary.get('ticket_cobrado_base', 0)
                ticket_cobrado_change = mtd_summary.get('ticket_cobrado_change', 0)
                promedio_diario_ventas_actual = mtd_summary.get('promedio_diario_ventas_actual', 0)
                promedio_diario_ventas_necesario = mtd_summary.get('promedio_diario_ventas_necesario', 0)
                facturas_emitidas_diarias = mtd_summary.get('facturas_emitidas_diarias', 0)
                ticket_requerido = mtd_summary.get('ticket_requerido_restante', 0)
                proyeccion_ventas = mtd_summary.get('proyeccion_ventas_fin_mes', 0)
                dias_transcurridos = mtd_summary.get('dias_transcurridos', 0)
                dias_restantes = mtd_summary.get('dias_restantes', 0)
                meta_ventas = mtd_summary.get('meta_ventas', 0)
                faltante_meta = mtd_summary.get('faltante_meta', 0)

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(
                        "Ventas MTD (clientes propios)",
                        format_currency(ventas_actual),
                        delta=f"{ventas_change:+.1f}%"
                    )
                with col2:
                    st.metric(
                        "Facturas emitidas MTD",
                        str(facturas_emitidas_actual),
                        delta=f"{facturas_emitidas_change:+.1f}%"
                    )
                with col3:
                    st.metric(
                        "Ticket promedio (ventas)",
                        format_currency(ticket_venta_actual),
                        delta=f"{ticket_venta_change:+.1f}%"
                    )

                col4, col5, col6 = st.columns(3)
                with col4:
                    st.metric("Meta mensual", format_currency(meta_ventas))
                with col5:
                    st.metric("Falta para meta", format_currency(faltante_meta if faltante_meta > 0 else 0))
                with col6:
                    st.metric("Promedio diario necesario (ventas)", format_currency(promedio_diario_ventas_necesario))

                col7, col8, col9 = st.columns(3)
                with col7:
                    st.metric("Promedio diario actual (ventas)", format_currency(promedio_diario_ventas_actual))
                with col8:
                    st.metric("Facturas emitidas/día", f"{facturas_emitidas_diarias:.2f}")
                with col9:
                    st.metric("Ticket requerido restante", format_currency(ticket_requerido))

                st.caption(
                    f"Referencia mes anterior: {format_currency(ventas_base)} con {facturas_emitidas_base} facturas emitidas. "
                    f"Días comparados: {dias_transcurridos}. Días restantes: {dias_restantes}."
                )

                if meta_ventas > 0:
                    if proyeccion_ventas >= meta_ventas:
                        st.success(
                            "\n".join(
                                [
                                    f"**Proyección con ticket actual:** {format_currency(proyeccion_ventas)}",
                                    f"**Exceso sobre la meta:** {format_currency(proyeccion_ventas - meta_ventas)}",
                                ]
                            )
                        )
                    else:
                        deficit = meta_ventas - proyeccion_ventas
                        st.warning(
                            "\n".join(
                                [
                                    f"**Proyección con ticket actual:** {format_currency(proyeccion_ventas)}",
                                    f"**Faltante vs meta:** {format_currency(deficit)}",
                                    f"**Ticket promedio requerido:** {format_currency(ticket_requerido)}",
                                    "Incrementa el ticket promedio o el volumen de facturas diarias para alcanzar la meta.",
                                ]
                            )
                        )

                st.markdown("#### 💵 Cobros (solo referencia)")
                col10, col11, col12 = st.columns(3)
                with col10:
                    st.metric(
                        "Ingresos cobrados MTD",
                        format_currency(ingresos_actual),
                        delta=f"{ingresos_change:+.1f}%"
                    )
                with col11:
                    st.metric(
                        "Facturas cobradas MTD",
                        str(facturas_cobradas_actual),
                        delta=f"{facturas_cobradas_change:+.1f}%"
                    )
                with col12:
                    st.metric(
                        "Ticket promedio cobrado",
                        format_currency(ticket_cobrado_actual),
                        delta=f"{ticket_cobrado_change:+.1f}%"
                    )

            # ========== SECCIÓN 4: ANÁLISIS DE RIESGO ==========
            st.markdown("---")
            ExecutiveComponents.render_risk_panel(summary['analisis_riesgo'])
            
            # ========== SECCIÓN 5: PROYECCIONES ==========
            st.markdown("---")
            st.markdown("### 🔮 Proyecciones Fin de Mes")
            
            proyecciones = summary['proyecciones']
            
            if proyecciones:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Revenue Proyectado",
                        format_currency(proyecciones.get('proyeccion_revenue', 0)),
                        help=f"Basado en {proyecciones.get('dias_transcurridos', 0)} días de datos"
                    )
                
                with col2:
                    st.metric(
                        "Comisión Proyectada",
                        format_currency(proyecciones.get('proyeccion_comision', 0)),
                        help=f"Confianza: {proyecciones.get('confianza', 'N/A').upper()}"
                    )
                
                with col3:
                    dias_restantes = proyecciones.get('dias_restantes', 0)
                    st.metric(
                        "Días Restantes",
                        dias_restantes,
                        help=f"De {proyecciones.get('dias_mes', 0)} días del mes"
                    )
                
                # Barra de progreso del mes
                dias_transcurridos = proyecciones.get('dias_transcurridos', 0)
                dias_mes = proyecciones.get('dias_mes', 30)
                progreso_mes = (dias_transcurridos / dias_mes * 100) if dias_mes > 0 else 0
                
                st.markdown("#### Progreso del Mes")
                st.progress(progreso_mes / 100)
                st.caption(f"Día {dias_transcurridos} de {dias_mes} ({progreso_mes:.1f}%)")
            
            # ========== FOOTER CON TIMESTAMP ==========
            st.markdown("---")
            st.caption(f"📅 Actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        except Exception as e:
            st.error(f"❌ Error al cargar el dashboard ejecutivo: {str(e)}")
            st.info("Por favor, intenta recargar la página.")
            import traceback
            with st.expander("Detalles técnicos del error"):
                st.code(traceback.format_exc())
    
    # ========================
    # TAB DASHBOARD
    # ========================
    
    def render_dashboard(self):
        """Renderiza la pestaña del dashboard con diseño mejorado"""
        from ui.theme_manager import ThemeManager
        
        theme = ThemeManager.get_theme()
        
        # Título personalizado mejorado
        ExecutiveComponents.render_page_header(
            "📈 Dashboard General",
            "Visión Operativa · KPIs · Análisis de Negocio"
        )
        
        df = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        if not df.empty:
            df = self.db_manager.agregar_campos_faltantes(df)
            
            # Aplicar filtro de mes si está seleccionado
            mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
            if mes_filter != "Todos":
                df = df[df["mes_factura"] == mes_filter]
                st.info(f"📅 Mostrando datos de: {mes_filter}")
        
        if not df.empty:
            metricas = self.metrics_calc.calcular_metricas_separadas(df)
            facturas_pendientes = len(df[df["pagado"] == False])
        else:
            metricas = self.metrics_calc.calcular_metricas_separadas(pd.DataFrame())
            facturas_pendientes = 0
        
        # ========== SECCIÓN 1: KPIs PRINCIPALES (Diseño Mejorado) ==========
        st.markdown("---")
        st.markdown("### 💰 KPIs Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        total_comisiones = metricas["comision_propios"] + metricas["comision_externos"]
        
        with col1:
            ExecutiveComponents._render_executive_metric(
                "Ventas Meta (Propios)",
                format_currency(metricas["ventas_propios"]),
                None,
                "🎯",
                theme['gradient_1']
            )
        
        with col2:
            ExecutiveComponents._render_executive_metric(
                "Comisión Total",
                format_currency(total_comisiones),
                None,
                "💰",
                theme['gradient_2']
            )
        
        with col3:
            ExecutiveComponents._render_executive_metric(
                "Facturas Pendientes",
                str(facturas_pendientes),
                None,
                "📋",
                theme['gradient_3']
            )
        
        with col4:
            ExecutiveComponents._render_executive_metric(
                "% Clientes Propios",
                f"{metricas['porcentaje_propios']:.1f}%",
                None,
                "👥",
                theme['gradient_4']
            )
        
        # ========== SECCIÓN 2: DESGLOSE POR TIPO DE CLIENTE (Diseño Integrado) ==========
        st.markdown("---")
        st.markdown("### 📊 Desglose por Tipo de Cliente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Card completo integrado
            ventas_propios = format_currency(metricas["ventas_propios"])
            comision_propios = format_currency(metricas["comision_propios"])
            facturas_propios = str(metricas["facturas_propios"])
            
            st.markdown(
                f"""<div style="background: {theme['surface']}; border-radius: 16px; padding: 24px; border-left: 4px solid {theme['primary']}; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 0;">
                    <h3 style="margin: 0 0 24px 0; color: {theme['text_primary']}; font-size: 1.2rem; font-weight: 700;">🎯 Clientes Propios (Para Meta)</h3>
                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        <div style="padding: 16px; background: rgba(99, 102, 241, 0.1); border-radius: 12px; border-left: 3px solid {theme['primary']};">
                            <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_secondary']}; font-weight: 600;">💵 VENTAS</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: {theme['text_primary']};">{ventas_propios}</p>
                        </div>
                        <div style="padding: 16px; background: rgba(16, 185, 129, 0.1); border-radius: 12px; border-left: 3px solid #10b981;">
                            <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_secondary']}; font-weight: 600;">💎 COMISIÓN</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: {theme['text_primary']};">{comision_propios}</p>
                        </div>
                        <div style="padding: 16px; background: rgba(148, 163, 184, 0.1); border-radius: 12px; border-left: 3px solid #94a3b8;">
                            <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_secondary']}; font-weight: 600;">📄 FACTURAS</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: {theme['text_primary']};">{facturas_propios}</p>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True
            )
        
        with col2:
            # Card completo integrado
            ventas_externos = format_currency(metricas["ventas_externos"])
            comision_externos = format_currency(metricas["comision_externos"])
            facturas_externos = str(metricas["facturas_externos"])
            
            st.markdown(
                f"""<div style="background: {theme['surface']}; border-radius: 16px; padding: 24px; border-left: 4px solid {theme['secondary']}; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 0;">
                    <h3 style="margin: 0 0 24px 0; color: {theme['text_primary']}; font-size: 1.2rem; font-weight: 700;">🌐 Clientes Externos (Solo Comisión)</h3>
                    <div style="display: flex; flex-direction: column; gap: 16px;">
                        <div style="padding: 16px; background: rgba(34, 197, 94, 0.1); border-radius: 12px; border-left: 3px solid #22c55e;">
                            <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_secondary']}; font-weight: 600;">💵 VENTAS</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: {theme['text_primary']};">{ventas_externos}</p>
                        </div>
                        <div style="padding: 16px; background: rgba(139, 92, 246, 0.1); border-radius: 12px; border-left: 3px solid #8b5cf6;">
                            <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_secondary']}; font-weight: 600;">💎 COMISIÓN</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: {theme['text_primary']};">{comision_externos}</p>
                        </div>
                        <div style="padding: 16px; background: rgba(148, 163, 184, 0.1); border-radius: 12px; border-left: 3px solid #94a3b8;">
                            <p style="margin: 0 0 8px 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_secondary']}; font-weight: 600;">📄 FACTURAS</p>
                            <p style="margin: 0; font-size: 24px; font-weight: 700; color: {theme['text_primary']};">{facturas_externos}</p>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True
            )
        
        st.markdown("---")
        
        # Contenedor principal para alinear todo
        with st.container():
            # Progreso Meta y Recomendaciones IA
            col1, col2 = st.columns([1, 1])
            
            with col1:
                self._render_progreso_meta(df, meta_actual)
            
            with col2:
                self._render_progreso_clientes_nuevos(df, meta_actual)
            
            # Recomendaciones motivacionales - Mismo ancho que las columnas de arriba
            self._render_recomendaciones_motivacionales(df, meta_actual)
    
    def _render_progreso_meta(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza el progreso de la meta mensual con estilo moderno"""
        from ui.theme_manager import ThemeManager
        
        theme = ThemeManager.get_theme()
        
        progreso_data = self.metrics_calc.calcular_progreso_meta(df, meta_actual)
        
        meta = progreso_data["meta_ventas"]
        actual = progreso_data["ventas_actuales"]
        progreso_meta = progreso_data["progreso"]
        faltante = progreso_data["faltante"]
        
        # Calcular días restantes del mes
        hoy = date.today()
        if hoy.month == 12:
            ultimo_dia_mes = date(hoy.year, 12, 31)
        else:
            ultimo_dia_mes = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
        
        dias_restantes = max(1, (ultimo_dia_mes - hoy).days + 1)
        velocidad_necesaria = faltante / dias_restantes if dias_restantes > 0 else 0
        
        # Header con estilo moderno
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border-radius: 16px;
                padding: 20px;
                border-left: 4px solid {theme['primary']};
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            '>
                <h3 style='
                    margin: 0;
                    color: {theme['text_primary']};
                    font-size: 1.2rem;
                    font-weight: 700;
                '>
                    📈 Progreso Meta Mensual
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # KPIs en cards modernos
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            ExecutiveComponents._render_executive_metric(
                "Meta",
                format_currency(meta),
                None,
                "🎯",
                theme['gradient_1']
            )
        with col_b:
            ExecutiveComponents._render_executive_metric(
                "Actual",
                format_currency(actual),
                None,
                "💰",
                theme['gradient_2']
            )
        with col_c:
            ExecutiveComponents._render_executive_metric(
                "Faltante",
                format_currency(faltante),
                None,
                "📊",
                theme['gradient_3']
            )
        
        # Barra de progreso mejorada
        color = theme['success'] if progreso_meta > 80 else theme['warning'] if progreso_meta > 50 else theme['error']
        st.markdown(f"""
        <div style='
            background: {theme['surface']};
            border-radius: 16px;
            padding: 20px;
            margin-top: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        '>
            <div class="progress-bar" style="margin: 1rem 0;">
                <div class="progress-fill" style="width: {min(progreso_meta, 100)}%; background: {color}"></div>
            </div>
            <p style='
                margin: 12px 0 0 0;
                color: {theme['text_primary']};
                font-size: 14px;
                font-weight: 600;
            '>
                <strong>{progreso_meta:.1f}%</strong> completado | <strong>Necesitas:</strong> {format_currency(velocidad_necesaria)}/día
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_progreso_clientes_nuevos(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza el progreso de la meta de clientes nuevos con estilo moderno"""
        from ui.theme_manager import ThemeManager
        
        theme = ThemeManager.get_theme()
        
        # Obtener meta de clientes nuevos
        meta_clientes = meta_actual.get("meta_clientes_nuevos", 0)
        
        # Calcular clientes nuevos del mes actual basándose en el campo cliente_nuevo
        clientes_nuevos_lista = []
        clientes_detalle = []  # Inicializar fuera del if para disponibilidad global
        if not df.empty:
            mes_actual = date.today().strftime("%Y-%m")
            
            # Filtrar por mes actual para otras métricas
            df_mes_actual = df[df["mes_factura"] == mes_actual]
            
            # Obtener año actual para la meta de clientes nuevos
            anio_actual = date.today().strftime("%Y")
            df_anio_actual = df[df["mes_factura"].str.startswith(anio_actual)]
            
            # Verificar si existe la columna cliente_nuevo
            if 'cliente_nuevo' in df.columns:
                # Contar clientes únicos marcados como nuevos DEL AÑO ACTUAL
                # (Los clientes nuevos son una meta anual, no mensual)
                df_clientes_nuevos = df_anio_actual[df_anio_actual["cliente_nuevo"] == True]
                clientes_nuevos_lista = sorted(df_clientes_nuevos["cliente"].unique().tolist())
                clientes_nuevos_mes = len(clientes_nuevos_lista)
                
                # Obtener información detallada de cada cliente (mes de factura)
                clientes_detalle = []
                for cliente in clientes_nuevos_lista:
                    facturas_cliente = df_clientes_nuevos[df_clientes_nuevos["cliente"] == cliente]
                    primer_mes = facturas_cliente["mes_factura"].min() if not facturas_cliente.empty else "N/A"
                    clientes_detalle.append({"cliente": cliente, "mes": primer_mes})
            else:
                # Fallback: usar lógica anterior si no existe el campo
                df_mes_propios = df_mes_actual[df_mes_actual["cliente_propio"] == True]
                clientes_mes_actual = set(df_mes_propios["cliente"].unique())
                
                df_meses_anteriores = df[df["mes_factura"] < mes_actual]
                clientes_anteriores = set(df_meses_anteriores["cliente"].unique())
                
                clientes_nuevos = clientes_mes_actual - clientes_anteriores
                
                # Lista de palabras clave para excluir
                palabras_excluidas = [
                    "BLANCO CAMARGO",
                    "INVERSIONES CÁRDENAS",
                    "CARDENAS PIEDRAHITA"
                ]
                
                clientes_filtrados = []
                for cliente in clientes_nuevos:
                    excluir = False
                    for palabra in palabras_excluidas:
                        if palabra.upper() in cliente.upper():
                            excluir = True
                            break
                    if not excluir:
                        clientes_filtrados.append(cliente)
                
                clientes_nuevos_lista = sorted(clientes_filtrados)
                clientes_nuevos_mes = len(clientes_nuevos_lista)
        else:
            clientes_nuevos_mes = 0
        
        # Calcular progreso
        if meta_clientes > 0:
            progreso_clientes = (clientes_nuevos_mes / meta_clientes) * 100
        else:
            progreso_clientes = 0
        
        faltante_clientes = max(0, meta_clientes - clientes_nuevos_mes)
        
        # Calcular velocidad necesaria (días restantes del mes)
        hoy = date.today()
        if hoy.month == 12:
            ultimo_dia_mes = date(hoy.year, 12, 31)
        else:
            ultimo_dia_mes = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
        
        dias_restantes = max(1, (ultimo_dia_mes - hoy).days + 1)
        
        if dias_restantes > 0 and faltante_clientes > 0:
            clientes_por_dia = faltante_clientes / dias_restantes
        else:
            clientes_por_dia = 0
        
        # Header con estilo moderno
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border-radius: 16px;
                padding: 20px;
                border-left: 4px solid {theme['secondary']};
                box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                margin-bottom: 20px;
            '>
                <h3 style='
                    margin: 0;
                    color: {theme['text_primary']};
                    font-size: 1.2rem;
                    font-weight: 700;
                '>
                    👥 Meta Clientes Nuevos (2025)
                </h3>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # KPIs en cards modernos
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            ExecutiveComponents._render_executive_metric(
                "Meta",
                f"{meta_clientes} clientes",
                None,
                "🎯",
                theme['gradient_4']
            )
        with col_b:
            ExecutiveComponents._render_executive_metric(
                "Actual",
                f"{clientes_nuevos_mes} clientes",
                None,
                "✅",
                theme['gradient_5']
            )
        with col_c:
            ExecutiveComponents._render_executive_metric(
                "Faltante",
                f"{faltante_clientes} clientes",
                None,
                "📊",
                theme['gradient_1']
            )
        
        # Barra de progreso mejorada
        color = theme['success'] if progreso_clientes > 80 else theme['warning'] if progreso_clientes > 50 else theme['error']
        st.markdown(f"""
        <div style='
            background: {theme['surface']};
            border-radius: 16px;
            padding: 20px;
            margin-top: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        '>
            <div class="progress-bar" style="margin: 1rem 0;">
                <div class="progress-fill" style="width: {min(progreso_clientes, 100)}%; background: {color}"></div>
            </div>
            <p style='
                margin: 12px 0 0 0;
                color: {theme['text_primary']};
                font-size: 14px;
                font-weight: 600;
            '>
                <strong>{progreso_clientes:.1f}%</strong> completado | <strong>Necesitas:</strong> {clientes_por_dia:.1f} clientes/día
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Mostrar lista de clientes contados con sus meses
        if clientes_nuevos_mes > 0:
            st.markdown("---")
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border-radius: 16px;
                    padding: 20px;
                    margin-top: 16px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                '>
                    <h4 style='
                        margin: 0 0 12px 0;
                        color: {theme['text_primary']};
                        font-size: 1.1rem;
                        font-weight: 700;
                    '>
                        📋 Clientes Nuevos Registrados en 2025
                    </h4>
                    <p style='
                        margin: 0 0 16px 0;
                        color: {theme['text_secondary']};
                        font-size: 0.9rem;
                    '>
                        ℹ️ Nota: Se cuentan todos los clientes nuevos del año 2025, no solo del mes actual
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Mostrar lista de clientes con sus meses en cards
            if clientes_detalle:
                # Mostrar con detalle de mes
                for detalle in clientes_detalle:
                    mes_display = detalle['mes'].replace('-', '/') if detalle['mes'] != "N/A" else "N/A"
                    st.markdown(
                        f"""
                        <div style='
                            background: {theme['surface']};
                            border-radius: 12px;
                            padding: 16px;
                            margin-bottom: 12px;
                            border-left: 3px solid {theme['primary']};
                            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                        '>
                            <p style='
                                margin: 0;
                                color: {theme['text_primary']};
                                font-size: 0.95rem;
                                font-weight: 600;
                            '>
                                • <strong>{detalle['cliente']}</strong> - Mes: {mes_display}
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            elif clientes_nuevos_lista:
                # Si no hay detalle, mostrar lista simple
                for cliente in clientes_nuevos_lista:
                    st.markdown(
                        f"""
                        <div style='
                            background: {theme['surface']};
                            border-radius: 12px;
                            padding: 16px;
                            margin-bottom: 12px;
                            border-left: 3px solid {theme['primary']};
                            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
                        '>
                            <p style='
                                margin: 0;
                                color: {theme['text_primary']};
                                font-size: 0.95rem;
                                font-weight: 600;
                            '>
                                • <strong>{cliente}</strong>
                            </p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
        else:
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border-radius: 16px;
                    padding: 20px;
                    margin-top: 16px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                '>
                    <p style='
                        margin: 0;
                        color: {theme['text_secondary']};
                        font-size: 0.95rem;
                    '>
                        📝 Aún no hay clientes nuevos registrados en 2025
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    def _render_recomendaciones_motivacionales(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza recomendaciones motivacionales basadas en el progreso"""
        
        # Calcular datos del presupuesto
        progreso_data = self.metrics_calc.calcular_progreso_meta(df, meta_actual)
        meta = progreso_data["meta_ventas"]
        actual = progreso_data["ventas_actuales"]
        faltante = progreso_data["faltante"]
        progreso = progreso_data["progreso"]
        
        # Calcular días restantes del mes
        hoy = date.today()
        if hoy.month == 12:
            ultimo_dia_mes = date(hoy.year, 12, 31)
        else:
            ultimo_dia_mes = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
        
        dias_restantes = max(1, (ultimo_dia_mes - hoy).days + 1)
        
        # Frases motivacionales según el cumplimiento de la meta
        if progreso >= 100:
            # Meta cumplida - Frases de celebración que cambian
            frases_motivacionales = [
                "🏆 ¡Eres un campeón! Tu dedicación dio sus frutos.",
                "⭐ ¡Extraordinario! Superaste todas las expectativas.",
                "🎯 ¡Perfección! Tu profesionalismo es ejemplar.",
                "💫 ¡Imparable! Has elevado el estándar de excelencia.",
                "🌟 ¡Brillante! Tu éxito inspira a todos.",
                "🚀 ¡A otro nivel! Tu potencial no tiene límites.",
                "💎 ¡Valioso! Has demostrado tu verdadero poder.",
                "🎊 ¡Victoria merecida! Disfruta tu logro.",
                "🏅 ¡Medallista de oro! Tu esfuerzo vale oro.",
                "🌈 ¡Llegaste al tesoro! El éxito es tuyo.",
                "🔥 ¡Imparable! Tu pasión te llevó a la cima.",
                "💪 ¡Fuerza titánica! Nada puede detenerte.",
                "🎨 ¡Obra maestra! Tu trabajo es arte puro.",
                "🦅 ¡Vuelo perfecto! Alcanzaste las alturas."
            ]
        elif progreso >= 80:
            # Muy cerca - Frases de último empujón que cambian
            frases_motivacionales = [
                "💪 ¡Casi lo logras! Un último empujón y es tuyo.",
                "🎯 ¡A un paso! La meta está tan cerca.",
                "🔥 ¡Último tramo! Dale todo lo que tienes.",
                "🚀 ¡Sprint final! Acelera hacia la victoria.",
                "⭐ ¡Tan cerca! Puedes lograrlo.",
                "🏃 ¡Último esfuerzo! Cruza la línea de meta.",
                "💫 ¡La cima te espera! Solo un poco más.",
                "🎊 ¡Casi celebramos! Termina con fuerza.",
                "🌟 ¡Gran trayectoria! El final será épico.",
                "💎 ¡Casi pulido! Último toque brillante."
            ]
        elif progreso >= 50:
            # A mitad - Frases de motivación que cambian
            frases_motivacionales = [
                "💪 ¡Vas bien! Mantén el ritmo ganador.",
                "🎯 ¡Mitad del camino! Sigue avanzando firme.",
                "🚀 ¡Buen progreso! Acelera el paso ahora.",
                "⭐ ¡Vas por buen camino! No pares.",
                "🔥 ¡Encendido! Mantén viva tu pasión.",
                "🌟 ¡Brillando! Continúa iluminando el camino.",
                "💫 ¡Firme! Cada día te acerca más.",
                "🏃 ¡Buen ritmo! La meta se acerca.",
                "💎 ¡Valor creciente! Sigues puliéndote."
            ]
        else:
            # Inicio - Frases de ánimo que cambian
            frases_motivacionales = [
                "💪 ¡Tú puedes! Cada gran logro comienza ahora.",
                "🎯 ¡Enfócate! La constancia vence todo.",
                "🔥 ¡Enciéndete! El éxito requiere acción.",
                "🚀 ¡Despega! Tu potencial es enorme.",
                "⭐ ¡Brilla! Este es tu momento.",
                "💫 ¡Persiste! Los logros toman tiempo.",
                "🌟 ¡Adelante! Cada esfuerzo suma.",
                "🏃 ¡Acelera! El tiempo es ahora.",
                "💎 ¡Eres valioso! Demuéstralo hoy.",
                "🦅 ¡Levántate! Vuela contra el viento.",
                "🌺 ¡Florece! Incluso en lo difícil creces."
            ]
        
        # Seleccionar frase del día (basada en el día del mes, ajustada al tamaño de la lista)
        indice_frase = hoy.day % len(frases_motivacionales)
        frase_del_dia = frases_motivacionales[indice_frase]
        
        # Tarjeta motivacional - Ancho completo con estilo moderno
        from ui.theme_manager import ThemeManager
        
        theme = ThemeManager.get_theme()
        st.markdown("---")
        
        # Preparar variables según el progreso
        if progreso >= 100:
            emoji_titulo = "🎉"
            titulo = "¡META CUMPLIDA!"
            color_border = theme['success']
            color_bg = "rgba(16, 185, 129, 0.15)"
            mensaje_principal = f"¡Felicitaciones! Has superado la meta del mes con <strong>{format_currency(actual)}</strong>. ¡Excelente trabajo! 🏆"
            plan_accion = ""
        elif progreso >= 80:
            venta_necesaria_por_dia = faltante / dias_restantes
            dias_para_meta = int(faltante / venta_necesaria_por_dia) if venta_necesaria_por_dia > 0 else 0
            emoji_titulo = "🎯"
            titulo = "¡Casi lo logras!"
            color_border = theme['info']
            color_bg = "rgba(59, 130, 246, 0.15)"
            mensaje_principal = f"<strong>Te falta:</strong> {format_currency(faltante)} para cumplir la meta"
            plan_accion_items = [
                f"Si vendes <strong>{format_currency(venta_necesaria_por_dia)}</strong> diarios, cumplirás la meta en <strong>{dias_para_meta} días</strong> 📈",
                f"Tienes <strong>{dias_restantes} días</strong> para cerrar este mes con éxito",
                f"Estás en el <strong>{progreso:.1f}%</strong> - ¡Un último empujón! 💪"
            ]
        elif progreso >= 50:
            venta_necesaria_por_dia = faltante / dias_restantes
            emoji_titulo = "💼"
            titulo = "¡Vas por buen camino!"
            color_border = theme['warning']
            color_bg = "rgba(245, 158, 11, 0.15)"
            mensaje_principal = f"<strong>Te falta:</strong> {format_currency(faltante)} para cumplir la meta"
            plan_accion_items = [
                f"Necesitas vender <strong>{format_currency(venta_necesaria_por_dia)}</strong> por día",
                f"Quedan <strong>{dias_restantes} días</strong> para alcanzar la meta",
                f"Llevas <strong>{progreso:.1f}%</strong> completado - ¡Sigue así! ⚡"
            ]
        else:
            venta_necesaria_por_dia = faltante / dias_restantes
            emoji_titulo = "🚀"
            titulo = "¡Es hora de acelerar!"
            color_border = theme['error']
            color_bg = "rgba(239, 68, 68, 0.15)"
            mensaje_principal = f"<strong>Te falta:</strong> {format_currency(faltante)} para cumplir la meta"
            plan_accion_items = [
                f"Necesitas vender <strong>{format_currency(venta_necesaria_por_dia)}</strong> diarios",
                f"Tienes <strong>{dias_restantes} días</strong> por delante - ¡Usa el tiempo sabiamente! ⏰",
                f"Llevas <strong>{progreso:.1f}%</strong> - ¡Cada día cuenta! 🔥"
            ]
        
        # Renderizar card moderno usando componentes de Streamlit
        if progreso >= 100:
            # Card para meta cumplida
            st.markdown(
                f"""<div style="background: {theme['surface']}; border-radius: 16px; padding: 24px; border-left: 4px solid {color_border}; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 0;">
                    <h3 style="margin: 0 0 16px 0; color: {theme['text_primary']}; font-size: 1.4rem; font-weight: 700;">{emoji_titulo} {titulo}</h3>
                    <p style="margin: 0 0 16px 0; color: {theme['text_primary']}; font-size: 1rem; line-height: 1.6;">{mensaje_principal}</p>
                    <p style="margin: 16px 0 0 0; color: {theme['text_primary']}; font-size: 1rem; font-weight: 600; padding: 12px; background: {color_bg}; border-radius: 8px;">{frase_del_dia}</p>
                </div>""",
                unsafe_allow_html=True
            )
        else:
            # Card con plan de acción - renderizado completo en un solo bloque
            plan_accion_html = ""
            for item in plan_accion_items:
                plan_accion_html += f'<p style="margin: 8px 0; padding-left: 20px; color: {theme["text_primary"]}; font-size: 0.95rem; line-height: 1.6;"><span style="color: {color_border}; font-weight: 700; margin-right: 8px;">•</span>{item}</p>'
            
            st.markdown(
                f"""<div style="background: {theme['surface']}; border-radius: 16px; padding: 24px; border-left: 4px solid {color_border}; box-shadow: 0 4px 12px rgba(0,0,0,0.08); margin-bottom: 0;">
                    <h3 style="margin: 0 0 16px 0; color: {theme['text_primary']}; font-size: 1.4rem; font-weight: 700;">{emoji_titulo} {titulo}</h3>
                    <p style="margin: 0 0 16px 0; color: {theme['text_primary']}; font-size: 1rem; line-height: 1.6;">{mensaje_principal}</p>
                    <p style="margin: 16px 0 12px 0; color: {theme['text_primary']}; font-size: 1rem; font-weight: 700;">Plan de acción:</p>
                    {plan_accion_html}
                    <p style="margin: 16px 0 0 0; color: {theme['text_primary']}; font-size: 1rem; font-weight: 600; padding: 12px; background: {color_bg}; border-radius: 8px;">{frase_del_dia}</p>
                </div>""",
                unsafe_allow_html=True
            )
    
    # ========================
    # TAB COMISIONES
    # ========================
    
    def render_comisiones(self):
        """Renderiza la pestaña de gestión de comisiones"""
        st.header("Gestión de Comisiones")
        
        # Botón para limpiar cache
        col_refresh, col_empty = st.columns([1, 3])
        with col_refresh:
            if st.button("🔄 Actualizar Datos", type="secondary"):
                self.db_manager.limpiar_cache()
                keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
                for key in keys_to_delete:
                    del st.session_state[key]
                safe_rerun()
        
        # Filtros
        with st.container():
            st.markdown("### Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"], key="estado_filter_comisiones")
            with col2:
                # Obtener lista de clientes para el desplegable
                lista_clientes = self.db_manager.obtener_lista_clientes()
                opciones_clientes = ["Todos"] + lista_clientes
                cliente_filter = st.selectbox("Cliente", opciones_clientes, key="comisiones_cliente_filter")
            with col3:
                monto_min = st.number_input("Valor mínimo", min_value=0, value=0, step=100000)
            with col4:
                aplicar_filtros = st.button("🔍 Aplicar Filtros")
        
        # Cargar y filtrar datos
        df = self.db_manager.cargar_datos()
        
        if not df.empty:
            df = self.db_manager.agregar_campos_faltantes(df)
            
            # Aplicar filtro de mes del sidebar (solo si hay datos y el mes existe)
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and "mes_factura" in df.columns:
                    df = df[df["mes_factura"] == mes_filter]
                    if not df.empty:
                        st.info(f"📅 Filtrando por mes: {mes_filter}")
            except Exception:
                pass  # Ignorar errores de filtrado
            
            df_filtrado = self._aplicar_filtros_comisiones(df, estado_filter, cliente_filter, monto_min)
        else:
            df_filtrado = pd.DataFrame()
        
        # Mostrar resumen
        self._render_resumen_comisiones(df_filtrado)
        
        st.markdown("---")
        
        # Mostrar facturas
        if not df_filtrado.empty:
            self._render_facturas_detalladas(df_filtrado)
        else:
            st.info("No hay facturas que coincidan con los filtros aplicados")
            if df.empty:
                st.warning("No hay datos en la base de datos. Registra tu primera venta en la pestaña 'Nueva Venta'.")
    
    def _aplicar_filtros_comisiones(self, df: pd.DataFrame, estado_filter: str, 
                                   cliente_filter: str, monto_min: float) -> pd.DataFrame:
        """Aplica los filtros seleccionados a los datos de comisiones"""
        df_filtrado = df.copy()
        
        if estado_filter == "Pendientes":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
        elif estado_filter == "Pagadas":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
        elif estado_filter == "Vencidas":
            df_filtrado = df_filtrado[
                (df_filtrado["dias_vencimiento"].notna()) & 
                (df_filtrado["dias_vencimiento"] < 0) & 
                (df_filtrado["pagado"] == False)
            ]
        
        # Filtrar por cliente (exacto si se selecciona uno del desplegable)
        if cliente_filter and cliente_filter != "Todos":
            df_filtrado = df_filtrado[df_filtrado["cliente"] == cliente_filter]
        
        if monto_min > 0:
            df_filtrado = df_filtrado[df_filtrado["valor"] >= monto_min]
        
        return df_filtrado
    
    def _render_resumen_comisiones(self, df_filtrado: pd.DataFrame):
        """Renderiza el resumen de comisiones"""
        if not df_filtrado.empty:
            st.markdown("### Resumen")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Facturas", len(df_filtrado))
            with col2:
                st.metric("Total Comisiones", format_currency(df_filtrado["comision"].sum()))
            with col3:
                st.metric("Valor Promedio", format_currency(df_filtrado["valor"].mean()))
            with col4:
                pendientes = len(df_filtrado[df_filtrado["pagado"] == False])
                st.metric("Pendientes", pendientes)
    
    def _render_facturas_detalladas(self, df_filtrado: pd.DataFrame):
        """Renderiza las facturas con detalles y acciones"""
        st.markdown("### Facturas Detalladas")
        
        # Ordenar por prioridad
        def calcular_prioridad(row):
            if row['pagado']:
                return 3
            elif row.get('dias_vencimiento') is not None:
                if row['dias_vencimiento'] < 0:
                    return 0
                elif row['dias_vencimiento'] <= 5:
                    return 1
                else:
                    return 2
            return 2
        
        df_filtrado['prioridad'] = df_filtrado.apply(calcular_prioridad, axis=1)
        df_filtrado = df_filtrado.sort_values(['prioridad', 'fecha_factura'], ascending=[True, False])
        
        for index, (_, factura) in enumerate(df_filtrado.iterrows()):
            factura_id = factura.get('id')
            if not factura_id:
                continue
            
            # Renderizar card de factura
            self.ui_components.render_factura_card(factura, index)
            
            # Renderizar botones de acción
            actions = self.ui_components.render_factura_action_buttons(factura, index)
            
            # Procesar acciones
            self._procesar_acciones_factura(factura, actions)
            
            st.markdown("---")
    
    def _procesar_acciones_factura(self, factura: pd.Series, actions: Dict[str, bool]):
        """Procesa las acciones de los botones de factura"""
        factura_id = factura.get('id')
        
        # Evitar múltiples reruns simultáneos
        if st.session_state.get("_processing_action", False):
            return
        
        # Limpiar otros estados si se presiona una nueva acción
        if any(actions.values()):
            for key in list(st.session_state.keys()):
                if key.startswith(f"show_") and str(factura_id) in key:
                    try:
                        del st.session_state[key]
                    except KeyError:
                        pass
        
        # Procesar acciones y solo hacer rerun una vez al final
        needs_rerun = False
        
        if actions.get('edit'):
            st.session_state[f"show_edit_{factura_id}"] = True
            needs_rerun = True
        
        if actions.get('pay'):
            st.session_state[f"show_pago_{factura_id}"] = True
            needs_rerun = True
        
        if actions.get('detail'):
            st.session_state[f"show_detail_{factura_id}"] = True
            needs_rerun = True
        
        if actions.get('comprobante'):
            st.session_state[f"show_comprobante_{factura_id}"] = True
            needs_rerun = True
        
        # Solo hacer rerun una vez si es necesario
        if needs_rerun:
            st.session_state["_processing_action"] = True
            safe_rerun()
        
        # Mostrar modales según el estado
        self._mostrar_modales_factura(factura)
    
    def _mostrar_modales_factura(self, factura: pd.Series):
        """Muestra los modales según el estado de la sesión"""
        factura_id = factura.get('id')
        
        if st.session_state.get(f"show_edit_{factura_id}", False):
            with st.expander(f"✏️ Editando: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_modal_editar(factura)
        
        if st.session_state.get(f"show_pago_{factura_id}", False):
            with st.expander(f"💳 Procesando Pago: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_modal_pago(factura)
        
        if st.session_state.get(f"show_comprobante_{factura_id}", False):
            with st.expander(f"📄 Comprobante: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_comprobante(factura.get("comprobante_url"))
                if st.button("❌ Cerrar", key=f"close_comp_{factura_id}"):
                    try:
                        del st.session_state[f"show_comprobante_{factura_id}"]
                    except KeyError:
                        pass
                    if not st.session_state.get("_processing_action", False):
                        st.session_state["_processing_action"] = True
                        safe_rerun()
        
        if st.session_state.get(f"show_detail_{factura_id}", False):
            with st.expander(f"📊 Detalles: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_detalles_completos(factura)
                if st.button("❌ Cerrar", key=f"close_detail_{factura_id}"):
                    del st.session_state[f"show_detail_{factura_id}"]
                    safe_rerun()
    
    # ========================
    # TAB NUEVA VENTA
    # ========================
    
    def render_nueva_venta(self):
        """Renderiza la pestaña de nueva venta con integración de catálogo y clientes B2B"""
        st.header("🛒 Registrar Nueva Venta")
        
        # Inicializar client_purchases_manager
        client_purchases_manager = ClientPurchasesManager(self.db_manager.supabase)
        
        # Obtener lista de clientes B2B
        df_clientes_b2b = client_purchases_manager.listar_clientes()
        lista_clientes_b2b = []
        if not df_clientes_b2b.empty:
            lista_clientes_b2b = [f"{row['nombre']} (NIT: {row['nit']})" for _, row in df_clientes_b2b.iterrows()]
        
        # Obtener lista de clientes existentes (legacy)
        lista_clientes = self.db_manager.obtener_lista_clientes()
        
        # Selector de cliente
        st.markdown("### 👤 Seleccionar Cliente")
        col_sel1, col_sel2 = st.columns([2, 1])
        
        with col_sel1:
            modo_cliente = st.radio(
                "Tipo de Cliente",
                ["Cliente B2B", "Cliente Manual"],
                horizontal=True,
                key="modo_cliente_nueva_venta"
            )
        
        with col_sel2:
            st.markdown("<br>", unsafe_allow_html=True)
        
        # Inicializar productos en session_state
        if 'productos_venta' not in st.session_state:
            st.session_state['productos_venta'] = []
        
        cliente_b2b_seleccionado = None
        cliente_nit = None
        cliente_nombre = ""
        
        if modo_cliente == "Cliente B2B":
            if lista_clientes_b2b:
                cliente_b2b_idx = st.selectbox(
                    "Seleccionar Cliente B2B *",
                    options=range(len(lista_clientes_b2b)),
                    format_func=lambda x: lista_clientes_b2b[x],
                    key="select_cliente_b2b"
                )
                cliente_b2b_seleccionado = df_clientes_b2b.iloc[cliente_b2b_idx]
                cliente_nit = cliente_b2b_seleccionado['nit']
                cliente_nombre = cliente_b2b_seleccionado['nombre']
                
                # Mostrar info del cliente
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.info(f"**Cupo:** {format_currency(cliente_b2b_seleccionado.get('cupo_total', 0))}")
                with col2:
                    st.info(f"**Utilizado:** {format_currency(cliente_b2b_seleccionado.get('cupo_utilizado', 0))}")
                with col3:
                    st.info(f"**Disponible:** {format_currency(cliente_b2b_seleccionado.get('cupo_total', 0) - cliente_b2b_seleccionado.get('cupo_utilizado', 0))}")
                with col4:
                    descuento_cliente = cliente_b2b_seleccionado.get('descuento_predeterminado', 0) or 0
                    if descuento_cliente > 0:
                        st.success(f"**Descuento:** {descuento_cliente:.2f}%")
                    else:
                        st.info("**Descuento:** No configurado")
            else:
                st.warning("⚠️ No hay clientes B2B registrados. Ve a '📈 Análisis B2B' para registrar clientes.")
                return
        else:
            # Modo manual (legacy)
            opciones_clientes = ["-- Nuevo Cliente --"] + lista_clientes
            cliente_seleccionado = st.selectbox(
                "Cliente",
                opciones_clientes,
                key="nueva_venta_cliente_select",
                help="Selecciona un cliente existente para auto-completar sus datos"
            )
            cliente_nombre = cliente_seleccionado if cliente_seleccionado != "-- Nuevo Cliente --" else ""
        
        st.markdown("---")
        
        # Selector de productos del catálogo
        st.markdown("### 📦 Seleccionar Productos del Catálogo")
        
        # Cargar catálogo
        df_catalogo = self.catalog_manager.cargar_catalogo()
        
        if df_catalogo.empty:
            st.warning("⚠️ El catálogo está vacío. Ve a '🛒 Catálogo' para cargar productos.")
        else:
            # Debug: mostrar columnas disponibles (temporal)
            # st.write(f"Columnas disponibles: {df_catalogo.columns.tolist()}")
            # st.write(f"Primera fila: {df_catalogo.iloc[0].to_dict() if not df_catalogo.empty else 'N/A'}")
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Crear lista de productos para el selectbox
                productos_opciones = []
                for _, prod in df_catalogo.iterrows():
                    # Usar nombres de columnas en minúsculas (como están en la BD)
                    cod_ur = prod.get('cod_ur', '') or prod.get('Cod_UR', '') or ''
                    descripcion = prod.get('descripcion', '') or prod.get('Descripcion', '') or 'Sin descripción'
                    referencia = prod.get('referencia', '') or prod.get('Referencia', '') or ''
                    
                    # Crear nombre display más descriptivo
                    if cod_ur and descripcion:
                        nombre_display = f"{cod_ur} - {descripcion[:60]}"
                    elif cod_ur:
                        nombre_display = f"{cod_ur} - {referencia[:40] if referencia else 'Sin descripción'}"
                    elif descripcion:
                        nombre_display = f"{descripcion[:60]}"
                    else:
                        nombre_display = "Producto sin información"
                    
                    productos_opciones.append((cod_ur, nombre_display, prod))
                
                if productos_opciones:
                    producto_seleccionado_idx = st.selectbox(
                        "Buscar Producto",
                        options=range(len(productos_opciones)),
                        format_func=lambda x: productos_opciones[x][1],
                        key="select_producto_catalogo"
                    )
                    
                    producto_seleccionado = productos_opciones[producto_seleccionado_idx][2]
                else:
                    st.warning("No hay productos disponibles en el catálogo")
                    producto_seleccionado = None
            
            with col2:
                cantidad = st.number_input("Cantidad", min_value=1, value=1, step=1, key="cantidad_producto")
                
                # Mostrar descuentos por volumen si existen
                if producto_seleccionado is not None:
                    detalle_descuento = producto_seleccionado.get('detalle_descuento', '') or producto_seleccionado.get('DetalleDescuento', '') or ''
                    
                    # Obtener descuento del cliente (si es B2B)
                    descuento_cliente = 0.0
                    if modo_cliente == "Cliente B2B" and cliente_b2b_seleccionado is not None:
                        descuento_cliente = float(cliente_b2b_seleccionado.get('descuento_predeterminado', 0) or 0)
                    
                    if detalle_descuento:
                        info_descuentos = DiscountParser.obtener_info_descuentos(detalle_descuento)
                        if info_descuentos:
                            descuento_volumen = DiscountParser.calcular_descuento_por_cantidad(detalle_descuento, cantidad)
                            descuento_total = descuento_cliente + descuento_volumen
                            
                            if descuento_total > 0:
                                st.success(f"💰 Descuento total: {descuento_total:.1f}%")
                                if descuento_cliente > 0:
                                    st.caption(f"  Cliente: {descuento_cliente}%")
                                if descuento_volumen > 0:
                                    st.caption(f"  Volumen: {descuento_volumen}%")
                            else:
                                st.info(f"💡 Descuentos disponibles por volumen:")
                                for desc in info_descuentos:
                                    st.caption(f"  • {desc['descripcion']}")
                                if descuento_cliente > 0:
                                    st.caption(f"  + Descuento cliente: {descuento_cliente}%")
                    elif descuento_cliente > 0:
                        st.info(f"💰 Descuento cliente: {descuento_cliente}%")
            
            with col3:
                if producto_seleccionado is not None:
                    # Obtener precio (probar diferentes nombres de columna)
                    precio_base = producto_seleccionado.get('precio', 0) or producto_seleccionado.get('Precio', 0) or 0
                    
                    # Calcular descuento por volumen si existe
                    detalle_descuento = producto_seleccionado.get('detalle_descuento', '') or producto_seleccionado.get('DetalleDescuento', '') or ''
                    descuento_volumen = DiscountParser.calcular_descuento_por_cantidad(detalle_descuento, cantidad) if detalle_descuento else 0.0
                    
                    # Obtener descuento del cliente (si es B2B)
                    descuento_cliente = 0.0
                    if modo_cliente == "Cliente B2B" and cliente_b2b_seleccionado is not None:
                        descuento_cliente = float(cliente_b2b_seleccionado.get('descuento_predeterminado', 0) or 0)
                    
                    # Sumar descuentos: cliente + volumen
                    descuento_total = descuento_cliente + descuento_volumen
                    
                    # Aplicar descuento total al precio
                    if descuento_total > 0:
                        precio_con_descuento = precio_base * (1 - descuento_total / 100)
                        
                        # Crear texto de ayuda con desglose
                        ayuda_texto = f"Precio original: {format_currency(precio_base)}"
                        if descuento_cliente > 0:
                            ayuda_texto += f"\nDescuento cliente: {descuento_cliente}%"
                        if descuento_volumen > 0:
                            ayuda_texto += f"\nDescuento por volumen: {descuento_volumen}%"
                        ayuda_texto += f"\nDescuento total: {descuento_total}%"
                        
                        precio_unitario = st.number_input(
                            f"Precio Unitario (con {descuento_total:.1f}% desc.)",
                            min_value=0.0,
                            value=float(precio_con_descuento),
                            step=1000.0,
                            format="%.0f",
                            key="precio_producto",
                            help=ayuda_texto
                        )
                    else:
                        precio_unitario = st.number_input(
                            "Precio Unitario",
                            min_value=0.0,
                            value=float(precio_base),
                            step=1000.0,
                            format="%.0f",
                            key="precio_producto"
                        )
                else:
                    precio_unitario = st.number_input(
                        "Precio Unitario",
                        min_value=0.0,
                        value=0.0,
                        step=1000.0,
                        format="%.0f",
                        key="precio_producto"
                    )
            
            if st.button("➕ Agregar Producto", use_container_width=True, key="btn_agregar_producto"):
                if producto_seleccionado is not None:
                    # Obtener datos con nombres correctos de columnas
                    cod_ur = producto_seleccionado.get('cod_ur', '') or producto_seleccionado.get('Cod_UR', '') or ''
                    descripcion = producto_seleccionado.get('descripcion', '') or producto_seleccionado.get('Descripcion', '') or 'Sin descripción'
                    marca = producto_seleccionado.get('marca', '') or producto_seleccionado.get('Marca', '') or ''
                    linea = producto_seleccionado.get('linea', '') or producto_seleccionado.get('Linea', '') or ''
                    
                    # Calcular descuentos totales
                    detalle_descuento = producto_seleccionado.get('detalle_descuento', '') or producto_seleccionado.get('DetalleDescuento', '') or ''
                    descuento_volumen = DiscountParser.calcular_descuento_por_cantidad(detalle_descuento, cantidad) if detalle_descuento else 0.0
                    
                    # Obtener descuento del cliente (si es B2B)
                    descuento_cliente = 0.0
                    if modo_cliente == "Cliente B2B" and cliente_b2b_seleccionado is not None:
                        descuento_cliente = float(cliente_b2b_seleccionado.get('descuento_predeterminado', 0) or 0)
                    
                    # Descuento total (cliente + volumen)
                    descuento_total = descuento_cliente + descuento_volumen
                    
                    producto_data = {
                        'cod_articulo': cod_ur,
                        'descripcion': descripcion,
                        'cantidad': cantidad,
                        'precio_unitario': precio_unitario,
                        'precio_base': producto_seleccionado.get('precio', 0) or producto_seleccionado.get('Precio', 0) or 0,
                        'descuento_cliente': descuento_cliente,
                        'descuento_volumen': descuento_volumen,
                        'descuento_total': descuento_total,
                        'subtotal': cantidad * precio_unitario,
                        'marca': marca,
                        'linea': linea
                    }
                    st.session_state['productos_venta'].append(producto_data)
                    
                    # Mostrar mensaje con descuentos aplicados
                    if descuento_total > 0:
                        mensaje = f"✅ Producto agregado: {descripcion[:50]}"
                        if descuento_cliente > 0:
                            mensaje += f"\n💰 Descuento cliente: {descuento_cliente}%"
                        if descuento_volumen > 0:
                            mensaje += f"\n📦 Descuento volumen: {descuento_volumen}%"
                        mensaje += f"\n💎 Descuento total: {descuento_total:.1f}%"
                        st.success(mensaje)
                    else:
                        st.success(f"✅ Producto agregado: {descripcion[:50]}")
                    st.rerun()
                else:
                    st.error("Por favor, selecciona un producto primero")
        
        st.markdown("---")
        
        # Mostrar productos agregados
        if st.session_state['productos_venta']:
            st.markdown("### 🛍️ Productos del Pedido")
            
            # Crear DataFrame para mostrar
            df_productos = pd.DataFrame(st.session_state['productos_venta'])
            
            # Agregar columna de acciones
            for idx, row in df_productos.iterrows():
                col1, col2, col3, col4, col5, col6 = st.columns([1, 3, 1, 1, 1, 1])
                with col1:
                    st.write(f"**{idx + 1}**")
                with col2:
                    st.write(f"{row['descripcion'][:60]}")
                    st.caption(f"Ref: {row['cod_articulo']} | {row.get('marca', 'N/A')}")
                with col3:
                    st.write(f"{row['cantidad']} und")
                with col4:
                    st.write(format_currency(row['precio_unitario']))
                with col5:
                    st.write(f"**{format_currency(row['subtotal'])}**")
                with col6:
                    if st.button("🗑️", key=f"eliminar_{idx}", help="Eliminar producto"):
                        st.session_state['productos_venta'].pop(idx)
                        st.rerun()
            
            # Calcular totales
            subtotal_productos = df_productos['subtotal'].sum()
            iva = subtotal_productos * 0.19
            total_con_iva = subtotal_productos + iva
            
            st.markdown("---")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Subtotal Productos", format_currency(subtotal_productos))
            with col2:
                st.metric("IVA (19%)", format_currency(iva))
            with col3:
                st.metric("**TOTAL CON IVA**", format_currency(total_con_iva))
            with col4:
                if modo_cliente == "Cliente B2B" and cliente_b2b_seleccionado is not None:
                    cupo_disponible = cliente_b2b_seleccionado.get('cupo_total', 0) - cliente_b2b_seleccionado.get('cupo_utilizado', 0)
                    if total_con_iva > cupo_disponible:
                        st.error(f"⚠️ Excede cupo disponible: {format_currency(cupo_disponible)}")
                    else:
                        st.success(f"✅ Cupo OK: {format_currency(cupo_disponible)}")
        else:
            subtotal_productos = 0
            iva = 0
            total_con_iva = 0
        
        st.markdown("---")
        
        # Formulario con valores por defecto basados en el patrón
        with st.form("nueva_venta_form", clear_on_submit=False):
            st.markdown("### 📋 Información de la Venta")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pedido = st.text_input("Número de Pedido *", placeholder="Ej: PED-001", key="nueva_venta_pedido")
                
                # Campo de cliente (pre-llenado)
                cliente = st.text_input(
                    "Nombre del Cliente *", 
                    value=cliente_nombre,
                    placeholder="Ej: DISTRIBUIDORA CENTRAL", 
                    key="nueva_venta_cliente_nombre",
                    disabled=(modo_cliente == "Cliente B2B")
                )
                
                factura = st.text_input("Número de Factura", placeholder="Ej: FAC-1001", key="nueva_venta_factura")
            
            with col2:
                fecha_factura = st.date_input("Fecha de Factura *", value=date.today(), key="nueva_venta_fecha")
                
                # Valor total calculado automáticamente o manual
                usar_total_manual = st.checkbox("Ingresar total manualmente", key="usar_total_manual")
                if usar_total_manual:
                    valor_total = st.number_input("Valor Total (con IVA) *", min_value=0.0, step=10000.0, format="%.0f", key="nueva_venta_valor")
                else:
                    valor_total = total_con_iva
                    st.metric("Valor Total (con IVA)", format_currency(valor_total))
                
                # Checkbox para marcar si es cliente nuevo
                es_cliente_nuevo = st.checkbox(
                    "Cliente Nuevo (cuenta para meta)", 
                    value=False,
                    key="nueva_venta_es_cliente_nuevo",
                    help="Marca esto si es la primera vez que este cliente compra"
                )
            
            st.markdown("### Información de Envío")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ciudad_destino = st.selectbox(
                    "Ciudad de Destino *",
                    options=["Medellín", "Bogotá", "Resto"],
                    index=0,
                    key="nueva_venta_ciudad",
                    help="Ciudad donde se enviará el pedido"
                )
            
            with col2:
                # Checkbox de recogida local (solo visible si es Medellín)
                if ciudad_destino == "Medellín":
                    recogida_local = st.checkbox(
                        "Recogida Local",
                        value=False,
                        key="nueva_venta_recogida_local",
                        help="El cliente recoge el pedido localmente (sin flete)"
                    )
                else:
                    recogida_local = False
            
            # Determinar si debe tener flete (para mostrar el campo)
            if valor_total > 0:
                from business.freight_validator import FreightValidator
                valor_neto_temp = valor_total / 1.19
                debe_tener_flete, _ = FreightValidator.debe_tener_flete(
                    valor_neto_temp, ciudad_destino, recogida_local
                )
            else:
                debe_tener_flete = False
            
            with col3:
                # Campo de flete (siempre visible pero con ayuda contextual)
                if debe_tener_flete:
                    valor_flete = st.number_input(
                        "Valor Flete ⚠️",
                        min_value=0.0,
                        step=10000.0,
                        format="%.0f",
                        value=0.0,
                        key="nueva_venta_flete",
                        help="⚠️ Este pedido DEBE incluir flete"
                    )
                else:
                    valor_flete = st.number_input(
                        "Valor Flete (opcional)",
                        min_value=0.0,
                        step=10000.0,
                        format="%.0f",
                        value=0.0,
                        key="nueva_venta_flete",
                        help="✅ Este pedido NO requiere flete"
                    )
            
            st.markdown("### Configuración de Comisión")
            
            # Valores por defecto
            cliente_propio_default = False
            descuento_pie_default = False
            condicion_especial_default = False
            descuento_adicional_default = 0.0
            
            # Si es cliente B2B, cargar descuento predeterminado del cliente
            if modo_cliente == "Cliente B2B" and cliente_b2b_seleccionado is not None:
                descuento_adicional_default = float(cliente_b2b_seleccionado.get('descuento_predeterminado', 0) or 0)
                
                # También intentar obtener otras configuraciones desde historial (opcional)
                patron_descuentos = client_purchases_manager.obtener_patron_descuentos_cliente(cliente_nit)
                if patron_descuentos.get('num_facturas', 0) > 0:
                    cliente_propio_default = patron_descuentos.get('cliente_propio', False)
                    descuento_pie_default = patron_descuentos.get('descuento_pie_factura', False)
                    condicion_especial_default = patron_descuentos.get('condicion_especial', False)
            else:
                # Si es cliente manual, usar patrón del sistema legacy
                patron_cliente = self.db_manager.obtener_patron_cliente(cliente_nombre)
                if patron_cliente.get('existe', False):
                    cliente_propio_default = patron_cliente.get('cliente_propio', False)
                    descuento_pie_default = patron_cliente.get('descuento_pie_factura', False)
                    condicion_especial_default = patron_cliente.get('condicion_especial', False)
                    descuento_adicional_default = patron_cliente.get('descuento_adicional', 0.0)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cliente_propio = st.checkbox("Cliente Propio", value=cliente_propio_default, key="nueva_venta_cliente_propio")
            with col2:
                descuento_pie_factura = st.checkbox("Descuento a Pie", value=descuento_pie_default, key="nueva_venta_descuento_pie")
            with col3:
                condicion_especial = st.checkbox("Condición Especial", value=condicion_especial_default, key="nueva_venta_condicion")
            with col4:
                descuento_adicional = st.number_input(
                    "Desc. Adicional (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    step=0.5, 
                    value=descuento_adicional_default, 
                    key="nueva_venta_descuento_adicional",
                    help=f"Descuento del cliente: {descuento_adicional_default:.2f}% (puedes modificarlo)"
                )
            
            # Preview de cálculos
            if valor_total > 0:
                st.markdown("---")
                st.markdown("### Preview de Comisión")
                
                # IMPORTANTE: Restar el flete antes de calcular la comisión
                # El flete NO se incluye en la base de comisión
                valor_productos_con_iva = valor_total - valor_flete
                
                # Calcular subtotal sin IVA
                subtotal_sin_iva = valor_productos_con_iva / 1.19
                
                # Si hay descuento a pie (15%), aplicarlo al subtotal
                if descuento_pie_factura:
                    subtotal_con_descuento = subtotal_sin_iva * 0.85  # Restar 15%
                    descuento_aplicado = subtotal_sin_iva * 0.15
                else:
                    subtotal_con_descuento = subtotal_sin_iva
                    descuento_aplicado = 0
                
                # Calcular IVA sobre el subtotal con descuento
                iva_calculado = subtotal_con_descuento * 0.19
                
                # Total final con descuento a pie
                total_con_descuento_pie = subtotal_con_descuento + iva_calculado
                
                # Verificar si hay descuento adicional (cliente + volumen de productos)
                # Si hay descuento por volumen en algún producto, también cuenta como descuento adicional
                tiene_descuento_volumen = False
                productos_venta_actual = st.session_state.get('productos_venta', [])
                if productos_venta_actual:
                    for prod in productos_venta_actual:
                        if prod.get('descuento_volumen', 0) > 0:
                            tiene_descuento_volumen = True
                            break
                
                # Si hay descuento adicional del cliente O descuento por volumen, reduce la comisión
                tiene_descuento_adicional = descuento_adicional > 0 or tiene_descuento_volumen
                
                # Calcular comisión usando el valor correcto
                calc = self.comision_calc.calcular_comision_inteligente(
                    total_con_descuento_pie, 
                    cliente_propio, 
                    tiene_descuento_adicional, 
                    descuento_pie_factura
                )
                
                col1, col2, col3, col4, col5 = st.columns(5)
                with col1:
                    st.metric("Subtotal Productos", format_currency(subtotal_sin_iva))
                with col2:
                    if descuento_pie_factura:
                        st.metric("Desc. 15% a Pie", format_currency(-descuento_aplicado), delta="-15%")
                    else:
                        st.metric("Descuento a Pie", "No aplica")
                with col3:
                    st.metric("Subtotal con Desc.", format_currency(subtotal_con_descuento))
                with col4:
                    st.metric("IVA (19%)", format_currency(iva_calculado))
                with col5:
                    st.metric("TOTAL CLIENTE", format_currency(total_con_descuento_pie + valor_flete))
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Base Comisión", format_currency(calc['base_comision']))
                with col2:
                    st.metric("Porcentaje", f"{calc['porcentaje']}%")
                with col3:
                    st.metric("Comisión Final", format_currency(calc['comision']))
                
                # Validación de flete
                from business.freight_validator import FreightValidator
                debe_tener_flete, razon_flete = FreightValidator.debe_tener_flete(
                    calc['base_comision'], ciudad_destino, recogida_local
                )
                
                # Mostrar alerta de flete
                if debe_tener_flete:
                    if valor_flete > 0:
                        st.success(f"✅ **Flete incluido correctamente: {format_currency(valor_flete)}**")
                    else:
                        st.warning(f"⚠️ **Este pedido debe incluir flete**\n\n{razon_flete}")
                else:
                    if valor_flete > 0:
                        st.info(f"ℹ️ **Flete opcional agregado: {format_currency(valor_flete)}**\n\n{razon_flete}")
                    else:
                        st.success(f"✅ **Este pedido NO requiere flete**\n\n{razon_flete}")
                
                # Mensaje informativo sobre descuentos
                mensaje_descuentos = []
                if descuento_adicional > 0:
                    mensaje_descuentos.append(f"Descuento cliente: {descuento_adicional}%")
                if tiene_descuento_volumen:
                    mensaje_descuentos.append("Descuento por volumen aplicado")
                
                descuento_info = " + ".join(mensaje_descuentos) if mensaje_descuentos else "Sin descuentos adicionales"
                
                st.info(f"""
                **Detalles del cálculo:**
                - Tipo cliente: {'Propio' if cliente_propio else 'Externo'}
                - Porcentaje comisión: {calc['porcentaje']}%
                - {'Descuento aplicado en factura' if descuento_pie_factura else 'Sin descuento a pie'}
                - Descuentos adicionales: {descuento_info}
                - **Nota:** El flete NO afecta la base de comisión
                - **⚠️ Importante:** Si hay descuento adicional (cliente o volumen), la comisión se reduce en 1 punto porcentual
                """)
            
            st.markdown("---")
            
            # Botones
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                submit = st.form_submit_button("Registrar Venta", type="primary", use_container_width=True)
            
            with col2:
                if st.form_submit_button("Limpiar", use_container_width=True):
                    safe_rerun()
            
            with col3:
                if st.form_submit_button("Previsualizar", use_container_width=True):
                    if pedido and cliente and valor_total > 0:
                        st.success("Los datos se ven correctos para registrar")
                    else:
                        st.warning("Faltan campos obligatorios")
            
            # Lógica de guardado
            if submit:
                productos_venta = st.session_state.get('productos_venta', [])
                self._procesar_nueva_venta(
                    pedido, cliente, factura, fecha_factura, valor_total, 
                    condicion_especial, cliente_propio, descuento_pie_factura, 
                    descuento_adicional, es_cliente_nuevo, ciudad_destino, recogida_local, valor_flete,
                    cliente_nit=cliente_nit if modo_cliente == "Cliente B2B" else None,
                    productos_venta=productos_venta
                )
    
    def _procesar_nueva_venta(self, pedido: str, cliente: str, factura: str, fecha_factura: date,
                             valor_total: float, condicion_especial: bool, cliente_propio: bool,
                             descuento_pie_factura: bool, descuento_adicional: float, es_cliente_nuevo: bool = False,
                             ciudad_destino: str = "Resto", recogida_local: bool = False, valor_flete: float = 0,
                             cliente_nit: str = None, productos_venta: list = None):
        """Procesa el registro de una nueva venta"""
        if pedido and cliente and valor_total > 0:
            try:
                # Calcular fechas
                dias_pago = 60 if condicion_especial else 35
                dias_max = 60 if condicion_especial else 45
                fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                
                # IMPORTANTE: El flete NO se incluye en la base de comisión ni en el valor_neto
                # El valor_total proporcionado ya incluye todos los descuentos aplicados
                # Calculamos siempre desde el total: valor_neto = (total - flete) / 1.19
                
                # 1. Restar el flete del valor total
                valor_productos_con_iva = valor_total - valor_flete
                
                # 2. Calcular valor_neto sin IVA del total (esto es SIEMPRE correcto)
                # valor_neto es el subtotal sin IVA, ya con todos los descuentos reflejados
                valor_neto_calculado = valor_productos_con_iva / 1.19
                
                # 3. Calcular IVA: debe ser la diferencia exacta para que total = neto + IVA + flete
                iva_calculado = valor_productos_con_iva - valor_neto_calculado
                
                # 4. Verificar consistencia (debe ser siempre exacta)
                total_verificado = valor_neto_calculado + iva_calculado + valor_flete
                if abs(valor_total - total_verificado) > 0.01:
                    # Ajustar para asegurar exactitud (redondeo)
                    iva_calculado = valor_productos_con_iva - valor_neto_calculado
                
                # 5. Para la comisión, usar el total sin flete
                total_con_descuento_pie = valor_neto_calculado + iva_calculado
                
                # Verificar si hay descuento adicional (cliente + volumen de productos)
                # Si hay descuento por volumen en algún producto, también cuenta como descuento adicional
                tiene_descuento_volumen = False
                if productos_venta:
                    for prod in productos_venta:
                        if prod.get('descuento_volumen', 0) > 0:
                            tiene_descuento_volumen = True
                            break
                
                # Si hay descuento adicional del cliente O descuento por volumen, reduce la comisión
                tiene_descuento_adicional = descuento_adicional > 0 or tiene_descuento_volumen
                
                # Calcular comisión usando el valor correcto
                calc = self.comision_calc.calcular_comision_inteligente(
                    total_con_descuento_pie, 
                    cliente_propio, 
                    tiene_descuento_adicional, 
                    descuento_pie_factura
                )
                
                # 6. El valor_total_final es exactamente el valor_total proporcionado
                # ya que calculamos valor_neto e IVA a partir de él
                valor_total_final = valor_total
                
                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura if factura else f"FAC-{pedido}",
                    "valor": float(valor_total_final),  # Total exacto proporcionado
                    "valor_neto": float(valor_neto_calculado),  # Calculado: (total - flete) / 1.19
                    "iva": float(iva_calculado),  # Calculado: (total - flete) - valor_neto
                    "base_comision": float(calc['base_comision']),
                    "comision": float(calc['comision']),
                    "porcentaje": float(calc['porcentaje']),
                    "fecha_factura": fecha_factura.isoformat(),
                    "fecha_pago_est": fecha_pago_est.isoformat(),
                    "fecha_pago_max": fecha_pago_max.isoformat(),
                    "cliente_propio": cliente_propio,
                    "descuento_pie_factura": descuento_pie_factura,
                    "descuento_adicional": float(descuento_adicional),
                    "condicion_especial": condicion_especial,
                    "cliente_nuevo": es_cliente_nuevo,
                    "ciudad_destino": ciudad_destino,
                    "recogida_local": recogida_local,
                    "valor_flete": float(valor_flete),
                    "pagado": False
                }
                
                # Validación final antes de guardar
                # Validación final: debe ser siempre exacta
                valor_verificado = data["valor_neto"] + data["iva"] + data["valor_flete"]
                diferencia_final = abs(data["valor"] - valor_verificado)
                if diferencia_final > 0.01:
                    # Si hay diferencia por redondeo, ajustar el IVA para que sea exacta
                    data["iva"] = data["valor"] - data["valor_neto"] - data["valor_flete"]
                    # Recalcular la comisión con el total ajustado
                    total_con_descuento_pie = data["valor_neto"] + data["iva"]
                    calc = self.comision_calc.calcular_comision_inteligente(
                        total_con_descuento_pie, 
                        cliente_propio, 
                        tiene_descuento_adicional, 
                        descuento_pie_factura
                    )
                    data["base_comision"] = float(calc['base_comision'])
                    data["comision"] = float(calc['comision'])
                    data["porcentaje"] = float(calc['porcentaje'])
                
                # Insertar venta
                venta_insertada = self.db_manager.insertar_venta(data)
                
                if venta_insertada:
                    # Obtener el ID de la factura recién insertada para enlazarla
                    factura_id = None
                    try:
                        factura_response = self.db_manager.supabase.table("comisiones").select("id").eq(
                            "pedido", pedido
                        ).eq("cliente", cliente).order("created_at", desc=True).limit(1).execute()
                        
                        if factura_response.data:
                            factura_id = factura_response.data[0]['id']
                    except Exception as e:
                        st.warning(f"⚠️ No se pudo obtener ID de factura: {str(e)}")
                    
                    # Si hay productos del catálogo y cliente B2B, guardarlos y enlazarlos
                    if productos_venta and cliente_nit:
                        try:
                            client_purchases_manager = ClientPurchasesManager(self.db_manager.supabase)
                            cliente_b2b = client_purchases_manager.obtener_cliente(cliente_nit)
                            
                            if cliente_b2b:
                                num_documento = factura if factura else pedido
                                compras_ids = []
                                
                                # Verificar si las columnas de sincronización existen
                                # Intentar insertar sin factura_id primero para verificar
                                try:
                                    # Probar si existe la columna factura_id
                                    test_query = self.db_manager.supabase.table('compras_clientes').select('factura_id').limit(1).execute()
                                    tiene_factura_id = True
                                except:
                                    tiene_factura_id = False
                                
                                # Guardar cada producto como compra y enlazarlo con la factura
                                for producto in productos_venta:
                                    compra_data = {
                                        'cliente_id': cliente_b2b['id'],
                                        'nit_cliente': cliente_nit,
                                        'fuente': 'FE',
                                        'num_documento': num_documento,
                                        'fecha': fecha_factura.isoformat(),
                                        'cod_articulo': producto['cod_articulo'],
                                        'detalle': producto['descripcion'],
                                        'cantidad': producto['cantidad'],
                                        'valor_unitario': producto['precio_unitario'],
                                        'descuento': producto.get('descuento_total', descuento_adicional),  # Guardar descuento total (cliente + volumen)
                                        'total': producto['subtotal'],
                                        'familia': producto.get('linea', ''),
                                        'marca': producto.get('marca', ''),
                                        'es_devolucion': False
                                    }
                                    
                                    # Solo agregar campos de sincronización si existen
                                    if tiene_factura_id and factura_id:
                                        compra_data['factura_id'] = factura_id
                                        compra_data['sincronizado'] = True
                                        compra_data['fecha_sincronizacion'] = datetime.now().isoformat()
                                    
                                    # Insertar compra
                                    compra_result = self.db_manager.supabase.table('compras_clientes').insert(compra_data).execute()
                                    
                                    if compra_result.data:
                                        compras_ids.append(compra_result.data[0]['id'])
                                
                                # Si hay factura_id y las columnas existen, actualizar la factura
                                if factura_id and compras_ids:
                                    try:
                                        # Verificar si existe la columna compra_cliente_id
                                        test_query = self.db_manager.supabase.table('comisiones').select('compra_cliente_id').limit(1).execute()
                                        self.db_manager.supabase.table('comisiones').update({
                                            'compra_cliente_id': compras_ids[0],
                                            'sincronizado_compras': True
                                        }).eq('id', factura_id).execute()
                                    except:
                                        # Si no existe la columna, solo continuar sin error
                                        pass
                                
                                # Actualizar cupo utilizado del cliente
                                nuevo_cupo_utilizado = cliente_b2b.get('cupo_utilizado', 0) + valor_total
                                self.db_manager.supabase.table('clientes_b2b').update({
                                    'cupo_utilizado': nuevo_cupo_utilizado,
                                    'fecha_actualizacion': datetime.now().isoformat()
                                }).eq('id', cliente_b2b['id']).execute()
                                
                                st.success(f"✅ Venta registrada y enlazada completamente")
                                st.info(f"📦 {len(productos_venta)} producto(s) guardado(s) en historial. Cupo actualizado. Descuento: {descuento_adicional}%")
                        
                        except Exception as e:
                            st.warning(f"⚠️ Venta registrada, pero hubo un error guardando productos: {str(e)}")
                            import traceback
                            with st.expander("Detalles del error"):
                                st.code(traceback.format_exc())
                    
                    st.success("¡Venta registrada correctamente!")
                    st.success(f"Comisión calculada: {format_currency(calc['comision'])}")
                    
                    # Limpiar productos de la sesión
                    if 'productos_venta' in st.session_state:
                        st.session_state['productos_venta'] = []
                    
                    st.balloons()
                    
                    # Mostrar resumen
                    st.markdown("### Resumen de la venta:")
                    st.write(f"**Cliente:** {cliente}")
                    st.write(f"**Pedido:** {pedido}")
                    st.write(f"**Valor:** {format_currency(valor_total)}")
                    st.write(f"**Comisión:** {format_currency(calc['comision'])} ({calc['porcentaje']}%)")
                    st.write(f"**Fecha límite pago:** {fecha_pago_max.strftime('%d/%m/%Y')}")
                else:
                    st.error("Error al registrar la venta")
                    
            except Exception as e:
                st.error(f"Error procesando la venta: {str(e)}")
        else:
            st.error("Por favor completa todos los campos marcados con *")
    
    # ========================
    # TAB NUEVA VENTA SIMPLE
    # ========================
    
    def render_nueva_venta_simple(self):
        """Renderiza la pestaña de nueva venta EXACTA como la imagen"""
        from ui.theme_manager import ThemeManager
        theme = ThemeManager.get_theme()
        
        # Inicializar estado de productos
        if 'productos_venta' not in st.session_state:
            st.session_state['productos_venta'] = []
        
        # Título y subtítulo EXACTO como imagen
        st.markdown(
            f"""
            <div style='margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    color: {theme['text_primary']};
                    margin-bottom: 0.5rem;
                '>
                    Nueva Venta
                </h1>
                <p style='color: {theme['text_secondary']}; font-size: 1rem; margin: 0;'>
                    Registra una venta rápidamente
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Obtener lista de clientes existentes
        lista_clientes = self.db_manager.obtener_lista_clientes()
        
        # Cargar catálogo de productos para búsqueda automática
        try:
            from database.catalog_manager import CatalogManager
            catalog_manager = CatalogManager(self.db_manager.supabase)
            df_catalogo = catalog_manager.cargar_catalogo()
        except:
            df_catalogo = pd.DataFrame()
        
        # CARD INFORMACIÓN DE LA VENTA - Fecha, Pedido, Factura
        with st.container(border=True):
            st.markdown("### Información de la Venta")
            col_fecha, col_pedido, col_factura = st.columns(3)
            
            with col_fecha:
                fecha_venta = st.date_input(
                    "Fecha *",
                    value=date.today(),
                    key="fecha_venta_simple",
                    help="Fecha de la venta"
                )
            
            with col_pedido:
                numero_pedido = st.text_input(
                    "Número de Pedido *",
                    placeholder="Ej: PED-001",
                    key="numero_pedido_simple",
                    help="Número del pedido"
                )
            
            with col_factura:
                numero_factura = st.text_input(
                    "Número de Factura",
                    placeholder="Ej: FAC-1001",
                    key="numero_factura_simple",
                    help="Número de factura (opcional)"
                )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CARD CLIENTE - EXACTO como imagen
        with st.container(border=True):
            col_header1, col_header2 = st.columns([1, 0.1])
            with col_header1:
                st.markdown("### Cliente")
            with col_header2:
                st.markdown("⋮")  # Tres puntos
            
            # Buscador/Selector de cliente - OBTENER CLIENTES DE LA TABLA COMISIONES
            try:
                # Obtener TODOS los clientes únicos de la tabla comisiones
                df_comisiones = self.db_manager.cargar_datos()
                
                if not df_comisiones.empty and 'cliente' in df_comisiones.columns:
                    # Obtener nombres únicos de clientes de la tabla comisiones
                    nombres_clientes_comisiones = df_comisiones['cliente'].dropna().unique().tolist()
                    nombres_clientes_comisiones = sorted([c for c in nombres_clientes_comisiones if c and str(c).strip()])
                    
                    # También intentar obtener clientes de la tabla clientes_b2b para complementar
                    try:
                        from database.client_purchases_manager import ClientPurchasesManager
                        clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                        
                        # Obtener clientes B2B con paginación
                        all_clientes_b2b_data = []
                        page_size = 1000
                        offset = 0
                        
                        while True:
                            clientes_b2b_response = clientes_manager.supabase.table("clientes_b2b").select(
                                "nombre"
                            ).range(offset, offset + page_size - 1).execute()
                            
                            if not clientes_b2b_response.data:
                                break
                            
                            all_clientes_b2b_data.extend(clientes_b2b_response.data)
                            
                            if len(clientes_b2b_response.data) < page_size:
                                break
                            
                            offset += page_size
                        
                        # Combinar clientes de comisiones con clientes B2B
                        if all_clientes_b2b_data:
                            df_clientes_b2b = pd.DataFrame(all_clientes_b2b_data)
                            nombres_clientes_b2b = df_clientes_b2b['nombre'].dropna().unique().tolist()
                            # Combinar ambas listas y eliminar duplicados
                            todos_los_clientes = list(set(nombres_clientes_comisiones + nombres_clientes_b2b))
                            todos_los_clientes = sorted([c for c in todos_los_clientes if c and str(c).strip()])
                        else:
                            todos_los_clientes = nombres_clientes_comisiones
                    except:
                        # Si hay error con clientes_b2b, usar solo los de comisiones
                        todos_los_clientes = nombres_clientes_comisiones
                    
                    if todos_los_clientes:
                        opciones_clientes = ["-- Seleccione o busque un cliente --"] + todos_los_clientes
                    else:
                        opciones_clientes = ["-- Seleccione o busque un cliente --"] + lista_clientes
                else:
                    # Si no hay datos en comisiones, usar lista legacy
                    opciones_clientes = ["-- Seleccione o busque un cliente --"] + lista_clientes
            except Exception as e:
                # Si hay error, mostrar lista legacy y log del error
                st.warning(f"⚠️ Error al cargar clientes: {str(e)}. Mostrando clientes del historial.")
                opciones_clientes = ["-- Seleccione o busque un cliente --"] + lista_clientes
            
            cliente_seleccionado = st.selectbox(
                "🔍 Buscar cliente",
                options=opciones_clientes,
                key="cliente_venta_select",
                label_visibility="collapsed"
            )
            
            # Guardar cliente seleccionado y obtener patrón del cliente
            if cliente_seleccionado and cliente_seleccionado != "-- Seleccione o busque un cliente --":
                st.session_state['cliente_venta'] = cliente_seleccionado
                
                # Obtener patrón del cliente (cliente_propio, descuento_pie_factura, etc.)
                patron_cliente = self.db_manager.obtener_patron_cliente(cliente_seleccionado)
                
                # Guardar información del patrón del cliente
                st.session_state['cliente_propio'] = patron_cliente.get('cliente_propio', False)
                st.session_state['descuento_pie_factura'] = patron_cliente.get('descuento_pie_factura', False)
                st.session_state['descuento_adicional_cliente'] = patron_cliente.get('descuento_adicional', 0.0)
                st.session_state['condicion_especial_cliente'] = patron_cliente.get('condicion_especial', False)
                
                # Mostrar información del historial si existe
                if patron_cliente.get('existe', False):
                    tipo_cliente = "Cliente Propio" if st.session_state['cliente_propio'] else "Cliente Externo"
                    desc_pie = "Sí" if st.session_state['descuento_pie_factura'] else "No"
                    st.caption(f"📋 Historial detectado: {tipo_cliente} | Descuento Pie: {desc_pie}")
                
                # Controles manuales para configurar el cliente (SIEMPRE VISIBLES cuando hay cliente)
                st.markdown("---")
                st.markdown("**⚙️ Configuración de Comisión (Puedes modificar):**")
                
                col_config1, col_config2, col_config3 = st.columns(3)
                
                with col_config1:
                    cliente_propio_manual = st.checkbox(
                        "Cliente Propio",
                        value=st.session_state.get('cliente_propio', False),
                        key="cliente_propio_manual",
                        help="Marca si este cliente es propio (mayor comisión)"
                    )
                    st.session_state['cliente_propio'] = cliente_propio_manual
                
                with col_config2:
                    descuento_pie_manual = st.checkbox(
                        "Descuento a Pie de Factura",
                        value=st.session_state.get('descuento_pie_factura', False),
                        key="descuento_pie_manual",
                        help="Marca si el cliente tiene descuento a pie de factura"
                    )
                    st.session_state['descuento_pie_factura'] = descuento_pie_manual
                
                with col_config3:
                    descuento_adicional_manual = st.number_input(
                        "Descuento Adicional (%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(st.session_state.get('descuento_adicional_cliente', 0.0)),
                        step=0.5,
                        key="descuento_adicional_manual",
                        help="Descuento adicional a aplicar (afecta la comisión)"
                    )
                    st.session_state['descuento_adicional_cliente'] = descuento_adicional_manual
            else:
                st.session_state['cliente_venta'] = None
                st.session_state['cliente_propio'] = False
                st.session_state['descuento_pie_factura'] = False
                st.session_state['descuento_adicional_cliente'] = 0.0
                st.session_state['condicion_especial_cliente'] = False
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CARD PRODUCTOS - EXACTO como imagen
        with st.container(border=True):
            st.markdown("### Productos")
            
            # Tabla de productos con headers
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.markdown("**Producto**")
            with col2:
                st.markdown("**Cantidad**")
            with col3:
                st.markdown("**Detalles**")
            with col4:
                st.markdown("**Acción**")
            
            # Filas de productos existentes
            if st.session_state['productos_venta']:
                for idx, producto in enumerate(st.session_state['productos_venta']):
                    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                    with col1:
                        nombre_display = producto.get('nombre', producto.get('codigo', 'N/A'))
                        precio_unitario_original = producto.get('precio_unitario', 0)
                        cantidad_prod = producto.get('cantidad', 1)
                        precio_final_actual = producto.get('precio_final', precio_unitario_original)
                        subtotal_prod = precio_final_actual * cantidad_prod
                        st.markdown(f"**{nombre_display}**")
                        st.caption(f"{format_currency(precio_final_actual)} x {cantidad_prod} = {format_currency(subtotal_prod)}")
                    with col2:
                        # Cantidad editable
                        cantidad_editada = st.number_input(
                            "Cantidad",
                            min_value=1,
                            value=int(cantidad_prod),
                            key=f"cantidad_edit_{idx}",
                            label_visibility="collapsed",
                            help="Edita la cantidad del producto"
                        )
                        
                        # Si la cantidad cambió, recalcular precio final con descuentos por escala
                        if cantidad_editada != cantidad_prod:
                            # Buscar producto en catálogo para obtener detalle_descuento
                            codigo_producto_original = producto.get('codigo', '')
                            descuento_escala_actualizado = producto.get('descuento_escala', 0)  # Mantener descuento original por defecto
                            
                            # Si tenemos precio_unitario_original válido y catálogo, recalcular descuento por escala
                            if precio_unitario_original > 0 and codigo_producto_original and not df_catalogo.empty:
                                codigo_upper = str(codigo_producto_original).strip().upper()
                                producto_match = df_catalogo[
                                    (df_catalogo['cod_ur'].astype(str).str.upper() == codigo_upper) |
                                    (df_catalogo['referencia'].astype(str).str.upper() == codigo_upper)
                                ]
                                
                                if not producto_match.empty:
                                    producto_catalogo = producto_match.iloc[0]
                                    # Recalcular descuento por escala con la nueva cantidad
                                    detalle_descuento = producto_catalogo.get('detalle_descuento', '') or ''
                                    if detalle_descuento:
                                        from utils.discount_parser import DiscountParser
                                        descuento_escala_actualizado = DiscountParser.calcular_descuento_por_cantidad(
                                            detalle_descuento, cantidad_editada
                                        )
                                    else:
                                        # Si no hay detalle_descuento, mantener el precio_unitario sin descuento
                                        descuento_escala_actualizado = 0
                            
                            # Calcular precio final actualizado
                            if precio_unitario_original > 0:
                                # Si tenemos precio unitario, calcular precio final con descuento
                                precio_final_actualizado = precio_unitario_original * (1 - descuento_escala_actualizado / 100) if descuento_escala_actualizado > 0 else precio_unitario_original
                            else:
                                # Si no hay precio unitario, mantener el precio final original (sin recalcular descuento)
                                precio_final_actualizado = precio_final_actual
                            
                            # Actualizar producto en session_state
                            st.session_state['productos_venta'][idx]['cantidad'] = cantidad_editada
                            st.session_state['productos_venta'][idx]['precio_final'] = precio_final_actualizado
                            st.session_state['productos_venta'][idx]['descuento_escala'] = descuento_escala_actualizado
                            
                            # Rerun para actualizar la visualización
                            st.rerun()
                    with col3:
                        st.markdown(producto.get('detalles', '-'))
                    with col4:
                        if st.button("🗑️", key=f"eliminar_{idx}", use_container_width=True):
                            st.session_state['productos_venta'].pop(idx)
                            st.rerun()
            
            # Agregar nuevo producto
            st.markdown("---")
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                codigo_producto = st.text_input(
                    "🔍 Código del producto",
                    key="codigo_producto_input",
                    placeholder="Ingrese código (ej: MZ07205)",
                    label_visibility="collapsed",
                    help="Ingrese el código del producto para buscar automáticamente precio y descuentos"
                )
                
                # Buscar producto en catálogo cuando se ingrese código
                producto_encontrado = None
                precio_producto = 0
                descuento_escala = 0
                nombre_producto = codigo_producto if codigo_producto else ""
                
                if codigo_producto and not df_catalogo.empty:
                    # Buscar por código (cod_ur o referencia)
                    codigo_upper = codigo_producto.strip().upper()
                    producto_match = df_catalogo[
                        (df_catalogo['cod_ur'].astype(str).str.upper() == codigo_upper) |
                        (df_catalogo['referencia'].astype(str).str.upper() == codigo_upper)
                    ]
                    
                    if not producto_match.empty:
                        producto_encontrado = producto_match.iloc[0]
                        nombre_producto = producto_encontrado.get('descripcion', codigo_producto)
                        precio_producto = float(producto_encontrado.get('precio', 0))
                        
                        # Calcular descuento por escala si existe
                        detalle_descuento = producto_encontrado.get('detalle_descuento', '') or ''
                        if detalle_descuento:
                            from utils.discount_parser import DiscountParser
                            cantidad_actual = st.session_state.get('cantidad_producto', 1)
                            descuento_escala = DiscountParser.calcular_descuento_por_cantidad(detalle_descuento, cantidad_actual)
                            
                            # Mostrar info de descuentos disponibles
                            info_descuentos = DiscountParser.obtener_info_descuentos(detalle_descuento)
                            if info_descuentos:
                                descuentos_texto = ", ".join([f"{d['cantidad']} und: {d['descuento']}%" for d in info_descuentos])
                                st.caption(f"💰 Escalas: {descuentos_texto}")
                        else:
                            st.caption(f"✅ {nombre_producto}")
                            st.caption(f"💰 Precio: {format_currency(precio_producto)}")
            
            with col2:
                cantidad = st.number_input(
                    "Cantidad",
                    min_value=1,
                    value=1,
                    key="cantidad_producto",
                    label_visibility="collapsed",
                    help="Cantidad del producto"
                )
                
                # Guardar cantidad en session_state para recalcular descuento
                st.session_state['cantidad_producto_temp'] = cantidad
            
            with col3:
                detalles = st.text_input(
                    "Detalles",
                    key="detalles_producto",
                    label_visibility="collapsed",
                    help="Detalles adicionales del producto"
                )
                
                # Mostrar precio y descuento si hay producto encontrado (recalcular aquí)
                if codigo_producto and not df_catalogo.empty:
                    codigo_upper = codigo_producto.strip().upper()
                    producto_match = df_catalogo[
                        (df_catalogo['cod_ur'].astype(str).str.upper() == codigo_upper) |
                        (df_catalogo['referencia'].astype(str).str.upper() == codigo_upper)
                    ]
                    
                    if not producto_match.empty:
                        producto_encontrado_col3 = producto_match.iloc[0]
                        precio_producto_col3 = float(producto_encontrado_col3.get('precio', 0))
                        detalle_descuento_col3 = producto_encontrado_col3.get('detalle_descuento', '') or ''
                        
                        # Recalcular descuento con la cantidad actual
                        descuento_escala_col3 = 0
                        if detalle_descuento_col3:
                            from utils.discount_parser import DiscountParser
                            descuento_escala_col3 = DiscountParser.calcular_descuento_por_cantidad(detalle_descuento_col3, cantidad)
                        
                        precio_final_col3 = precio_producto_col3 * (1 - descuento_escala_col3 / 100) if descuento_escala_col3 > 0 else precio_producto_col3
                        if descuento_escala_col3 > 0:
                            st.caption(f"Desc: {descuento_escala_col3}%")
                            st.caption(f"Final: {format_currency(precio_final_col3)}")
            
            with col4:
                if st.button("➕ Agregar producto", key="agregar_producto", use_container_width=True):
                    if codigo_producto:
                        # Buscar producto nuevamente para obtener datos actualizados
                        precio_final_agregar = 0
                        nombre_producto_agregar = codigo_producto
                        precio_unitario_agregar = 0
                        descuento_escala_agregar = 0
                        
                        if not df_catalogo.empty:
                            codigo_upper = codigo_producto.strip().upper()
                            producto_match = df_catalogo[
                                (df_catalogo['cod_ur'].astype(str).str.upper() == codigo_upper) |
                                (df_catalogo['referencia'].astype(str).str.upper() == codigo_upper)
                            ]
                            
                            if not producto_match.empty:
                                producto_encontrado_agregar = producto_match.iloc[0]
                                nombre_producto_agregar = producto_encontrado_agregar.get('descripcion', codigo_producto)
                                precio_unitario_agregar = float(producto_encontrado_agregar.get('precio', 0))
                                
                                # Calcular descuento por escala
                                detalle_descuento_agregar = producto_encontrado_agregar.get('detalle_descuento', '') or ''
                                if detalle_descuento_agregar:
                                    from utils.discount_parser import DiscountParser
                                    descuento_escala_agregar = DiscountParser.calcular_descuento_por_cantidad(detalle_descuento_agregar, cantidad)
                                
                                precio_final_agregar = precio_unitario_agregar * (1 - descuento_escala_agregar / 100) if descuento_escala_agregar > 0 else precio_unitario_agregar
                        
                        nuevo_producto = {
                            'codigo': codigo_producto,
                            'nombre': nombre_producto_agregar,
                            'cantidad': cantidad,
                            'detalles': detalles,
                            'precio_unitario': precio_unitario_agregar,
                            'precio_final': precio_final_agregar,
                            'descuento_escala': descuento_escala_agregar
                        }
                        st.session_state['productos_venta'].append(nuevo_producto)
                        
                        # No limpiar codigo_producto_input porque el widget ya existe
                        # Solo limpiar cantidad y detalles usando rerun para resetear
                        st.rerun()
                    else:
                        st.warning("Por favor ingrese un código de producto")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # SECCIÓN DE RESUMEN - Calcular desde productos reales
        subtotal = 0
        if st.session_state['productos_venta']:
            for producto in st.session_state['productos_venta']:
                precio_final = producto.get('precio_final', producto.get('precio_unitario', 0))
                cantidad = producto.get('cantidad', 1)
                subtotal += precio_final * cantidad
        
        iva = int(subtotal * 0.19)
        total = subtotal + iva
        
        col_sub, col_iva, col_total = st.columns([1, 1, 2])
        with col_sub:
            st.markdown(f"**Subtotal:** {format_currency(subtotal)}")
        with col_iva:
            st.markdown(f"**IVA 19%:** {format_currency(iva)}")
        with col_total:
            st.markdown(f"### TOTAL: {format_currency(total)}")
        
        # BOTÓN REGISTRAR VENTA - EXACTO como imagen
        if st.button("Registrar Venta", type="primary", use_container_width=True, key="registrar_venta"):
            if not st.session_state.get('cliente_venta'):
                st.error("Por favor selecciona un cliente")
            elif not st.session_state.get('numero_pedido_simple'):
                st.error("Por favor ingresa el número de pedido")
            elif not st.session_state['productos_venta']:
                st.error("Por favor agrega al menos un producto")
            else:
                # Obtener valores del formulario
                fecha_venta = st.session_state.get('fecha_venta_simple', date.today())
                numero_pedido = st.session_state.get('numero_pedido_simple', '')
                numero_factura = st.session_state.get('numero_factura_simple', '') or f"FAC-{numero_pedido}"
                
                # Calcular valor total desde productos (ya incluye descuentos por escala)
                subtotal_productos = 0
                for producto in st.session_state['productos_venta']:
                    precio_final = producto.get('precio_final', producto.get('precio_unitario', 0))
                    cantidad = producto.get('cantidad', 1)
                    subtotal_productos += precio_final * cantidad
                
                # Agregar IVA al subtotal
                valor_total_con_iva = subtotal_productos * 1.19
                
                # Obtener configuración del cliente desde session_state
                cliente_propio = st.session_state.get('cliente_propio', False)
                descuento_pie_factura = st.session_state.get('descuento_pie_factura', False)
                descuento_adicional = st.session_state.get('descuento_adicional_cliente', 0.0)
                condicion_especial = st.session_state.get('condicion_especial_cliente', False)
                
                # Verificar si hay descuentos por escala en productos
                tiene_descuento_escala = any(prod.get('descuento_escala', 0) > 0 for prod in st.session_state['productos_venta'])
                # Si hay descuento por escala, se considera como descuento adicional
                descuento_adicional_final = descuento_adicional if descuento_adicional > 0 or tiene_descuento_escala else 0.0
                
                # Procesar la venta usando el método existente
                try:
                    self._procesar_nueva_venta(
                        pedido=numero_pedido,
                        cliente=st.session_state['cliente_venta'],
                        factura=numero_factura,
                        fecha_factura=fecha_venta,
                        valor_total=valor_total_con_iva,
                        condicion_especial=condicion_especial,
                        cliente_propio=cliente_propio,
                        descuento_pie_factura=descuento_pie_factura,
                        descuento_adicional=descuento_adicional_final,
                        es_cliente_nuevo=False,
                        ciudad_destino="Resto",
                        recogida_local=False,
                        valor_flete=0.0,
                        cliente_nit=None,
                        productos_venta=st.session_state['productos_venta']
                    )
                    st.success("✅ Venta registrada correctamente")
                    # Limpiar productos después de registrar
                    st.session_state['productos_venta'] = []
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al registrar la venta: {str(e)}")
                    import traceback
                    with st.expander("Detalles del error"):
                        st.code(traceback.format_exc())
        
        # SECCIÓN DE CRÉDITO (solo si hay cliente seleccionado)
        if st.session_state.get('cliente_venta'):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            try:
                # Obtener información del cliente B2B nuevamente - USAR EL MÉTODO listar_clientes()
                from database.client_purchases_manager import ClientPurchasesManager
                clientes_manager = ClientPurchasesManager(self.db_manager.supabase)
                
                # Usar listar_clientes() para obtener TODOS los clientes B2B activos
                df_clientes_b2b = clientes_manager.listar_clientes()
                
                if not df_clientes_b2b.empty:
                    cliente_b2b = df_clientes_b2b[df_clientes_b2b['nombre'] == st.session_state['cliente_venta']]
                    
                    if not cliente_b2b.empty:
                        # Tabs de crédito
                        tab1, tab2, tab3, tab4 = st.tabs(["Compras", "Crédito", "Facturas", "Recomendaciones"])
                        
                        with tab2:  # Tab Crédito activo
                            st.markdown(f'<span style="color: #22c55e;">●</span> **{st.session_state["cliente_venta"]}**', unsafe_allow_html=True)
                            
                            with st.container(border=True):
                                st.markdown("**Factura** | **Fecha** | **Crédito** | **Restante**")
                                st.markdown("---")
                                st.markdown(f"N.° 874152 | 21 Mar 2024 | {format_currency(150000000)} | {format_currency(283700000)} <span style='color: #22c55e;'>●</span>", unsafe_allow_html=True)
                                st.markdown(f"N.° 874109 | 15 Ene 2024 | {format_currency(122500000)} | {format_currency(433700000)} <span style='color: #22c55e;'>●</span>", unsafe_allow_html=True)
                                st.markdown(f"N.° 873832 | 10 Dic 2023 | {format_currency(100000000)} | {format_currency(556200000)} <span style='color: #ef4444;'>●</span>", unsafe_allow_html=True)
                            
                            if st.button("Línea de Crédito", type="primary", key="linea_credito"):
                                st.info("Funcionalidad de línea de crédito")
            except Exception as e:
                # Silenciar error si no se puede cargar información de crédito
                pass
    
    # ========================
    # TAB DEVOLUCIONES
    # ========================
    
    # ========================
    # TAB DEVOLUCIONES
    # ========================
    
    def render_devoluciones(self):
        """Renderiza la pestaña de devoluciones"""
        st.header("Gestión de Devoluciones")
        
        # Botones de acción
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("➕ Nueva Devolución", type="primary"):
                st.session_state['show_nueva_devolucion'] = True
                safe_rerun()
        
        with col2:
            if st.button("🔄 Actualizar", type="secondary"):
                self.db_manager.limpiar_cache()
                safe_rerun()
        
        # Modal nueva devolución
        if st.session_state.get('show_nueva_devolucion', False):
            with st.expander("➕ Nueva Devolución", expanded=True):
                facturas_df = self.db_manager.obtener_facturas_para_devolucion()
                self.ui_components.render_modal_nueva_devolucion(facturas_df)
        
        st.markdown("---")
        
        # Cargar y mostrar devoluciones
        df_devoluciones = self.db_manager.cargar_devoluciones()
        
        # Aplicar filtro de mes del sidebar si hay devoluciones
        if not df_devoluciones.empty:
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and 'fecha_devolucion' in df_devoluciones.columns:
                    df_devoluciones['mes_devolucion'] = pd.to_datetime(df_devoluciones['fecha_devolucion']).dt.to_period('M').astype(str)
                    df_devoluciones = df_devoluciones[df_devoluciones['mes_devolucion'] == mes_filter]
                    if not df_devoluciones.empty:
                        st.info(f"📅 Mostrando devoluciones de: {mes_filter}")
            except Exception:
                pass
        
        if not df_devoluciones.empty:
            self._render_resumen_devoluciones(df_devoluciones)
            self._render_devoluciones_detalladas(df_devoluciones)
        else:
            self._render_ayuda_devoluciones()
    
    def _render_resumen_devoluciones(self, df_devoluciones: pd.DataFrame):
        """Renderiza el resumen de devoluciones"""
        st.markdown("### Resumen")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Devoluciones", len(df_devoluciones))
        with col2:
            total_devuelto = df_devoluciones['valor_devuelto'].sum()
            st.metric("Valor Total Devuelto", format_currency(total_devuelto))
        with col3:
            afectan_comision = len(df_devoluciones[df_devoluciones['afecta_comision'] == True])
            st.metric("Afectan Comisión", afectan_comision)
        with col4:
            valor_promedio = df_devoluciones['valor_devuelto'].mean()
            st.metric("Valor Promedio", format_currency(valor_promedio))
    
    def _render_filtros_devoluciones(self):
        """Renderiza filtros para devoluciones"""
        st.markdown("### Filtros")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            afecta_filter = st.selectbox("Afecta Comisión", ["Todos", "Sí", "No"], key="afecta_filter_devoluciones")
        with col2:
            cliente_filter = st.text_input("Buscar cliente", key="devoluciones_cliente_filter")
        with col3:
            fecha_desde = st.date_input("Desde", value=date.today() - timedelta(days=30))
        with col4:
            fecha_hasta = st.date_input("Hasta", value=date.today())
        
        return {
            "afecta_filter": afecta_filter,
            "cliente_filter": cliente_filter,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta
        }
    
    def _render_devoluciones_detalladas(self, df_devoluciones: pd.DataFrame):
        """Renderiza las devoluciones con filtros aplicados"""
        filtros = self._render_filtros_devoluciones()
        
        # Aplicar filtros
        df_filtrado = self._aplicar_filtros_devoluciones(df_devoluciones, filtros)
        
        st.markdown("---")
        
        if not df_filtrado.empty:
            st.markdown("### Devoluciones Registradas")
            
            df_filtrado = df_filtrado.sort_values('fecha_devolucion', ascending=False)
            
            for index, (_, devolucion) in enumerate(df_filtrado.iterrows()):
                self.ui_components.render_devolucion_card(devolucion, index)
                st.markdown("---")
        else:
            st.info("No hay devoluciones que coincidan con los filtros aplicados")
    
    def _aplicar_filtros_devoluciones(self, df_devoluciones: pd.DataFrame, filtros: Dict[str, Any]) -> pd.DataFrame:
        """Aplica filtros a las devoluciones"""
        df_filtrado = df_devoluciones.copy()
        
        if filtros["afecta_filter"] == "Sí":
            df_filtrado = df_filtrado[df_filtrado['afecta_comision'] == True]
        elif filtros["afecta_filter"] == "No":
            df_filtrado = df_filtrado[df_filtrado['afecta_comision'] == False]
        
        if filtros["cliente_filter"]:
            df_filtrado = df_filtrado[df_filtrado['factura_cliente'].str.contains(filtros["cliente_filter"], case=False, na=False)]
        
        # Filtro por fechas
        df_filtrado['fecha_devolucion'] = pd.to_datetime(df_filtrado['fecha_devolucion'])
        df_filtrado = df_filtrado[
            (df_filtrado['fecha_devolucion'].dt.date >= filtros["fecha_desde"]) &
            (df_filtrado['fecha_devolucion'].dt.date <= filtros["fecha_hasta"])
        ]
        
        return df_filtrado
    
    def _render_ayuda_devoluciones(self):
        """Renderiza ayuda cuando no hay devoluciones"""
        st.info("No hay devoluciones registradas")
        st.markdown("""
        **¿Cómo registrar una devolución?**
        1. Haz clic en "Nueva Devolución"
        2. Selecciona la factura correspondiente
        3. Ingresa el valor y motivo
        4. Indica si afecta la comisión
        5. Registra la devolución
        """)
    
    # ========================
    # TAB CLIENTES
    # ========================
    
    def render_clientes(self):
        """Renderiza la pestaña de gestión de clientes"""
        st.header("Gestión de Clientes")
        st.info("Módulo en desarrollo - Próximamente funcionalidad completa de gestión de clientes")
        
        df = self.db_manager.cargar_datos()
        
        # Aplicar filtro de mes del sidebar
        if not df.empty:
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and "mes_factura" in df.columns:
                    df = df[df["mes_factura"] == mes_filter]
                    if not df.empty:
                        st.info(f"📅 Mostrando clientes de: {mes_filter}")
            except Exception:
                pass
        
        if not df.empty:
            self._render_top_clientes(df)
        else:
            st.warning("No hay datos de clientes disponibles")
    
    def _render_top_clientes(self, df: pd.DataFrame):
        """Renderiza el top 10 de clientes"""
        clientes_stats = df.groupby('cliente').agg({
            'valor_neto': ['sum', 'mean', 'count'],
            'comision': 'sum',
            'fecha_factura': 'max'
        }).round(0)
        
        clientes_stats.columns = ['Total Compras', 'Ticket Promedio', 'Número Compras', 'Total Comisiones', 'Última Compra']
        clientes_stats = clientes_stats.sort_values('Total Compras', ascending=False).head(10)
        
        st.markdown("### Top 10 Clientes")
        
        for cliente, row in clientes_stats.iterrows():
            with st.container(border=True):
                st.markdown(f"**{cliente}**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total", format_currency(row['Total Compras']))
                with col2:
                    st.metric("Ticket", format_currency(row['Ticket Promedio']))
                with col3:
                    st.metric("Compras", int(row['Número Compras']))
                with col4:
                    st.metric("Comisiones", format_currency(row['Total Comisiones']))
    
    # ========================
    # TAB NOTIFICACIONES
    # ========================
    
    # ========================
    # TABS NO UTILIZADOS (Comentados para referencia futura)
    # ========================
    
    # def render_notifications(self):
    #     """Renderiza la pestaña de notificaciones"""
    #     self.notification_ui.render_notification_dashboard()
    
    # def render_sales_pipeline(self):
    #     """Renderiza la pestaña de pipeline de ventas"""
    #     self.kanban_ui.render_pipeline_dashboard()
    
    # def render_ml_analytics(self):
    #     """Renderiza la pestaña de Machine Learning y Analytics"""
    #     df = self.db_manager.cargar_datos()
    #     self.ml_ui.render_ml_dashboard(df)
    
    # ========================
    # TAB IA & ALERTAS
    # ========================
    
    # ========================
    # TAB ANÁLISIS DE GUÍAS
    # ========================
    
    def render_guides_analysis(self):
        """Renderiza la pestaña de análisis de guías de despacho con estilo ejecutivo"""
        from ui.theme_manager import ThemeManager
        from ui.executive_components import ExecutiveComponents
        
        # Aplicar estilos globales del dashboard ejecutivo
        ExecutiveComponents.apply_global_styles()
        
        # Título personalizado
        GuidesComponentsUI.render_page_header(
            "📦 Análisis de Guías de Despacho",
            "Carga tu archivo Excel y analiza el desempeño de guías y transportadoras"
        )
        
        # Cargar archivo y seleccionar hoja
        file, hoja_seleccionada, calcular_tiempo_acido = GuidesComponentsUI.render_upload_and_select()
        
        if file is None or hoja_seleccionada is None:
            st.info("👆 Por favor, sube un archivo Excel y selecciona el mes a analizar")
            return
        
        # Procesar análisis
        try:
            analyzer = GuidesAnalyzer()
            
            with st.spinner(f"📊 Analizando datos de {hoja_seleccionada}..."):
                # Cargar datos
                df = analyzer.cargar_excel(file, hoja_seleccionada, calcular_tiempo_acido=calcular_tiempo_acido)
                
                if calcular_tiempo_acido:
                    st.success("✅ 'Tiempo ácido' calculado automáticamente usando días laborables (excluyendo domingos y festivos)")
                
                if df.empty:
                    st.error("El archivo está vacío o no se pudo cargar")
                    return
                
                # Mostrar preview de datos
                with st.expander("👁️ Vista previa de los datos (primeras 5 filas)", expanded=False):
                    st.dataframe(df.head(), use_container_width=True)
                
                # Procesar análisis completo
                analisis = analyzer.procesar_analisis_completo(df)
                
                # Renderizar dashboard
                GuidesComponentsUI.render_dashboard_completo(analisis)
                
        except Exception as e:
            st.error(f"❌ Error procesando el análisis: {str(e)}")
            st.exception(e)
    
    # ========================
    # TAB CATÁLOGO/TIENDA
    # ========================
    
    def render_catalog_store(self):
        """Renderiza la pestaña del catálogo tipo tienda"""
        # Cargar automáticamente el catálogo desde el escritorio si no está cargado
        self._cargar_catalogo_automatico()
        
        # Tabs dentro del catálogo
        tab1, tab2 = st.tabs(["🛒 Ver Catálogo", "📤 Actualizar Catálogo"])
        
        with tab1:
            self.catalog_store_ui.render_catalog_store()
        
        with tab2:
            self.catalog_store_ui.render_catalog_upload()
    
    def _cargar_catalogo_automatico(self):
        """Carga automáticamente el catálogo desde el escritorio si existe"""
        import os
        ruta_escritorio = r"C:\Users\Contact Cemter UR\Desktop\Ctalogo.xlsx"
        
        # Verificar si el archivo existe
        if not os.path.exists(ruta_escritorio):
            return
        
        # Verificar si ya se cargó en esta sesión
        if st.session_state.get('catalogo_cargado_automatico', False):
            return
        
        # Verificar si hay productos en la BD
        df_catalogo = self.catalog_manager.cargar_catalogo()
        
        # Si ya hay suficientes productos en la BD, NO cargar automáticamente
        if not df_catalogo.empty and len(df_catalogo) >= 10:
            # Marcar como cargado para evitar intentos futuros
            st.session_state['catalogo_cargado_automatico'] = True
            return
        
        # Si no hay productos o hay muy pocos, cargar automáticamente
        if df_catalogo.empty or len(df_catalogo) < 10:
            try:
                with st.spinner("🔄 Cargando catálogo automáticamente desde el escritorio..."):
                    resultado = self.catalog_manager.cargar_catalogo_desde_excel(ruta_escritorio)
                    
                    if "error" in resultado:
                        # Mostrar error solo si es sobre tabla no encontrada
                        if "no existe" in resultado["error"].lower() or "table" in resultado["error"].lower():
                            st.warning(f"⚠️ {resultado['error']}")
                        else:
                            st.error(f"❌ {resultado['error']}")
                    else:
                        st.session_state['catalogo_cargado_automatico'] = True
                        st.cache_data.clear()
                        # Mostrar mensaje de éxito solo una vez
                        if resultado.get('productos_nuevos', 0) > 0 or resultado.get('productos_actualizados', 0) > 0:
                            st.success(f"✅ Catálogo cargado: {resultado.get('total_productos', 0)} productos disponibles")
            except Exception as e:
                # Solo mostrar errores críticos
                error_msg = str(e)
                if "Could not find the table" in error_msg or "PGRST205" in error_msg:
                    st.warning("⚠️ La tabla del catálogo no existe. Por favor, ejecuta el script SQL primero.")
                else:
                    # Si hay error, marcar como cargado para evitar loops infinitos
                    st.session_state['catalogo_cargado_automatico'] = True
                    st.error(f"❌ Error al cargar catálogo: {error_msg}")
        else:
            # Verificar si el archivo del escritorio es más reciente (solo si hay pocos productos)
            # Si ya hay muchos productos, no actualizar automáticamente
            pass
    
    def render_ia_alertas(self):
        """Renderiza la pestaña de IA y alertas"""
        st.header("Inteligencia Artificial & Alertas")
        
        df = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        # Aplicar filtro de mes del sidebar
        if not df.empty:
            try:
                mes_filter = st.session_state.get("mes_filter_sidebar", "Todos")
                if mes_filter != "Todos" and "mes_factura" in df.columns:
                    df = df[df["mes_factura"] == mes_filter]
                    if not df.empty:
                        st.info(f"📅 Mostrando análisis de: {mes_filter}")
            except Exception:
                pass
        
        # Análisis predictivo
        self._render_analisis_predictivo(df, meta_actual)
        
        st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self._render_alertas_criticas(df)
        
        with col2:
            self._render_recomendaciones_estrategicas()
    
    def _render_analisis_predictivo(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza análisis predictivo con datos reales"""
        st.markdown("### Análisis Predictivo")
        
        # Calcular métricas reales
        prediccion_meta = self.metrics_calc.calcular_prediccion_meta(df, meta_actual)
        tendencia_comisiones = self.metrics_calc.calcular_tendencia_comisiones(df)
        clientes_riesgo = self.metrics_calc.identificar_clientes_riesgo(df)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                label="Predicción Meta",
                value=f"{prediccion_meta['probabilidad']}%",
                delta=f"Proyección: {prediccion_meta['tendencia']}",
                help=f"Basado en velocidad actual vs necesaria. Quedan {prediccion_meta['dias_necesarios']} días"
            )
            
            if prediccion_meta['probabilidad'] < 50:
                st.error(f"⚠️ Necesitas aumentar ventas {format_currency(prediccion_meta.get('velocidad_necesaria', 0))}/día")
            elif prediccion_meta['probabilidad'] > 80:
                st.success("🎯 Muy probable cumplir meta")
            else:
                st.warning("📈 Mantén el ritmo actual")
        
        with col2:
            st.metric(
                label="Tendencia Comisiones",
                value=tendencia_comisiones['crecimiento'],
                delta=tendencia_comisiones['delta'],
                delta_color=tendencia_comisiones.get('direccion', 'normal')
            )
        
        with col3:
            st.metric(
                label="Clientes en Riesgo",
                value=str(clientes_riesgo['cantidad']),
                delta=clientes_riesgo['delta'],
                delta_color="inverse"
            )
            
            if clientes_riesgo['clientes']:
                with st.expander("Ver Detalles", expanded=False):
                    for cliente in clientes_riesgo['clientes']:
                        color = "🚨" if cliente['tipo'] == 'critico' else "⚠️"
                        st.write(f"{color} **{cliente['cliente']}**: {cliente['razon']} (Riesgo: {format_currency(cliente['impacto'])})")
    
    def _render_alertas_criticas(self, df: pd.DataFrame):
        """Renderiza alertas críticas"""
        st.markdown("### Alertas Críticas")
        
        alertas_encontradas = False
        
        if not df.empty:
            # Facturas vencidas (solo no pagadas)
            vencidas = df[
                (df["dias_vencimiento"].notna()) & 
                (df["dias_vencimiento"] < 0) & 
                (df["pagado"] == False)
            ]
            for _, factura in vencidas.head(3).iterrows():
                st.error(f"**Factura Vencida:** {factura.get('cliente', 'N/A')} - {factura.get('pedido', 'N/A')} ({format_currency(factura.get('valor_neto', 0))})")
                alertas_encontradas = True
            
            # Próximas a vencer (solo no pagadas)
            prox_vencer = df[
                (df["dias_vencimiento"].notna()) & 
                (df["dias_vencimiento"] >= 0) & 
                (df["dias_vencimiento"] <= 5) & 
                (df["pagado"] == False)
            ]
            for _, factura in prox_vencer.head(3).iterrows():
                st.warning(f"**Próximo Vencimiento:** {factura.get('cliente', 'N/A')} vence en {factura.get('dias_vencimiento', 0)} días")
                alertas_encontradas = True
            
            # Altas comisiones pendientes
            if not df.empty:
                alto_valor = df[df["comision"] > df["comision"].quantile(0.8)]
                for _, factura in alto_valor.head(2).iterrows():
                    if not factura.get("pagado"):
                        st.info(f"**Alta Comisión Pendiente:** {format_currency(factura.get('comision', 0))} esperando pago")
                        alertas_encontradas = True
        
        if not alertas_encontradas:
            st.success("No hay alertas críticas en este momento")
    
    def _render_recomendaciones_estrategicas(self):
        """Renderiza insights estratégicos del negocio"""
        st.markdown("### Insights Estratégicos")
        
        insights = self.ai_recommendations.generar_recomendaciones_reales()
        
        for i, insight in enumerate(insights):
            prioridad_color = "🔴" if insight.get('prioridad', 'media') == 'alta' else "🟡" if insight.get('prioridad', 'media') == 'media' else "🟢"
            tipo_emoji = {
                'Cartera': '💼',
                'Comisiones': '💰',
                'Clientes': '👥',
                'Ticket': '💎',
                'Riesgo': '🚨',
                'General': '✅',
                'Sin datos': 'ℹ️',
                'Error': '⚠️'
            }.get(insight.get('tipo', 'General'), '📊')
            
            with st.container(border=True):
                col_a, col_b = st.columns([3, 1])
                
                with col_a:
                    st.markdown(f"### {tipo_emoji} {insight.get('titulo', 'Insight')}")
                    st.markdown(f"**Análisis:** {insight.get('insight', 'N/A')}")
                    st.markdown(f"**Métrica:** {insight.get('metrica', 'N/A')}")
                    st.markdown(f"**Acción Recomendada:** {insight.get('accion_recomendada', 'N/A')}")
                    st.markdown(f"**Prioridad:** {prioridad_color} {insight.get('prioridad', 'media').title()}")
                
                with col_b:
                    impacto_valor = insight.get('impacto', 0)
                    if impacto_valor > 0:
                        st.metric(
                            label="Impacto Estimado",
                            value=format_currency(impacto_valor),
                            delta="Potencial" if insight.get('tipo') in ['Cartera', 'Clientes', 'Ticket'] else "En riesgo",
                            delta_color="normal" if insight.get('tipo') in ['Cartera', 'Clientes', 'Ticket'] else "inverse"
                        )
                    else:
                        st.info("N/A")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Actualizar Insights", use_container_width=True, key="btn_actualizar_insights"):
                safe_rerun()
        with col2:
            st.caption("Los insights se actualizan automáticamente con cada venta registrada")
    
    # ========================
    # TAB RADICACIÓN FACTURAS
    # ========================
    
    def render_radicacion_facturas(self):
        """Renderiza la pestaña de radicación de facturas"""
        st.header("💬 Mensajes para Clientes")
        
        # Botón de actualizar
        if st.button("🔄 Actualizar", type="secondary", key="btn_actualizar_radicacion"):
            self.db_manager.limpiar_cache()
            safe_rerun()
        
        st.markdown("---")
        
        # Pestañas para facturas pendientes, urgentes y búsqueda por cliente
        tab1, tab2, tab3 = st.tabs(["📋 Facturas Pendientes", "🚨 Urgentes", "👤 Buscar Cliente"])
        
        with tab1:
            self._render_facturas_pendientes_radicacion()
        
        with tab2:
            self._render_facturas_urgentes_radicacion()
        
        with tab3:
            self._render_busqueda_cliente_mensaje()
    
    def _render_facturas_pendientes_radicacion(self):
        """Renderiza facturas pendientes para generar mensajes (agrupadas por cliente y fecha de vencimiento)"""
        pendientes = self.invoice_radication.obtener_facturas_pendientes_radicacion()
        
        if pendientes.empty:
            st.info("No hay facturas pendientes en este momento")
            return
        
        # Normalizar nombres de clientes (eliminar espacios extra, convertir a string, normalizar mayúsculas)
        pendientes['cliente'] = pendientes['cliente'].astype(str).str.strip().str.upper()
        
        # Agrupar facturas por cliente y fecha de vencimiento
        # Normalizar fechas: convertir a datetime y luego a fecha (sin hora) para agrupar correctamente
        pendientes['fecha_pago_est'] = pd.to_datetime(pendientes['fecha_pago_est'], errors='coerce')
        # Normalizar a medianoche para eliminar diferencias de hora
        pendientes['fecha_pago_est'] = pendientes['fecha_pago_est'].dt.normalize()
        # Crear string de fecha para agrupar (solo fecha, sin hora)
        pendientes['fecha_vencimiento_str'] = pendientes['fecha_pago_est'].dt.strftime('%Y-%m-%d')
        # También crear columna de fecha para validación
        pendientes['fecha_vencimiento'] = pendientes['fecha_pago_est'].dt.date
        
        # Eliminar filas con fechas inválidas o clientes inválidos antes de agrupar
        pendientes = pendientes[
            (pendientes['fecha_vencimiento'].notna()) & 
            (pendientes['cliente'].notna()) & 
            (pendientes['cliente'] != '') &
            (pendientes['cliente'] != 'NAN')
        ].copy()
        
        # Agrupar por cliente y fecha de vencimiento (usando la fecha normalizada)
        grupos = pendientes.groupby(['cliente', 'fecha_vencimiento_str'], dropna=False, sort=False)
        
        total_grupos = len(grupos)
        total_facturas = len(pendientes)
        
        st.markdown(f"### {total_facturas} Factura(s) Pendiente(s) en {total_grupos} grupo(s)")
        st.info("💡 Las facturas del mismo cliente que vencen el mismo día se agrupan automáticamente en un solo mensaje")
        
        for (cliente, fecha_venc), grupo in grupos:
            facturas_grupo = grupo.to_dict('records')
            num_facturas = len(facturas_grupo)
            
            # Usar el ID de la primera factura como clave para el grupo
            primera_factura = facturas_grupo[0]
            grupo_id = f"{cliente}_{fecha_venc}"
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Mostrar si es un grupo o factura individual
                    if num_facturas > 1:
                        st.markdown(f"**👥 {cliente}** - {num_facturas} facturas agrupadas")
                        st.write(f"📅 **Vencen el:** {pd.to_datetime(fecha_venc).strftime('%d/%m/%Y')}")
                        
                        # Mostrar todas las facturas del grupo
                        facturas_info = []
                        total_valor = 0
                        total_comision = 0
                        
                        for factura in facturas_grupo:
                            factura_num = factura.get('factura', 'N/A')
                            pedido = factura.get('pedido', 'N/A')
                            valor = factura.get('valor', 0)
                            comision = factura.get('comision', 0)
                            facturas_info.append(f"• Factura #{factura_num} (Pedido: {pedido})")
                            total_valor += float(valor)
                            total_comision += float(comision)
                        
                        with st.expander(f"Ver {num_facturas} factura(s)", expanded=False):
                            for info in facturas_info:
                                st.write(info)
                        
                        st.write(f"💰 **Total:** {format_currency(total_valor)} | **Comisión Total:** {format_currency(total_comision)}")
                    else:
                        # Factura individual
                        factura = primera_factura
                        factura_id = factura.get('id')
                        st.markdown(f"**{cliente}**")
                        st.write(f"📋 Pedido: {factura.get('pedido')} | Factura: {factura.get('factura')}")
                        st.write(f"💰 Valor: {format_currency(factura.get('valor', 0))} | Comisión: {format_currency(factura.get('comision', 0))}")
                        st.write(f"📅 Fecha Vencimiento: {pd.to_datetime(fecha_venc).strftime('%d/%m/%Y')}")
                    
                    # Calcular días desde facturación (usar primera factura)
                    try:
                        fecha_fac = pd.to_datetime(primera_factura.get('fecha_factura'))
                        dias_desde = (pd.Timestamp.now() - fecha_fac).days
                        color_dias = "🟢" if dias_desde <= 3 else "🟡" if dias_desde <= 7 else "🔴"
                        st.caption(f"{color_dias} {dias_desde} días desde la facturación")
                    except:
                        pass
                
                with col2:
                    # Botón para generar mensaje al cliente
                    if st.button(
                        f"💬 Generar Mensaje{' Unificado' if num_facturas > 1 else ''}", 
                        key=f"mensaje_{grupo_id}", 
                        type="primary", 
                        use_container_width=True
                    ):
                        st.session_state[f"show_mensaje_{grupo_id}"] = True
                        safe_rerun()
            
            # Modal para mensaje al cliente
            if st.session_state.get(f"show_mensaje_{grupo_id}", False):
                with st.container(border=True):
                    st.markdown(f"### 💬 Mensaje para Cliente: {cliente}")
                    # Si hay múltiples facturas, usar mensaje unificado
                    if num_facturas > 1:
                        mensaje = self.invoice_radication.generar_mensaje_cliente_unificado(facturas_grupo)
                    else:
                        mensaje = self.invoice_radication.generar_mensaje_cliente(primera_factura)
                    
                    st.markdown("#### Mensaje generado:")
                    st.text_area(
                        "Copie este mensaje:",
                        value=mensaje,
                        height=400,
                        key=f"textarea_mensaje_{grupo_id}"
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success(f"✅ Listo para copiar y enviar al cliente ({num_facturas} factura{'s' if num_facturas > 1 else ''} incluida{'s' if num_facturas > 1 else ''})")
                    with col_b:
                        if st.button("❌ Cerrar", key=f"cerrar_mensaje_{grupo_id}"):
                            if f"show_mensaje_{grupo_id}" in st.session_state:
                                del st.session_state[f"show_mensaje_{grupo_id}"]
                            safe_rerun()
    
    def _render_facturas_urgentes_radicacion(self):
        """Renderiza facturas vencidas - URGENTE (agrupadas por cliente y fecha de vencimiento)"""
        urgentes = self.invoice_radication.obtener_facturas_vencidas_sin_radicar()
        
        if urgentes.empty:
            st.success("✅ No hay facturas urgentes")
            return
        
        # Normalizar nombres de clientes (eliminar espacios extra, convertir a string, normalizar mayúsculas)
        urgentes['cliente'] = urgentes['cliente'].astype(str).str.strip().str.upper()
        
        # Agrupar facturas por cliente y fecha de vencimiento
        # Normalizar fechas: convertir a datetime y luego a fecha (sin hora) para agrupar correctamente
        urgentes['fecha_pago_est'] = pd.to_datetime(urgentes['fecha_pago_est'], errors='coerce')
        # Normalizar a medianoche para eliminar diferencias de hora
        urgentes['fecha_pago_est'] = urgentes['fecha_pago_est'].dt.normalize()
        # Crear string de fecha para agrupar (solo fecha, sin hora)
        urgentes['fecha_vencimiento_str'] = urgentes['fecha_pago_est'].dt.strftime('%Y-%m-%d')
        # También crear columna de fecha para validación
        urgentes['fecha_vencimiento'] = urgentes['fecha_pago_est'].dt.date
        
        # Eliminar filas con fechas inválidas o clientes inválidos antes de agrupar
        urgentes = urgentes[
            (urgentes['fecha_vencimiento'].notna()) & 
            (urgentes['cliente'].notna()) & 
            (urgentes['cliente'] != '') &
            (urgentes['cliente'] != 'NAN')
        ].copy()
        
        # Agrupar por cliente y fecha de vencimiento (usando la fecha normalizada)
        grupos = urgentes.groupby(['cliente', 'fecha_vencimiento_str'], dropna=False, sort=False)
        
        total_grupos = len(grupos)
        total_facturas = len(urgentes)
        
        st.error(f"### 🚨 {total_facturas} Factura(s) URGENTE(S) en {total_grupos} grupo(s)")
        st.warning("Estas facturas están vencidas. Envía el mensaje con urgencia para gestionar el cobro.")
        st.info("💡 Las facturas del mismo cliente que vencen el mismo día se agrupan automáticamente en un solo mensaje")
        
        for (cliente, fecha_venc), grupo in grupos:
            facturas_grupo = grupo.to_dict('records')
            num_facturas = len(facturas_grupo)
            
            # Usar el ID de la primera factura como clave para el grupo
            primera_factura = facturas_grupo[0]
            grupo_id = f"urgente_{cliente}_{fecha_venc}"
            dias_vencida = abs(int(primera_factura.get('dias_vencimiento', 0)))
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Mostrar si es un grupo o factura individual
                    if num_facturas > 1:
                        st.markdown(f"**🚨 {cliente}** - {num_facturas} facturas agrupadas")
                        st.error(f"⏰ **VENCIDAS hace {dias_vencida} días** - Vencían el: {pd.to_datetime(fecha_venc).strftime('%d/%m/%Y')}")
                        
                        # Mostrar todas las facturas del grupo
                        facturas_info = []
                        total_valor = 0
                        total_comision = 0
                        
                        for factura in facturas_grupo:
                            factura_num = factura.get('factura', 'N/A')
                            pedido = factura.get('pedido', 'N/A')
                            valor = factura.get('valor', 0)
                            comision = factura.get('comision', 0)
                            facturas_info.append(f"• Factura #{factura_num} (Pedido: {pedido})")
                            total_valor += float(valor)
                            total_comision += float(comision)
                        
                        with st.expander(f"Ver {num_facturas} factura(s) vencida(s)", expanded=False):
                            for info in facturas_info:
                                st.write(info)
                        
                        st.write(f"💰 **Total:** {format_currency(total_valor)} | **Comisión Total:** {format_currency(total_comision)}")
                    else:
                        # Factura individual
                        factura = primera_factura
                        factura_id = factura.get('id')
                        st.markdown(f"**🚨 {cliente}**")
                        st.write(f"📋 Pedido: {factura.get('pedido')} | Factura: {factura.get('factura')}")
                        st.write(f"💰 Valor: {format_currency(factura.get('valor', 0))} | Comisión: {format_currency(factura.get('comision', 0))}")
                        st.error(f"⏰ VENCIDA hace {dias_vencida} días")
                
                with col2:
                    # Botón para generar mensaje al cliente
                    if st.button(
                        f"💬 Generar Mensaje{' Unificado' if num_facturas > 1 else ''}", 
                        key=f"mensaje_{grupo_id}", 
                        type="primary", 
                        use_container_width=True
                    ):
                        st.session_state[f"show_mensaje_{grupo_id}"] = True
                        safe_rerun()
            
            # Modal para mensaje al cliente
            if st.session_state.get(f"show_mensaje_{grupo_id}", False):
                with st.container(border=True):
                    st.markdown(f"### 💬 Mensaje para Cliente: {cliente}")
                    # Si hay múltiples facturas, usar mensaje unificado
                    if num_facturas > 1:
                        mensaje = self.invoice_radication.generar_mensaje_cliente_unificado(facturas_grupo)
                    else:
                        mensaje = self.invoice_radication.generar_mensaje_cliente(primera_factura)
                    
                    st.markdown("#### Mensaje generado:")
                    st.text_area(
                        "Copie este mensaje:",
                        value=mensaje,
                        height=400,
                        key=f"textarea_mensaje_{grupo_id}"
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success(f"✅ Listo para copiar y enviar al cliente ({num_facturas} factura{'s' if num_facturas > 1 else ''} incluida{'s' if num_facturas > 1 else ''})")
                    with col_b:
                        if st.button("❌ Cerrar", key=f"cerrar_mensaje_{grupo_id}"):
                            if f"show_mensaje_{grupo_id}" in st.session_state:
                                del st.session_state[f"show_mensaje_{grupo_id}"]
                            safe_rerun()
    
    def _render_busqueda_cliente_mensaje(self):
        """Renderiza búsqueda de cliente para generar mensajes"""
        st.markdown("### 👤 Buscar Cliente para Generar Mensaje")
        st.info("Selecciona un cliente para ver sus facturas y generar mensajes personalizados")
        
        # Cargar todas las facturas
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            st.warning("No hay facturas registradas")
            return
        
        # Filtrar solo facturas no pagadas
        df_no_pagadas = df[df['pagado'] == False].copy()
        
        if df_no_pagadas.empty:
            st.success("✅ No hay facturas pendientes de pago")
            return
        
        # Obtener lista de clientes únicos con facturas pendientes
        clientes = sorted(df_no_pagadas['cliente'].unique())
        
        # Selectbox para elegir cliente
        cliente_seleccionado = st.selectbox(
            "📋 Seleccione un cliente:",
            options=["-- Seleccione un cliente --"] + list(clientes),
            key="select_cliente_mensaje"
        )
        
        if cliente_seleccionado == "-- Seleccione un cliente --":
            st.info("👆 Seleccione un cliente para ver sus facturas")
            return
        
        # Filtrar facturas del cliente seleccionado
        facturas_cliente = df_no_pagadas[df_no_pagadas['cliente'] == cliente_seleccionado].copy()
        facturas_cliente = facturas_cliente.sort_values('fecha_factura', ascending=False)
        
        st.markdown(f"### 📊 Facturas de: **{cliente_seleccionado}**")
        st.caption(f"Total de facturas pendientes: {len(facturas_cliente)}")
        
        # Mostrar cada factura
        for index, (_, factura) in enumerate(facturas_cliente.iterrows()):
            factura_id = factura.get('id')
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"📋 **Pedido:** {factura.get('pedido')} | **Factura:** {factura.get('factura')}")
                    st.write(f"💰 Valor: {format_currency(factura.get('valor', 0))} | Comisión: {format_currency(factura.get('comision', 0))}")
                    st.write(f"📅 Fecha Factura: {factura.get('fecha_factura')}")
                    
                    # Mostrar estado según días de vencimiento
                    dias_venc = factura.get('dias_vencimiento')
                    if dias_venc is not None:
                        if dias_venc < 0:
                            st.error(f"⚠️ VENCIDA hace {abs(int(dias_venc))} días")
                        elif dias_venc <= 5:
                            st.warning(f"⏰ Vence en {int(dias_venc)} días")
                        else:
                            st.success(f"✅ Vence en {int(dias_venc)} días")
                
                with col2:
                    # Botón para generar mensaje
                    if st.button("💬 Generar Mensaje", key=f"mensaje_busqueda_{factura_id}", type="primary", use_container_width=True):
                        st.session_state[f"show_mensaje_busqueda_{factura_id}"] = True
                        safe_rerun()
            
            # Modal para mensaje al cliente
            if st.session_state.get(f"show_mensaje_busqueda_{factura_id}", False):
                with st.container(border=True):
                    st.markdown(f"### 💬 Mensaje para: {factura.get('cliente')}")
                    mensaje = self.invoice_radication.generar_mensaje_cliente(factura)
                    
                    st.markdown("#### Mensaje generado:")
                    st.text_area(
                        "Copie este mensaje:",
                        value=mensaje,
                        height=400,
                        key=f"textarea_mensaje_busqueda_{factura_id}"
                    )
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success("✅ Listo para copiar y enviar al cliente")
                    with col_b:
                        if st.button("❌ Cerrar", key=f"cerrar_mensaje_busqueda_{factura_id}"):
                            if f"show_mensaje_busqueda_{factura_id}" in st.session_state:
                                del st.session_state[f"show_mensaje_busqueda_{factura_id}"]
                            safe_rerun()
