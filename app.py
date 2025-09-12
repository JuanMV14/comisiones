import os
from datetime import date
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

from utils import calcular_comision, render_table, mostrar_dashboard
from queries import (
    get_facturas_pendientes,
    get_facturas_pagadas,
    insert_factura,
)

# ========================
# Configuración inicial
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gestión de Comisiones", layout="wide")

# ========================
# App
# ========================
def main():
    st.title("📊 Gestión de Comisiones")

    tabs = st.tabs(["📈 Dashboard", "📝 Registrar Venta", "📌 Facturas Pendientes", "✅ Facturas Pagadas"])

    # ========================
    # DASHBOARD
    # ========================
    with tabs[0]:
        facturas_pend = get_facturas_pendientes(supabase)
        facturas_pag = get_facturas_pagadas(supabase)
        mostrar_dashboard(facturas_pend, facturas_pag)

    # ========================
    # REGISTRAR VENTA
    # ========================
    with tabs[1]:
        st.subheader("Registrar Nueva Venta")

        with st.form("registro_venta", clear_on_submit=True):
            pedido = st.text_input("Número de Pedido")
            cliente = st.text_input("Cliente")
            factura = st.text_input("Factura")
            valor_base = st.number_input("Valor Base (sin IVA, sin descuento)", min_value=0.0, step=1000.0)
            porcentaje = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, value=5.0)
            fecha_pedido = st.date_input("Fecha Pedido", value=date.today())
            fecha_factura = st.date_input("Fecha Factura", value=date.today())
            tiene_descuento = st.selectbox("¿Tiene descuento a pie de factura?", ["Sí", "No"]) == "Sí"

            submitted = st.form_submit_button("Registrar")

            if submitted:
                comision = calcular_comision(
                    valor_base,
                    porcentaje,
                    fecha_factura,
                    fecha_factura,  # al inicio igual a la fecha de factura
                    tiene_descuento,
                )

                data = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura,
                    "valor": valor_base,
                    "valor_base": valor_base,
                    "porcentaje": porcentaje,
                    "comision": comision,
                    "fecha_pedido": str(fecha_pedido),
                    "fecha_factura": str(fecha_factura),
                    "tiene_descuento_factura": tiene_descuento,
                    "pagado": False,
                }

                insert_factura(supabase, data)
                st.success("✅ Venta registrada correctamente")

    # ========================
    # FACTURAS PENDIENTES
    # ========================
    with tabs[2]:
        facturas_pend = get_facturas_pendientes(supabase)
        if not facturas_pend.empty:
            st.subheader("Facturas Pendientes")
            render_table(facturas_pend, supabase, editable=True)
        else:
            st.info("No hay facturas pendientes.")

    # ========================
    # FACTURAS PAGADAS
    # ========================
    with tabs[3]:
        facturas_pag = get_facturas_pagadas(supabase)
        if not facturas_pag.empty:
            st.subheader("Facturas Pagadas")
            render_table(facturas_pag, supabase, editable=True)
        else:
            st.info("No hay facturas pagadas.")


if __name__ == "__main__":
    main()
