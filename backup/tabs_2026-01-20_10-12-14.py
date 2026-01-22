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
from business.sales_pipeline import SalesPipeline
from business.ml_analytics import MLAnalytics
from business.client_product_recommendations import ClientProductRecommendations
from ui.client_recommendations_components import ClientRecommendationsUI
from database.catalog_manager import CatalogManager
from ui.catalog_store_components import CatalogStoreUI
from database.client_purchases_manager import ClientPurchasesManager
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
    # TAB DASHBOARD EJECUTIVO
    # ========================
    
    def render_executive_dashboard(self):
        """Renderiza el Dashboard Ejecutivo Profesional para Gerencia"""
        # Limpiar flags de procesamiento
        self._clear_processing_flags()
        
        try:
            from ui.theme_manager import ThemeManager
            
            theme = ThemeManager.get_theme()
            
            # Título personalizado
            st.markdown(
                f"""
                <div style='text-align: center; margin-bottom: 2rem;'>
                    <h1 style='
                        font-size: 2.5rem;
                        font-weight: 800;
                        background: {theme['gradient_1']};
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        margin-bottom: 0.5rem;
                    '>
                        📊 Dashboard Ejecutivo
                    </h1>
                    <p style='color: {theme['text_secondary']}; font-size: 1rem;'>
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
            
            # ========== SECCIÓN 5: TOP PERFORMERS ==========
            st.markdown("---")
            st.markdown("### 🏆 Top Performers")
            ExecutiveComponents.render_top_performers(summary['top_performers'])
            
            # ========== SECCIÓN 6: PROYECCIONES ==========
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
        """Renderiza la pestaña de nueva venta simple (versión anterior básica)"""
        st.header("➕ Nueva Venta Simple")
        st.caption("Formulario simplificado para registrar ventas rápidamente")
        
        # Obtener lista de clientes existentes
        lista_clientes = self.db_manager.obtener_lista_clientes()
        
        # Formulario simple
        with st.form("nueva_venta_simple_form", clear_on_submit=True):
            st.markdown("### 📋 Información de la Venta")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pedido = st.text_input("Número de Pedido *", placeholder="Ej: PED-001", key="nueva_venta_simple_pedido")
                
                # Selector de cliente con opción de nuevo
                opciones_clientes = ["-- Nuevo Cliente --"] + lista_clientes
                cliente_seleccionado = st.selectbox(
                    "Cliente *",
                    opciones_clientes,
                    key="nueva_venta_simple_cliente_select",
                    help="Selecciona un cliente existente o crea uno nuevo"
                )
                
                # Asignar cliente según selección
                if cliente_seleccionado == "-- Nuevo Cliente --":
                    cliente = st.text_input(
                        "Nombre del Cliente *", 
                        placeholder="Ej: DISTRIBUIDORA CENTRAL", 
                        key="nueva_venta_simple_cliente_nombre"
                    )
                else:
                    cliente = cliente_seleccionado
                
                factura = st.text_input("Número de Factura", placeholder="Ej: FAC-1001", key="nueva_venta_simple_factura")
            
            with col2:
                fecha_factura = st.date_input("Fecha de Factura *", value=date.today(), key="nueva_venta_simple_fecha")
                
                valor_total = st.number_input(
                    "Valor Total (con IVA) *", 
                    min_value=0.0, 
                    step=10000.0, 
                    format="%.0f", 
                    key="nueva_venta_simple_valor",
                    help="Valor total incluyendo IVA"
                )
                
                # Checkbox para marcar si es cliente nuevo
                es_cliente_nuevo = st.checkbox(
                    "Cliente Nuevo (cuenta para meta)", 
                    value=(cliente_seleccionado == "-- Nuevo Cliente --"),
                    key="nueva_venta_simple_es_cliente_nuevo",
                    help="Marca esto si es la primera vez que este cliente compra"
                )
            
            st.markdown("### Información de Envío")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                ciudad_destino = st.selectbox(
                    "Ciudad de Destino *",
                    options=["Medellín", "Bogotá", "Resto"],
                    index=0,
                    key="nueva_venta_simple_ciudad",
                    help="Ciudad donde se enviará el pedido"
                )
            
            with col2:
                # Checkbox de recogida local (solo visible si es Medellín)
                if ciudad_destino == "Medellín":
                    recogida_local = st.checkbox(
                        "Recogida Local",
                        value=False,
                        key="nueva_venta_simple_recogida_local",
                        help="El cliente recoge el pedido localmente (sin flete)"
                    )
                else:
                    recogida_local = False
                    st.info("Recogida local solo disponible para Medellín")
            
            with col3:
                # Campo de flete
                valor_flete = st.number_input(
                    "Valor Flete",
                    min_value=0.0,
                    step=10000.0,
                    format="%.0f",
                    value=0.0,
                    key="nueva_venta_simple_flete",
                    help="Valor del flete (si aplica)"
                )
            
            st.markdown("### Configuración de Comisión")
            
            # Valores por defecto basados en patrón del cliente
            cliente_propio_default = False
            descuento_pie_default = False
            condicion_especial_default = False
            descuento_adicional_default = 0.0
            
            if cliente and cliente != "-- Nuevo Cliente --":
                patron_cliente = self.db_manager.obtener_patron_cliente(cliente)
                if patron_cliente.get('existe', False):
                    cliente_propio_default = patron_cliente.get('cliente_propio', False)
                    descuento_pie_default = patron_cliente.get('descuento_pie_factura', False)
                    condicion_especial_default = patron_cliente.get('condicion_especial', False)
                    descuento_adicional_default = patron_cliente.get('descuento_adicional', 0.0)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                cliente_propio = st.checkbox(
                    "Cliente Propio", 
                    value=cliente_propio_default, 
                    key="nueva_venta_simple_cliente_propio"
                )
            with col2:
                descuento_pie_factura = st.checkbox(
                    "Descuento a Pie", 
                    value=descuento_pie_default, 
                    key="nueva_venta_simple_descuento_pie"
                )
            with col3:
                condicion_especial = st.checkbox(
                    "Condición Especial", 
                    value=condicion_especial_default, 
                    key="nueva_venta_simple_condicion"
                )
            with col4:
                descuento_adicional = st.number_input(
                    "Desc. Adicional (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    step=0.5, 
                    value=descuento_adicional_default, 
                    key="nueva_venta_simple_descuento_adicional",
                    help="Descuento adicional a aplicar"
                )
            
            # Preview de comisión
            if valor_total > 0:
                st.markdown("---")
                st.markdown("### Preview de Comisión")
                
                # Restar el flete antes de calcular la comisión
                valor_productos_con_iva = valor_total - valor_flete
                
                # Calcular valor_neto e IVA correctamente desde el total
                # El valor total ya incluye todos los descuentos aplicados
                valor_neto_calculado = valor_productos_con_iva / 1.19
                iva_calculado = valor_productos_con_iva - valor_neto_calculado
                
                # Total final sin flete (para cálculo de comisión)
                total_con_descuento_pie = valor_neto_calculado + iva_calculado
                
                # Calcular comisión
                tiene_descuento_adicional = descuento_adicional > 0
                calc = self.comision_calc.calcular_comision_inteligente(
                    total_con_descuento_pie, 
                    cliente_propio, 
                    tiene_descuento_adicional, 
                    descuento_pie_factura
                )
                
                # Calcular descuento a pie si aplica (para mostrar en preview)
                # El descuento a pie (15%) ya está reflejado en el valor_total proporcionado
                # Si hay descuento a pie, el valor_neto es directamente el calculado
                # Si NO hay descuento a pie, el valor_neto sería menor (85% del original)
                if descuento_pie_factura:
                    descuento_pie_monto = 0  # Ya está incluido en el valor_total
                else:
                    # Sin descuento a pie, el valor_neto base sería mayor
                    # Calcular cuál sería el valor_neto si no hubiera descuento a pie
                    valor_neto_sin_descuento_pie = valor_neto_calculado / 0.85
                    descuento_pie_monto = valor_neto_sin_descuento_pie - valor_neto_calculado
                
                # Mostrar métricas
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Valor Base", format_currency(valor_productos_con_iva))
                with col2:
                    st.metric("Descuento Pie", format_currency(descuento_pie_monto) if descuento_pie_factura else format_currency(0))
                with col3:
                    st.metric("Comisión", format_currency(calc['comision']))
                with col4:
                    st.metric("Porcentaje", f"{calc['porcentaje']}%")
            
            # Botón de submit
            submitted = st.form_submit_button("💾 Registrar Venta", type="primary", use_container_width=True)
            
            if submitted:
                # Validar campos
                if not pedido or not cliente or not valor_total or valor_total <= 0:
                    st.error("❌ Por favor completa todos los campos marcados con *")
                elif cliente_seleccionado == "-- Nuevo Cliente --" and (not cliente or not cliente.strip()):
                    st.error("❌ Por favor ingresa el nombre del cliente")
                elif cliente_seleccionado != "-- Nuevo Cliente --" and not cliente:
                    st.error("❌ Por favor selecciona un cliente válido")
                else:
                    # Procesar venta (usar el método existente pero sin productos)
                    self._procesar_nueva_venta(
                        pedido=pedido,
                        cliente=cliente,
                        factura=factura if factura else f"FAC-{pedido}",
                        fecha_factura=fecha_factura,
                        valor_total=valor_total,
                        condicion_especial=condicion_especial,
                        cliente_propio=cliente_propio,
                        descuento_pie_factura=descuento_pie_factura,
                        descuento_adicional=descuento_adicional,
                        es_cliente_nuevo=es_cliente_nuevo,
                        ciudad_destino=ciudad_destino,
                        recogida_local=recogida_local,
                        valor_flete=valor_flete,
                        cliente_nit=None,
                        productos_venta=None
                    )
    
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
