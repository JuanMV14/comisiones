import os
from datetime import date, timedelta
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# -------------------------
# CARGAR VARIABLES DE ENTORNO
# -------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# CONFIG STREAMLIT
# -------------------------
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

# -------------------------
# FUNCIONES AUXILIARES
# -------------------------
def subir_comprobante(archivo, nombre_archivo):
    """Subir comprobante al bucket privado"""
    try:
        supabase.storage.from_(BUCKET).upload(nombre_archivo, archivo.getvalue(), {"upsert": True})
        return True
    except Exception as e:
        st.error(f"Error al subir comprobante: {e}")
        return False

def obtener_link_comprobante(nombre_archivo, exp=300):
    """Obtener link firmado (temporal)"""
    try:
        return supabase.storage.from_(BUCKET).create_signed_url(nombre_archivo, exp)["signedURL"]
    except Exception:
        return None

def normalizar_fechas(df):
    """Convertir todas las fechas a datetime para evitar TypeError"""
    for col in ["fecha", "fecha_factura", "fecha_pago_estimada", "fecha_pago_max", "fecha_pago_real"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

# -------------------------
# INTERFAZ PRINCIPAL
# -------------------------
tabs = st.tabs(["📝 Registrar Venta", "📊 Dashboard", "📑 Facturas / Historial"])

# ==============================
# TAB 1: REGISTRAR VENTA
# ==============================
with tabs[0]:
    st.header("📝 Registrar Venta")

    with st.form("form_venta"):
        numero_pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        referencia = st.text_input("Referencia")
        valor_factura = st.number_input("Valor Factura", min_value=0.01, step=0.01)

        fecha_pedido = st.date_input("Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("Fecha de factura", value=date.today())

        condicion_especial = st.checkbox("Cliente con condición especial (60 días)")
        dias_pago = 60 if condicion_especial else 35
        dias_max = 60 if condicion_especial else 45

        fecha_pago_estimada = fecha_factura + timedelta(days=dias_pago)
        fecha_pago_max = fecha_factura + timedelta(days=dias_max)

        st.write(f"📅 Fecha estimada de pago: **{fecha_pago_estimada}**")
        st.write(f"⚠️ Fecha máxima de pago: **{fecha_pago_max}**")

        comprobante = st.file_uploader("Adjuntar comprobante de pago (opcional)", type=["pdf", "jpg", "png"])

        submitted = st.form_submit_button("💾 Guardar Venta")

        if submitted:
            data = {
                "numero_pedido": numero_pedido,
                "cliente": cliente,
                "referencia": referencia,
                "valor_factura": valor_factura,
                "fecha": str(fecha_pedido),
                "fecha_factura": str(fecha_factura),
                "fecha_pago_estimada": str(fecha_pago_estimada),
                "fecha_pago_max": str(fecha_pago_max),
                "condicion_especial": condicion_especial,
                "pagado": False,
            }

            try:
                resp = supabase.table("comisiones").insert(data).execute()
                if resp.data:
                    st.success("✅ Venta registrada correctamente")

                    if comprobante:
                        nombre_archivo = f"{numero_pedido}_{cliente}_{comprobante.name}"
                        if subir_comprobante(comprobante, nombre_archivo):
                            st.success("📂 Comprobante subido")
                else:
                    st.error(f"❌ Error al registrar: {resp}")
            except Exception as e:
                st.error(f"❌ Error inesperado: {e}")

# ==============================
# TAB 2: DASHBOARD
# ==============================
with tabs[1]:
    st.header("📊 Dashboard de Comisiones")

    try:
        resp = supabase.table("comisiones").select("*").execute()
        df = pd.DataFrame(resp.data)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        df = pd.DataFrame()

    if not df.empty:
        df = normalizar_fechas(df)

        total_facturado = df["valor_factura"].sum()
        total_pagado = df[df["pagado"] == True]["valor_factura"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("✅ Pagado", f"${total_pagado:,.2f}")
        col3.metric("⏳ Pendiente", f"${total_facturado - total_pagado:,.2f}")

        st.markdown("---")
        st.subheader("🏆 Ranking Clientes (por facturación)")

        ranking = df.groupby("cliente")["valor_factura"].sum().reset_index().sort_values(by="valor_factura", ascending=False)

        max_val = ranking["valor_factura"].max()
        for _, row in ranking.iterrows():
            porcentaje = (row["valor_factura"] / max_val) * 100 if max_val else 0
            st.markdown(f"""
                <div style='margin-bottom:10px;'>
                    <b>{row['cliente']}</b> - ${row['valor_factura']:,.2f}
                    <div style='background:#ddd; border-radius:10px; height:20px;'>
                        <div style='width:{porcentaje:.2f}%; background:#3498db; height:20px; border-radius:10px;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("⚠️ Alertas de vencimiento")

        hoy = date.today()
        vencimientos = df[
            (df["pagado"] == False) &
            (df["fecha_pago_max"].notna()) &
            (df["fecha_pago_max"].dt.date <= hoy + timedelta(days=5))
        ]

        if vencimientos.empty:
            st.success("✅ No hay facturas próximas a vencer")
        else:
            for _, row in vencimientos.iterrows():
                st.warning(f"Factura {row['numero_pedido']} de {row['cliente']} vence el {row['fecha_pago_max'].date()}")

    else:
        st.info("No hay datos registrados aún.")

# ==============================
# TAB 3: FACTURAS / HISTORIAL
# ==============================
with tabs[2]:
    st.header("📑 Facturas / Historial")

    try:
        resp = supabase.table("comisiones").select("*").execute()
        df = pd.DataFrame(resp.data)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        df = pd.DataFrame()

    if not df.empty:
        df = normalizar_fechas(df)
        df = df.sort_values("fecha_factura", ascending=False)

        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"""
                    <div style='padding:15px; margin-bottom:10px; border:1px solid #ddd; border-radius:10px;'>
                        <h4>📌 Pedido {row['numero_pedido']} - {row['cliente']}</h4>
                        <p><b>Referencia:</b> {row['referencia']}</p>
                        <p><b>Valor:</b> ${row['valor_factura']:,.2f}</p>
                        <p><b>Fecha Pedido:</b> {row['fecha'].date() if pd.notna(row['fecha']) else '-'}</p>
                        <p><b>Fecha Factura:</b> {row['fecha_factura'].date() if pd.notna(row['fecha_factura']) else '-'}</p>
                        <p><b>Fecha Pago Estimada:</b> {row['fecha_pago_estimada'].date() if pd.notna(row['fecha_pago_estimada']) else '-'}</p>
                        <p><b>Fecha Máxima Pago:</b> {row['fecha_pago_max'].date() if pd.notna(row['fecha_pago_max']) else '-'}</p>
                        <p><b>Pagado:</b> {"✅ Sí" if row['pagado'] else "❌ No"}</p>
                    </div>
                """, unsafe_allow_html=True)

                if "comprobante_url" in row and row["comprobante_url"]:
                    link = obtener_link_comprobante(row["comprobante_url"])
                    if link:
                        st.markdown(f"[📂 Ver comprobante]({link})")
                st.markdown("---")
    else:
        st.info("No hay facturas registradas aún.")
