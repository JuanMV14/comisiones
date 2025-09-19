# ui/componentes.py
from datetime import datetime, date
from typing import Optional, Dict, Any
import streamlit as st
import pandas as pd

try:
    from business.calculations import MetricsCalculator, ComisionCalculator
except Exception:
    MetricsCalculator = None
    ComisionCalculator = None

class UIComponents:
    def __init__(self, db_manager):
        self.db = db_manager

    def _safe_load_meta(self) -> Dict[str, Any]:
        mes_actual = date.today().strftime("%Y-%m")
        try:
            if hasattr(self.db, "obtener_meta_mes_actual"):
                meta = self.db.obtener_meta_mes_actual()
                if meta:
                    return meta
        except Exception:
            pass
        try:
            if hasattr(self.db, "supabase"):
                resp = self.db.supabase.table("metas_mensuales").select("*").eq("mes", mes_actual).execute()
                if resp and resp.data:
                    return resp.data[0]
        except Exception:
            pass
        return {
            "mes": mes_actual,
            "meta_ventas": 0,
            "meta_clientes_nuevos": 0,
            "ventas_actuales": 0,
            "clientes_nuevos_actuales": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _save_meta_via_db(self, mes: str, meta_ventas: float, meta_clientes: int) -> bool:
        try:
            if hasattr(self.db, "actualizar_meta"):
                result = self.db.actualizar_meta(mes, meta_ventas, meta_clientes)
                return bool(result)
        except Exception:
            pass
        try:
            if hasattr(self.db, "supabase"):
                sup = self.db.supabase
                existing = sup.table("metas_mensuales").select("id").eq("mes", mes).execute()
                data = {
                    "meta_ventas": float(meta_ventas),
                    "meta_clientes_nuevos": int(meta_clientes),
                    "updated_at": datetime.now().isoformat()
                }
                if existing and existing.data:
                    res = sup.table("metas_mensuales").update(data).eq("mes", mes).execute()
                else:
                    data["mes"] = mes
                    data["created_at"] = datetime.now().isoformat()
                    res = sup.table("metas_mensuales").insert(data).execute()
                return bool(res.data)
        except Exception as e:
            st.error(f"Error guardando meta (fallback): {str(e)}")
        return False

    def render_sidebar_meta(self):
        with st.expander("🎯 Meta Mensual", expanded=True):
            meta = self._safe_load_meta()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Mes", meta.get("mes", date.today().strftime("%Y-%m")))
                st.metric("Meta Ventas", f"${int(meta.get('meta_ventas', 0)):,}".replace(",", "."))
            with col2:
                st.metric("Meta Clientes", int(meta.get("meta_clientes_nuevos", 0)))
            try:
                df = pd.DataFrame()
                if hasattr(self.db, "cargar_datos"):
                    df = self.db.cargar_datos()
                if MetricsCalculator and not df.empty:
                    progreso = MetricsCalculator.calcular_progreso_meta(df, meta)
                    ventas_actuales = progreso.get("ventas_actuales", 0)
                    progreso_pct = progreso.get("progreso", 0)
                    faltante = progreso.get("faltante", 0)
                else:
                    ventas_actuales = meta.get("ventas_actuales", 0)
                    progreso_pct = 0
                    faltante = meta.get("meta_ventas", 0) - ventas_actuales
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Ventas actuales (propias)", f"${int(ventas_actuales):,}".replace(",", "."), f"{progreso_pct:.1f}%")
                with col_b:
                    st.metric("Faltante", f"${int(max(0, faltante)):,}".replace(",", "."))
            except Exception as e:
                st.warning("No se pudo calcular progreso de meta: " + str(e))
            st.markdown("---")
            col_edit, col_help = st.columns([2, 1])
            with col_edit:
                if st.button("✏️ Editar Meta"):
                    st.session_state.show_meta_config = True
            with col_help:
                st.button("❓ Ayuda", help="La meta usa solo ventas de clientes propios. Las comisiones se contabilizan aparte.")

    def render_sidebar_filters(self):
        with st.expander("🔎 Filtros", expanded=False):
            estado = st.selectbox("Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"],
                                  key="ui_estado_filter", index=0)
            cliente_busqueda = st.text_input("Buscar cliente", key="comisiones_cliente_filter", placeholder="Nombre del cliente")
            hoy = date.today()
            fecha_inicio = st.date_input("Desde", value=hoy.replace(day=1), key="comisiones_fecha_inicio")
            fecha_fin = st.date_input("Hasta", value=hoy, key="comisiones_fecha_fin")
            monto_min = st.number_input("Valor mínimo", min_value=0.0, value=0.0, step=10000.0, key="comisiones_monto_min")
            tipo_cliente = st.selectbox("Tipo cliente", ["Todos", "Propios", "Externos"], key="ui_tipo_cliente")
            col1, col2 = st.columns([2, 1])
            with col1:
                if st.button("🔍 Aplicar Filtros"):
                    st.session_state["comisiones_estado_filter"] = estado
                    st.session_state["comisiones_cliente_filter"] = cliente_busqueda
                    st.session_state["comisiones_fecha_inicio"] = fecha_inicio.isoformat() if fecha_inicio else None
                    st.session_state["comisiones_fecha_fin"] = fecha_fin.isoformat() if fecha_fin else None
                    st.session_state["comisiones_monto_min"] = float(monto_min)
                    if tipo_cliente == "Propios":
                        st.session_state["comisiones_cliente_propio"] = True
                    elif tipo_cliente == "Externos":
                        st.session_state["comisiones_cliente_propio"] = False
                    else:
                        st.session_state.pop("comisiones_cliente_propio", None)
                    st.experimental_rerun()
            with col2:
                if st.button("🧹 Limpiar"):
                    keys = [
                        "comisiones_estado_filter", "comisiones_cliente_filter",
                        "comisiones_fecha_inicio", "comisiones_fecha_fin",
                        "comisiones_monto_min", "comisiones_cliente_propio"
                    ]
                    for k in keys:
                        if k in st.session_state:
                            del st.session_state[k]
                    st.experimental_rerun()

    def render_meta_config_modal(self):
        st.markdown("## ⚙️ Configuración de Meta Mensual")
        meta = self._safe_load_meta()
        mes_default = meta.get("mes", date.today().strftime("%Y-%m"))
        with st.form("meta_config_form", clear_on_submit=False):
            st.info("Ajusta la meta mensual. Recuerda que solo las ventas de clientes propios cuentan para la meta.")
            mes_input = st.text_input("Mes (YYYY-MM)", value=mes_default, help="Formato: 2025-07")
            meta_ventas = st.number_input("Meta Ventas (COP)", min_value=0.0, value=float(meta.get("meta_ventas", 0)), step=50000.0)
            meta_clientes = st.number_input("Meta Clientes Nuevos", min_value=0, value=int(meta.get("meta_clientes_nuevos", 0)))
            bono = st.checkbox("Bono aplicable (visual)", value=bool(meta.get("bono_aplicable", False)))
            valor_bono = st.number_input("Valor Bono (COP)", value=float(meta.get("valor_bono", 0)), min_value=0.0)
            col1, col2 = st.columns([2, 1])
            with col1:
                guardar = st.form_submit_button("💾 Guardar Meta")
            with col2:
                cancelar = st.form_submit_button("❌ Cancelar")
            if cancelar:
                st.session_state.show_meta_config = False
                st.experimental_rerun()
            if guardar:
                if not mes_input or len(mes_input) < 7:
                    st.error("Mes inválido. Usa formato YYYY-MM (ej: 2025-07).")
                else:
                    ok = self._save_meta_via_db(mes_input, float(meta_ventas), int(meta_clientes))
                    if ok:
                        st.success("✅ Meta guardada correctamente.")
                        st.session_state.show_meta_config = False
                        try:
                            st.cache_data.clear()
                        except Exception:
                            pass
                        st.experimental_rerun()
                    else:
                        st.error("❌ No se pudo guardar la meta. Revisa la conexión o permisos.")
