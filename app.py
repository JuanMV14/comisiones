import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from dotenv import load_dotenv
from supabase import create_client, Client

# =======================
# CONFIGURACIÓN
# =======================
load_dotenv()  # Cargar credenciales desde .env

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

# =======================
# FUNCIONES AUXILIARES
# =======================
def insertar_venta(pedido, cliente, referencia, factura, valor_factura, fecha_pedido,
                   fecha_factura, condicion_especial):
    """Inserta una nueva venta en la tabla comisiones"""
    # Calcular fechas de pago según condición
    if condicion_especial:
        fecha_pago = fecha_factura + timedelta(days=60)
        fecha_max = fecha_factura + timedelta(days=60)
    else:
        fecha_pago = fecha_factura + timedelta(days=35)
        fecha_max = fecha_factura + timedelta(days=45)

    data = {
        "pedido": pedido,
        "cliente": cliente,
        "referencia": referencia,
        "factura": factura,
        "valor_factura": valor_factura,
        "fecha_pedido": fecha_pedido.isoformat(),
        "fecha_factura": fecha_factura.isoformat(),
        "fecha_pago": fecha_pago.isoformat(),
        "fecha_pago_max": fecha_max.isoformat(),
        "condicion_especial": condicion_especial,
        "pagado": False,
    }

    resp = supabase.table("comisiones").insert(data).execute()
    return resp


def obtener_ventas():
    """Obtiene todas las ventas"""
    resp = supabase.table("comisiones").select("*").execute()
    return resp.data if resp.data else []


def marcar_pagada(id_, file=None):
    """Marca una factura como pagada y guarda comprobante si existe"""
    comprobante_file = None
    if file:
        # Subir archivo a bucket privado
        nombre_archivo = f"comprobante_{id_}_{file.name}"
        supabase.storage.from_(BUCKET).upload(nombre_archivo, file.getvalue())
        comprobante_file = nombre_archivo

    update_data = {
        "pagado": True,
        "fecha_pago_real": date.today().isoformat()
    }
    if comprobante_file:
        update_data["comprobante_file"] = comprobante_file

    supabase.table("comisiones").update(update_data).eq("id", id_).execute()


def generar_url_firmada(file_name, exp_seconds=300):
    """Genera URL firmada de comprobante en bucket privado"""
    try:
        res = supabase.storage.from_(BUCKET).create_signed_url(file_name, exp_seconds)
        return res.get("signedURL")
    except Exception:
        return None


# =======================
# INTERFAZ
# =======================
tabs = st.tabs(["📝 Registrar Venta", "📑 Facturas Pendientes", "📊 Dashboard", "📜 Historial"])

# -----------------------
# TAB 1: Registrar Venta
# -----------------------
with tabs[0]:
    st.header("📝 Registrar Nueva Venta")

    with st.form("form_registrar"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        referencia = st.text_input("Referencia")
        factura = st.text_input("Número de Factura")
        valor_factura = st.number_input("Valor Factura", min_value=0.0)
        fecha_pedido = st.date_input("Fecha Pedido", value=date.today())
        fecha_factura = st.date_input("Fecha Factura", value=date.today())
        condicion_especial = st.checkbox("¿Condición especial (60 días)?", value=False)

        submitted = st.form_submit_button("💾 Guardar")
        if submitted:
            try:
                resp = insertar_venta(pedido, cliente, referencia, factura, valor_factura,
                                      fecha_pedido, fecha_factura, condicion_especial)
                if resp.data:
                    st.success("✅ Venta registrada correctamente")
                else:
                    st.error(f"❌ Error al registrar: {resp}")
            except Exception as e:
                st.error(f"⚠️ Error inesperado: {e}")

# -----------------------
# TAB 2: Facturas Pendientes
# -----------------------
with tabs[1]:
    st.header("📑 Facturas Pendientes")

    ventas = obtener_ventas()
    if not ventas:
        st.info("No hay facturas registradas.")
    else:
        df = pd.DataFrame(ventas)
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"])
        df["fecha_pago"] = pd.to_datetime(df["fecha_pago"])
        df["fecha_pago_max"] = pd.to_datetime(df["fecha_pago_max"])

        pendientes = df[df["pagado"] == False]

        for _, row in pendientes.iterrows():
            with st.container():
                st.subheader(f"🧾 Factura {row['factura']}")
                st.write(f"📌 Pedido: {row['pedido']}")
                st.write(f"👤 Cliente: {row['cliente']}")
                st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                st.write(f"📅 Fecha Pedido: {row['fecha_pedido']}")
                st.write(f"📅 Fecha Factura: {row['fecha_factura'].date()}")
                st.write(f"⏳ Fecha Estimada Pago: {row['fecha_pago'].date()}")
                st.write(f"⚠️ Fecha Máxima Pago: {row['fecha_pago_max'].date()}")

                # Botón para marcar pagada
                with st.form(f"form_pago_{row['id']}"):
                    file = st.file_uploader("Subir comprobante", type=["pdf", "png", "jpg", "jpeg"],
                                            key=f"file_{row['id']}")
                    submitted = st.form_submit_button("✅ Marcar como Pagada")
                    if submitted:
                        marcar_pagada(row["id"], file)
                        st.success("Factura marcada como pagada")
                        st.rerun()

# -----------------------
# TAB 3: Dashboard
# -----------------------
with tabs[2]:
    st.header("📊 Dashboard de Ventas")

    ventas = obtener_ventas()
    if not ventas:
        st.info("No hay datos.")
    else:
        df = pd.DataFrame(ventas)
        df["valor_factura"] = df["valor_factura"].astype(float)
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"])

        # Ranking clientes
        st.subheader("🏆 Ranking Clientes")
        ranking = df.groupby("cliente")["valor_factura"].sum().sort_values(ascending=False).head(5)
        st.bar_chart(ranking)

        # Alertas
        st.subheader("⚠️ Alertas de vencimiento")
        hoy = date.today()
        df["fecha_pago_max"] = pd.to_datetime(df["fecha_pago_max"])
        alertas = df[(df["pagado"] == False) & (df["fecha_pago_max"].dt.date <= hoy + timedelta(days=5))]
        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencer.")
        else:
            st.warning("⚠️ Facturas próximas a vencer:")
            st.dataframe(alertas[["factura", "cliente", "fecha_pago_max"]])

        # Ventas por mes
        st.subheader("📅 Ventas por Mes")
        df["mes"] = df["fecha_factura"].dt.to_period("M").astype(str)
        resumen = df.groupby("mes")["valor_factura"].sum().reset_index()
        fig = px.bar(resumen, x="mes", y="valor_factura", title="Ventas por Mes")
        st.plotly_chart(fig, use_container_width=True)

# -----------------------
# TAB 4: Historial
# -----------------------
with tabs[3]:
    st.header("📜 Historial de Facturas")

    ventas = obtener_ventas()
    if not ventas:
        st.info("No hay historial aún.")
    else:
        df = pd.DataFrame(ventas)
        st.dataframe(df, use_container_width=True)

        # Mostrar link comprobante si existe
        for _, row in df.iterrows():
            if row.get("comprobante_file"):
                url = generar_url_firmada(row["comprobante_file"])
                if url:
                    st.markdown(f"📎 [Ver comprobante de {row['factura']}]({url})", unsafe_allow_html=True)
