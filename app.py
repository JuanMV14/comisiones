import os
from datetime import datetime, date
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

from utils import calcular_comision, render_table
from queries import (
    get_facturas_pendientes,
    get_facturas_pagadas,
    update_factura,
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

    tabs = st.tabs(["📌 Facturas Pendientes", "✅ Facturas Pagadas"])

    # ========================
    # FACTURAS PENDIENTES
    # ========================
    with tabs[0]:
        facturas_pend = get_facturas_pendientes(supabase)

        if not facturas_pend.empty:
            st.subheader("Facturas Pendientes")
            render_table(facturas_pend, supabase, editable=True)
        else:
            st.info("No hay facturas pendientes.")

    # ========================
    # FACTURAS PAGADAS
    # ========================
    with tabs[1]:
        facturas_pag = get_facturas_pagadas(supabase)

        if not facturas_pag.empty:
            st.subheader("Facturas Pagadas")
            render_table(facturas_pag, supabase, editable=True)
        else:
            st.info("No hay facturas pagadas.")


if __name__ == "__main__":
    main()
