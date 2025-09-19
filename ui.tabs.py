# ui/tabs.py
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from typing import Any

from business.calculations import ComisionCalculator, MetricsCalculator
from utils.formatting import format_currency

class TabRenderer:
    def __init__(self, db_manager, ui_components):
        self.db = db_manager
        self.ui = ui_components

    def render_dashboard(self):
        st.header("Dashboard")
        df = self.db.cargar_datos()
        meta = self.db.obtener_meta_mes_actual()
        metrics = MetricsCalculator.calcular_metricas_separadas(df) if not df.empty else {}
        col1, col2 = st.columns(2)
        with col1:
            ventas_propios = metrics.get("ventas_propios", 0)
            st.metric("Ventas - Propios", format_currency(ventas_propios))
            st.metric("Comisión - Propios", format_currency(metrics.get("comision_propios", 0)))
        with col2:
            ventas_externos = metrics.get("ventas_externos", 0)
            st.metric("Ventas - Externos", format_currency(ventas_externos))
            st.metric("Comisión - Externos", format_currency(metrics.get("comision_externos", 0)))

        # Progreso de la meta (solo propios)
        progreso = MetricsCalculator.calcular_progreso_meta(df, meta) if not df.empty else {"progreso": 0, "ventas_actuales": 0, "faltante": meta.get("meta_ventas", 0)}
        st.markdown("---")
        st.subheader("Progreso meta (solo ventas de clientes propios)")
        st.progress(min(1.0, progreso.get("progreso", 0) / 100.0))
        st.write(f"Ventas actuales (propios): {format_currency(progreso.get('ventas_actuales', 0))}")
        st.write(f"Faltante: {format_currency(progreso.get('faltante', 0))}")

    def _aplicar_filtros(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        # Filtros desde session_state
        estado = st.session_state.get("comisiones_estado_filter", "Todos")
        cliente_q = st.session_state.get("comisiones_cliente_filter", "").strip()
        fecha_inicio = st.session_state.get("comisiones_fecha_inicio", None)
        fecha_fin = st.session_state.get("comisiones_fecha_fin", None)
        monto_min = st.session_state.get("comisiones_monto_min", 0)
        tipo_cliente = st.session_state.get("comisiones_cliente_propio", None)

        res = df.copy()
        if cliente_q:
            res = res[res['cliente'].str.contains(cliente_q, case=False, na=False)]
        if fecha_inicio:
            res = res[res['fecha_factura'] >= pd.to_datetime(fecha_inicio)]
        if fecha_fin:
            res = res[res['fecha_factura'] <= pd.to_datetime(fecha_fin)]
        if monto_min:
            res = res[res['valor'] >= float(monto_min)]
        if estado != "Todos":
            if estado == "Pagadas":
                res = res[res['pagado'] == True]
            elif estado == "Pendientes":
                res = res[res['pagado'] == False]
            elif estado == "Vencidas":
                res = res[(res['pagado'] == False) & (res['dias_vencimiento'].notna()) & (res['dias_vencimiento'] < 0)]
        if tipo_cliente is not None:
            res = res[res['cliente_propio'] == bool(tipo_cliente)]
        return res

    def render_comisiones(self):
        st.header("Gestión de Comisiones")
        df = self.db.cargar_datos()
        if df.empty:
            st.info("No hay facturas registradas.")
            return

        df_filtered = self._aplicar_filtros(df)

        st.markdown(f"### Resultados ({len(df_filtered)})")
        for idx, row in df_filtered.sort_values("fecha_factura", ascending=False).iterrows():
            with st.container():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{row.get('pedido','N/A')} — {row.get('cliente','N/A')}**")
                    st.caption(f"Factura: {row.get('factura','N/A')}")
                    st.write(f"Valor: {format_currency(row.get('valor',0))}  —  Comisión: {format_currency(row.get('comision', 0))} ({row.get('porcentaje',0)}%)")
                with col2:
                    if row.get('pagado', False):
                        st.success("PAGADA")
                    else:
                        dias_v = row.get('dias_vencimiento')
                        if dias_v is None:
                            st.info("PENDIENTE")
                        elif dias_v < 0:
                            st.error(f"VENCIDA ({abs(int(dias_v))} días)")
                        else:
                            st.warning(f"VENCE en {int(dias_v)} días")

                # Botones de acciones
                bcol1, bcol2, bcol3 = st.columns([1,1,1])
                if bcol1.button("✏️ Editar", key=f"edit_{row.get('id')}"):
                    st.session_state[f"show_edit_{row.get('id')}"] = True
                    st.experimental_rerun()
                if bcol2.button("💳 Pagar", key=f"pay_{row.get('id')}"):
                    st.session_state[f"show_pago_{row.get('id')}"] = True
                    st.experimental_rerun()
                if bcol3.button("🔍 Ver", key=f"view_{row.get('id')}"):
                    st.session_state[f"view_{row.get('id')}"] = row.to_dict()
                    st.experimental_rerun()

                # Mostrar modal/edición si se solicitó (simple pattern)
                if st.session_state.get(f"view_{row.get('id')}") is not None:
                    factura = st.session_state.get(f"view_{row.get('id')}")
                    st.write("### Detalle")
                    st.json(factura)
                    if st.button("Cerrar", key=f"close_view_{row.get('id')}"):
                        del st.session_state[f"view_{row.get('id')}"]
                        st.experimental_rerun()

    def render_nueva_venta(self):
        st.header("Registrar Nueva Venta")
        with st.form("nueva_venta_form", clear_on_submit=True):
            pedido = st.text_input("Pedido")
            cliente = st.text_input("Cliente")
            valor = st.number_input("Valor Total (COP)", min_value=0.0, step=1000.0)
            cliente_propio = st.checkbox("Cliente propio", value=True)
            descuento_adicional = st.number_input("Descuento adicional (%)", min_value=0.0, value=0.0, step=0.5)
            descuento_pie = st.checkbox("Descuento en factura (pie)", value=False)
            fecha_factura = st.date_input("Fecha factura", value=date.today())
            submit = st.form_submit_button("Registrar venta")
            if submit:
                calc = ComisionCalculator.calcular_comision_inteligente(valor, cliente_propio, descuento_adicional, descuento_pie)
                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "valor": float(valor),
                    "valor_neto": calc["valor_neto"],
                    "iva": calc["iva"],
                    "base_comision": calc["base_comision"],
                    "comision": float(calc["comision"]),
                    "porcentaje": float(calc["porcentaje"]),
                    "cliente_propio": bool(cliente_propio),
                    "descuento_adicional": float(descuento_adicional),
                    "descuento_pie_factura": bool(descuento_pie),
                    "fecha_factura": fecha_factura.isoformat()
                }
                ok = self.db.insertar_venta(data)
                if ok:
                    st.success("Venta registrada correctamente.")
                else:
                    st.error("Error registrando la venta.")

    def render_devoluciones(self):
        st.header("Devoluciones")
        facturas = self.db.cargar_datos()
        if facturas.empty:
            st.info("No hay facturas para devolver.")
            return
        # Pueden integrarse los modales y lógica de tu versión original (simplificado aquí)
        st.markdown("Funcionalidad de devoluciones en el gestor (usa tu lógica original para insertar y ajustar comisiones).")

    def render_clientes(self):
        st.header("Clientes")
        st.info("Listado de clientes (implementa consultas a la tabla clientes si la tienes).")

    def render_ia_alertas(self):
        st.header("IA & Alertas")
        st.info("Recomendaciones automáticas y alertas basadas en comisiones/ventas.")
