import os
from datetime import date, datetime
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

from queries import (
    obtener_facturas,
    insertar_factura,
    marcar_factura_pagada,
)
from utils import safe_get_public_url

# ========================
# Configuración inicial
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def main():
    st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
    st.title("📊 Gestión de Comisiones")

    # Cargar facturas desde Supabase
    df = obtener_facturas(supabase)

    # Menú lateral
    menu = st.sidebar.radio("Menú", ["Registrar factura", "Facturas pendientes", "Facturas pagadas", "Alertas"])

    if menu == "Registrar factura":
        registrar_factura(df)

    elif menu == "Facturas pendientes":
        mostrar_facturas(df, estado="pendiente")

    elif menu == "Facturas pagadas":
        mostrar_facturas(df, estado="pagada")

    elif menu == "Alertas":
        mostrar_alertas(df)


# ========================
# Registrar Factura
# ========================
def registrar_factura(df):
    st.header("📝 Registrar Factura")

    with st.form("form_factura"):
        pedido = st.text_input("Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Factura")
        valor = st.number_input("Valor", min_value=0.0, format="%.2f")
        porcentaje = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, value=10.0)
        fecha_factura = st.date_input("Fecha factura", date.today())

        submitted = st.form_submit_button("Registrar")

        if submitted:
            comision = valor * (porcentaje / 100)
            nueva_factura = {
                "pedido": pedido,
                "cliente": cliente,
                "factura": factura,
                "valor": valor,
                "porcentaje": porcentaje,
                "comision": comision,
                "fecha_factura": fecha_factura.isoformat(),
                "pagado": False,
            }
            insertar_factura(supabase, nueva_factura)
            st.success("Factura registrada correctamente ✅")


# ========================
# Mostrar Facturas
# ========================
def mostrar_facturas(df, estado="pendiente"):
    if df.empty:
        st.info("No hay facturas registradas aún.")
        return

    if estado == "pendiente":
        facturas = df[df["pagado"] == False]
        st.header("📌 Facturas Pendientes")
    else:
        facturas = df[df["pagado"] == True]
        st.header("✅ Facturas Pagadas")

    if facturas.empty:
        st.info("No hay facturas en este estado.")
        return

    for _, row in facturas.iterrows():
        with st.expander(f"Factura {row['factura']} - Cliente: {row['cliente']}"):
            st.write(f"📅 Fecha factura: {row['fecha_factura']}")
            st.write(f"💵 Valor: {row['valor']}")
            st.write(f"📊 Porcentaje: {row['porcentaje']}%")
            st.write(f"💰 Comisión: {row['comision']}")

            if not row["pagado"]:
                archivo = st.file_uploader("Subir comprobante de pago", type=["jpg", "png", "pdf"], key=row["id"])
                if archivo:
                    # Guardar en Supabase Storage
                    path = f"{row['id']}/{archivo.name}"
                    supabase.storage.from_(BUCKET).upload(path, archivo.getvalue())
                    url = safe_get_public_url(supabase, BUCKET, path)

                    marcar_factura_pagada(supabase, row["id"], url)
                    st.success("Factura marcada como pagada ✅")
                    st.rerun()
            else:
                if row["comprobante_url"]:
                    st.markdown(f"📎 [Ver comprobante]({row['comprobante_url']})")


# ========================
# Mostrar Alertas
# ========================
def mostrar_alertas(df):
    st.header("🚨 Alertas")

    if df.empty:
        st.info("No hay facturas registradas aún.")
        return

    hoy = pd.to_datetime(date.today())

    vencidas = df[(df["pagado"] == False) & (pd.to_datetime(df["fecha_factura"]) < hoy)]

    if vencidas.empty:
        st.success("No hay facturas vencidas 🎉")
    else:
        st.error("⚠️ Facturas vencidas:")
        for _, row in vencidas.iterrows():
            st.write(f"- Factura {row['factura']} (Cliente: {row['cliente']}) - Fecha: {row['fecha_factura']}")


if __name__ == "__main__":
    main()
