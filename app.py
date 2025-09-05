import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# =========================
# Conexión a Supabase
# =========================
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Gestión de Comisiones", layout="wide")

# =========================
# Funciones auxiliares
# =========================
@st.cache_data
def load_data():
    data = supabase.table("comisiones").select("*").execute()
    return pd.DataFrame(data.data)

def save_data(row_id, updated_data):
    supabase.table("comisiones").update(updated_data).eq("id", row_id).execute()

# =========================
# Cargar datos
# =========================
df = load_data()
if not df.empty:
    if "fecha_factura" in df.columns:
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")
    if "fecha_pago_real" in df.columns:
        df["fecha_pago_real"] = pd.to_datetime(df["fecha_pago_real"], errors="coerce")
    if "fecha_pago_max" in df.columns:
        df["fecha_pago_max"] = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
    df["mes_factura"] = df["fecha_factura"].dt.strftime("%Y-%m") if "fecha_factura" in df else None

# =========================
# Tabs principales
# =========================
tabs = st.tabs([
    "📝 Registrar Venta",
    "📂 Facturas Pendientes",
    "✅ Facturas Pagadas",
    "📊 Dashboard",
    "⚠️ Alertas",
    "💼 Editar Facturas"
])

# =========================
# TAB 1 - Registrar Venta
# =========================
with tabs[0]:
    st.header("📝 Registrar Venta")
    with st.form("registro_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        valor_factura = st.number_input("Valor Factura", min_value=0.0, step=1000.0)
        fecha_factura = st.date_input("Fecha Factura", value=date.today())
        fecha_pago_max = st.date_input("Fecha Máxima de Pago", value=date.today())
        porcentaje = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, value=1.5, step=0.1)
        submitted = st.form_submit_button("Guardar")
        if submitted:
            valor_comision = valor_factura * (porcentaje / 100)
            supabase.table("comisiones").insert({
                "pedido": pedido,
                "cliente": cliente,
                "valor_factura": valor_factura,
                "fecha_factura": fecha_factura.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "valor_comision": valor_comision,
                "pagado": False
            }).execute()
            st.success("✅ Venta registrada correctamente")
            st.cache_data.clear()
            st.experimental_rerun()

# =========================
# TAB 2 - Facturas Pendientes
# =========================
with tabs[1]:
    st.header("📂 Facturas Pendientes")
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pendientes = df[df["pagado"] == False].sort_values("fecha_factura", ascending=False)
        try:
            st.dataframe(df_pendientes[["pedido", "cliente", "valor_factura", "fecha_factura", "fecha_pago_max", "valor_comision"]])
        except KeyError:
            st.warning("⚠️ Algunas columnas no existen en los datos. Mostrando todas las disponibles.")
            st.dataframe(df_pendientes)

# =========================
# TAB 3 - Facturas Pagadas
# =========================
with tabs[2]:
    st.header("✅ Facturas Pagadas")
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pagadas = df[df["pagado"] == True].sort_values("fecha_pago_real", ascending=False)
        try:
            st.dataframe(df_pagadas[["pedido", "cliente", "valor_factura", "fecha_factura", "fecha_pago_real", "valor_comision"]])
        except KeyError:
            st.warning("⚠️ Algunas columnas no existen en los datos. Mostrando todas las disponibles.")
            st.dataframe(df_pagadas)

# =========================
# TAB 4 - Dashboard
# =========================
with tabs[3]:
    st.header("📊 Dashboard")
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        total_facturado = df["valor_factura"].sum()
        total_comision = df["valor_comision"].sum() if "valor_comision" in df else 0
        total_pagado = df[df["pagado"] == True]["valor_factura"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Facturado", f"${total_facturado:,.0f}")
        col2.metric("Total Comisión", f"${total_comision:,.0f}")
        col3.metric("Facturas Pagadas", f"${total_pagado:,.0f}")

        st.subheader("📅 Facturas por Mes")
        if "mes_factura" in df:
            st.bar_chart(df.groupby("mes_factura")["valor_factura"].sum())

# =========================
# TAB 5 - Alertas
# =========================
with tabs[4]:
    st.header("⚠️ Alertas de Facturas Vencidas")
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        hoy = pd.to_datetime(date.today())
        if "fecha_pago_max" in df:
            vencidas = df[(df["pagado"] == False) & (df["fecha_pago_max"] < hoy)]
            if vencidas.empty:
                st.success("✅ No hay facturas vencidas.")
            else:
                st.error("⚠️ Hay facturas vencidas pendientes de pago:")
                st.dataframe(vencidas)

# =========================
# TAB 6 - Editar Facturas
# =========================
with tabs[5]:
    st.header("💼 Editar Facturas")
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        # Selección de mes
        meses = ["Todos"] + sorted(df["mes_factura"].dropna().unique())
        mes_seleccionado = st.selectbox("Selecciona el mes (Fecha Factura)", meses)

        if mes_seleccionado != "Todos":
            df_filtrado = df[df["mes_factura"] == mes_seleccionado]
        else:
            df_filtrado = df.copy()

        if df_filtrado.empty:
            st.info("No hay facturas para ese mes.")
        else:
            pedido_seleccionado = st.selectbox("Selecciona la factura a editar", df_filtrado["pedido"].astype(str).tolist())
            factura = df_filtrado[df_filtrado["pedido"] == pedido_seleccionado].iloc[0]

            st.write(f"**Cliente:** {factura['cliente']}")
            valor_factura = st.number_input("Valor Factura", value=float(factura["valor_factura"]))
            porcentaje = st.number_input(
                "Porcentaje de Comisión (%)",
                value=float(factura.get("valor_comision", 0) / valor_factura * 100 if valor_factura else 0),
                min_value=0.0, max_value=100.0, step=0.1
            )
            pagado = st.selectbox("Pagado?", ["No", "Sí"], index=1 if factura["pagado"] else 0)
            fecha_pago_real = st.date_input(
                "Fecha de Pago Real",
                value=factura["fecha_pago_real"].date() if pd.notnull(factura.get("fecha_pago_real")) else date.today()
            )

            if st.button("💾 Guardar cambios"):
                valor_comision = valor_factura * (porcentaje / 100)
                save_data(factura["id"], {
                    "valor_factura": valor_factura,
                    "valor_comision": valor_comision,
                    "pagado": (pagado == "Sí"),
                    "fecha_pago_real": fecha_pago_real.isoformat() if pagado == "Sí" else None
                })
                st.success("✅ Cambios guardados correctamente")
                st.cache_data.clear()
                st.experimental_rerun()
