import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from typing import Dict, Any

from database.queries import DatabaseManager
from ui.components import UIComponents
from business.calculations import ComisionCalculator, MetricsCalculator
from business.ai_recommendations import AIRecommendations
from utils.formatting import format_currency

class TabRenderer:
    """Renderizador de todas las pestañas de la aplicación"""
    
    def __init__(self, db_manager: DatabaseManager, ui_components: UIComponents):
        self.db_manager = db_manager
        self.ui_components = ui_components
        self.comision_calc = ComisionCalculator()
        self.metrics_calc = MetricsCalculator()
        self.ai_recommendations = AIRecommendations(db_manager)
    
    # ========================
    # TAB DASHBOARD
    # ========================
    
    def render_dashboard(self):
        """Renderiza la pestaña del dashboard"""
        st.header("Dashboard Ejecutivo")
        
        df = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
        if not df.empty:
            df = self.db_manager.agregar_campos_faltantes(df)
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        if not df.empty:
            metricas = self.metrics_calc.calcular_metricas_separadas(df)
            facturas_pendientes = len(df[df["pagado"] == False])
        else:
            metricas = self.metrics_calc.calcular_metricas_separadas(pd.DataFrame())
            facturas_pendientes = 0
        
        with col1:
            st.metric(
                "Ventas Meta (Propios)",
                format_currency(metricas["ventas_propios"]),
                help="Solo clientes propios cuentan para la meta"
            )
        
        with col2:
            total_comisiones = metricas["comision_propios"] + metricas["comision_externos"]
            st.metric("Comisión Total", format_currency(total_comisiones))
        
        with col3:
            st.metric("Facturas Pendientes", facturas_pendientes)
        
        with col4:
            st.metric("% Clientes Propios", f"{metricas['porcentaje_propios']:.1f}%")
        
        # Desglose por tipo de cliente
        st.markdown("---")
        st.markdown("### Desglose por Tipo de Cliente")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Clientes Propios (Para Meta)")
            st.metric("Ventas", format_currency(metricas["ventas_propios"]))
            st.metric("Comisión", format_currency(metricas["comision_propios"]))
            st.metric("Facturas", metricas["facturas_propios"])
        
        with col2:
            st.markdown("#### Clientes Externos (Solo Comisión)")
            st.metric("Ventas", format_currency(metricas["ventas_externos"]))
            st.metric("Comisión", format_currency(metricas["comision_externos"]))
            st.metric("Facturas", metricas["facturas_externos"])
        
        st.markdown("---")
        
        # Progreso Meta y Recomendaciones IA
        col1, col2 = st.columns([1, 1])
        
        with col1:
            self._render_progreso_meta(df, meta_actual)
        
        with col2:
            self._render_recomendaciones_dashboard()
    
    def _render_progreso_meta(self, df: pd.DataFrame, meta_actual: Dict[str, Any]):
        """Renderiza el progreso de la meta mensual"""
        st.markdown("### Progreso Meta Mensual")
        
        progreso_data = self.metrics_calc.calcular_progreso_meta(df, meta_actual)
        
        meta = progreso_data["meta_ventas"]
        actual = progreso_data["ventas_actuales"]
        progreso_meta = progreso_data["progreso"]
        faltante = progreso_data["faltante"]
        
        dias_restantes = max(1, (date(date.today().year, 12, 31) - date.today()).days)
        velocidad_necesaria = faltante / dias_restantes
        
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("Meta", format_currency(meta))
        with col_b:
            st.metric("Actual", format_currency(actual))
        with col_c:
            st.metric("Faltante", format_currency(faltante))
        
        color = "#10b981" if progreso_meta > 80 else "#f59e0b" if progreso_meta > 50 else "#ef4444"
        st.markdown(f"""
        <div class="progress-bar" style="margin: 1rem 0;">
            <div class="progress-fill" style="width: {min(progreso_meta, 100)}%; background: {color}"></div>
        </div>
        <p><strong>{progreso_meta:.1f}%</strong> completado | <strong>Necesitas:</strong> {format_currency(velocidad_necesaria)}/día</p>
        """, unsafe_allow_html=True)
    
    def _render_recomendaciones_dashboard(self):
        """Renderiza las recomendaciones IA en el dashboard"""
        st.markdown("### Recomendaciones IA")
        
        recomendaciones = self.ai_recommendations.generar_recomendaciones_reales()
        
        for rec in recomendaciones:
            st.markdown(f"""
            <div class="alert-{'high' if rec['prioridad'] == 'alta' else 'medium'}">
                <h4 style="margin:0; color: #ffffff;">{rec['cliente']}</h4>
                <p style="margin:0.5rem 0; color: #ffffff;"><strong>{rec['accion']}</strong> ({rec['probabilidad']}% prob.)</p>
                <p style="margin:0; color: #ffffff; font-size: 0.9rem;">{rec['razon']}</p>
                <p style="margin:0.5rem 0 0 0; color: #ffffff; font-weight: bold;">💰 +{format_currency(rec['impacto_comision'])} comisión</p>
            </div>
            """, unsafe_allow_html=True)
    
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
                st.rerun()
        
        # Filtros
        with st.container():
            st.markdown("### Filtros")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                estado_filter = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"], key="estado_filter_comisiones")
            with col2:
                cliente_filter = st.text_input("Buscar cliente", key="comisiones_cliente_filter")
            with col3:
                monto_min = st.number_input("Valor mínimo", min_value=0, value=0, step=100000)
            with col4:
                aplicar_filtros = st.button("🔍 Aplicar Filtros")
        
        # Cargar y filtrar datos
        df = self.db_manager.cargar_datos()
        
        if not df.empty:
            df = self.db_manager.agregar_campos_faltantes(df)
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
        
        if cliente_filter:
            df_filtrado = df_filtrado[df_filtrado["cliente"].str.contains(cliente_filter, case=False, na=False)]
        
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
        
        # Limpiar otros estados si se presiona una nueva acción
        if any(actions.values()):
            for key in list(st.session_state.keys()):
                if key.startswith(f"show_") and str(factura_id) in key:
                    del st.session_state[key]
        
        if actions.get('edit'):
            st.session_state[f"show_edit_{factura_id}"] = True
            st.rerun()
        
        if actions.get('pay'):
            st.session_state[f"show_pago_{factura_id}"] = True
            st.rerun()
        
        if actions.get('detail'):
            st.session_state[f"show_detail_{factura_id}"] = True
            st.rerun()
        
        if actions.get('comprobante'):
            st.session_state[f"show_comprobante_{factura_id}"] = True
            st.rerun()
        
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
                    del st.session_state[f"show_comprobante_{factura_id}"]
                    st.rerun()
        
        if st.session_state.get(f"show_detail_{factura_id}", False):
            with st.expander(f"📊 Detalles: {factura.get('pedido', 'N/A')}", expanded=True):
                self.ui_components.render_detalles_completos(factura)
                if st.button("❌ Cerrar", key=f"close_detail_{factura_id}"):
                    del st.session_state[f"show_detail_{factura_id}"]
                    st.rerun()
    
    # ========================
    # TAB NUEVA VENTA
    # ========================
    
    def render_nueva_venta(self):
        """Renderiza la pestaña de nueva venta"""
        st.header("Registrar Nueva Venta")
        
        with st.form("nueva_venta_form", clear_on_submit=False):
            st.markdown("### Información Básica")
            
            col1, col2 = st.columns(2)
            
            with col1:
                pedido = st.text_input("Número de Pedido *", placeholder="Ej: PED-001", key="nueva_venta_pedido")
                cliente = st.text_input("Cliente *", placeholder="Ej: DISTRIBUIDORA CENTRAL", key="nueva_venta_cliente")
                factura = st.text_input("Número de Factura", placeholder="Ej: FAC-1001", key="nueva_venta_factura")
            
            with col2:
                fecha_factura = st.date_input("Fecha de Factura *", value=date.today(), key="nueva_venta_fecha")
                valor_total = st.number_input("Valor Total (con IVA) *", min_value=0.0, step=10000.0, format="%.0f", key="nueva_venta_valor")
                condicion_especial = st.checkbox("Condición Especial (60 días de pago)", key="nueva_venta_condicion")
            
            st.markdown("### Configuración de Comisión")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cliente_propio = st.checkbox("Cliente Propio", key="nueva_venta_cliente_propio")
            with col2:
                descuento_pie_factura = st.checkbox("Descuento a Pie de Factura", key="nueva_venta_descuento_pie")
            with col3:
                descuento_adicional = st.number_input("Descuento Adicional (%)", min_value=0.0, max_value=100.0, step=0.5, key="nueva_venta_descuento_adicional")
            
            # Preview de cálculos
            if valor_total > 0:
                st.markdown("---")
                st.markdown("### Preview de Comisión")
                
                calc = self.comision_calc.calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Valor Neto", format_currency(calc['valor_neto']))
                with col2:
                    st.metric("IVA (19%)", format_currency(calc['iva']))
                with col3:
                    st.metric("Base Comisión", format_currency(calc['base_comision']))
                with col4:
                    st.metric("Comisión Final", format_currency(calc['comision']))
                
                st.info(f"""
                **Detalles del cálculo:**
                - Tipo cliente: {'Propio' if cliente_propio else 'Externo'}
                - Porcentaje comisión: {calc['porcentaje']}%
                - {'Descuento aplicado en factura' if descuento_pie_factura else 'Descuento automático del 15%'}
                - Descuento adicional: {descuento_adicional}%
                """)
            
            st.markdown("---")
            
            # Botones
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                submit = st.form_submit_button("Registrar Venta", type="primary", use_container_width=True)
            
            with col2:
                if st.form_submit_button("Limpiar", use_container_width=True):
                    st.rerun()
            
            with col3:
                if st.form_submit_button("Previsualizar", use_container_width=True):
                    if pedido and cliente and valor_total > 0:
                        st.success("Los datos se ven correctos para registrar")
                    else:
                        st.warning("Faltan campos obligatorios")
            
            # Lógica de guardado
            if submit:
                self._procesar_nueva_venta(pedido, cliente, factura, fecha_factura, valor_total, 
                                         condicion_especial, cliente_propio, descuento_pie_factura, descuento_adicional)
    
    def _procesar_nueva_venta(self, pedido: str, cliente: str, factura: str, fecha_factura: date,
                             valor_total: float, condicion_especial: bool, cliente_propio: bool,
                             descuento_pie_factura: bool, descuento_adicional: float):
        """Procesa el registro de una nueva venta"""
        if pedido and cliente and valor_total > 0:
            try:
                # Calcular fechas
                dias_pago = 60 if condicion_especial else 35
                dias_max = 60 if condicion_especial else 45
                fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
                fecha_pago_max = fecha_factura + timedelta(days=dias_max)
                
                # Calcular comisión
                calc = self.comision_calc.calcular_comision_inteligente(valor_total, cliente_propio, descuento_adicional, descuento_pie_factura)
                
                # Preparar datos
                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura if factura else f"FAC-{pedido}",
                    "valor": float(valor_total),
                    "valor_neto": float(calc['valor_neto']),
                    "iva": float(calc['iva']),
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
                    "pagado": False
                }
                
                # Insertar
                if self.db_manager.insertar_venta(data):
                    st.success("¡Venta registrada correctamente!")
                    st.success(f"Comisión calculada: {format_currency(calc['comision'])}")
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
                st.rerun()
        
        with col2:
            if st.button("🔄 Actualizar", type="secondary"):
                self.db_manager.limpiar_cache()
                st.rerun()
        
        # Modal nueva devolución
        if st.session_state.get('show_nueva_devolucion', False):
            with st.expander("➕ Nueva Devolución", expanded=True):
                facturas_df = self.db_manager.obtener_facturas_para_devolucion()
                self.ui_components.render_modal_nueva_devolucion(facturas_df)
        
        st.markdown("---")
        
        # Cargar y mostrar devoluciones
        df_devoluciones = self.db_manager.cargar_devoluciones()
        
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
    # TAB IA & ALERTAS
    # ========================
    
    def render_ia_alertas(self):
        """Renderiza la pestaña de IA y alertas"""
        st.header("Inteligencia Artificial & Alertas")
        
        df = self.db_manager.cargar_datos()
        meta_actual = self.db_manager.obtener_meta_mes_actual()
        
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
        """Renderiza recomendaciones estratégicas"""
        st.markdown("### Recomendaciones Estratégicas")
        
        recomendaciones = self.ai_recommendations.generar_recomendaciones_reales()
        
        for i, rec in enumerate(recomendaciones):
            with st.container(border=True):
                with st.expander(f"#{i+1} {rec['cliente']} - {rec['probabilidad']}% probabilidad", expanded=True):
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.markdown(f"**Acción:** {rec['accion']}")
                        st.markdown(f"**Producto:** {rec['producto']}")
                        st.markdown(f"**Razón:** {rec['razon']}")
                        
                        prioridad_color = "🔴" if rec['prioridad'] == 'alta' else "🟡"
                        st.markdown(f"**Prioridad:** {prioridad_color} {rec['prioridad'].title()}")
                    
                    with col_b:
                        st.metric(
                            label="Impacto Comisión",
                            value=format_currency(rec['impacto_comision']),
                            delta=f"+{rec['probabilidad']}%"
                        )
                    
                    if st.button(f"Ejecutar Acción", key=f"action_rec_{i}"):
                        st.success(f"Acción programada para {rec['cliente']}")
        
        if st.button("Generar Nuevas Recomendaciones"):
            st.rerun()
