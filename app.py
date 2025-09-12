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

# ========================
# Funciones auxiliares
# ========================
def mostrar_dashboard(df):
    st.subheader("📊 Dashboard de Comisiones")

    # Asegurar que fecha_factura sea datetime
    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")

    # Selector de mes y año
    meses = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio",
        7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }
    df["mes"] = df["fecha_factura"].dt.month
    df["año"] = df["fecha_factura"].dt.year

    años_disponibles = sorted(df["año"].dropna().unique(), reverse=True)
    año_sel = st.selectbox("Selecciona el año", años_disponibles)
    meses_disponibles = sorted(df[df["año"] == año_sel]["mes"].dropna().unique())
    mes_sel = st.selectbox("Selecciona el mes", [meses[m] for m in meses_disponibles])

    mes_num = [k for k, v in meses.items() if v == mes_sel][0]
    df_filtrado = df[(df["año"] == año_sel) & (df["mes"] == mes_num)]

    if df_filtrado.empty:
        st.info("No hay datos para este mes.")
        return

    resumen = df_filtrado.groupby("cliente")["valor_venta"].sum().reset_index()

    # Barra horizontal progresiva
    fig = px.bar(
        resumen,
        x="valor_venta",
        y="cliente",
        orientation="h",
        text="valor_venta",
        title=f"Ventas netas - {mes_sel} {año_sel}",
    )
    fig.update_traces(texttemplate="%{text:.2s}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True)


def mostrar_facturas(df):
    st.subheader("📑 Facturas Pendientes")
    pendientes = df[df["comprobante_url"].isna()]

    if pendientes.empty:
        st.success("✅ No hay facturas pendientes")
    else:
        for _, row in pendientes.iterrows():
            with st.expander(f"Factura #{row['factura']} - Cliente: {row['cliente']}"):
                st.write(f"**Fecha:** {row['fecha_factura']}")
                st.write(f"**Valor Venta:** {row['valor_venta']}")
                st.write(f"**Comisión:** {row['comision']}")

                with st.form(f"form_pendiente_{row['id']}"):
                    nuevo_valor = st.number_input("Editar valor de venta", value=row['valor_venta'])
                    nuevo_cliente = st.text_input("Editar cliente", value=row['cliente'])
                    archivo = st.file_uploader("Subir comprobante", type=["jpg", "png", "pdf"], key=f"file_{row['id']}")
                    guardar = st.form_submit_button("Guardar cambios")

                    if guardar:
                        url = row["comprobante_url"]
                        if archivo:
                            url = upload_comprobante(archivo, row["factura"])
                        update_comision(row["id"], nuevo_valor, nuevo_cliente, url)
                        st.success("Factura actualizada correctamente")
                        st.rerun()

    st.subheader("💰 Facturas Pagadas")
    pagadas = df[df["comprobante_url"].notna()]

    if pagadas.empty:
        st.info("No hay facturas pagadas")
    else:
        for _, row in pagadas.iterrows():
            with st.expander(f"Factura #{row['factura']} - Cliente: {row['cliente']} ✅"):
                st.write(f"**Fecha:** {row['fecha_factura']}")
                st.write(f"**Valor Venta:** {row['valor_venta']}")
                st.write(f"**Comisión:** {row['comision']}")
                if row["comprobante_url"]:
                    st.markdown(f"[📎 Ver comprobante]({row['comprobante_url']})")


def mostrar_alertas(df):
    st.subheader("⚠️ Alertas")

    hoy = date.today()
    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce")

    # Facturas vencidas = pendientes sin comprobante y con fecha pasada
    vencidas = df[df["comprobante_url"].isna() & (df["fecha_factura"].dt.date < hoy)]

    if vencidas.empty:
        st.success("✅ No hay facturas vencidas")
    else:
        st.error("⚠️ Facturas vencidas:")
        for _, row in vencidas.iterrows():
            st.write(f"- Factura #{row['factura']} de {row['cliente']} (Fecha: {row['fecha_factura'].date()})")


def main():
    st.title("📌 Gestión de Comisiones y Facturas")

    menu = ["Dashboard", "Facturas", "Alertas"]
    choice = st.sidebar.radio("Menú", menu)

    df = get_all_comisiones()

    if not df.empty:
        if choice == "Dashboard":
            mostrar_dashboard(df)
        elif choice == "Facturas":
            mostrar_facturas(df)
        elif choice == "Alertas":
            mostrar_alertas(df)
    else:
        st.warning("No hay datos cargados aún.")


if __name__ == "__main__":
    main()
