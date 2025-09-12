import streamlit as st
import pandas as pd
from datetime import datetime

# ========================
# Imports seguros
# ========================
try:
    from queries import (
        get_all_comisiones,
        insert_comision,
        update_comision
    )
    from utils import calcular_comision, calcular_dias_pago
except ImportError as e:
    st.error(f"❌ Error al importar módulos: {e}")
    st.stop()
except Exception as e:
    st.error(f"⚠️ Ocurrió un error inesperado al cargar módulos: {e}")
    st.stop()

# ========================
# Configuración inicial
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")

# ========================
# Funciones auxiliares
# ========================
def mostrar_tabla(df, titulo, tipo):
    """Muestra tabla de facturas con botón de edición por fila."""
    st.subheader(titulo)

    if df.empty:
        st.info("No hay facturas registradas.")
        return

    for i, row in df.iterrows():
        with st.container():
            cols = st.columns([2, 2, 2, 2, 2, 1])
            cols[0].write(f"📌 Pedido: {row['pedido']}")
            cols[1].write(f"Cliente: {row['cliente']}")
            cols[2].write(f"Factura: {row['factura']}")
            cols[3].write(f"Valor: ${row['valor']:,}")
            cols[4].write(f"Comisión: ${row['comision']:,}")
            edit_btn = cols[5].button("✏️ Editar", key=f"edit_{tipo}_{row['id']}")

            if edit_btn:
                with st.form(f"edit_form_{tipo}_{row['id']}"):
                    nuevo_valor = st.number_input(
                        "Valor factura", min_value=0.0, value=float(row["valor"])
                    )
                    nuevo_porcentaje = st.number_input(
                        "Porcentaje comisión", min_value=0.0, value=float(row["porcentaje"])
                    )
                    pagado = st.checkbox("Pagado", value=row["pagado"])
                    fecha_pago = st.date_input(
                        "Fecha de pago",
                        value=row["fecha_pago"] if row["fecha_pago"] else datetime.today().date()
                    )

                    submitted = st.form_submit_button("Guardar cambios")
                    if submitted:
                        dias_pago = calcular_dias_pago(row["fecha_factura"], fecha_pago)
                        nueva_comision = calcular_comision(
                            nuevo_valor,
                            nuevo_porcentaje,
                            row["tiene_descuento_factura"],
                            dias_pago
                        )

                        update_comision(
                            row["id"],
                            {
                                "valor": nuevo_valor,
                                "porcentaje": nuevo_porcentaje,
                                "pagado": pagado,
                                "fecha_pago": fecha_pago.isoformat(),
                                "comision": nueva_comision,
                            },
                        )
                        st.success("✅ Factura actualizada correctamente")
                        st.experimental_rerun()

# ========================
# Secciones de la App
# ========================
def dashboard():
    st.subheader("📊 Dashboard de Comisiones")

    data = get_all_comisiones()
    if not data:
        st.info("No hay registros aún.")
        return

    df = pd.DataFrame(data)

    # Filtro por mes
    df["mes"] = pd.to_datetime(df["fecha_factura"]).dt.to_period("M")
    meses = df["mes"].unique().astype(str).tolist()
    mes_sel = st.selectbox("Selecciona un mes", meses)
    df_mes = df[df["mes"].astype(str) == mes_sel]

    # KPIs
    total_ventas = df_mes["valor"].sum()
    total_comision = df_mes["comision"].sum()
    facturas_pend = df_mes[~df_mes["pagado"]].shape[0]
    facturas_pag = df_mes[df_mes["pagado"]].shape[0]

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("💵 Total Ventas", f"${total_ventas:,.0f}")
    kpi2.metric("🎯 Total Comisión", f"${total_comision:,.0f}")
    kpi3.metric("📌 Pendientes", facturas_pend)
    kpi4.metric("✅ Pagadas", facturas_pag)

    # Ranking clientes
    st.markdown("### 🏆 Ranking Clientes")
    ranking = df_mes.groupby("cliente")["comision"].sum().reset_index()
    ranking = ranking.sort_values("comision", ascending=False)
    st.table(ranking)

def registrar_venta():
    st.subheader("📝 Registrar Venta")
    with st.form("nueva_venta"):
        pedido = st.text_input("Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Factura")
        valor = st.number_input("Valor base", min_value=0.0, step=100.0)
        porcentaje = st.number_input("Porcentaje comisión", min_value=0.0, step=0.5)
        tiene_desc = st.checkbox("¿Tiene descuento a pie de factura?")
        fecha_factura = st.date_input("Fecha factura", value=datetime.today().date())

        submitted = st.form_submit_button("Registrar")
        if submitted:
            comision = calcular_comision(valor, porcentaje, tiene_desc, dias_pago=None)
            insert_comision(
                pedido, cliente, factura, valor, porcentaje,
                comision, fecha_factura, tiene_desc
            )
            st.success("✅ Venta registrada correctamente")
            st.experimental_rerun()

def facturas_pendientes():
    data = get_all_comisiones()
    if not data:
        st.info("No hay registros.")
        return
    df = pd.DataFrame(data)
    df_pend = df[~df["pagado"]]
    mostrar_tabla(df_pend, "📌 Facturas Pendientes", "pendientes")

def facturas_pagadas():
    data = get_all_comisiones()
    if not data:
        st.info("No hay registros.")
        return
    df = pd.DataFrame(data)
    df_pag = df[df["pagado"]]
    mostrar_tabla(df_pag, "✅ Facturas Pagadas", "pagadas")

# ========================
# Main
# ========================
def main():
    st.title("📊 Sistema de Comisiones")

    menu = ["Dashboard", "Registrar Venta", "Facturas Pendientes", "Facturas Pagadas"]
    choice = st.sidebar.selectbox("Navegación", menu)

    if choice == "Dashboard":
        dashboard()
    elif choice == "Registrar Venta":
        registrar_venta()
    elif choice == "Facturas Pendientes":
        facturas_pendientes()
    elif choice == "Facturas Pagadas":
        facturas_pagadas()


if __name__ == "__main__":
    main()
