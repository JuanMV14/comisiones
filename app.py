#!/usr/bin/env python3
"""
CRM Inteligente - Versión Optimizada
Sistema completo de gestión de comisiones con IA, alertas y recomendaciones
"""

import os
import streamlit as st
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
from supabase import create_client, Client

# Importar módulos del sistema
from database.queries import DatabaseManager
from ui.components import UIComponents
from ui.tabs import TabRenderer
from business.calculations import ComisionCalculator, MetricsCalculator
from business.ai_recommendations import AIRecommendations
from business.client_classification import ClientClassifier
from business.monthly_commission_calculator import MonthlyCommissionCalculator
from business.invoice_alerts import InvoiceAlertsSystem
from business.product_recommendations import ProductRecommendationSystem
from utils.formatting import format_currency
from config.settings import AppConfig

# ========================
# CONFIGURACIÓN INICIAL
# ========================
load_dotenv()

# Validar configuración
config_validation = AppConfig.validate_environment()
if not config_validation["valid"]:
    st.error("❌ Error de configuración:")
    for error in config_validation["errors"]:
        st.error(f"- {error}")
    st.stop()

# Configurar Supabase
supabase: Client = create_client(
    AppConfig.SUPABASE_URL, 
    AppConfig.SUPABASE_KEY
)

# Configurar Streamlit
st.set_page_config(
    page_title=AppConfig.APP_TITLE,
    layout=AppConfig.PAGE_LAYOUT,
    initial_sidebar_state="expanded",
    page_icon=AppConfig.APP_ICON
)

# ========================
# INICIALIZACIÓN DE SISTEMAS
# ========================
@st.cache_resource
def initialize_systems():
    """Inicializa todos los sistemas del CRM"""
    # Sistema de base de datos
    db_manager = DatabaseManager(supabase)
    
    # Sistemas de negocio
    comision_calc = ComisionCalculator()
    metrics_calc = MetricsCalculator()
    ai_recommendations = AIRecommendations(db_manager)
    
    # Nuevos sistemas
    client_classifier = ClientClassifier(db_manager)
    monthly_calc = MonthlyCommissionCalculator(db_manager)
    invoice_alerts = InvoiceAlertsSystem(db_manager)
    product_recommendations = ProductRecommendationSystem(db_manager)
    
    # Sistema de UI
    ui_components = UIComponents(db_manager)
    tab_renderer = TabRenderer(db_manager, ui_components)
    
    return {
        "db_manager": db_manager,
        "comision_calc": comision_calc,
        "metrics_calc": metrics_calc,
        "ai_recommendations": ai_recommendations,
        "client_classifier": client_classifier,
        "monthly_calc": monthly_calc,
        "invoice_alerts": invoice_alerts,
        "product_recommendations": product_recommendations,
        "ui_components": ui_components,
        "tab_renderer": tab_renderer
    }

# ========================
# FUNCIONES DE UI ESPECÍFICAS
# ========================
def render_client_classification_tab(systems):
    """Renderiza la pestaña de clasificación de clientes"""
    st.header("🤖 Clasificación de Clientes con IA")
    
    client_classifier = systems["client_classifier"]
    
    # Sección de entrenamiento del modelo
    st.markdown("### Entrenar Modelo de Clasificación")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        meses_historial = st.slider(
            "Meses de historial para entrenar",
            min_value=3,
            max_value=24,
            value=12,
            help="Recomendado: 12-18 meses para modelos robustos"
        )
    
    with col2:
        if st.button("🚀 Entrenar Modelo", type="primary"):
            with st.spinner("Entrenando modelo de clasificación..."):
                resultado = client_classifier.entrenar_modelo(meses_historial)
            
            if resultado["success"]:
                st.success("✅ Modelo entrenado exitosamente!")
                
                # Mostrar resultados del entrenamiento
                st.markdown("#### Resultados del Entrenamiento")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Clientes Entrenados", resultado["clientes_entrenados"])
                with col2:
                    st.metric("Meses Analizados", resultado["meses_analizados"])
                with col3:
                    st.metric("Clusters Identificados", len(resultado["clusters"]))
                
                # Mostrar clusters
                st.markdown("#### Clusters de Clientes Identificados")
                for cluster_id, cluster_data in resultado["clusters"].items():
                    with st.expander(f"{cluster_data['caracteristicas']['nombre']} ({cluster_data['cantidad']} clientes)"):
                        st.write(f"**Descripción:** {cluster_data['caracteristicas']['descripcion']}")
                        st.write(f"**Estrategia:** {cluster_data['caracteristicas']['estrategia_recomendada']}")
                        st.write(f"**Productos sugeridos:** {', '.join(cluster_data['caracteristicas']['productos_sugeridos'])}")
                        
                        # Mostrar métricas
                        metricas = cluster_data['caracteristicas']['metricas_promedio']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Frecuencia", f"{metricas['frecuencia_compras']:.1f}")
                        with col2:
                            st.metric("Ticket Promedio", format_currency(metricas['ticket_promedio']))
                        with col3:
                            st.metric("Puntualidad", f"{metricas['puntualidad_pago']:.0f} días")
                
                # Recomendación de tiempo
                st.info(f"💡 **Recomendación:** {resultado['recomendacion_tiempo']}")
                
            else:
                st.error(f"❌ Error: {resultado['message']}")
                st.info(f"💡 **Sugerencia:** {resultado['recomendacion']}")
    
    st.markdown("---")
    
    # Sección de recomendaciones por cliente
    st.markdown("### Recomendaciones por Cliente")
    
    # Obtener lista de clientes
    df = systems["db_manager"].cargar_datos()
    if not df.empty:
        clientes = df['cliente'].unique()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            cliente_seleccionado = st.selectbox(
                "Seleccionar Cliente",
                clientes,
                help="Selecciona un cliente para ver recomendaciones de importación"
            )
        
        with col2:
            if st.button("📋 Generar Recomendaciones"):
                with st.spinner("Generando recomendaciones..."):
                    recomendaciones = systems["product_recommendations"].generar_recomendaciones_importacion(cliente_seleccionado)
                
                if "error" not in recomendaciones:
                    st.success(f"✅ Recomendaciones generadas para {cliente_seleccionado}")
                    
                    # Mostrar recomendaciones
                    perfil = recomendaciones["perfil_cliente"]
                    rec = recomendaciones["recomendaciones"]
                    
                    # Perfil del cliente
                    st.markdown("#### Perfil del Cliente")
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Clasificación", perfil["clasificacion"])
                    with col2:
                        st.metric("Volumen Total", format_currency(perfil["volumen_total"]))
                    with col3:
                        st.metric("Ticket Promedio", format_currency(perfil["ticket_promedio"]))
                    with col4:
                        st.metric("Puntualidad", perfil["puntualidad"])
                    
                    # Recomendaciones de productos
                    st.markdown("#### Productos Recomendados")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Productos Principales:**")
                        for producto in rec["productos_principales"]:
                            st.write(f"• {producto}")
                    
                    with col2:
                        st.markdown("**Productos Complementarios:**")
                        for producto in rec["productos_complementarios"]:
                            st.write(f"• {producto}")
                    
                    # Descuentos aplicables
                    st.markdown("#### Descuentos Aplicables")
                    descuentos = recomendaciones["descuentos_aplicables"]
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Descuento Base", f"{descuentos['descuento_base']*100:.1f}%")
                    with col2:
                        st.metric("Descuento Adicional", f"{descuentos['descuento_adicional']*100:.1f}%")
                    with col3:
                        st.metric("Bonificación Puntualidad", f"{descuentos['bonificacion_puntualidad']*100:.1f}%")
                    with col4:
                        st.metric("Descuento Total", f"{descuentos['descuento_total']*100:.1f}%")
                    
                    # Mensaje personalizado
                    st.markdown("#### Mensaje Personalizado")
                    st.info(recomendaciones["mensaje_personalizado"])
                    
                    # Estrategia de contacto
                    estrategia = recomendaciones["estrategia_contacto"]
                    st.markdown("#### Estrategia de Contacto")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Canal:** {estrategia['canal_preferido']}")
                        st.write(f"**Frecuencia:** {estrategia['frecuencia_contacto']}")
                    with col2:
                        st.write(f"**Momento óptimo:** {estrategia['momento_optimo']}")
                        st.write(f"**Objetivo:** {estrategia['objetivo_contacto']}")
                
                else:
                    st.error(f"❌ Error: {recomendaciones['error']}")
    else:
        st.warning("No hay datos de clientes disponibles")

def render_monthly_commissions_tab(systems):
    """Renderiza la pestaña de comisiones mensuales"""
    st.header("💰 Comisiones Mensuales")
    
    monthly_calc = systems["monthly_calc"]
    
    # Selector de mes
    col1, col2 = st.columns([1, 1])
    
    with col1:
        mes_seleccionado = st.selectbox(
            "Seleccionar Mes",
            ["Mes Anterior", "Mes Actual", "Mes Específico"],
            help="Selecciona el mes para calcular comisiones"
        )
    
    with col2:
        if mes_seleccionado == "Mes Específico":
            mes_input = st.text_input(
                "Mes (YYYY-MM)",
                value=date.today().strftime("%Y-%m"),
                help="Formato: 2024-01"
            )
        else:
            mes_input = None
    
    # Botón de cálculo
    if st.button("📊 Calcular Comisiones", type="primary"):
        with st.spinner("Calculando comisiones..."):
            if mes_seleccionado == "Mes Anterior":
                resultado = monthly_calc.calcular_comisiones_mes()
            elif mes_seleccionado == "Mes Actual":
                resultado = monthly_calc.calcular_proyeccion_mes_actual()
            else:
                resultado = monthly_calc.calcular_comisiones_mes(mes_input)
        
        if "error" not in resultado:
            st.success("✅ Comisiones calculadas exitosamente!")
            
            # Mostrar resumen principal
            st.markdown("#### Resumen de Comisiones")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Comisiones Brutas",
                    format_currency(resultado.get("total_comisiones_brutas", resultado.get("proyeccion_comisiones_brutas", 0)))
                )
            with col2:
                st.metric(
                    "Descuento Salud (4%)",
                    format_currency(resultado.get("descuento_salud", 0))
                )
            with col3:
                st.metric(
                    "Descuento Reserva (2.5%)",
                    format_currency(resultado.get("descuento_reserva", 0))
                )
            with col4:
                st.metric(
                    "Comisiones Netas",
                    format_currency(resultado.get("comisiones_netas", resultado.get("proyeccion_comisiones_netas", 0)))
                )
            
            # Mostrar detalles
            if "detalle_facturas" in resultado:
                st.markdown("#### Detalle de Facturas")
                
                # Crear DataFrame para mostrar
                df_detalle = pd.DataFrame(resultado["detalle_facturas"])
                
                if not df_detalle.empty:
                    # Mostrar columnas relevantes
                    columnas_mostrar = [
                        "cliente", "pedido", "factura", "valor", 
                        "comision", "comision_final", "descuento_aplicado"
                    ]
                    
                    df_mostrar = df_detalle[columnas_mostrar].copy()
                    df_mostrar.columns = [
                        "Cliente", "Pedido", "Factura", "Valor",
                        "Comisión Original", "Comisión Final", "Descuento Aplicado"
                    ]
                    
                    st.dataframe(df_mostrar, use_container_width=True)
            
            # Mostrar resumen por cliente
            if "resumen_por_cliente" in resultado:
                st.markdown("#### Resumen por Cliente")
                
                df_resumen = pd.DataFrame(resultado["resumen_por_cliente"])
                if not df_resumen.empty:
                    st.dataframe(df_resumen, use_container_width=True)
            
            # Mostrar alertas
            if "alertas" in resultado and resultado["alertas"]:
                st.markdown("#### Alertas")
                for alerta in resultado["alertas"]:
                    st.warning(f"⚠️ {alerta}")
            
            # Mostrar proyección si es mes actual
            if mes_seleccionado == "Mes Actual" and "probabilidad_cumplimiento" in resultado:
                st.markdown("#### Proyección del Mes")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "Probabilidad Cumplimiento",
                        f"{resultado['probabilidad_cumplimiento']:.1f}%"
                    )
                
                with col2:
                    st.metric(
                        "Velocidad Actual",
                        format_currency(resultado.get("velocidad_actual", 0)) + "/día"
                    )
        
        else:
            st.error(f"❌ Error: {resultado['error']}")
    
    st.markdown("---")
    
    # Historial de comisiones
    st.markdown("### Historial de Comisiones")
    
    if st.button("📈 Ver Historial"):
        with st.spinner("Obteniendo historial..."):
            historial = monthly_calc.obtener_historial_comisiones(12)
        
        if "error" not in historial:
            st.success("✅ Historial obtenido exitosamente!")
            
            # Mostrar gráfico de tendencias
            if historial["historial"]:
                df_historial = pd.DataFrame(historial["historial"])
                df_historial['mes'] = pd.to_datetime(df_historial['mes'])
                
                st.markdown("#### Tendencias de Comisiones")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Tendencia", f"{historial['tendencia_porcentaje']:+.1f}%")
                with col2:
                    st.metric("Promedio Mensual", format_currency(historial['promedio_mensual']))
                with col3:
                    st.metric("Total Período", format_currency(historial['total_periodo']))
                
                # Gráfico de líneas
                st.line_chart(
                    df_historial.set_index('mes')['comisiones_netas'],
                    use_container_width=True
                )
        else:
            st.error(f"❌ Error: {historial['error']}")

def render_invoice_alerts_tab(systems):
    """Renderiza la pestaña de alertas de facturas"""
    st.header("🚨 Alertas de Vencimiento")
    
    invoice_alerts = systems["invoice_alerts"]
    
    # Botón para generar alertas
    if st.button("🔍 Generar Alertas", type="primary"):
        with st.spinner("Generando alertas..."):
            alertas = invoice_alerts.generar_alertas_vencimiento()
        
        if "error" not in alertas:
            st.success("✅ Alertas generadas exitosamente!")
            
            # Mostrar resumen
            resumen = alertas["resumen"]
            st.markdown("#### Resumen de Alertas")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Alertas", resumen["total_alertas"])
            with col2:
                st.metric("Críticas", resumen["criticas"], delta=f"-{resumen['criticas']}" if resumen['criticas'] > 0 else None)
            with col3:
                st.metric("Urgentes", resumen["urgentes"])
            with col4:
                st.metric("Normales", resumen["normales"])
            
            # Mostrar montos en riesgo
            st.markdown("#### Montos en Riesgo")
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Monto Total en Riesgo",
                    format_currency(resumen["monto_total_riesgo"])
                )
            with col2:
                st.metric(
                    "Comisión en Riesgo",
                    format_currency(resumen["comision_total_riesgo"])
                )
            
            # Mostrar alertas por categoría
            if alertas["alertas"]:
                st.markdown("#### Alertas Detalladas")
                
                # Agrupar por tipo
                alertas_criticas = [a for a in alertas["alertas"] if a["tipo"] == "CRÍTICA"]
                alertas_urgentes = [a for a in alertas["alertas"] if a["tipo"] == "URGENTE"]
                alertas_normales = [a for a in alertas["alertas"] if a["tipo"] == "NORMAL"]
                
                # Mostrar alertas críticas
                if alertas_criticas:
                    st.markdown("##### 🚨 Alertas Críticas")
                    for alerta in alertas_criticas:
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{alerta['cliente']}** - {alerta['pedido']}")
                                st.write(f"Factura: {alerta['factura']} | Valor: {format_currency(alerta['valor'])}")
                                st.write(f"Comisión: {format_currency(alerta['comision'])} | {alerta['mensaje']}")
                                st.write(f"**Acción:** {alerta['accion_recomendada']}")
                            
                            with col2:
                                st.error(f"🚨 {alerta['dias_vencida']} días vencida")
                
                # Mostrar alertas urgentes
                if alertas_urgentes:
                    st.markdown("##### ⚠️ Alertas Urgentes")
                    for alerta in alertas_urgentes:
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{alerta['cliente']}** - {alerta['pedido']}")
                                st.write(f"Factura: {alerta['factura']} | Valor: {format_currency(alerta['valor'])}")
                                st.write(f"Comisión: {format_currency(alerta['comision'])} | {alerta['mensaje']}")
                                st.write(f"**Acción:** {alerta['accion_recomendada']}")
                            
                            with col2:
                                st.warning(f"⚠️ {alerta['dias_restantes']} días restantes")
                
                # Mostrar alertas normales
                if alertas_normales:
                    st.markdown("##### ⏰ Alertas Normales")
                    for alerta in alertas_normales:
                        with st.container(border=True):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**{alerta['cliente']}** - {alerta['pedido']}")
                                st.write(f"Factura: {alerta['factura']} | Valor: {format_currency(alerta['valor'])}")
                                st.write(f"Comisión: {format_currency(alerta['comision'])} | {alerta['mensaje']}")
                                st.write(f"**Acción:** {alerta['accion_recomendada']}")
                            
                            with col2:
                                st.info(f"⏰ {alerta['dias_restantes']} días restantes")
            
            # Mostrar recomendaciones
            if alertas["recomendaciones"]:
                st.markdown("#### Recomendaciones")
                for rec in alertas["recomendaciones"]:
                    if rec["tipo"] == "CLIENTE_PROBLEMÁTICO":
                        st.error(f"🚨 **{rec['cliente']}**: {rec['problema']}")
                        st.write(f"**Acción:** {rec['accion']}")
                    else:
                        st.warning(f"⚠️ **{rec['problema']}**")
                        st.write(f"**Acción:** {rec['accion']}")
        
        else:
            st.error(f"❌ Error: {alertas['error']}")
    
    st.markdown("---")
    
    # Recordatorios automáticos
    st.markdown("### Recordatorios Automáticos")
    
    if st.button("📅 Generar Recordatorios"):
        with st.spinner("Generando recordatorios..."):
            recordatorios = invoice_alerts.generar_recordatorios_automaticos()
        
        if "error" not in recordatorios:
            st.success("✅ Recordatorios generados exitosamente!")
            
            resumen = recordatorios["resumen"]
            st.markdown("#### Resumen de Recordatorios")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Recordatorios", resumen["total_recordatorios"])
            with col2:
                st.metric("Primeros", resumen["primeros"])
            with col3:
                st.metric("Segundos", resumen["segundos"])
            with col4:
                st.metric("Finales", resumen["finales"])
            
            # Mostrar recordatorios
            if recordatorios["recordatorios"]:
                st.markdown("#### Recordatorios a Enviar")
                for recordatorio in recordatorios["recordatorios"]:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        
                        with col1:
                            st.markdown(f"**{recordatorio['cliente']}** - {recordatorio['pedido']}")
                            st.write(f"Factura: {recordatorio['factura']} | Valor: {format_currency(recordatorio['valor'])}")
                            st.write(f"**Mensaje:** {recordatorio['mensaje']}")
                            st.write(f"**Acción:** {recordatorio['accion']}")
                        
                        with col2:
                            if recordatorio['tipo'] == 'PRIMER_RECORDATORIO':
                                st.info(f"📧 {recordatorio['dias_restantes']} días")
                            elif recordatorio['tipo'] == 'SEGUNDO_RECORDATORIO':
                                st.warning(f"📞 {recordatorio['dias_restantes']} días")
                            else:
                                st.error(f"🚨 {recordatorio['dias_restantes']} días")
        
        else:
            st.error(f"❌ Error: {recordatorios['error']}")

# ========================
# APLICACIÓN PRINCIPAL
# ========================
def main():
    """Aplicación principal optimizada"""
    # Cargar CSS
    load_css()
    
    # Inicializar sistemas
    systems = initialize_systems()
    
    # Sidebar
    with st.sidebar:
        st.title("🧠 CRM Inteligente")
        st.markdown("---")
        
        # Meta mensual
        systems["ui_components"].render_sidebar_meta()
        
        st.markdown("---")
        
        # Filtros globales
        filtros = systems["ui_components"].render_sidebar_filters()
        
        # Botón de limpieza
        if st.button("🔄 Limpiar Estados"):
            keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.cache_data.clear()
            st.rerun()
    
    # Layout principal
    st.title("🧠 CRM Inteligente - Versión Optimizada")
    
    # Tabs principales
    tabs = st.tabs([
        "Dashboard",
        "Comisiones",
        "Nueva Venta",
        "Devoluciones",
        "Clientes",
        "🤖 Clasificación IA",
        "💰 Comisiones Mensuales",
        "🚨 Alertas Facturas",
        "IA & Recomendaciones"
    ])
    
    # Tab 1-5: Tabs existentes
    with tabs[0]:
        systems["tab_renderer"].render_dashboard()
    
    with tabs[1]:
        systems["tab_renderer"].render_comisiones()
    
    with tabs[2]:
        systems["tab_renderer"].render_nueva_venta()
    
    with tabs[3]:
        systems["tab_renderer"].render_devoluciones()
    
    with tabs[4]:
        systems["tab_renderer"].render_clientes()
    
    # Tab 6: Clasificación de Clientes
    with tabs[5]:
        render_client_classification_tab(systems)
    
    # Tab 7: Comisiones Mensuales
    with tabs[6]:
        render_monthly_commissions_tab(systems)
    
    # Tab 8: Alertas de Facturas
    with tabs[7]:
        render_invoice_alerts_tab(systems)
    
    # Tab 9: IA y Recomendaciones (existente)
    with tabs[8]:
        systems["tab_renderer"].render_ia_alertas()

def load_css():
    """Carga estilos CSS para fondo oscuro"""
    st.markdown("""
    <style>
        .main .block-container {
            background-color: #0f1419 !important;
            color: #ffffff !important;
        }
        
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stText, p, span, div {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 800 !important;
            text-shadow: 0 0 10px rgba(255,255,255,0.3) !important;
        }
        
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid #ffffff !important;
            border-radius: 0.75rem !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px) !important;
        }
        
        div[data-testid="metric-container"] > div {
            color: #ffffff !important;
            font-weight: 800 !important;
            font-size: 16px !important;
        }
        
        .stButton > button {
            border-radius: 0.5rem !important;
            border: 2px solid #ffffff !important;
            font-weight: 800 !important;
            font-size: 14px !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            transition: all 0.2s ease !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.2) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255,255,255,0.2) !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            font-weight: 900 !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.1);
            padding: 0.5rem;
            border-radius: 0.75rem;
            border: 2px solid #ffffff;
            backdrop-filter: blur(10px);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid #ffffff !important;
            border-radius: 0.5rem !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            padding: 0.75rem 1.5rem !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            font-weight: 900 !important;
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 1rem;
            height: 1.5rem;
            overflow: hidden;
            width: 100%;
            border: 2px solid #ffffff;
            backdrop-filter: blur(10px);
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 1rem;
            transition: width 0.3s ease;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid #ffffff;
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(255,255,255,0.1);
            color: #ffffff;
            backdrop-filter: blur(15px);
        }
        
        .alert-high { 
            background: rgba(239, 68, 68, 0.2); 
            border: 2px solid #ef4444;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .alert-medium { 
            background: rgba(251, 146, 60, 0.2); 
            border: 2px solid #fb923c;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .alert-low { 
            background: rgba(34, 197, 94, 0.2); 
            border: 2px solid #22c55e;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")
