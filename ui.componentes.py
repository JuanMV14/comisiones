import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any, Optional, List

from database.queries import DatabaseManager
from business.calculations import ComisionCalculator, MetricsCalculator
from utils.formatting import format_currency

class UIComponents:
    """Componentes reutilizables de la interfaz de usuario"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.comision_calc = ComisionCalculator()
        self.metrics_calc = MetricsCalculator()
    
    # ========================
    # SIDEBAR COMPONENTS
    # ========================
    
    def render_sidebar_meta(self):
        """Renderiza la sección de meta mensual en el sidebar"""
        st.subheader("Meta Mensual")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Config"):
                st.session_state.show_meta_config = True
        
        with col2:
            if st.button("Ver Meta"):
                st.session_state.show_meta_detail = True
        
        # Cargar datos y calcular progreso
        df_tmp = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        progreso_data = self.metrics_calc.calcular_progreso_meta(df_tmp, meta_actual)
        
        progreso = progreso_data["progreso"]
        ventas_mes = progreso_data["ventas_actuales"]
        
        # Renderizar card de progreso
        st.markdown(f"""
        <div class="metric-card">
            <h4>{date.today().strftime("%B %Y")}</h4>
            <p><strong>Meta:</strong> {format_currency(meta_actual["meta_ventas"])}</p>
            <p><strong>Actual:</strong> {format_currency(ventas_mes)}</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {min(progreso, 100)}%; background: {'#10b981' if progreso > 80 else '#f59e0b' if progreso > 50 else '#ef4444'}"></div>
            </div>
            <small>{progreso:.1f}% completado</small>
        </div>
        """, unsafe_allow_html=True)
    
    def render_sidebar_filters(self):
        """Renderiza los filtros globales en el sidebar"""
        df_tmp = self.db_manager.cargar_datos()
        meses_disponibles = ["Todos"] + (sorted(df_tmp["mes_factura"].dropna().unique().tolist()) if not df_tmp.empty else [])
        
        mes_seleccionado = st.selectbox(
            "📅 Filtrar por mes",
            meses_disponibles,
            index=0
        )
        
        return {"mes_seleccionado": mes_seleccionado}
    
    # ========================
    # MODAL COMPONENTS  
    # ========================
    
    def render_meta_config_modal(self):
        """Renderiza el modal de configuración de meta"""
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        with st.form("config_meta"):
            st.markdown("### Configurar Meta Mensual")
            
            col1, col2 = st.columns(2)
            with col1:
                nueva_meta = st.number_input(
                    "Meta de Ventas (COP)", 
                    value=float(meta_actual["meta_ventas"]),
                    min_value=0,
                    step=100000,
                    key="config_meta_ventas"
                )
            
            with col2:
                nueva_meta_clientes = st.number_input(
                    "Meta Clientes Nuevos", 
                    value=meta_actual["meta_clientes_nuevos"],
                    min_value=0,
                    step=1,
                    key="config_meta_clientes"
                )

            bono_potencial = nueva_meta * 0.005
            st.info(f"**Bono potencial:** {format_currency(bono_potencial)} (0.5% de la meta)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar Meta", type="primary"):
                    mes_actual_str = date.today().strftime("%Y-%m")
                    if self.db_manager.actualizar_meta(mes_actual_str, nueva_meta, nueva_meta_clientes):
                        st.success("Meta actualizada correctamente")
                        st.session_state.show_meta_config = False
                        st.rerun()
                    else:
                        st.error("Error al guardar la meta")
            
            with col2:
                if st.form_submit_button("Cancelar"):
                    st.session_state.show_meta_config = False
                    st.rerun()
    
    # ========================
    # FACTURA COMPONENTS
    # ========================
    
    def render_factura_card(self, factura: pd.Series, index: int):
        """Renderiza una card de factura"""
        estado_pagado = factura.get("pagado", False)
        
        if estado_pagado:
            estado_badge = "PAGADA"
            estado_color = "success"
            estado_icon = "✅"
        else:
            dias_venc = factura.get("dias_vencimiento")
            if dias_venc is not None and dias_venc < 0:
                estado_badge = f"VENCIDA ({abs(dias_venc)} días)"
                estado_color = "error"
                estado_icon = "🚨"
            elif dias_venc is not None and dias_venc <= 5:
                estado_badge = f"POR VENCER ({dias_venc} días)"
                estado_color = "warning"
                estado_icon = "⚠️"
            else:
                estado_badge = "PENDIENTE"
                estado_color = "info"
                estado_icon = "⏳"
        
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"## 🧾 {factura.get('pedido', 'N/A')} - {factura.get('cliente', 'N/A')}")
                st.caption(f"Factura: {factura.get('factura', 'N/A')}")
            
            with col2:
                if estado_color == "error":
                    st.error(f"{estado_icon} {estado_badge}")
                elif estado_color == "success":
                    st.success(f"{estado_icon} {estado_badge}")
                elif estado_color == "warning":
                    st.warning(f"{estado_icon} {estado_badge}")
                else:
                    st.info(f"{estado_icon} {estado_badge}")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Valor Neto", format_currency(factura.get('valor_neto', 0)))
            with col2:
                st.metric("Base Comisión", format_currency(factura.get('base_comision', 0)))
            with col3:
                st.metric("Comisión", format_currency(factura.get('comision', 0)))
            with col4:
                fecha_factura = factura.get('fecha_factura')
                if pd.notna(fecha_factura):
                    fecha_str = pd.to_datetime(fecha_factura).strftime('%d/%m/%Y')
                else:
                    fecha_str = "N/A"
                st.metric("Fecha", fecha_str)

            # Mostrar información adicional
            if not estado_pagado:
                dias_venc = factura.get('dias_vencimiento')
                if dias_venc is not None:
                    if dias_venc < 0:
                        st.error(f"⚠️ Vencida hace {abs(dias_venc)} días")
                    elif dias_venc <= 5:
                        st.warning(f"⏰ Vence en {dias_venc} días")
            else:
                fecha_pago = factura.get('fecha_pago_real')
                if pd.notna(fecha_pago):
                    st.success(f"💰 Pagada el {pd.to_datetime(fecha_pago).strftime('%d/%m/%Y')}")
    
    def render_factura_action_buttons(self, factura: pd.Series, index: int) -> Dict[str, bool]:
        """Renderiza los botones de acción para una factura"""
        factura_id = factura.get('id')
        if not factura_id:
            return {}
            
        unique_key = f"{factura_id}_{index}_{int(datetime.now().timestamp() / 100)}"
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        actions = {}
        
        with col1:
            actions['edit'] = st.button("✏️ Editar", key=f"edit_{unique_key}")
        
        with col2:
            if not factura.get("pagado"):
                actions['pay'] = st.button("💳 Pagar", key=f"pay_{unique_key}")
            else:
                st.success("✅ Pagada")
                actions['pay'] = False
        
        with col3:
            actions['detail'] = st.button("📊 Detalles", key=f"detail_{unique_key}")
        
        with col4:
            if factura.get("comprobante_url"):
                actions['comprobante'] = st.button("📄 Comprobante", key=f"comp_{unique_key}")
            else:
                st.caption("Sin comprobante")
                actions['comprobante'] = False
        
        with col5:
            if factura.get("pagado"):
                dias_pago = factura.get("dias_pago_real", 0)
                if dias_pago > 80:
                    st.error("⚠️ Sin comisión")
                else:
                    st.success(f"✅ {dias_pago} días")
            else:
                dias_venc = factura.get("dias_vencimiento")
                if dias_venc is not None:
                    if dias_venc < 0:
                        st.error(f"🚨 -{abs(dias_venc)}d")
                    elif dias_venc <= 5:
                        st.warning(f"⏰ {dias_venc}d")
                    else:
                        st.info(f"📅 {dias_venc}d")
        
        with col6:
            if factura.get("pagado"):
                st.success("✅ COMPLETO")
            else:
                dias_venc = factura.get("dias_vencimiento")
                if dias_venc is not None:
                    if dias_venc < 0:
                        st.error("🚨 CRÍTICO")
                    elif dias_venc <= 5:
                        st.warning("⚠️ ALTO")
                    else:
                        st.info("📋 MEDIO")
        
        return actions
    
    # ========================
    # MODAL FORMS
    # ========================
    
    def render_modal_editar(self, factura: pd.Series):
        """Modal de edición de factura"""
        factura_id = factura.get('id')
        if not factura_id:
            st.error("ERROR: Factura sin ID")
            return
        
        form_key = f"edit_form_{factura_id}"
        
        with st.form(form_key
