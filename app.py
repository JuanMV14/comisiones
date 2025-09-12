import streamlit as st
import pandas as pd
from datetime import date, datetime
from queries import get_all_comisiones, insert_comision, update_comision
from utils import process_dataframe, calcular_fechas_pago, calcular_comision

# ========================
# Configuración
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")

# ========================
# Cargar datos
# ========================
def cargar_datos():
    try:
        data = get_all_comisiones()
        return process_dataframe(data)
    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        return pd.DataFrame()


df_tmp = cargar_datos()
meses_disponibles = ["Todos"] + (sorted(df_tmp["mes_factura"].dropna().unique().tolist()) if not df_tmp.empty else [])

if "mes_global" not in st.session_state:
    st.session_state["mes_global"] = "Todos"

st.session_state["mes_global"] = st.selectbox(
    "📅 Filtrar por mes (Fecha Factura)",
    meses_disponibles,
    index=meses_disponibles.index(st.session_state["mes_global"]) if st.session_state["mes_global"] in meses_disponibles else 0
)

# ========================
# Tabs
# ========================
tabs = st.tabs([
    "➕ Registrar Venta",
    "📂 Facturas Pendientes",
    "✅ Facturas Pagadas",
    "📈 Dashboard",
    "⚠️ Alertas"
])

# ========================
# TAB 1 - Registrar Venta
# ========================
with tabs[0]:
    st.header("➕ Registrar nueva venta")

    with st.form("form_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Factura")
        valor = st.number_input("Valor Factura (neto, antes de IVA)", min_value=0.0, step=1000.0)
        porcentaje = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, step=0.5)
        fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        condicion_especial = st.selectbox("Condición Especial?", ["No", "Sí"]) == "Sí"
        tiene_descuento = st.selectbox("¿Cliente con descuento a pie de factura?", ["Sí", "No"]) == "Sí"
        devoluciones = st.number_input("Devoluciones", min_value=0.0, step=1000.0, value=0.0)

        submit = st.form_submit_button("💾 Registrar")

    if submit:
        try:
            fecha_pago_est, fecha_pago_max = calcular_fechas_pago(fecha_factura, condicion_especial)
            comision = calcular_comision(valor, porcentaje, tiene_descuento, None, fecha_factura, devoluciones)

            data = {
                "pedido": pedido,
                "cliente": cliente,
                "factura": factura,
                "valor": valor,
                "comision": comision,
                "porcentaje": porcentaje,
                "fecha_factura": fecha_factura.isoformat(),
                "fecha_pago_est": fecha_pago_est.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "condicion_especial": condicion_especial,
                "tiene_descuento": tiene_descuento,
                "devoluciones": devoluciones,
                "pagado": False,
            }
            insert_comision(data)
            st.success("✅ Venta registrada correctamente")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

# ========================
# TAB 2 - Facturas Pendientes
# ========================
with tabs[1]:
    st.header("📂 Facturas Pendientes")
    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pendientes = df[df["pagado"] == False]
        if st.session_state["mes_global"] != "Todos":
            df_pendientes = df_pendientes[df_pendientes["mes_factura"] == st.session_state["mes_global"]]

        if df_pendientes.empty:
            st.success("✅ No hay facturas pendientes")
        else:
            for _, row in df_pendientes.iterrows():
                with st.expander(f"Pedido {row['pedido']} - {row['cliente']}"):
                    st.write(f"**Factura:** {row.get('factura', 'N/A')}")
                    st.write(f"**Valor Factura:** ${row['valor']:,.2f}")
                    st.write(f"**Fecha Factura:** {row['fecha_factura'].date() if pd.notna(row['fecha_factura']) else 'N/A'}")
                    st.write(f"**Fecha Máxima Pago:** {row['fecha_pago_max'].date() if pd.notna(row['fecha_pago_max']) else 'N/A'}")

                    if st.button(f"✏️ Editar {row['id']}", key=f"edit_pend_{row['id']}"):
                        with st.form(f"form_edit_{row['id']}"):
                            valor = st.number_input("Valor Factura", value=float(row['valor']))
                            porcentaje = st.number_input("Porcentaje Comisión (%)", value=float(row['porcentaje']))
                            pagado = st.selectbox("Pagado?", ["No", "Sí"], index=0)
                            fecha_pago_real = st.date_input("Fecha de Pago Real", value=date.today())
                            devoluciones = st.number_input("Devoluciones", value=float(row.get("devoluciones", 0.0)))
                            guardar = st.form_submit_button("💾 Guardar cambios")

                        if guardar:
                            comision = calcular_comision(valor, porcentaje, row["tiene_descuento"],
                                                         fecha_pago_real, row["fecha_factura"], devoluciones)
                            update_comision(int(row["id"]), {
                                "valor": valor,
                                "porcentaje": porcentaje,
                                "comision": comision,
                                "pagado": (pagado == "Sí"),
                                "fecha_pago_real": fecha_pago_real.isoformat() if pagado == "Sí" else None,
                                "devoluciones": devoluciones,
                                "updated_at": datetime.now().isoformat()
                            })
                            st.success("✅ Cambios guardados")
                            st.rerun()

# ========================
# TAB 3 - Facturas Pagadas
# ========================
with tabs[2]:
    st.header("✅ Facturas Pagadas")
    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pagadas = df[df["pagado"] == True]
        if st.session_state["mes_global"] != "Todos":
            df_pagadas = df_pagadas[df_pagadas["mes_factura"] == st.session_state["mes_global"]]

        if df_pagadas.empty:
            st.info("No hay facturas pagadas todavía.")
        else:
            for _, row in df_pagadas.iterrows():
                with st.expander(f"Pedido {row['pedido']} - {row['cliente']}"):
                    st.write(f"**Factura:** {row.get('factura', 'N/A')}")
                    st.write(f"**Valor Factura:** ${row['valor']:,.2f}")
                    st.write(f"**Fecha Factura:** {row['fecha_factura'].date() if pd.notna(row['fecha_factura']) else 'N/A'}")
                    st.write(f"**Fecha Pago Real:** {row['fecha_pago_real'].date() if pd.notna(row['fecha_pago_real']) else 'N/A'}")

                    if st.button(f"✏️ Editar {row['id']}", key=f"edit_pag_{row['id']}"):
                        with st.form(f"form_edit_{row['id']}"):
                            valor = st.number_input("Valor Factura", value=float(row['valor']))
                            porcentaje = st.number_input("Porcentaje Comisión (%)", value=float(row['porcentaje']))
                            devoluciones = st.number_input("Devoluciones", value=float(row.get("devoluciones", 0.0)))
                            fecha_pago_real = st.date_input("Fecha de Pago Real", value=row['fecha_pago_real'].date() if pd.notna(row['fecha_pago_real']) else date.today())
                            guardar = st.form_submit_button("💾 Guardar cambios")

                        if guardar:
                            comision = calcular_comision(valor, porcentaje, row["tiene_descuento"],
                                                         fecha_pago_real, row["fecha_factura"], devoluciones)
                            update_comision(int(row["id"]), {
                                "valor": valor,
                                "porcentaje": porcentaje,
                                "comision": comision,
                                "devoluciones": devoluciones,
                                "fecha_pago_real": fecha_pago_real.isoformat(),
                                "updated_at": datetime.now().isoformat()
                            })
                            st.success("✅ Cambios guardados")
                            st.rerun()

# ========================
# TAB 4 - Dashboard
# ========================
with tabs[3]:
    st.header("📈 Dashboard de Comisiones")
    df = cargar_datos()

    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        if st.session_state["mes_global"] != "Todos":
            df = df[df["mes_factura"] == st.session_state["mes_global"]]

        total_facturado = df["valor"].sum()
        total_comisiones = df["comision"].sum()
        total_pagado = df[df["pagado"]]["valor"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

        st.subheader("🏆 Ranking de Clientes")
        if not df.empty:
            ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
            for _, row in ranking.iterrows():
                st.write(f"**{row['cliente']}** - 💵 ${row['valor']:,.2f}")
                st.progress(min(1.0, row["valor"] / total_facturado) if total_facturado else 0)

# ========================
# TAB 5 - Alertas
# ========================
with tabs[4]:
    st.header("⚠️ Alertas de vencimiento")
    df = cargar_datos()
    if not df.empty and "fecha_pago_max" in df.columns:
        hoy = datetime.now()
        fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
        limite = hoy + pd.Timedelta(days=5)
        alertas = df[(df["pagado"] == False) & (fechas_pago <= limite)]

        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencerse")
        else:
            for _, row in alertas.iterrows():
                st.error(f"⚠️ Pedido {row['pedido']} ({row['cliente']}) vence el {row['fecha_pago_max'].date()}")
    else:
        st.info("No hay datos de fechas de pago.")

