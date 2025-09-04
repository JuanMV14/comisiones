import os
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from dotenv import load_dotenv

# ========================
# Cargar variables de entorno
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Funciones auxiliares
# ========================
def subir_comprobante(file, pedido_id):
    """Sube un comprobante al bucket privado"""
    if file is None:
        return None
    extension = os.path.splitext(file.name)[1]
    path = f"comprobantes/{pedido_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}{extension}"
    try:
        supabase.storage.from_(BUCKET).upload(
            path,
            file.getvalue(),
            file_options={"upsert": "true"}  # ✅ Fix aplicado
        )
        return path
    except Exception as e:
        st.error(f"❌ Error al subir comprobante: {e}")
        return None

def link_comprobante(path):
    """Genera un link firmado temporal al comprobante"""
    try:
        res = supabase.storage.from_(BUCKET).create_signed_url(path, 300)
        return res["signedURL"]
    except Exception:
        return None

def cargar_datos():
    """Carga los datos desde Supabase"""
    try:
        data = supabase.table("comisiones").select("*").execute()
        if not data.data:
            return pd.DataFrame()
        df = pd.DataFrame(data.data)

        # Normalizar columnas que pueden variar de nombre
        if "valor" in df.columns and "valor_factura" not in df.columns:
            df.rename(columns={"valor": "valor_factura"}, inplace=True)

        if "comision" in df.columns and "valor_comision" not in df.columns:
            df.rename(columns={"comision": "valor_comision"}, inplace=True)

        # Convertir fechas a datetime
        for col in ["fecha", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Asegurar columna pagado
        if "pagado" not in df.columns:
            df["pagado"] = False

        return df
    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        return pd.DataFrame()

# ========================
# Layout principal con Tabs
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")

tabs = st.tabs(["➕ Registrar Venta", "📑 Facturas", "📈 Dashboard", "⚠️ Alertas"])

# ========================
# TAB 1 - Registrar Venta
# ========================
with tabs[0]:
    st.header("➕ Registrar nueva venta")

    with st.form("form_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        referencia = st.text_input("Referencia")
        valor_factura = st.number_input("Valor Factura", min_value=0.0, step=1000.0)
        comision = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, step=0.5)
        fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        condicion_especial = st.selectbox("Condición Especial?", ["No", "Sí"])

        submit = st.form_submit_button("💾 Registrar")

    if submit:
        try:
            valor_comision = valor_factura * (comision / 100)
            dias_pago = 60 if condicion_especial == "Sí" else 35
            dias_max = 60 if condicion_especial == "Sí" else 45

            fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
            fecha_pago_max = fecha_factura + timedelta(days=dias_max)

            data = {
                "pedido": pedido,
                "cliente": cliente,
                "referencia": referencia,
                "valor_factura": valor_factura,
                "valor_comision": valor_comision,
                "fecha": datetime.now().isoformat(),
                "fecha_factura": fecha_factura.isoformat(),
                "fecha_pago_est": fecha_pago_est.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "condicion_especial": (condicion_especial == "Sí"),
                "pagado": False,
            }
            supabase.table("comisiones").insert(data).execute()
            st.success("✅ Venta registrada correctamente")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

# ========================
# TAB 2 - Facturas
# ========================
with tabs[1]:
    st.header("📑 Facturas registradas")
    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas todavía.")
    else:
        for _, row in df.iterrows():
            with st.container(border=True):
                st.subheader(f"🧾 Pedido: {row['pedido']} - Cliente: {row['cliente']}")
                st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                st.write(f"💰 Comisión: ${row.get('valor_comision', 0):,.2f}")
                st.write(f"📅 Fecha Factura: {row['fecha_factura'].date() if pd.notna(row['fecha_factura']) else '-'}")
                st.write(f"📅 Fecha Estimada Pago: {row['fecha_pago_est'].date() if pd.notna(row.get('fecha_pago_est')) else '-'}")
                st.write(f"📅 Fecha Máxima Pago: {row['fecha_pago_max'].date() if pd.notna(row.get('fecha_pago_max')) else '-'}")
                st.write(f"✅ Pagado: {'Sí' if row['pagado'] else 'No'}")

                # Subir comprobante
                comprobante = st.file_uploader(f"📎 Subir comprobante (Pedido {row['pedido']})", type=["pdf", "jpg", "png"], key=f"comp_{row['pedido']}")
                if comprobante:
                    path = subir_comprobante(comprobante, row['pedido'])
                    if path:
                        supabase.table("comisiones").update({"comprobante_url": path, "pagado": True}).eq("id", row["id"]).execute()
                        st.success("📎 Comprobante cargado y factura marcada como pagada")
                        st.rerun()

                # Mostrar link si ya existe comprobante
                if row.get("comprobante_url"):
                    url = link_comprobante(row["comprobante_url"])
                    if url:
                        st.markdown(f"[🔗 Ver comprobante]({url})", unsafe_allow_html=True)

# ========================
# TAB 3 - Dashboard
# ========================
with tabs[2]:
    st.header("📈 Dashboard de Comisiones")
    df = cargar_datos()
    if df.empty:
        st.info("No hay datos para mostrar en el dashboard.")
    else:
        total_facturado = df["valor_factura"].sum()
        total_comisiones = df.get("valor_comision", pd.Series([0])).sum()
        total_pagado = df[df["pagado"]]["valor_factura"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

        # Ranking clientes
        st.subheader("🏆 Ranking de Clientes")
        ranking = df.groupby("cliente")["valor_factura"].sum().reset_index().sort_values(by="valor_factura", ascending=False)
        for _, row in ranking.iterrows():
            st.write(f"**{row['cliente']}**")
            st.progress(min(1.0, row["valor_factura"] / total_facturado))

# ========================
# TAB 4 - Alertas
# ========================
with tabs[3]:
    st.header("⚠️ Alertas de vencimiento")
    df = cargar_datos()
    hoy = datetime.now()

    if not df.empty and "fecha_pago_max" in df.columns:
        fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")

        # ✅ Convertimos todo a datetime para evitar el TypeError
        limite = hoy + timedelta(days=5)
        alertas = df[(df["pagado"] == False) & (fechas_pago <= limite)]

        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencerse")
        else:
            for _, row in alertas.iterrows():
                st.error(f"⚠️ Pedido {row['pedido']} ({row['cliente']}) vence el {row['fecha_pago_max'].date()}")
    else:
        st.info("No hay datos de fechas de pago para generar alertas.")
