import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from queries import (
    get_all_facturas,
    insertar_factura,
    update_factura,
    marcar_factura_pagada,
)
from utils import upload_comprobante, safe_get_public_url

# ==============================================
# Helpers
# ==============================================
def formatear_mes(dt: pd.Timestamp) -> str:
    return dt.strftime("%B %Y").capitalize()

def parse_mes(mes_str: str) -> datetime:
    return datetime.strptime(mes_str, "%B %Y")

# ==============================================
# Registrar Factura
# ==============================================
def registrar_factura():
    st.header("📝 Registrar Factura")
    with st.form("form_registrar"):
        numero = st.text_input("Número de factura")
        cliente = st.text_input("Cliente")
        valor_neto = st.number_input("Valor neto (sin IVA, menos descuentos)", min_value=0.0)
        fecha_factura = st.date_input("Fecha de factura")
        tiene_descuento = st.selectbox("¿Tiene descuento a pie de factura?", ["Sí", "No"])
        submitted = st.form_submit_button("Registrar")

        if submitted:
            insertar_factura(
                numero,
                cliente,
                valor_neto,
                fecha_factura,
                tiene_descuento == "Sí"
            )
            st.success("✅ Factura registrada correctamente")

# ==============================================
# Mostrar Facturas (pendientes / pagadas)
# ==============================================
def mostrar_facturas(df, estado):
    st.header(f"📂 Facturas {estado.capitalize()}")
    df_estado = df[df["estado"] == estado]

    if df_estado.empty:
        st.info("No hay facturas en este estado.")
        return

    for _, row in df_estado.iterrows():
        with st.expander(f"Factura #{row['numero']} - Cliente: {row['cliente']}"):
            st.write(f"**Fecha:** {row['fecha_factura']}")
            st.write(f"**Valor Neto:** {row['valor_neto']:,}")
            st.write(f"**Estado:** {row['estado']}")
            if row.get("comprobante_url"):
                st.markdown(f"[📎 Ver comprobante]({row['comprobante_url']})")

            if st.button(f"✏️ Editar {row['numero']}", key=f"edit_{row['id']}"):
                with st.form(f"form_edit_{row['id']}"):
                    cliente = st.text_input("Cliente", value=row["cliente"])
                    valor_neto = st.number_input("Valor neto", value=row["valor_neto"])
                    fecha_factura = st.date_input("Fecha de factura", value=pd.to_datetime(row["fecha_factura"]))
                    tiene_descuento = st.selectbox(
                        "¿Tiene descuento a pie de factura?",
                        ["Sí", "No"],
                        index=0 if row.get("tiene_descuento", False) else 1
                    )
                    file = st.file_uploader("Subir comprobante", type=["jpg", "png", "pdf"])

                    submitted = st.form_submit_button("Guardar cambios")
                    if submitted:
                        comprobante_url = row.get("comprobante_url")
                        if file:
                            comprobante_url = upload_comprobante(file, row["numero"])

                        update_factura(
                            row["id"],
                            cliente,
                            valor_neto,
                            fecha_factura,
                            tiene_descuento == "Sí",
                            comprobante_url
                        )
                        st.success("✅ Factura actualizada")

                    if estado == "pendiente":
                        if st.form_submit_button("Marcar como pagada"):
                            marcar_factura_pagada(row["id"])
                            st.success("✅ Factura marcada como pagada")

# ==============================================
# Dashboard
# ==============================================
def mostrar_dashboard(df):
    st.header("📊 Dashboard de Ventas y Comisiones")

    if df.empty:
        st.info("No hay facturas registradas aún.")
        return

    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"])
    df["mes"] = df["fecha_factura"].dt.to_period("M").dt.to_timestamp()

    # Selector de mes
    meses_disponibles = sorted(df["mes"].unique())
    meses_labels = [formatear_mes(m) for m in meses_disponibles]
    mes_sel = st.selectbox("Seleccionar mes", meses_labels)
    mes_dt = parse_mes(mes_sel)

    # Filtrar acumulado hasta el mes
    df_filtrado = df[df["mes"] <= mes_dt]

    # ===== Métricas
    total_ventas = df_filtrado["valor_neto"].sum()
    total_comisiones = df_filtrado["comision"].sum()
    pendientes = (df_filtrado["estado"] == "pendiente").sum()
    pagadas = (df_filtrado["estado"] == "pagada").sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💰 Total Ventas Netas", f"${total_ventas:,.0f}")
    col2.metric("📈 Total Comisiones", f"${total_comisiones:,.0f}")
    col3.metric("🟡 Pendientes", pendientes)
    col4.metric("🟢 Pagadas", pagadas)

    # ===== Ranking clientes (barras horizontales)
    ranking = df_filtrado.groupby("cliente")["valor_neto"].sum().reset_index()
    ranking = ranking.sort_values("valor_neto", ascending=True)

    fig_rank = px.bar(
        ranking,
        x="valor_neto",
        y="cliente",
        orientation="h",
        labels={"valor_neto": "Ventas Netas", "cliente": "Cliente"},
        title=f"🏆 Ranking de Clientes acumulado hasta {mes_sel}",
    )
    st.plotly_chart(fig_rank, use_container_width=True)

    # ===== Evolución de comisiones
    evolucion = df_filtrado.groupby("mes")["comision"].sum().reset_index()
    fig_line = px.line(
        evolucion,
        x="mes",
        y="comision",
        markers=True,
        labels={"mes": "Mes", "comision": "Comisión"},
        title="📈 Evolución de Comisiones"
    )
    st.plotly_chart(fig_line, use_container_width=True)

# ==============================================
# Alertas
# ==============================================
def mostrar_alertas(df):
    st.header("⚠️ Alertas")
    hoy = datetime.now().date()
    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"]).dt.date
    vencidas = df[(df["estado"] == "pendiente") & (df["fecha_factura"] < hoy)]

    if vencidas.empty:
        st.success("✅ No hay facturas vencidas.")
        return

    for _, row in vencidas.iterrows():
        st.error(f"Factura #{row['numero']} del cliente {row['cliente']} vencida desde {row['fecha_factura']}")

# ==============================================
# Main
# ==============================================
def main():
    st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
    st.sidebar.title("Menú")
    menu = st.sidebar.radio("Ir a:", ["Registrar Factura", "Facturas Pendientes", "Facturas Pagadas", "Dashboard", "Alertas"])

    df = get_all_facturas()
    if not df.empty:
        if "fecha_factura" not in df.columns:
            st.error("⚠️ No se encontró la columna 'fecha_factura' en la tabla de Supabase.")
            return

    if menu == "Registrar Factura":
        registrar_factura()
    elif menu == "Facturas Pendientes":
        mostrar_facturas(df, "pendiente")
    elif menu == "Facturas Pagadas":
        mostrar_facturas(df, "pagada")
    elif menu == "Dashboard":
        mostrar_dashboard(df)
    elif menu == "Alertas":
        mostrar_alertas(df)

if __name__ == "__main__":
    main()
