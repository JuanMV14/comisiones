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
import time

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

# Importar mÃ³dulos de anÃ¡lisis de clientes
from database.client_purchases_manager import ClientPurchasesManager
from ui.client_analysis_components import ClientAnalysisUI
from database.catalog_manager import CatalogManager
from database.sync_manager import SyncManager
from business.client_analytics import ClientAnalytics
from ui.client_analytics_components import ClientAnalyticsUI

# ========================
# CONFIGURACIÓN INICIAL
# ========================
load_dotenv()

# ========================
# FUNCIONES HELPER
# ========================
from utils.streamlit_helpers import safe_rerun

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
    layout="wide",  # Layout wide para diseño dashboard
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
    
    # Sistema de catÃ¡logo
    catalog_manager = CatalogManager(supabase)
    
    # Sistema de anÃ¡lisis de clientes
    client_purchases_manager = ClientPurchasesManager(supabase)
    sync_manager = SyncManager(supabase)
    client_analysis_ui = ClientAnalysisUI(client_purchases_manager, catalog_manager, sync_manager)
    
    # Sistema de analytics de clientes
    client_analytics = ClientAnalytics(supabase)
    client_analytics_ui = ClientAnalyticsUI(client_analytics)
    
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
        "catalog_manager": catalog_manager,
        "client_purchases_manager": client_purchases_manager,
        "sync_manager": sync_manager,
        "client_analysis_ui": client_analysis_ui,
        "client_analytics": client_analytics,
        "client_analytics_ui": client_analytics_ui,
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
            potencial_mes = monthly_calc.calcular_potencial_mes_actual()
            if potencial_mes.get("error"):
                st.warning(f"No fue posible calcular la comisión potencial: {potencial_mes['error']}")
                potencial_datos = {}
            else:
                potencial_datos = potencial_mes
            col1, col2, col3 = st.columns(3)
            
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
            with col3:
                st.metric(
                    "Comisión Potencial (Mes en curso)",
                    format_currency(potencial_datos.get("comisiones_netas", 0)),
                    delta=f"{potencial_datos.get('facturas_objetivo', 0)} facturas"
                )
            
            if potencial_datos.get("facturas_objetivo", 0) > 0:
                st.info(
                    f"Si cobras todas las facturas con vencimiento este mes, podrías sumar "
                    f"{format_currency(potencial_datos.get('comisiones_netas', 0))} adicionales."
                )
                st.caption(
                    f"{format_currency(potencial_datos.get('comisiones_brutas', 0))} brutas sobre "
                    f"{format_currency(potencial_datos.get('valor_total_facturas', 0))} facturado."
                )

                detalle_pendientes = potencial_datos.get("detalle_facturas", [])
                if detalle_pendientes:
                    df_pendientes = pd.DataFrame(detalle_pendientes)
                    columnas_prioritarias = [
                        col for col in [
                            "factura_base",
                            "factura",
                            "cliente",
                            "valor",
                            "comision_ajustada",
                            "fecha_pago_est"
                        ] if col in df_pendientes.columns
                    ]
                    if columnas_prioritarias:
                        df_pendientes = df_pendientes[columnas_prioritarias]
                    if "valor" in df_pendientes.columns:
                        df_pendientes["valor"] = df_pendientes["valor"].apply(format_currency)
                    if "comision_ajustada" in df_pendientes.columns:
                        df_pendientes["comision_ajustada"] = df_pendientes["comision_ajustada"].apply(format_currency)
                    if "fecha_pago_est" in df_pendientes.columns:
                        df_pendientes["fecha_pago_est"] = pd.to_datetime(df_pendientes["fecha_pago_est"]).dt.strftime("%d/%m/%Y")

                    st.markdown("##### Facturas pendientes del mes")
                    st.dataframe(df_pendientes, use_container_width=True, hide_index=True)
            elif not potencial_mes.get("error"):
                st.caption("Sin facturas pendientes con fecha límite en el mes en curso.")
            
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
    try:
        # Cargar CSS
        load_css()
        
        # Inicializar sistemas
        systems = initialize_systems()
        
        # Sidebar con navegación vertical - Diseño EXACTO tipo card
        with st.sidebar:
            # Logo/Título limpio
            st.markdown("""
            <div style='padding: 1.5rem 0 2rem 0; border-bottom: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 2rem;'>
                <h2 style='margin: 0; color: #FFFFFF; font-size: 1.75rem; font-weight: 800; letter-spacing: -0.5px;'>CRM</h2>
                <p style='margin: 0.5rem 0 0 0; color: #94A3B8; font-size: 0.875rem; font-weight: 500;'>Sistema de Gestión</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Todas las opciones de navegación
            opciones_vendedor = [
                "Panel del Vendedor",
                "Clientes",
                "Nueva Venta Simple",
                "Catálogo",
                "Mensajería",
                "Mis Comisiones"
            ]
            
            opciones_gerencia = [
                "Dashboard Ejecutivo",
                "Análisis Geográfico",
                "Análisis Comercial",
                "Comisiones",
                "Gestión Clientes B2B",
                "Análisis Compras",
                "Devoluciones",
                "Importaciones y Stock",
                "Reportes"
            ]
            
            # Mapeo con emojis para compatibilidad interna
            todas_opciones_con_emoji = [
                "🏠 Panel del Vendedor",
                "👥 Clientes",
                "⚡ Nueva Venta Simple",
                "🛒 Catálogo",
                "💬 Mensajería",
                "💰 Mis Comisiones",
                "📊 Dashboard Ejecutivo",
                "🗺️ Análisis Geográfico",
                "📈 Análisis Comercial",
                "💰 Comisiones",
                "👔 Gestión Clientes B2B",
                "📦 Análisis Compras",
                "↩️ Devoluciones",
                "📥 Importaciones y Stock",
                "📋 Reportes"
            ]
            
            # Selector de página
            if 'pagina_actual' not in st.session_state:
                st.session_state['pagina_actual'] = todas_opciones_con_emoji[0]
            
            pagina_actual_key = st.session_state.get('pagina_actual', todas_opciones_con_emoji[0])
            
            def quitar_emoji(texto):
                import re
                emoji_pattern = re.compile("["
                    u"\U0001F600-\U0001F64F"
                    u"\U0001F300-\U0001F5FF"
                    u"\U0001F680-\U0001F6FF"
                    u"\U0001F1E0-\U0001F1FF"
                    u"\U00002702-\U000027B0"
                    u"\U000024C2-\U0001F251"
                    "]+", flags=re.UNICODE)
                return emoji_pattern.sub(r'', texto).strip()
            
            pagina_actual_sin_emoji = quitar_emoji(pagina_actual_key)
            
            # Navegación tipo CARD - estilo exacto
            st.markdown("<p style='color: #94A3B8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem;'>NAVEGACIÓN</p>", unsafe_allow_html=True)
            
            for opcion in opciones_vendedor:
                is_selected = opcion == pagina_actual_sin_emoji
                if st.button(
                    opcion,
                    key=f"nav_v_{opcion}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    for opcion_emoji in todas_opciones_con_emoji:
                        if quitar_emoji(opcion_emoji) == opcion:
                            st.session_state['pagina_actual'] = opcion_emoji
                            break
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Separador visual para gerencia
            st.markdown("<p style='color: #94A3B8; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.1em; margin: 1.5rem 0 1rem 0;'>ADMINISTRACIÓN</p>", unsafe_allow_html=True)
            
            for opcion in opciones_gerencia:
                is_selected = opcion == pagina_actual_sin_emoji
                if st.button(
                    opcion,
                    key=f"nav_g_{opcion}",
                    use_container_width=True,
                    type="primary" if is_selected else "secondary"
                ):
                    for opcion_emoji in todas_opciones_con_emoji:
                        if quitar_emoji(opcion_emoji) == opcion:
                            st.session_state['pagina_actual'] = opcion_emoji
                            break
                    st.rerun()
            
            pagina_seleccionada = st.session_state.get('pagina_actual', todas_opciones_con_emoji[0])
    
        # Layout principal - Header superior profesional
        pagina_actual = st.session_state.get('pagina_actual', '🏠 Panel del Vendedor')
        
        # Función helper para quitar emojis
        def quitar_emoji_helper(texto):
            import re
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"
                u"\U0001F300-\U0001F5FF"
                u"\U0001F680-\U0001F6FF"
                u"\U0001F1E0-\U0001F1FF"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE)
            return emoji_pattern.sub(r'', texto).strip()
        
        titulo_pagina = quitar_emoji_helper(pagina_actual)
        
        # Header superior
        col_header1, col_header2 = st.columns([3, 1])
        with col_header1:
            st.markdown(f"<h1 style='margin: 0; color: {ThemeManager.get_theme()['text_primary']}; font-size: 2rem; font-weight: 700;'>{titulo_pagina}</h1>", unsafe_allow_html=True)
        with col_header2:
            # Usuario logueado (simulado - puedes conectarlo con autenticación real)
            st.markdown(f"""
            <div style='text-align: right; padding-top: 0.5rem;'>
                <span style='color: {ThemeManager.get_theme()['text_secondary']}; font-size: 0.9rem;'>Usuario: </span>
                <span style='color: {ThemeManager.get_theme()['text_primary']}; font-weight: 600;'>Vendedor</span>
            </div>
            """, unsafe_allow_html=True)
        
        theme_header = ThemeManager.get_theme()
        st.markdown(f"<hr style='margin: 1rem 0 2rem 0; border: none; border-top: 1px solid {theme_header['border']};'>", unsafe_allow_html=True)
        
        # Función helper para renderizar páginas con manejo de errores
        def render_page_safe(render_func, *args, **kwargs):
            """Renderiza una página con manejo de errores"""
            try:
                render_func(*args, **kwargs)
            except Exception as e:
                st.error(f"❌ Error al cargar esta sección: {str(e)}")
                st.info("Por favor, intenta recargar la página o contacta al administrador.")
                import traceback
                with st.expander("Detalles técnicos del error"):
                    st.code(traceback.format_exc())
        
        # La página actual ya está definida arriba
        
        # Mapeo de páginas a funciones de renderizado
        paginas_funciones = {
            # ZONA 1: ASISTENTE PARA VENDEDORES
            "🏠 Panel del Vendedor": systems["tab_renderer"].render_panel_vendedor,
            "👥 Clientes": systems["tab_renderer"].render_clientes_vendedor,
            "⚡ Nueva Venta Simple": systems["tab_renderer"].render_nueva_venta_simple,
            "🛒 Catálogo": systems["tab_renderer"].render_catalog_store,
            "💬 Mensajería": systems["tab_renderer"].render_mensajeria_comunicacion,
            "💰 Mis Comisiones": systems["tab_renderer"].render_comisiones_vendedor,
            
            # ZONA 2: PANEL ESTRATÉGICO PARA GERENCIA
            "📊 Dashboard Ejecutivo": systems["tab_renderer"].render_executive_dashboard,
            "🗺️ Análisis Geográfico": systems["tab_renderer"].render_analisis_geografico,
            "📈 Análisis Comercial": systems["tab_renderer"].render_analisis_comercial_avanzado,
            "💰 Comisiones": systems["tab_renderer"].render_comisiones,
            "👔 Gestión Clientes B2B": systems["client_analysis_ui"].render_gestion_clientes,
            "📦 Análisis Compras": systems["tab_renderer"].render_analisis_compras_comportamiento,
            "↩️ Devoluciones": systems["tab_renderer"].render_devoluciones,
            "📥 Importaciones y Stock": systems["tab_renderer"].render_importaciones_stock,
            "📋 Reportes": systems["tab_renderer"].render_reportes_exportacion
        }
        
        # Renderizar la página seleccionada
        if pagina_actual in paginas_funciones:
            render_page_safe(paginas_funciones[pagina_actual])
        else:
            st.error(f"Página '{pagina_actual}' no encontrada")
    
    except Exception as e:
        st.error(f"❌ Error crítico en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")
        import traceback
        with st.expander("Detalles técnicos del error"):
            st.code(traceback.format_exc())

def load_css():
    """Carga estilos CSS modernos con sistema de temas - Diseño Corporativo Dark EXACTO"""
    # Aplicar tema moderno
    ThemeManager.apply_theme()
    theme = ThemeManager.get_theme()
    
    # CSS adicional específico de la app - Diseño Corporativo Dark EXACTO como imágenes
    st.markdown(f"""
    <style>
        /* ============================================
           CONFIGURACIÓN BASE - TEMA DARK CORPORATIVO EXACTO
           Colores: #0F172A (fondo), #020617 (sidebar/cards)
           ============================================ */
        
        /* Fondo principal - EXACTO */
        .stApp {{
            background: #0F172A !important;
        }}
        
        /* Contenedor principal */
        .main .block-container {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }}
        
        /* Sidebar - Fondo oscuro EXACTO tipo card */
        [data-testid="stSidebar"] {{
            background: #020617 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
            min-width: 250px !important;
        }}
        
        /* Sidebar - Espaciado superior */
        [data-testid="stSidebar"] > div:first-child {{
            padding-top: 2rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }}
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: {theme['text_primary']} !important;
        }}
        
        /* Textos globales */
        html, body, .stApp, .stMarkdown, p, span, li, label, small, code, pre, div {{
            color: {theme['text_primary']} !important;
        }}
        
        .stCaption {{ 
            color: {theme['text_secondary']} !important; 
        }}
        
        h1, h2, h3, h4, h5, h6 {{
            color: {theme['text_primary']} !important;
            font-weight: 700 !important;
            letter-spacing: -0.5px !important;
        }}
        
        /* ============================================
           METRICS / CARDS
           ============================================ */
        
        div[data-testid="metric-container"] {{
            background: #020617 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.3s ease !important;
        }}
        
        div[data-testid="metric-container"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4) !important;
            border-color: rgba(37, 99, 235, 0.3) !important;
        }}
        
        div[data-testid="metric-container"] > div {{
            color: #94A3B8 !important;
            font-weight: 600 !important;
            font-size: 0.875rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }}
        
        div[data-testid="metric-container"] [data-testid="stMarkdownContainer"] h3 {{
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 2.5rem !important;
        }}
        
        /* ============================================
           BOTONES - ESTILO CORPORATIVO
           ============================================ */
        
        .stButton > button {{
            border-radius: 10px !important;
            border: 1px solid {theme['border']} !important;
            font-weight: 600 !important;
            font-size: 14px !important;
            background-color: {theme['secondary']} !important;
            color: {theme['text_primary']} !important;
            transition: all 0.2s ease !important;
            padding: 0.5rem 1rem !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme['surface_light']} !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
            border-color: {theme['primary']} !important;
        }}
        
        .stButton > button[kind="primary"] {{
            background-color: {theme['primary']} !important;
            color: #ffffff !important;
            border-color: {theme['primary']} !important;
            font-weight: 600 !important;
        }}
        
        .stButton > button[kind="primary"]:hover {{
            background-color: #1d4ed8 !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }}
        
        .stButton > button[kind="secondary"] {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
            border-color: {theme['border']} !important;
        }}
        
        .stButton > button[kind="secondary"]:hover {{
            background-color: {theme['surface_light']} !important;
            border-color: {theme['primary']} !important;
        }}
        
        /* ============================================
           CARDS Y CONTAINERS
           ============================================ */
        
        
        .dashboard-card {{
            background: #020617 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }}
        
        /* Cards con border de Streamlit - estilo exacto */
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: #020617 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }}
        
        /* ============================================
           SIDEBAR - ESTILO CARD FLOTANTE EXACTO
           ============================================ */
        
        [data-testid="stSidebar"] .stMarkdown {{
            color: #E2E8F0 !important;
        }}
        
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
            color: #FFFFFF !important;
        }}
        
        /* Botones del sidebar tipo CARD con hover suave */
        [data-testid="stSidebar"] .stButton > button {{
            background-color: #020617 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            color: #94A3B8 !important;
            width: 100% !important;
            text-align: left !important;
            padding: 1rem 1.25rem !important;
            margin-bottom: 0.5rem !important;
            border-radius: 12px !important;
            font-weight: 500 !important;
            font-size: 14px !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
        }}
        
        [data-testid="stSidebar"] .stButton > button:hover {{
            background-color: rgba(37, 99, 235, 0.1) !important;
            color: #FFFFFF !important;
            border-color: rgba(37, 99, 235, 0.3) !important;
            transform: translateX(4px) !important;
            box-shadow: 0 4px 8px rgba(37, 99, 235, 0.2) !important;
        }}
        
        [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, #2563EB 0%, #1E40AF 100%) !important;
            color: #FFFFFF !important;
            border-color: #2563EB !important;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
        }}
        
        [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover {{
            background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%) !important;
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.4) !important;
        }}
        
        /* ============================================
           MÉTRICAS GRANDES - CARDS SUPERIORES
           ============================================ */
        
        .metric-card-large {{
            background: #020617 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 2rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            transition: all 0.3s ease !important;
        }}
        
        .metric-card-large:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4) !important;
            border-color: rgba(37, 99, 235, 0.3) !important;
        }}
        
        .metric-value-large {{
            font-size: 3rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            margin: 0.5rem 0 !important;
            line-height: 1.2 !important;
        }}
        
        .metric-label-large {{
            font-size: 0.875rem !important;
            font-weight: 600 !important;
            color: #94A3B8 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.05em !important;
        }}
        
        /* ============================================
           MAPA DE COLOMBIA - ESTILO DARK
           ============================================ */
        
        .mapa-colombia-container {{
            background: #020617 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 16px !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
            margin: 1.5rem 0 !important;
        }}
        
        /* Plotly map dark theme */
        .js-plotly-plot {{
            background: transparent !important;
        }}
        
        /* ============================================
           TABS - ESTILO MODERNO
           ============================================ */
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 4px !important;
            background: {theme['surface']} !important;
            padding: 0.5rem !important;
            border-radius: 10px !important;
            border: 1px solid {theme['border']} !important;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: transparent !important;
            border: none !important;
            border-radius: 8px !important;
            color: {theme['text_secondary']} !important;
            font-weight: 600 !important;
            padding: 0.75rem 1.25rem !important;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: {theme['primary']} !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }}
        
        /* ============================================
           TABLAS Y DATAFRAMES
           ============================================ */
        
        .stDataFrame {{
            background: {theme['surface']} !important;
            border-radius: 10px !important;
        }}
        
        /* ============================================
           HEADER SUPERIOR (si se necesita)
           ============================================ */
        
        .dashboard-header {{
            background: {theme['surface']} !important;
            border-bottom: 1px solid {theme['border']} !important;
            padding: 1rem 2rem !important;
            margin-bottom: 1.5rem !important;
            border-radius: 0 0 12px 12px !important;
        }}
        
        .progress-bar {{
            background: {theme['surface_light']} !important;
            border-radius: 1rem !important;
            height: 1.5rem !important;
            overflow: hidden !important;
            width: 100% !important;
            border: 2px solid {theme['border']} !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        .progress-fill {{
            height: 100% !important;
            border-radius: 1rem !important;
            transition: width 0.3s ease !important;
        }}
        
        .metric-card {{
            background: {theme['surface']} !important;
            border: 2px solid {theme['border']} !important;
            border-radius: 1rem !important;
            padding: 1.5rem !important;
            margin: 1rem 0 !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
            color: {theme['text_primary']} !important;
            backdrop-filter: blur(15px) !important;
        }}
        
        .alert-high {{ 
            background: rgba(239, 68, 68, 0.12) !important; 
            border: 2px solid #ef4444 !important;
            color: {theme['text_primary']} !important;
            padding: 1.5rem !important;
            border-radius: 0.5rem !important;
            margin: 1rem 0 !important;
            font-weight: 600 !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        .alert-medium {{ 
            background: rgba(251, 146, 60, 0.12) !important; 
            border: 2px solid #fb923c !important;
            color: {theme['text_primary']} !important;
            padding: 1.5rem !important;
            border-radius: 0.5rem !important;
            margin: 1rem 0 !important;
            font-weight: 600 !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        .alert-low {{ 
            background: rgba(34, 197, 94, 0.12) !important; 
            border: 2px solid #22c55e !important;
            color: {theme['text_primary']} !important;
            padding: 1.5rem !important;
            border-radius: 0.5rem !important;
            margin: 1rem 0 !important;
            font-weight: 600 !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        /* ============================================
           INPUTS, SELECTBOXES, TEXTAREA - TEMA DARK
           ============================================ */
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stDateInput > div > div > input {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
        }}
        
        .stSelectbox > div > div > select,
        .stMultiSelect > div > div > select {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
        }}
        
        textarea {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
        }}
        
        /* Labels de inputs */
        label {{
            color: {theme['text_primary']} !important;
        }}
        
        /* ============================================
           EXPANDERS - TEMA DARK
           ============================================ */
        
        .streamlit-expanderHeader {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
        }}
        
        /* ============================================
           TABLAS Y DATAFRAMES - TEMA DARK COMPLETO
           ============================================ */
        
        .stDataFrame table {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
        }}
        
        .stDataFrame th {{
            background-color: {theme['surface_light']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
        }}
        
        .stDataFrame td {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
            border: 1px solid {theme['border']} !important;
        }}
        
        /* ============================================
           ALERTAS Y MENSAJES - TEMA DARK
           ============================================ */
        
        .stAlert {{
            background-color: {theme['surface']} !important;
            border: 1px solid {theme['border']} !important;
            border-radius: 8px !important;
        }}
        
        .stSuccess, .stInfo, .stWarning, .stError {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
        }}
        
        /* ============================================
           CHECKBOXES, RADIO BUTTONS - TEMA DARK
           ============================================ */
        
        .stCheckbox label,
        .stRadio label {{
            color: {theme['text_primary']} !important;
        }}
        
        /* ============================================
           MULTISELECT - TEMA DARK
           ============================================ */
        
        [data-baseweb="select"] {{
            background-color: {theme['surface']} !important;
            border: 1px solid {theme['border']} !important;
        }}
        
        [data-baseweb="select"] > div {{
            background-color: {theme['surface']} !important;
            color: {theme['text_primary']} !important;
        }}
        
        /* ============================================
           CONTAINERS Y COLUMNS - TEMA DARK
           ============================================ */
        
        .main .block-container {{
            background: transparent !important;
        }}
        
        /* Forzar todos los divs con contenido a usar tema dark */
        div[data-testid="stMarkdownContainer"],
        div[data-testid="stVerticalBlock"] {{
            color: {theme['text_primary']} !important;
        }}
        
        /* ============================================
           SCROLLBAR - TEMA DARK
           ============================================ */
        
        ::-webkit-scrollbar {{
            width: 10px;
            height: 10px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {theme['background']};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {theme['border']};
            border-radius: 5px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {theme['surface_light']};
        }}
    </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    # Limpiar flags de actualización al inicio del ciclo de ejecución
    # Si llegamos aquí, significa que el rerun anterior ya completó, así que podemos limpiar los flags de manera segura
    if "_updating" in st.session_state:
        st.session_state["_updating"] = False
    if "_clearing" in st.session_state:
        st.session_state["_clearing"] = False
    # El flag _rerunning se limpia aquí porque si llegamos al inicio del script,
    # significa que el rerun anterior ya completó exitosamente
    if "_rerunning" in st.session_state:
        st.session_state["_rerunning"] = False
    
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")
        import traceback
        with st.expander("Detalles técnicos del error"):
            st.code(traceback.format_exc())