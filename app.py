import os
from datetime import datetime, timedelta, date
import pandas as pd
import streamlit as st
import altair as alt
from supabase import create_client, Client
from dotenv import load_dotenv

# ========================
# Conexión a Supabase
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Cargar datos
# ========================
@st.cache_data
def load_data():
    data = supabase.table("comisiones").select("*").execute()
    df = pd.DataFrame(data.data)
    if not df.empty:
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")
        df["fecha_pago_max"] = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
        df["fecha_pago_real"] = pd.to_datetime(df["fecha_pago_real"], errors="coerce")
        df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
    return df

df = load_data()

# ========================
# Configuración de Tabs
# ========================
tabs = st.tabs([
    "📝 Registrar Venta",
    "📂 Facturas Pendientes",
    "✅ Facturas Pagadas",
    "📊 Dashboard",
    "⚠️ Alertas",
    "💼 Editar Facturas"
])

# ========================
# TAB 1 - Registrar Venta
# ========================
with tabs[0]:
    st.header("📝 Registrar Nueva Venta")
    with st.form("registro_form"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        valor_factura = st.number_input("Valor Factura", min_value=0.0, step=1000.0)
        fecha_factura = st.date_input("Fecha Factura", value=date.today())
        fecha_pago_max = st.date_input("Fecha Límite de Pago", value=date.today() + timedelta(days=30))
        porcentaje = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, step=0.1, value=1.5)
        enviado = st.form_submit_button("Registrar Venta")

        if enviado:
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
            st.experimental_rerun()

# ========================
# TAB 2 - Facturas Pendientes
# ========================
with tabs[1]:
    st.header("📂 Facturas Pendientes")
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pendientes = df[df["pagado"] == False].sort_values("fecha_factura", ascending=False)
        st.dataframe(df_pendientes[["pedido", "cliente", "valor_factura", "fecha_factura", "fecha_pago_max", "valor_comision"]])

# ========================
# TAB 3 - Facturas Pagadas
# ========================
with tabs[2]:
    st.header("✅ Facturas Pagadas")
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pagadas = df[df["pagado"] == True].sort_values("fecha_pago_real", ascending=False)
        st.dataframe(df_pagadas[["pedido", "cliente", "valor_factura", "fecha_factura", "fecha_pago_real", "valor_comision"]])

# ========================
# TAB 4 - Dashboard
# ========================
with tabs[3]:
    st.header("📊 Dashboard de Comisiones")
    if df.empty:
        st.info("No hay datos disponibles.")
    else:
        total_facturado = df["valor_factura"].sum()
        total_comisiones = df["valor_comision"].sum()
        total_pagado = df[df["pagado"]]["valor_factura"].sum()

        col1,col2,col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

        # Ranking clientes
        st.subheader("🏆 Ranking de Clientes")
        ranking = df.groupby("cliente")["valor_factura"].sum().reset_index().sort_values(by="valor_factura", ascending=True)
        if not ranking.empty:
            chart_ranking = alt.Chart(ranking).mark_bar().encode(
                x=alt.X("valor_factura", title="Valor Facturado"),
                y=alt.Y("cliente", sort='-x', title="Cliente"),
                tooltip=["cliente", "valor_factura"]
            )
            st.altair_chart(chart_ranking, use_container_width=True)

        # Flujo comisiones
        st.subheader("📅 Flujo de Comisiones por Mes")
        flujo = df.groupby("mes_factura")["valor_comision"].sum().reset_index().sort_values("mes_factura")
        if not flujo.empty:
            chart_flujo = alt.Chart(flujo).mark_bar(color="#FF7F0E").encode(
                x=alt.X("mes_factura", title="Mes Factura"),
                y=alt.Y("valor_comision", title="Comisiones"),
                tooltip=["mes_factura", "valor_comision"]
            )
            st.altair_chart(chart_flujo, use_container_width=True)

# ========================
# TAB 5 - Alertas
# ========================
with tabs[4]:
    st.header("⚠️ Alertas de Vencimiento")
    if df.empty:
        st.info("No hay facturas.")
    else:
        hoy = datetime.now()
        limite = hoy + timedelta(days=5)
        alertas = df[(df["pagado"] == False) & (df["fecha_pago_max"] <= limite)]
        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencerse")
        else:
            for _, row in alertas.iterrows():
                st.error(f"⚠️ Pedido {row['pedido']} ({row['cliente']}) vence el {row['fecha_pago_max'].date()}")

# ========================
# TAB 6 - Editar Facturas
# ========================
with tabs[5]:
    st.header("💼 Editar Facturas")
    if df.empty:
        st.info("No hay facturas para editar.")
    else:
        pedido_seleccionado = st.selectbox("Selecciona una factura", df["pedido"].astype(str).tolist())
        factura = df[df["pedido"] == pedido_seleccionado].iloc[0]

        st.write(f"Cliente: **{factura['cliente']}**")
        valor_factura = st.number_input("Valor Factura", value=float(factura["valor_factura"]))
        porcentaje = st.number_input(
            "Porcentaje de Comisión (%)",
            value=float(factura["valor_comision"] / factura["valor_factura"] * 100 if factura["valor_factura"] else 0),
            min_value=0.0, max_value=100.0, step=0.1
        )
        pagado = st.selectbox("Pagado?", ["No", "Sí"], index=1 if factura["pagado"] else 0)
        fecha_pago_real = st.date_input(
            "Fecha de Pago Real",
            value=factura["fecha_pago_real"].date() if pd.notnull(factura["fecha_pago_real"]) else date.today()
        )

        if st.button("💾 Guardar cambios"):
            valor_comision = valor_factura * (porcentaje / 100)
            supabase.table("comisiones").update({
                "valor_factura": valor_factura,
                "valor_comision": valor_comision,
                "pagado": (pagado == "Sí"),
                "fecha_pago_real": fecha_pago_real.isoformat() if pagado == "Sí" else None
            }).eq("id", factura["id"]).execute()
            st.success("✅ Cambios guardados correctamente")
            st.experimental_rerun()
