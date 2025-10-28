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
from ui.theme_manager import ThemeManager
from ui.modern_components import ModernComponents
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
    modern_components = ModernComponents()
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
        "modern_components": modern_components,
        "tab_renderer": tab_renderer
    }

# ========================
# FUNCIONES DE UI ESPECÍFICAS
# ========================
def render_client_classification_tab(systems):
    """Renderiza la pestaña de clasificación de clientes"""
    st.header("🚧 Clasificación de Clientes con IA")
    
    st.markdown("---")
    
    # Mensaje de construcción
    st.info("### 🔨 Esta funcionalidad está en construcción")
    
    st.markdown("""
    **Próximamente:**
    
    - 🤖 Clasificación automática de clientes con Inteligencia Artificial
    - 📊 Análisis de patrones de compra y comportamiento
    - 🎯 Segmentación avanzada de clientes
    - 💡 Recomendaciones personalizadas por segmento
    - 📈 Predicción de comportamiento futuro
    - 🏷️ Análisis de marcas preferidas
    - 📉 Identificación de clientes en riesgo
    
    ---
    
    **Estado actual:** En desarrollo
    
    **Fecha estimada:** Próxima actualización
    """)
    
    # Placeholder visual
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Funcionalidad", "En desarrollo", delta="0%")
    with col2:
        st.metric("Progreso", "Planificación", delta="Fase inicial")
    with col3:
        st.metric("Estado", "🚧", delta="Próximamente")
    
    st.markdown("---")
    
    st.warning("💡 **Nota:** Esta funcionalidad estará disponible en una próxima actualización del sistema.")

def render_monthly_commissions_tab(systems):
    """Renderiza la pestaña de comisiones mensuales"""
    st.header("Comisiones Mensuales")
    
    monthly_calc = systems["monthly_calc"]
    
    # Selector de mes
    col1, col2 = st.columns([1, 1])
    
    with col1:
        mes_seleccionado = st.selectbox(
            "Seleccionar Mes",
            ["Mes Anterior", "Mes Actual", "Mes Específico"],
            help="Selecciona el mes para calcular comisiones",
            key="mes_comisiones"
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
    if st.button("Calcular Comisiones", type="primary"):
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
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Comisiones Brutas",
                    format_currency(resultado.get("total_comisiones_brutas", resultado.get("proyeccion_comisiones_brutas", 0)))
                )
            with col2:
                st.metric(
                    "Comisiones Netas",
                    format_currency(resultado.get("comisiones_netas", resultado.get("proyeccion_comisiones_netas", 0)))
                )
            
            st.markdown("#### Descuentos Aplicados")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Descuento Salud (4%)",
                    format_currency(resultado.get("descuento_salud", 0))
                )
            with col2:
                st.metric(
                    "Descuento Pensión (4%)",
                    format_currency(resultado.get("descuento_pension", 0))
                )
            with col3:
                st.metric(
                    "Descuento Reserva (2.5%)",
                    format_currency(resultado.get("descuento_reserva", 0))
                )
            with col4:
                st.metric(
                    "Total Descuentos (10.5%)",
                    format_currency(resultado.get("total_descuentos", 0))
                )
            
            # Mostrar detalles
            if "detalle_facturas" in resultado:
                st.markdown("---")
                st.markdown("#### 📋 Detalle de Facturas Contadas")
                
                # Crear DataFrame para mostrar
                df_detalle = pd.DataFrame(resultado["detalle_facturas"])
                
                if not df_detalle.empty:
                    st.info(f"**Total de facturas contadas:** {len(df_detalle)} facturas pagadas en este mes")
                    
                    # Preparar datos para mostrar
                    df_mostrar = df_detalle.copy()
                    
                    # Formatear montos
                    df_mostrar['Valor'] = df_mostrar['valor'].apply(lambda x: format_currency(x))
                    df_mostrar['Comisión Original'] = df_mostrar['comision'].apply(lambda x: format_currency(x))
                    df_mostrar['Comisión Final'] = df_mostrar['comision_final'].apply(lambda x: format_currency(x))
                    # Calcular porcentaje de descuento correctamente
                    # No mostrar descuento si hay devoluciones (causa cálculos incorrectos)
                    df_mostrar['Descuento'] = df_mostrar.apply(
                        lambda row: "N/A (Dev.)" if row.get('valor_devuelto', 0) > 0
                        else f"{((row['comision'] - row['comision_final']) / row['comision'] * 100):.1f}%" 
                        if row['comision'] > 0 and row['comision'] != row['comision_final']
                        else "0.0%", 
                        axis=1
                    )
                    
                    # Seleccionar y renombrar columnas
                    columnas_finales = {
                        'cliente': 'Cliente',
                        'pedido': 'Pedido',
                        'factura': 'Factura',
                        'fecha_pago': 'Fecha Pago',
                        'Valor': 'Valor Factura',
                        'Comisión Original': 'Comisión Base',
                        'Descuento': 'Desc. Aplicado',
                        'Comisión Final': 'Comisión Final'
                    }
                    
                    df_display = df_mostrar[list(columnas_finales.keys())].copy()
                    df_display.columns = list(columnas_finales.values())
                    
                    # Mostrar tabla
                    st.dataframe(df_display, use_container_width=True, hide_index=True)
                    
                    # Mostrar totales al final
                    st.markdown("##### Resumen de Totales:")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        total_valor = df_detalle['valor'].sum()
                        st.metric("Total Facturado", format_currency(total_valor))
                    
                    with col2:
                        total_comision_original = df_detalle['comision'].sum()
                        st.metric("Total Comisión Base", format_currency(total_comision_original))
                    
                    with col3:
                        total_comision_final = df_detalle['comision_final'].sum()
                        st.metric("Total Comisión Final", format_currency(total_comision_final))
                    
                    with col4:
                        ahorro_descuento = total_comision_original - total_comision_final
                        st.metric("Desc. Automático Total", format_currency(ahorro_descuento))
                else:
                    st.warning("No hay detalle de facturas disponible")
            
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
    
    # Sección de facturas por vencer y vencidas (siempre visible)
    st.markdown("---")
    st.markdown("### 📅 Estado de Facturas")
    
    # Obtener todas las facturas no pagadas
    df = systems["db_manager"].cargar_datos()
    
    if not df.empty:
        df_no_pagadas = df[df["pagado"] == False].copy()
        
        if not df_no_pagadas.empty:
            # Calcular mes actual
            hoy = date.today()
            mes_actual_inicio = date(hoy.year, hoy.month, 1)
            if hoy.month == 12:
                mes_actual_fin = date(hoy.year, 12, 31)
            else:
                mes_actual_fin = date(hoy.year, hoy.month + 1, 1) - timedelta(days=1)
            
            # Convertir fecha_pago_est a datetime
            df_no_pagadas['fecha_pago_est_dt'] = pd.to_datetime(df_no_pagadas['fecha_pago_est']).dt.date
            
            # 1. Facturas que vencen este mes (futuras)
            facturas_vencen_mes = df_no_pagadas[
                (df_no_pagadas['fecha_pago_est_dt'] >= mes_actual_inicio) & 
                (df_no_pagadas['fecha_pago_est_dt'] <= mes_actual_fin) &
                (df_no_pagadas['fecha_pago_est_dt'] >= hoy)
            ].sort_values('fecha_pago_est_dt')
            
            # 2. Facturas ya vencidas
            facturas_vencidas = df_no_pagadas[
                (df_no_pagadas['dias_vencimiento'].notna()) &
                (df_no_pagadas['dias_vencimiento'] < 0)
            ].sort_values('dias_vencimiento')
            
            # Mostrar facturas que vencen este mes
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📅 Se Vencen Este Mes")
                if not facturas_vencen_mes.empty:
                    st.info(f"**{len(facturas_vencen_mes)} factura(s)** por vencer este mes")
                    
                    for _, factura in facturas_vencen_mes.iterrows():
                        dias_restantes = (factura['fecha_pago_est_dt'] - hoy).days
                        
                        with st.container(border=True):
                            st.markdown(f"**{factura['cliente']}**")
                            st.write(f"📋 Pedido: {factura['pedido']} | Factura: {factura['factura']}")
                            st.write(f"💰 Valor: {format_currency(factura['valor'])}")
                            st.write(f"📅 Vence: {factura['fecha_pago_est_dt'].strftime('%d/%m/%Y')}")
                            
                            if dias_restantes <= 3:
                                st.error(f"⏰ **Vence en {dias_restantes} días** - ¡URGENTE!")
                            elif dias_restantes <= 7:
                                st.warning(f"⚠️ Vence en {dias_restantes} días")
                            else:
                                st.caption(f"🟢 Vence en {dias_restantes} días")
                else:
                    st.success("✅ No hay facturas por vencer este mes")
            
            with col2:
                st.markdown("#### 🚨 Ya Vencidas")
                if not facturas_vencidas.empty:
                    st.error(f"**{len(facturas_vencidas)} factura(s)** vencidas")
                    
                    for _, factura in facturas_vencidas.iterrows():
                        dias_vencida = abs(int(factura['dias_vencimiento']))
                        
                        with st.container(border=True):
                            st.markdown(f"**🚨 {factura['cliente']}**")
                            st.write(f"📋 Pedido: {factura['pedido']} | Factura: {factura['factura']}")
                            st.write(f"💰 Valor: {format_currency(factura['valor'])}")
                            st.error(f"⏰ **Vencida hace {dias_vencida} días**")
                            
                            if dias_vencida > 30:
                                st.error("🔴 MUY URGENTE - Más de 30 días vencida")
                            elif dias_vencida > 15:
                                st.warning("🟡 URGENTE - Más de 15 días vencida")
                else:
                    st.success("✅ No hay facturas vencidas")
        else:
            st.info("No hay facturas pendientes de pago")
    else:
        st.info("No hay datos de facturas")
    
    st.markdown("---")
    
    # Historial de comisiones
    st.markdown("### Historial de Comisiones")
    
    if st.button("Ver Historial"):
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
    st.header("Alertas de Vencimiento")
    
    invoice_alerts = systems["invoice_alerts"]
    
    # Botón para generar alertas
    if st.button("Generar Alertas", type="primary"):
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
    
    if st.button("Generar Recordatorios"):
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
        st.title("🧠 CRM Inteligente 2.0")
        st.caption("Sistema Inteligente de Gestión")
        
        st.markdown("---")
        
        # Toggle de tema
        ThemeManager.render_theme_toggle()
        
        st.markdown("---")
        
        # Meta mensual
        systems["ui_components"].render_sidebar_meta()
        
        st.markdown("---")
        
        # Filtros globales
        filtros = systems["ui_components"].render_sidebar_filters()
        
        st.markdown("---")
        
        # Botones de acción
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("🧹 Limpiar", use_container_width=True):
                keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
                for key in keys_to_delete:
                    del st.session_state[key]
                st.rerun()
    
    # Layout principal - Título con gradiente
    theme = ThemeManager.get_theme()
    st.markdown(
        f"""
        <div style='text-align: center; padding: 2rem 0;'>
            <h1 style='
                font-size: 3rem;
                font-weight: 800;
                background: {theme['gradient_1']};
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 0.5rem;
            '>
                CRM Inteligente 2.0
            </h1>
            <p style='color: {theme['text_secondary']}; font-size: 1.1rem;'>
                Sistema Avanzado de Gestión con IA y Analytics
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Tabs principales con emojis
    tabs = st.tabs([
        "👔 Dashboard Ejecutivo",
        "📊 Dashboard General",
        "💰 Comisiones",
        "➕ Nueva Venta",
        "↩️ Devoluciones",
        "📧 Mensajes",
        "👥 Clientes",
        "🤖 IA Clasificación",
        "📅 Comis. Mensuales",
        "🔔 Alertas",
        "📲 Notificaciones",
        "🎯 Pipeline Ventas",
        "🧠 IA & Recomendaciones"
    ])
    
    # Tab 0: Dashboard Ejecutivo (NUEVO)
    with tabs[0]:
        systems["tab_renderer"].render_executive_dashboard()
    
    # Tab 1: Dashboard General
    with tabs[1]:
        systems["tab_renderer"].render_dashboard()
    
    # Tab 2: Comisiones
    with tabs[2]:
        systems["tab_renderer"].render_comisiones()
    
    # Tab 3: Nueva Venta
    with tabs[3]:
        systems["tab_renderer"].render_nueva_venta()
    
    # Tab 4: Devoluciones
    with tabs[4]:
        systems["tab_renderer"].render_devoluciones()
    
    # Tab 5: Mensajes para Clientes
    with tabs[5]:
        systems["tab_renderer"].render_radicacion_facturas()
    
    # Tab 6: Clientes
    with tabs[6]:
        systems["tab_renderer"].render_clientes()
    
    # Tab 7: Clasificación de Clientes
    with tabs[7]:
        render_client_classification_tab(systems)
    
    # Tab 8: Comisiones Mensuales
    with tabs[8]:
        render_monthly_commissions_tab(systems)
    
    # Tab 9: Alertas de Facturas
    with tabs[9]:
        render_invoice_alerts_tab(systems)
    
    # Tab 10: Notificaciones
    with tabs[10]:
        systems["tab_renderer"].render_notifications()
    
    # Tab 11: Pipeline de Ventas (NUEVO)
    with tabs[11]:
        systems["tab_renderer"].render_sales_pipeline()
    
    # Tab 12: IA y Recomendaciones
    with tabs[12]:
        systems["tab_renderer"].render_ia_alertas()

def load_css():
    """Carga estilos CSS modernos con sistema de temas"""
    # Aplicar tema moderno
    ThemeManager.apply_theme()
    
    # CSS adicional específico de la app
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
        }
        
        div[data-testid="metric-container"] {
            background: var(--bg-surface) !important;
            border: 2px solid var(--border) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
            backdrop-filter: blur(10px) !important;
            transition: all 0.3s ease !important;
        }
        
        div[data-testid="metric-container"]:hover {
            transform: translateY(-4px) !important;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12) !important;
        }
        
        div[data-testid="metric-container"] > div {
            color: var(--text-primary) !important;
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
