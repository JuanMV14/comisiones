import os
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# -------------------------
# CONFIG
# -------------------------
load_dotenv()
st.set_page_config(page_title="📊 Comisiones", layout="wide")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# FUNCIONES
# -------------------------
def cargar_datos():
    try:
        response = supabase.table("comisiones").select("*").execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Error cargando datos: {e}")
        return pd.DataFrame()

def registrar_venta(pedido, cliente, factura, valor_factura, porcentaje, condicion_especial, fecha_pedido, fecha_factura):
    try:
        valor_comision = valor_factura * (porcentaje / 100)

        # lógica de plazos
        if condicion_especial:
            fecha_pago = fecha_factura + timedelta(days=60)
            fecha_max = fecha_factura + timedelta(days=60)
        else:
            fecha_pago = fecha_factura + timedelta(days=35)
            fecha_max = fecha_factura + timedelta(days=45)

        data = {
            "pedido": pedido,
            "cliente": cliente,
            "factura": factura,
            "valor_factura": valor_factura,
            "porcentaje": porcentaje,
            "valor_comision": valor_comision,
            "condicion_especial": condicion_especial,
            "fecha": fecha_pedido,
            "fecha_factura": fecha_factura,
            "fecha_pago_estimado": fecha_pago,
            "fecha_pago_max": fecha_max,
            "pagado": False,
        }

        resp = supabase.table("comisiones").insert(data).execute()
        return resp
    except Exception as e:
        st.error(f"❌ Error al registrar la venta: {e}")
        return None

def subir_comprobante(factura, file):
    try:
        file_path = f"{factura}/{file.name}"
        supabase.storage.from_(BUCKET).upload(file_path, file.getvalue(), {"upsert": True})
        return file_path
    except Exception as e:
        st.error(f"❌ Error subiendo comprobante: {e}")
        return None

def obtener_link_comprobante(path):
    try:
        if not path:
            return None
        resp = supabase.storage.from_(BUCKET).create_signed_url(path, 300)  # 5 minutos
        return resp.get("signedURL", None)
    except Exception:
        return None

def marcar_pagado(id, file=None):
    try:
        file_path = None
        if file:
            file_path = subir_comprobante(str(id), file)

        supabase.table("comisiones").update({
            "pagado": True,
            "fecha_pago_real": date.today(),
            "comprobante_url": file_path
        }).eq("id", id).execute()
        st.success("✅ Factura marcada como pagada")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error al actualizar pago: {e}")

# -------------------------
# APP
# -------------------------
st.title("📊 Control de Comisiones")

tabs = st.tabs(["📝 Registrar Venta", "📊 Dashboard", "📑 Historial"])

# =============================
# TAB 1 - Registrar Venta
# =============================
with tabs[0]:
    st.header("📝 Registrar Nueva Venta")

    with st.form("registro_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Número de Factura")
        valor_factura = st.number_input("Valor de la Factura", min_value=0.0, step=1000.0)
        porcentaje = st.number_input("Porcentaje de Comisión (%)", min_value=0.0, max_value=100.0, value=1.0)
        condicion_especial = st.checkbox("¿Cliente con condición especial (60 días)?")
        fecha_pedido = st.date_input("Fecha del Pedido", value=date.today())
        fecha_factura = st.date_input("Fecha de la Factura", value=date.today())

        submit = st.form_submit_button("Guardar Venta")
        if submit:
            resp = registrar_venta(pedido, cliente, factura, valor_factura, porcentaje,
                                   condicion_especial, fecha_pedido, fecha_factura)
            if resp:
                st.success("✅ Venta registrada correctamente")

# =============================
# TAB 2 - Dashboard
# =============================
with tabs[1]:
    st.header("📊 Dashboard")

    df = cargar_datos()
    if not df.empty:
        # Convertir fechas
        for col in ["fecha", "fecha_factura", "fecha_pago_estimado", "fecha_pago_max", "fecha_pago_real"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        hoy = date.today()

        # Alertas de vencimientos
        if "fecha_pago_max" in df.columns:
            vencimientos = df[
                (df["pagado"] == False) &
                (df["fecha_pago_max"].notnull()) &
                (df["fecha_pago_max"].dt.date <= hoy + timedelta(days=5))
            ]
            if not vencimientos.empty:
                st.warning("⚠️ Facturas próximas a vencer:")
                for _, row in vencimientos.iterrows():
                    st.write(f"- Cliente: {row['cliente']} | Factura: {row['factura']} | Vence: {row['fecha_pago_max'].date()}")

        # Ranking clientes
        st.subheader("🏆 Clientes con más compras")
        ranking = df.groupby("cliente")["valor_factura"].sum().reset_index().sort_values("valor_factura", ascending=False)
        max_val = ranking["valor_factura"].max()
        for _, row in ranking.iterrows():
            pct = (row["valor_factura"] / max_val) * 100 if max_val else 0
            st.markdown(f"""
                <div style='margin-bottom:10px;'>
                    <b>{row['cliente']}</b> - ${row['valor_factura']:,.2f}
                    <div style='background:#ddd; border-radius:10px; height:20px;'>
                        <div style='width:{pct:.2f}%; background:#3498db; height:20px; border-radius:10px;'></div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No hay registros aún.")

# =============================
# TAB 3 - Historial
# =============================
with tabs[2]:
    st.header("📑 Historial de Facturas")

    df = cargar_datos()
    if not df.empty:
        for _, row in df.iterrows():
            with st.container():
                st.markdown("---")
                st.subheader(f"📄 Factura {row['factura']} - Cliente: {row['cliente']}")
                st.write(f"🗓 Fecha Pedido: {row['fecha']}")
                st.write(f"🗓 Fecha Factura: {row['fecha_factura']}")
                st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                st.write(f"💰 Comisión: ${row['valor_comision']:,.2f}")
                st.write(f"⏳ Fecha Estimada de Pago: {row['fecha_pago_estimado']}")
                st.write(f"⏳ Fecha Máxima: {row['fecha_pago_max']}")
                st.write(f"✅ Pagado: {'Sí' if row['pagado'] else 'No'}")

                if row.get("pagado"):
                    if row.get("comprobante_url"):
                        link = obtener_link_comprobante(row["comprobante_url"])
                        if link:
                            st.markdown(f"[📎 Ver comprobante]({link})", unsafe_allow_html=True)
                else:
                    file = st.file_uploader(f"📤 Subir comprobante para factura {row['factura']}", type=["pdf", "jpg", "png"], key=f"file_{row['id']}")
                    if st.button(f"Marcar como pagada {row['factura']}", key=f"pagar_{row['id']}"):
                        marcar_pagado(row["id"], file)

    else:
        st.info("No hay facturas registradas aún.")
