import streamlit as st
import pandas as pd
from queries import (
    get_all_comisiones,
    insert_comision,
    update_comision,
)
from utils import upload_file, safe_get_public_url
import datetime


# ========================
# Función principal
# ========================
def main():
    st.set_page_config(page_title="Gestión de Comisiones", layout="wide")

    menu = ["Dashboard", "Registrar Venta", "Facturas Pendientes", "Facturas Pagadas", "Alertas"]
    choice = st.sidebar.radio("Menú", menu)

    df = get_all_comisiones()

    if df is None or df.empty:
        df = pd.DataFrame()

    if choice == "Dashboard":
        mostrar_dashboard(df)

    elif choice == "Registrar Venta":
        registrar_venta()

    elif choice == "Facturas Pendientes":
        mostrar_facturas(df, estado="pendiente")

    elif choice == "Facturas Pagadas":
        mostrar_facturas(df, estado="pagada")

    elif choice == "Alertas":
        mostrar_alertas(df)


# ========================
# Dashboard
# ========================
def mostrar_dashboard(df: pd.DataFrame):
    st.title("📊 Dashboard")

    if df.empty:
        st.info("No hay facturas registradas.")
        return

    # Conversión de fechas
    if "fecha_factura" in df.columns:
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")

    total_facturas = len(df)
    total_valor = df["valor"].sum() if "valor" in df.columns else 0
    total_pagadas = len(df[df["estado"] == "pagada"]) if "estado" in df.columns else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total facturas", total_facturas)
    col2.metric("Facturas pagadas", total_pagadas)
    col3.metric("Monto total facturado", f"${total_valor:,.0f}")

    # Ranking por cliente
    if "cliente" in df.columns:
        st.subheader("🏆 Ranking por clientes")
        ranking = df.groupby("cliente")["valor"].sum().sort_values(ascending=False)
        st.bar_chart(ranking)


# ========================
# Registro de Venta
# ========================
def registrar_venta():
    st.title("📝 Registrar Venta")

    with st.form("nueva_factura"):
        factura = st.text_input("Número de factura")
        pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        valor = st.number_input("Valor neto (antes de IVA, con descuento si aplica)", min_value=0.0)
        fecha = st.date_input("Fecha de factura", value=datetime.date.today())
        descuento_pie = st.selectbox("¿Tiene descuento a pie de factura?", ["Sí", "No"])
        submitted = st.form_submit_button("Registrar")

        if submitted:
            data = {
                "factura": factura,
                "pedido": pedido,
                "cliente": cliente,
                "valor": valor,
                "fecha_factura": str(fecha),
                "descuento_pie": True if descuento_pie == "Sí" else False,
                "estado": "pendiente",
            }
            insert_comision(data)
            st.success(f"✅ Factura {factura} registrada correctamente.")


# ========================
# Mostrar Facturas (Cards)
# ========================
def mostrar_facturas(df: pd.DataFrame, estado: str):
    st.title(f"📂 Facturas {estado.capitalize()}s")

    if df.empty:
        st.info("No hay facturas registradas.")
        return

    facturas = df[df["estado"] == estado] if "estado" in df.columns else pd.DataFrame()

    if facturas.empty:
        st.info(f"No hay facturas {estado}s.")
        return

    for _, row in facturas.iterrows():
        with st.container():
            st.markdown("---")
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"📑 Factura {row['factura']}")
                st.write(f"**Cliente:** {row['cliente']}")
                st.write(f"**Pedido:** {row['pedido']}")
                st.write(f"**Valor:** ${row['valor']:,.0f}")
                st.write(f"**Fecha:** {row['fecha_factura']}")
            with col2:
                if st.button("✏️ Editar", key=f"edit_{row['id']}"):
                    editar_factura(row)


# ========================
# Editar Factura
# ========================
def editar_factura(factura_row):
    st.subheader(f"Editar factura {factura_row['factura']}")

    with st.form(f"editar_{factura_row['id']}"):
        cliente = st.text_input("Cliente", factura_row["cliente"])
        pedido = st.text_input("Pedido", factura_row["pedido"])
        valor = st.number_input("Valor", value=float(factura_row["valor"]))
        estado = st.selectbox("Estado", ["pendiente", "pagada"], index=0 if factura_row["estado"] == "pendiente" else 1)
        comprobante = st.file_uploader("Subir comprobante de pago", type=["jpg", "png", "pdf"])

        submitted = st.form_submit_button("Guardar cambios")

        if submitted:
            update_data = {
                "cliente": cliente,
                "pedido": pedido,
                "valor": valor,
                "estado": estado,
            }

            if comprobante is not None:
                filename = f"{factura_row['factura']}_{comprobante.name}"
                upload_file(comprobante, filename)
                url = safe_get_public_url(filename)
                update_data["comprobante_url"] = url

            update_comision(factura_row["id"], update_data)
            st.success(f"✅ Factura {factura_row['factura']} actualizada.")


# ========================
# Alertas
# ========================
def mostrar_alertas(df: pd.DataFrame):
    st.title("🚨 Alertas")

    if df.empty:
        st.info("No hay facturas registradas.")
        return

    hoy = datetime.date.today()
    if "fecha_factura" in df.columns:
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce").dt.date
        vencidas = df[(df["estado"] == "pendiente") & (df["fecha_factura"] < hoy)]
    else:
        vencidas = pd.DataFrame()

    if vencidas.empty:
        st.success("✅ No hay facturas vencidas.")
        return

    for _, row in vencidas.iterrows():
        with st.container():
            st.markdown("---")
            st.subheader(f"⚠️ Factura {row['factura']} vencida")
            st.write(f"**Cliente:** {row['cliente']}")
            st.write(f"**Valor:** ${row['valor']:,.0f}")
            st.write(f"**Fecha:** {row['fecha_factura']}")


if __name__ == "__main__":
    main()
