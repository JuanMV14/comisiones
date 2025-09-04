import os
from datetime import date, timedelta
import pandas as pd
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

# ==============================
# CONFIGURACIÓN
# ==============================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

# ==============================
# HELPER: CARGAR Y CONVERTIR FECHAS
# ==============================
def cargar_datos():
    response = supabase.table("comisiones").select("*").execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        for col in ["fecha_pedido", "fecha_factura", "fecha_pago",
                    "fecha_maxima", "fecha_pago_real", "fecha_pago_max"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        if "valor" in df.columns:
            df["valor"] = df["valor"].astype(float)
    return df

# ==============================
# APP
# ==============================
st.title("📊 Control de Comisiones")

tabs = st.tabs(["➕ Registrar venta", "📈 Dashboard", "⚠️ Alertas", "📋 Facturas"])

# ==============================
# TAB 1: REGISTRO DE VENTA
# ==============================
with tabs[0]:
    st.header("➕ Registrar nueva venta")

    with st.form("registro_venta"):
        pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        referencia = st.text_input("Referencia")
        valor = st.number_input("Valor de la factura", min_value=0.0, step=1000.0)
        porcentaje = st.number_input("Porcentaje de comisión (%)", min_value=0.0, max_value=100.0, step=0.1)
        condicion_especial = st.checkbox("Cliente con condición especial (60 días)")

        fecha_pedido = st.date_input("📅 Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("📅 Fecha de la factura", value=date.today())

        # Fechas automáticas
        if condicion_especial:
            fecha_pago = fecha_factura + timedelta(days=60)
            fecha_maxima = fecha_factura + timedelta(days=60)
        else:
            fecha_pago = fecha_factura + timedelta(days=35)
            fecha_maxima = fecha_factura + timedelta(days=45)

        st.write(f"📆 Fecha de pago estimada: **{fecha_pago}**")
        st.write(f"📆 Fecha máxima: **{fecha_maxima}**")

        comprobante = st.file_uploader("📎 Adjuntar comprobante (opcional)", type=["jpg", "png", "pdf"])

        submitted = st.form_submit_button("💾 Guardar venta")

        if submitted:
            try:
                comision = valor * (porcentaje / 100.0)

                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "referencia": referencia,
                    "valor": valor,
                    "porcentaje": porcentaje,
                    "comision": comision,
                    "condicion_especial": condicion_especial,
                    "fecha_pedido": fecha_pedido.isoformat(),
                    "fecha_factura": fecha_factura.isoformat(),
                    "fecha_pago": fecha_pago.isoformat(),
                    "fecha_maxima": fecha_maxima.isoformat(),
                    "pagado": False
                }

                resp = supabase.table("comisiones").insert(data).execute()
                row_id = resp.data[0]["id"]

                # Subir comprobante si existe
                if comprobante:
                    ext = comprobante.name.split(".")[-1]
                    file_path = f"{row_id}.{ext}"
                    supabase.storage.from_(BUCKET).upload(file_path, comprobante.getvalue(), {"upsert": True})
                    supabase.table("comisiones").update({"comprobante_url": file_path}).eq("id", row_id).execute()

                st.success("✅ Venta registrada correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar la venta: {e}")

# ==============================
# TAB 2: DASHBOARD
# ==============================
with tabs[1]:
    st.header("📈 Dashboard de clientes")

    df = cargar_datos()
    if not df.empty:
        ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)

        max_val = ranking["valor"].max()

        for _, row in ranking.iterrows():
            porcentaje = (row["valor"] / max_val) * 100 if max_val > 0 else 0
            st.markdown(f"""
                <div style='margin-bottom:10px;'>
                    <b>{row['cliente']}</b> - ${row['valor']:,.2f}
                    <div style='background:#ddd; border-radius:10px; height:20px;'>
                        <div style='width:{porcentaje:.2f}%; background:#3498db; height:20px; border-radius:10px;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay datos registrados aún.")

# ==============================
# TAB 3: ALERTAS
# ==============================
with tabs[2]:
    st.header("⚠️ Facturas próximas a vencer")

    df = cargar_datos()
    if not df.empty and "fecha_pago_max" in df.columns:
        hoy = date.today()
        vencimientos = df[(df["pagado"] == False) & (df["fecha_pago_max"].dt.date <= hoy + timedelta(days=5))]

        if vencimientos.empty:
            st.success("✅ No hay facturas próximas a vencer.")
        else:
            for _, row in vencimientos.iterrows():
                st.warning(f"⚠️ Cliente: {row['cliente']} - Factura {row['referencia']} "
                           f"vence el {row['fecha_pago_max'].date()}")
    else:
        st.info("No hay facturas registradas o faltan fechas.")

# ==============================
# TAB 4: FACTURAS (Tarjetas)
# ==============================
with tabs[3]:
    st.header("📋 Historial de facturas")

    df = cargar_datos()
    if not df.empty:
        for _, row in df.sort_values("fecha_factura", ascending=False).iterrows():
            with st.container():
                st.markdown(f"""
                    <div style="border:1px solid #ccc; border-radius:10px; padding:15px; margin-bottom:10px;">
                        <h4>📄 Pedido {row['pedido']} - {row['cliente']}</h4>
                        <p><b>Referencia:</b> {row['referencia']}</p>
                        <p><b>Valor:</b> ${row['valor']:,.2f}</p>
                        <p><b>Fecha factura:</b> {row['fecha_factura'].date() if pd.notnull(row['fecha_factura']) else '-'}</p>
                        <p><b>Fecha pago estimada:</b> {row['fecha_pago'].date() if pd.notnull(row['fecha_pago']) else '-'}</p>
                        <p><b>Fecha máxima:</b> {row['fecha_maxima'].date() if pd.notnull(row['fecha_maxima']) else '-'}</p>
                        <p><b>Pagado:</b> {"✅ Sí" if row.get("pagado") else "❌ No"}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No hay facturas registradas aún.")
