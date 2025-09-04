import os
from datetime import date, datetime, timedelta

import pandas as pd
import streamlit as st
from supabase import create_client
from dotenv import load_dotenv

# ==============================
# CONFIG
# ==============================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

# ==============================
# FUNCIONES AUX
# ==============================
def subir_comprobante(file, filename):
    path = f"{filename}"
    supabase.storage.from_(BUCKET).upload(path, file, {"upsert": True})
    return path

def generar_link_temporal(path, segundos=300):
    try:
        res = supabase.storage.from_(BUCKET).create_signed_url(path, segundos)
        return res.get("signedURL", None)
    except Exception:
        return None

# ==============================
# APP PRINCIPAL
# ==============================
st.title("📊 Control de Comisiones")

tabs = st.tabs(["➕ Registrar Venta", "📑 Facturas", "📈 Dashboard"])

# ==============================
# TAB 1: REGISTRO DE VENTAS
# ==============================
with tabs[0]:
    st.header("➕ Registrar Venta")

    with st.form("form_registro"):
        pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Número de factura")
        valor_factura = st.number_input("Valor de la factura", min_value=0.0)
        comision = st.number_input("Porcentaje de comisión", min_value=0.0, max_value=1.0, step=0.01)

        condicion_especial = st.selectbox("¿Condición especial de pago?", ["No", "Sí"])
        fecha_pedido = st.date_input("Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("Fecha de factura", value=date.today())

        if condicion_especial == "Sí":
            fecha_pago_est = fecha_factura + timedelta(days=60)
            fecha_pago_max = fecha_factura + timedelta(days=60)
        else:
            fecha_pago_est = fecha_factura + timedelta(days=35)
            fecha_pago_max = fecha_factura + timedelta(days=45)

        comprobante = st.file_uploader("📎 Adjuntar comprobante (opcional)", type=["pdf", "jpg", "png"])
        submitted = st.form_submit_button("Guardar Venta")

        if submitted:
            try:
                comprobante_url = None
                if comprobante:
                    comprobante_url = subir_comprobante(
                        comprobante, f"{pedido}_{factura}_{comprobante.name}"
                    )

                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura,
                    "valor_factura": valor_factura,
                    "comision": comision,
                    "valor_comision": valor_factura * comision,
                    "condicion_especial": condicion_especial == "Sí",
                    "fecha_pedido": fecha_pedido.isoformat(),
                    "fecha_factura": fecha_factura.isoformat(),
                    "fecha_pago_est": fecha_pago_est.isoformat(),
                    "fecha_pago_max": fecha_pago_max.isoformat(),
                    "pagado": False,
                    "fecha_pago_real": None,
                    "comprobante_url": comprobante_url,
                }

                resp = supabase.table("comisiones").insert(data).execute()
                if resp.data:
                    st.success("✅ Venta registrada correctamente")
                    st.rerun()
                else:
                    st.error(f"❌ Error al registrar: {resp}")
            except Exception as e:
                st.error(f"❌ Error al registrar la venta: {e}")

# ==============================
# TAB 2: FACTURAS
# ==============================
with tabs[1]:
    st.header("📑 Facturas registradas")

    resp = supabase.table("comisiones").select("*").execute()
    df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame()

    if not df.empty:
        # Convertir fechas
        for col in ["fecha_pedido", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # ⚡ Parche: calcular valor_comision si no existe
        if "valor_comision" not in df.columns:
            if "valor_factura" in df.columns and "comision" in df.columns:
                df["valor_comision"] = df["valor_factura"].astype(float) * df["comision"].astype(float)
            else:
                df["valor_comision"] = 0.0

        # Mostrar facturas en tarjetas
        for _, row in df.iterrows():
            with st.container():
                st.subheader(f"📌 Pedido {row.get('pedido', '')} - Factura {row.get('factura', '')}")
                st.write(f"👤 Cliente: {row.get('cliente', '')}")
                st.write(f"💵 Valor: ${row.get('valor_factura', 0):,.2f}")
                st.write(f"💰 Comisión: ${row.get('valor_comision', 0):,.2f}")
                st.write(f"📅 Pedido: {row.get('fecha_pedido', '')}")
                st.write(f"📅 Factura: {row.get('fecha_factura', '')}")
                st.write(f"📅 Pago estimado: {row.get('fecha_pago_est', '')}")
                st.write(f"📅 Pago máximo: {row.get('fecha_pago_max', '')}")

                if row.get("pagado", False):
                    st.success(f"✅ Pagado el {row.get('fecha_pago_real', '')}")
                else:
                    if st.button(f"Marcar como pagado (Factura {row.get('factura', '')})", key=f"btn_pago_{row['id']}"):
                        supabase.table("comisiones").update({
                            "pagado": True,
                            "fecha_pago_real": date.today().isoformat()
                        }).eq("id", row["id"]).execute()
                        st.success("✅ Factura marcada como pagada")
                        st.rerun()

                if row.get("comprobante_url"):
                    link = generar_link_temporal(row["comprobante_url"])
                    if link:
                        st.markdown(f"[📎 Ver comprobante]({link})", unsafe_allow_html=True)

                st.markdown("---")
    else:
        st.info("No hay facturas registradas.")

# ==============================
# TAB 3: DASHBOARD
# ==============================
with tabs[2]:
    st.header("📈 Dashboard")

    if not df.empty:
        total_facturado = df["valor_factura"].sum() if "valor_factura" in df.columns else 0
        total_comisiones = df["valor_comision"].sum()
        total_pagado = df[df["pagado"] == True]["valor_factura"].sum()
        pendientes = total_facturado - total_pagado

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Pagado", f"${total_pagado:,.2f}")
        col4.metric("⌛ Pendiente", f"${pendientes:,.2f}")

        # Ranking de clientes
        st.subheader("🏆 Clientes que más compraron")
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

        # Alertas
        hoy = pd.to_datetime(date.today())
        if "fecha_pago_max" in df.columns:
            vencimientos = df[
                (df["pagado"] == False) &
                (pd.to_datetime(df["fecha_pago_max"], errors="coerce") <= hoy + timedelta(days=5))
            ]
            if not vencimientos.empty:
                st.warning("⚠️ Facturas próximas a vencer:")
                for _, row in vencimientos.iterrows():
                    st.write(f"Factura {row['factura']} - Cliente {row['cliente']} vence el {row['fecha_pago_max'].date()}")
    else:
        st.info("No hay datos para mostrar en el dashboard.")
