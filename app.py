import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client, Client

# ======================
# CONFIGURACIÓN SUPABASE
# ======================
SUPABASE_URL = "https://ihncwagxefayefcdngkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlobmN3YWd4ZWZheWVmY2RuZ2t3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDYwNDksImV4cCI6MjA3MjU4MjA0OX0.tzgjBgMJoZdSSw29661PDARz0wfQcdI2bNtZrOqwG54"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ======================
# FUNCIONES BD
# ======================
def insertar_comision(fecha, pedido, cliente, factura, valor, porcentaje, comision, pagado):
    data = {
        "fecha": str(fecha),
        "pedido": pedido,
        "cliente": cliente,
        "factura": factura,
        "valor": valor,
        "porcentaje": porcentaje,
        "comision": comision,
        "pagado": pagado,
    }
    return supabase.table("comisiones").insert(data).execute()

def obtener_comisiones():
    res = supabase.table("comisiones").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()

# ======================
# APP STREAMLIT
# ======================
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

st.title("📊 Control de Comisiones")
st.markdown("Registra y controla tus comisiones de ventas usando **Supabase**.")

tabs = st.tabs(["➕ Nueva Comisión", "📈 Dashboard", "📑 Historial"])

# ======================
# TAB 1: NUEVA COMISIÓN
# ======================
with tabs[0]:
    st.header("➕ Registrar nueva comisión")
    with st.form("form_comision"):
        fecha = st.date_input("Fecha", value=date.today())
        pedido = st.text_input("N° Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("N° Factura")
        valor = st.number_input("Valor venta", min_value=0.0, format="%.2f")
        porcentaje = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, format="%.2f")
        comision = valor * (porcentaje / 100)
        pagado = st.checkbox("¿Pagado?", value=False)

        submitted = st.form_submit_button("Guardar")
        if submitted:
            insertar_comision(fecha, pedido, cliente, factura, valor, porcentaje, comision, pagado)
            st.success("✅ Comisión registrada correctamente")

# ======================
# TAB 2: DASHBOARD
# ======================
with tabs[1]:
    st.header("📈 Dashboard mensual")

    df = obtener_comisiones()
    if df.empty:
        st.info("Aún no tienes comisiones registradas.")
    else:
        df["fecha"] = pd.to_datetime(df["fecha"])
        df["mes"] = df["fecha"].dt.to_period("M").astype(str)

        mes_sel = st.selectbox("Selecciona el mes", sorted(df["mes"].unique()), index=len(df["mes"].unique())-1)
        df_mes = df[df["mes"] == mes_sel]

        total_ventas = df_mes["valor"].sum()
        total_comisiones = df_mes["comision"].sum()
        pagado = df_mes[df_mes["pagado"] == True]["comision"].sum()
        pendiente = total_comisiones - pagado

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Ventas", f"${total_ventas:,.2f}")
        col2.metric("📊 Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Pagado", f"${pagado:,.2f}")
        col4.metric("⏳ Pendiente", f"${pendiente:,.2f}")

        st.bar_chart(df_mes.groupby("cliente")["comision"].sum())

# ======================
# TAB 3: HISTORIAL
# ======================
with tabs[2]:
    st.header("📑 Historial de comisiones")

    df = obtener_comisiones()
    if df.empty:
        st.info("No hay registros aún.")
    else:
        st.dataframe(df, use_container_width=True)
