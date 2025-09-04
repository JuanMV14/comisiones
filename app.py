import os
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

# ============================
# CARGAR VARIABLES DE ENTORNO
# ============================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================
# CONFIG STREAMLIT
# ============================
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

# ============================
# FUNCIONES AUXILIARES
# ============================
def cargar_datos():
    resp = supabase.table("comisiones").select("*").execute()
    if not resp.data:
        return pd.DataFrame()
    df = pd.DataFrame(resp.data)

    # Normalizar nombres de columnas
    if "valor" in df.columns and "valor_factura" not in df.columns:
        df = df.rename(columns={"valor": "valor_factura"})

    # Convertir columnas de fechas
    for col in ["fecha_pedido", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # Asegurar columnas booleanas
    if "pagado" in df.columns:
        df["pagado"] = df["pagado"].fillna(False)

    # Calcular valor_comision si no existe
    if "valor_comision" not in df.columns and "valor_factura" in df.columns and "comision" in df.columns:
        df["valor_comision"] = df["valor_factura"].astype(float) * df["comision"].astype(float)

    return df


def subir_comprobante(file, pedido):
    # Subir archivo al bucket privado
    path = f"{pedido}/{file.name}"
    supabase.storage.from_(BUCKET).upload(path, file.getvalue(), {"upsert": True})
    return path


def obtener_link_comprobante(path):
    try:
        # Crear link firmado válido por 5 minutos
        url = supabase.storage.from_(BUCKET).create_signed_url(path, 300)
        return url
    except Exception:
        return None

# ============================
# APP - TABS
# ============================
tabs = st.tabs(["➕ Registrar Venta", "📊 Dashboard", "📑 Facturas"])

# ============================
# TAB 1: REGISTRAR VENTA
# ============================
with tabs[0]:
    st.header("➕ Registrar Nueva Venta")

    with st.form("form_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        valor_factura = st.number_input("Valor de la factura", min_value=0.0)
        comision = st.number_input("Porcentaje comisión (%)", min_value=0.0) / 100
        condicion_especial = st.checkbox("Cliente con condición especial (60 días)", value=False)

        fecha_pedido = st.date_input("Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("Fecha de la factura", value=date.today())

        # Calcular fechas de pago automático
        dias = 60 if condicion_especial else 35
        dias_max = 60 if condicion_especial else 45
        fecha_pago_est = fecha_factura + timedelta(days=dias)
        fecha_pago_max = fecha_factura + timedelta(days=dias_max)

        st.write(f"📅 Fecha estimada de pago: {fecha_pago_est}")
        st.write(f"📅 Fecha máxima de pago: {fecha_pago_max}")

        submitted = st.form_submit_button("Guardar Venta")
        if submitted:
            try:
                resp = supabase.table("comisiones").insert({
                    "pedido": pedido,
                    "cliente": cliente,
                    "valor_factura": valor_factura,
                    "comision": comision,
                    "valor_comision": valor_factura * comision,
                    "condicion_especial": condicion_especial,
                    "fecha_pedido": str(fecha_pedido),
                    "fecha_factura": str(fecha_factura),
                    "fecha_pago_est": str(fecha_pago_est),
                    "fecha_pago_max": str(fecha_pago_max),
                    "pagado": False
                }).execute()
                if resp.data:
                    st.success("✅ Venta registrada con éxito")
                else:
                    st.error(f"❌ Error al registrar la venta: {resp}")
            except Exception as e:
                st.error(f"⚠️ Error: {e}")

# ============================
# TAB 2: DASHBOARD
# ============================
with tabs[1]:
    st.header("📊 Dashboard de Comisiones")

    df = cargar_datos()
    if df.empty:
        st.info("No hay registros aún.")
    else:
        total_facturado = df["valor_factura"].sum() if "valor_factura" in df.columns else 0
        total_comision = df["valor_comision"].sum() if "valor_comision" in df.columns else 0
        total_pagado = df[df["pagado"] == True]["valor_factura"].sum() if "valor_factura" in df.columns else 0

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisión", f"${total_comision:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

        st.markdown("---")
        st.subheader("🏆 Ranking de Clientes (Top Compradores)")
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
        st.subheader("⚠️ Alertas de Vencimiento")

        hoy = pd.to_datetime(date.today())
        fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
        limite = hoy + timedelta(days=5)

        vencimientos = df[
            (df["pagado"] == False) &
            (fechas_pago.notna()) &
            (fechas_pago <= limite)
        ]

        if vencimientos.empty:
            st.success("✅ No hay facturas próximas a vencer")
        else:
            for _, row in vencimientos.iterrows():
                st.error(f"⚠️ Pedido {row['pedido']} de {row['cliente']} vence el {row['fecha_pago_max'].date()}")

# ============================
# TAB 3: FACTURAS
# ============================
with tabs[2]:
    st.header("📑 Facturas Registradas")

    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas aún.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"📌 Pedido {row['pedido']} - {row['cliente']}"):
                st.write(f"📅 Fecha Pedido: {row['fecha_pedido'].date() if pd.notna(row['fecha_pedido']) else '-'}")
                st.write(f"📅 Fecha Factura: {row['fecha_factura'].date() if pd.notna(row['fecha_factura']) else '-'}")
                st.write(f"📅 Fecha Estimada Pago: {row['fecha_pago_est'].date() if pd.notna(row['fecha_pago_est']) else '-'}")
                st.write(f"📅 Fecha Máxima Pago: {row['fecha_pago_max'].date() if pd.notna(row['fecha_pago_max']) else '-'}")
                st.write(f"💵 Valor: ${row['valor_factura']:,.2f}" if "valor_factura" in row else "💵 Valor: -")
                st.write(f"💰 Comisión: ${row['valor_comision']:,.2f}" if "valor_comision" in row else "💰 Comisión: -")
                st.write(f"✅ Pagado: {'Sí' if row['pagado'] else 'No'}")

                # Subir comprobante
                comprobante = st.file_uploader(f"Subir comprobante para pedido {row['pedido']}", type=["pdf", "jpg", "png"], key=f"comp_{row['id']}")
                if comprobante:
                    path = subir_comprobante(comprobante, row['pedido'])
                    supabase.table("comisiones").update({"comprobante_url": path}).eq("id", row["id"]).execute()
                    st.success("📎 Comprobante subido")

                # Ver comprobante si existe
                if row.get("comprobante_url"):
                    url = obtener_link_comprobante(row["comprobante_url"])
                    if url:
                        st.markdown(f"[🔗 Ver comprobante]({url})", unsafe_allow_html=True)
