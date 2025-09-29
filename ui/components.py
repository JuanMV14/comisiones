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
            key="mes_filter_sidebar",
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
        
        with st.form(form_key, clear_on_submit=False):
            st.markdown(f"### Editar Factura - {factura.get('pedido', 'N/A')}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                nuevo_pedido = st.text_input("Pedido", value=str(factura.get('pedido', '')), key=f"edit_pedido_{factura_id}")
                nuevo_cliente = st.text_input("Cliente", value=str(factura.get('cliente', '')), key=f"edit_cliente_{factura_id}")
                nuevo_valor = st.number_input("Valor Total", value=float(factura.get('valor', 0)), min_value=0.0, key=f"edit_valor_{factura_id}")
            
            with col2:
                nueva_factura = st.text_input("Número Factura", value=str(factura.get('factura', '')), key=f"edit_factura_{factura_id}")
                cliente_propio = st.checkbox("Cliente Propio", value=bool(factura.get('cliente_propio', False)), key=f"edit_cliente_propio_{factura_id}")
                descuento_adicional = st.number_input("Descuento %", value=float(factura.get('descuento_adicional', 0)), key=f"edit_descuento_{factura_id}")
            
            nueva_fecha = st.date_input(
                "Fecha Factura", 
                value=pd.to_datetime(factura.get('fecha_factura', date.today())).date(),
                key=f"edit_fecha_{factura_id}"
            )
            
            # Recálculo de comisión
            st.markdown("#### Recálculo de Comisión")
            if nuevo_valor > 0:
                calc = self.comision_calc.calcular_comision_inteligente(
                    nuevo_valor, 
                    cliente_propio, 
                    descuento_adicional, 
                    factura.get('descuento_pie_factura', False)
                )
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Nueva Comisión", format_currency(calc['comision']))
                with col2:
                    st.metric("Porcentaje", f"{calc['porcentaje']}%")
                with col3:
                    st.metric("Base", format_currency(calc['base_comision']))
            
            col1, col2 = st.columns(2)
            with col1:
                guardar = st.form_submit_button("Guardar Cambios", type="primary")
            with col2:
                cancelar = st.form_submit_button("Cancelar")
            
            if cancelar:
                if f"show_edit_{factura_id}" in st.session_state:
                    del st.session_state[f"show_edit_{factura_id}"]
                st.rerun()
            
            if guardar:
                if nuevo_pedido and nuevo_cliente and nuevo_valor > 0:
                    self._procesar_guardar_edicion(factura, nuevo_pedido, nuevo_cliente, nueva_factura, 
                                                 nuevo_valor, cliente_propio, descuento_adicional, nueva_fecha)
                else:
                    st.error("Por favor completa todos los campos requeridos")
    
    def _procesar_guardar_edicion(self, factura: pd.Series, nuevo_pedido: str, nuevo_cliente: str, 
                                nueva_factura: str, nuevo_valor: float, cliente_propio: bool, 
                                descuento_adicional: float, nueva_fecha: date):
        """Procesa el guardado de la edición"""
        try:
            calc = self.comision_calc.calcular_comision_inteligente(
                nuevo_valor, 
                cliente_propio, 
                descuento_adicional,
                factura.get('descuento_pie_factura', False)
            )
            
            # Recalcular fechas de pago
            dias_pago = 60 if factura.get('condicion_especial', False) else 35
            dias_max = 60 if factura.get('condicion_especial', False) else 45
            fecha_pago_est = nueva_fecha + timedelta(days=dias_pago)
            fecha_pago_max = nueva_fecha + timedelta(days=dias_max)
            
            updates = {
                "pedido": nuevo_pedido,
                "cliente": nuevo_cliente,
                "factura": nueva_factura,
                "valor": nuevo_valor,
                "valor_neto": calc['valor_neto'],
                "iva": calc['iva'],
                "base_comision": calc['base_comision'],
                "comision": calc['comision'],
                "porcentaje": calc['porcentaje'],
                "fecha_factura": nueva_fecha.isoformat(),
                "fecha_pago_est": fecha_pago_est.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "cliente_propio": cliente_propio,
                "descuento_adicional": descuento_adicional
            }
            
            with st.spinner("Guardando cambios..."):
                resultado = self.db_manager.actualizar_factura(factura.get('id'), updates)
            
            if resultado:
                st.success("Factura actualizada exitosamente!")
                if f"show_edit_{factura.get('id')}" in st.session_state:
                    del st.session_state[f"show_edit_{factura.get('id')}"]
                st.rerun()
            else:
                st.error("Error actualizando la factura")
                
        except Exception as e:
            st.error(f"Error: {str(e)}")
    
    def render_modal_pago(self, factura: pd.Series):
        """Modal de procesamiento de pago"""
        factura_id = factura.get('id')
        if not factura_id:
            st.error("ERROR: Factura sin ID")
            return
        
        if factura.get('pagado'):
            st.warning("Esta factura ya está marcada como pagada")
            return
        
        form_key = f"pago_form_{factura_id}"
        
        with st.form(form_key, clear_on_submit=False):
            st.markdown(f"### Procesar Pago - {factura.get('pedido', 'N/A')}")
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_pago = st.date_input("Fecha de Pago", value=date.today(), key=f"pago_fecha_{factura_id}")
                metodo = st.selectbox("Método", ["Transferencia", "Efectivo", "Cheque", "Tarjeta"], key=f"pago_metodo_{factura_id}")
            with col2:
                referencia = st.text_input("Referencia", placeholder="Número de transacción", key=f"pago_referencia_{factura_id}")
                observaciones = st.text_area("Observaciones", placeholder="Notas del pago", key=f"pago_observaciones_{factura_id}")
            
            archivo = st.file_uploader(
                "Subir comprobante", 
                type=['pdf', 'jpg', 'jpeg', 'png'],
                key=f"archivo_pago_{factura_id}"
            )
            
            col1, col2 = st.columns(2)
            with col1:
                procesar = st.form_submit_button("PROCESAR PAGO", type="primary")
            with col2:
                cancelar = st.form_submit_button("Cancelar")
            
            if cancelar:
                if f"show_pago_{factura_id}" in st.session_state:
                    del st.session_state[f"show_pago_{factura_id}"]
                st.rerun()
            
            if procesar:
                self._procesar_pago(factura, fecha_pago, metodo, referencia, observaciones, archivo)
    
    def _procesar_pago(self, factura: pd.Series, fecha_pago: date, metodo: str, 
                      referencia: str, observaciones: str, archivo):
        """Procesa el pago de una factura"""
        with st.spinner("Procesando pago..."):
            try:
                comprobante_url = None
                if archivo:
                    comprobante_url = self.db_manager.subir_comprobante(archivo, factura.get('id'))
                
                # Calcular días de pago
                fecha_factura = pd.to_datetime(factura.get('fecha_factura'))
                dias = (pd.to_datetime(fecha_pago) - fecha_factura).days
                
                updates = {
                    "pagado": True,
                    "fecha_pago_real": fecha_pago.isoformat(),
                    "dias_pago_real": dias,
                    "metodo_pago": metodo,
                    "referencia": referencia,
                    "observaciones_pago": observaciones
                }
                
                if comprobante_url:
                    updates["comprobante_url"] = comprobante_url
                
                # Verificar si la comisión se pierde por pago tardío
                if dias > 80:
                    updates["comision_perdida"] = True
                    updates["razon_perdida"] = f"Pago tardío: {dias} días"
                    updates["comision_ajustada"] = 0
                else:
                    updates["comision_perdida"] = False
                    updates["comision_ajustada"] = factura.get('comision', 0)
                
                resultado = self.db_manager.actualizar_factura(factura.get('id'), updates)
                
                if resultado:
                    st.success("PAGO PROCESADO EXITOSAMENTE!")
                    st.balloons()
                    
                    if dias > 80:
                        st.warning(f"COMISIÓN PERDIDA: Pago realizado después de 80 días ({dias} días)")
                    
                    if f"show_pago_{factura.get('id')}" in st.session_state:
                        del st.session_state[f"show_pago_{factura.get('id')}"]
                    st.rerun()
                else:
                    st.error("Error procesando el pago")
                    
            except Exception as e:
                st.error(f"Error procesando pago: {str(e)}")
    
    # ========================
    # DEVOLUCION COMPONENTS
    # ========================
    
    def render_devolucion_card(self, devolucion: pd.Series, index: int):
        """Renderiza una card de devolución"""
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                cliente = devolucion.get('factura_cliente', 'N/A')
                pedido = devolucion.get('factura_pedido', 'N/A')
                st.markdown(f"## {pedido} - {cliente}")
                st.caption(f"Factura: {devolucion.get('factura_factura', 'N/A')}")
            
            with col2:
                if devolucion.get('afecta_comision', True):
                    st.error("AFECTA COMISIÓN")
                else:
                    st.success("NO AFECTA")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Valor Devuelto", format_currency(devolucion.get('valor_devuelto', 0)))
            
            with col2:
                valor_factura = devolucion.get('factura_valor', 0)
                porcentaje = (devolucion.get('valor_devuelto', 0) / valor_factura * 100) if valor_factura > 0 else 0
                st.metric("% de Factura", f"{porcentaje:.1f}%")
            
            with col3:
                if devolucion.get('afecta_comision', True):
                    comision_original = devolucion.get('factura_comision', 0)
                    comision_perdida = comision_original * (porcentaje / 100)
                    st.metric("Comisión Perdida", format_currency(comision_perdida))
                else:
                    st.metric("Comisión Perdida", format_currency(0))
            
            with col4:
                fecha_dev = devolucion.get('fecha_devolucion')
                if pd.notna(fecha_dev):
                    fecha_str = pd.to_datetime(fecha_dev).strftime('%d/%m/%Y')
                else:
                    fecha_str = "N/A"
                st.metric("Fecha", fecha_str)
            
            # Mostrar motivo si existe
            if devolucion.get('motivo'):
                st.markdown(f"**Motivo:** {devolucion.get('motivo')}")
    
    def render_modal_nueva_devolucion(self, facturas_df: pd.DataFrame):
        """Modal para crear nueva devolución"""
        with st.form("nueva_devolucion_form", clear_on_submit=False):
            st.markdown("### Registrar Nueva Devolución")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not facturas_df.empty:
                    opciones_factura = [f"{row['pedido']} - {row['cliente']} - {format_currency(row['valor'])}" 
                                       for _, row in facturas_df.iterrows()]
                    
                    factura_seleccionada = st.selectbox(
                        "Seleccionar Factura *",
                        options=range(len(opciones_factura)),
                        format_func=lambda x: opciones_factura[x] if x < len(opciones_factura) else "Seleccione...",
                        help="Factura sobre la cual se hará la devolución",
                        key="devolucion_factura_select"
                    )
                else:
                    st.error("No hay facturas disponibles")
                    return
                
                valor_devuelto = st.number_input(
                    "Valor a Devolver *",
                    min_value=0.0,
                    step=1000.0,
                    format="%.0f",
                    help="Valor total a devolver (incluye IVA si aplica)",
                    key="devolucion_valor"
                )
            
            with col2:
                fecha_devolucion = st.date_input(
                    "Fecha de Devolución *",
                    value=date.today(),
                    help="Fecha en que se procesa la devolución",
                    key="devolucion_fecha"
                )
                
                afecta_comision = st.checkbox(
                    "Afecta Comisión",
                    value=True,
                    help="Si esta devolución debe reducir la comisión calculada",
                    key="devolucion_afecta"
                )
            
            motivo = st.text_area(
                "Motivo de la Devolución",
                placeholder="Ej: Producto defectuoso, Error en pedido...",
                help="Descripción del motivo de la devolución",
                key="devolucion_motivo"
            )
            
            # Mostrar información de la factura seleccionada
            if factura_seleccionada is not None and factura_seleccionada < len(facturas_df):
                self._mostrar_info_factura_devolucion(facturas_df.iloc[factura_seleccionada], valor_devuelto, afecta_comision)
            
            st.markdown("---")
            
            col1, col2 = st.columns(2)
            
            with col1:
                registrar = st.form_submit_button("Registrar Devolución", type="primary", use_container_width=True)
            
            with col2:
                cancelar = st.form_submit_button("Cancelar", use_container_width=True)
            
            if cancelar:
                if 'show_nueva_devolucion' in st.session_state:
                    del st.session_state['show_nueva_devolucion']
                st.rerun()
            
            if registrar:
                if factura_seleccionada is not None and valor_devuelto > 0:
                    self._procesar_nueva_devolucion(facturas_df.iloc[factura_seleccionada], 
                                                   valor_devuelto, motivo, fecha_devolucion, afecta_comision)
                else:
                    st.error("Por favor completa todos los campos obligatorios")
    
    def _mostrar_info_factura_devolucion(self, factura_info: pd.Series, valor_devuelto: float, afecta_comision: bool):
        """Muestra información de la factura seleccionada para devolución"""
        st.markdown("---")
        st.markdown("### Información de la Factura")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Valor Factura", format_currency(factura_info['valor']))
        with col2:
            st.metric("Comisión Original", format_currency(factura_info['comision']))
        with col3:
            if valor_devuelto > 0 and afecta_comision:
                porcentaje_devuelto = valor_devuelto / factura_info['valor']
                comision_perdida = factura_info['comision'] * porcentaje_devuelto
                st.metric("Comisión Perdida", format_currency(comision_perdida))
    
    def _procesar_nueva_devolucion(self, factura_info: pd.Series, valor_devuelto: float, 
                                  motivo: str, fecha_devolucion: date, afecta_comision: bool):
        """Procesa el registro de una nueva devolución"""
        try:
            # Validar que el valor no exceda el de la factura
            if valor_devuelto > factura_info['valor']:
                st.error("El valor a devolver no puede ser mayor al valor de la factura")
                return
            
            data = {
                "factura_id": int(factura_info['id']),
                "valor_devuelto": float(valor_devuelto),
                "motivo": motivo.strip(),
                "fecha_devolucion": fecha_devolucion.isoformat(),
                "afecta_comision": afecta_comision
            }
            
            if self.db_manager.insertar_devolucion(data):
                st.success("Devolución registrada correctamente!")
                
                if afecta_comision:
                    st.warning("La comisión de la factura ha sido recalculada")
                
                st.balloons()
                
                # Mostrar resumen
                self._mostrar_resumen_devolucion(factura_info, valor_devuelto, fecha_devolucion, motivo)
                
                # Limpiar estado
                if 'show_nueva_devolucion' in st.session_state:
                    del st.session_state['show_nueva_devolucion']
                
                st.rerun()
            else:
                st.error("Error registrando la devolución")
                
        except Exception as e:
            st.error(f"Error procesando devolución: {str(e)}")
    
    def _mostrar_resumen_devolucion(self, factura_info: pd.Series, valor_devuelto: float, 
                                   fecha_devolucion: date, motivo: str):
        """Muestra resumen de la devolución registrada"""
        st.markdown("### Resumen de la Devolución")
        st.write(f"**Cliente:** {factura_info['cliente']}")
        st.write(f"**Pedido:** {factura_info['pedido']}")
        st.write(f"**Valor devuelto:** {format_currency(valor_devuelto)}")
        st.write(f"**Fecha:** {fecha_devolucion.strftime('%d/%m/%Y')}")
        if motivo:
            st.write(f"**Motivo:** {motivo}")
    
    # ========================
    # DETAIL COMPONENTS
    # ========================
    
    def render_detalles_completos(self, factura: pd.Series):
        """Muestra detalles completos de factura"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Información General")
            st.write(f"**Pedido:** {factura.get('pedido', 'N/A')}")
            st.write(f"**Cliente:** {factura.get('cliente', 'N/A')}")
            st.write(f"**Factura:** {factura.get('factura', 'N/A')}")
            st.write(f"**Cliente Propio:** {'Sí' if factura.get('cliente_propio') else 'No'}")
            
            fecha_factura = factura.get('fecha_factura')
            if pd.notna(fecha_factura):
                st.write(f"**Fecha Factura:** {pd.to_datetime(fecha_factura).strftime('%d/%m/%Y')}")
            
            fecha_pago_max = factura.get('fecha_pago_max')
            if pd.notna(fecha_pago_max):
                st.write(f"**Fecha Límite:** {pd.to_datetime(fecha_pago_max).strftime('%d/%m/%Y')}")
        
        with col2:
            st.markdown("#### Información Financiera")
            st.write(f"**Valor Total:** {format_currency(factura.get('valor', 0))}")
            st.write(f"**Valor Neto:** {format_currency(factura.get('valor_neto', 0))}")
            st.write(f"**IVA:** {format_currency(factura.get('iva', 0))}")
            st.write(f"**Base Comisión:** {format_currency(factura.get('base_comision', 0))}")
            st.write(f"**Comisión:** {format_currency(factura.get('comision', 0))} ({factura.get('porcentaje', 0)}%)")
            
            if factura.get('descuento_adicional', 0) > 0:
                st.write(f"**Descuento Adicional:** {factura.get('descuento_adicional', 0)}%")
        
        # Información de pago si existe
        if factura.get('pagado'):
            st.markdown("#### Información de Pago")
            col1, col2 = st.columns(2)
            
            with col1:
                fecha_pago_real = factura.get('fecha_pago_real')
                if pd.notna(fecha_pago_real):
                    st.write(f"**Fecha Pago:** {pd.to_datetime(fecha_pago_real).strftime('%d/%m/%Y')}")
                
                if factura.get('metodo_pago'):
                    st.write(f"**Método:** {factura.get('metodo_pago')}")
                
                if factura.get('referencia'):
                    st.write(f"**Referencia:** {factura.get('referencia')}")
            
            with col2:
                dias_pago = factura.get('dias_pago_real')
                if dias_pago is not None:
                    st.write(f"**Días de Pago:** {dias_pago}")
                
                if factura.get('comision_perdida'):
                    st.error("**Estado:** Comisión Perdida")
                    if factura.get('razon_perdida'):
                        st.write(f"**Razón:** {factura.get('razon_perdida')}")
                else:
                    st.success("**Estado:** Comisión Ganada")
        
        if factura.get('observaciones_pago'):
            st.markdown("#### Observaciones")
            st.write(factura.get('observaciones_pago'))
    
    def render_comprobante(self, comprobante_url: str):
        """Muestra comprobante de pago"""
        if comprobante_url:
            if comprobante_url.lower().endswith('.pdf'):
                st.markdown(f"[Ver Comprobante PDF]({comprobante_url})")
            else:
                try:
                    st.image(comprobante_url, caption="Comprobante de Pago", width=300)
                except:
                    st.markdown(f"[Ver Comprobante]({comprobante_url})")
        else:
            st.info("No hay comprobante subido")
