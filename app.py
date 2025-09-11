import os
from datetime import datetime, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# ========================
# Configuración de entorno
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Helpers de cálculos
# ========================
def calcular_valor_y_comisiones_row(valor, valor_base, tipo_cliente, fecha_factura, fecha_pago_real):
    """Calcula el valor_base y la comisión con base en las reglas de negocio."""
    descuento = 0.15  # 15%
    valor_base_calc = valor * (1 - descuento)

    # Si no hay fecha de pago real aún → no calcular días ni penalización
    dias = None
    penalizacion = 0
    if fecha_pago_real and fecha_factura:
        try:
            dias = (fecha_pago_real - fecha_factura).days
        except Exception:
            dias = None

    # Comisión base
    if tipo_cliente == "propio":
        comision = valor_base_calc * 0.12
    else:
        comision = valor_base_calc * 0.08

    # Penalización por pago tardío
    if dias is not None and dias > 30:
        comision *= 0.9  # -10%

    return {
        "valor_base": valor_base_calc,
        "comision": comision,
        "dias": dias
    }

# ========================
# Vistas de la aplicación
# ========================
def registrar_venta():
    st.subheader("📝 Registrar Nueva Venta")

    with st.form("registro_form"):
        pedido = st.text_input("Pedido")
        factura = st.text_input("Factura")
        cliente = st.text_input("Cliente")
        valor = st.number_input("Valor", min_value=0, step=1000)
        tipo_cliente = st.selectbox("Tipo Cliente", ["propio", "no_propio"])
        fecha_factura = st.date_input("Fecha Factura", value=date.today())
        submitted = st.form_submit_button("Registrar")

        if submitted:
            if not pedido or not factura or not cliente or valor <= 0:
                st.error("⚠️ Todos los campos son obligatorios")
                return

            calc = calcular_valor_y_comisiones_row(
                valor=valor,
                valor_base=None,
                tipo_cliente=tipo_cliente,
                fecha_factura=fecha_factura,
                fecha_pago_real=None
            )

            data = {
                "pedido": pedido,
                "factura": factura,
                "cliente": cliente,
                "valor": valor,
                "valor_base": calc["valor_base"],
                "tipo_cliente": tipo_cliente,
                "fecha_factura": str(fecha_factura),
                "comision": calc["comision"],
                "pagado": False
            }

            supabase.table("comisiones").insert(data).execute()
            st.success("✅ Venta registrada correctamente")


def listar_y_editar(pagadas=False):
    st.subheader("📋 Facturas Pagadas" if pagadas else "📋 Facturas Pendientes")

    query = supabase.table("comisiones").select("*").eq("pagado", pagadas).execute()
    rows = query.data if query.data else []

    if not rows:
        st.info("No hay registros para mostrar.")
        return

    for row in rows:
        with st.expander(f"Factura {row['factura']} - Cliente: {row['cliente']}"):
            with st.form(f"edit_{row['id']}"):
                valor = st.number_input("Valor", min_value=0, value=row.get("valor", 0), step=1000)
                tipo_cliente = st.selectbox("Tipo Cliente", ["propio", "no_propio"], index=0 if row.get("tipo_cliente") == "propio" else 1)
                fecha_factura = st.date_input("Fecha Factura", value=pd.to_datetime(row.get("fecha_factura")).date())
                fecha_pago_real = st.date_input("Fecha Pago Real", value=pd.to_datetime(row["fecha_pago_real"]).date() if row.get("fecha_pago_real") else date.today())
                pagado_check = st.checkbox("Pagado", value=row.get("pagado", False))

                submitted = st.form_submit_button("💾 Guardar cambios")

                if submitted:
                    calc = calcular_valor_y_comisiones_row(
                        valor=valor,
                        valor_base=row.get("valor_base", 0),
                        tipo_cliente=tipo_cliente,
                        fecha_factura=fecha_factura,
                        fecha_pago_real=fecha_pago_real if pagado_check else None
                    )

                    update_data = {
                        "valor": valor,
                        "valor_base": calc["valor_base"],
                        "tipo_cliente": tipo_cliente,
                        "fecha_factura": str(fecha_factura),
                        "fecha_pago_real": str(fecha_pago_real) if pagado_check else None,
                        "pagado": pagado_check,
                        "comision": calc["comision"],
                    }

                    supabase.table("comisiones").update(update_data).eq("id", row["id"]).execute()
                    st.success("✅ Registro actualizado")


def dashboard():
    st.subheader("📊 Dashboard de Comisiones")

    query = supabase.table("comisiones").select("*").execute()
    rows = query.data if query.data else []
    if not rows:
        st.info("No hay datos para mostrar en el dashboard.")
        return

    df = pd.DataFrame(rows)
    df["fecha_factura"] = pd.to_datetime(df["fecha_factura"])
    df["mes"] = df["fecha_factura"].dt.to_period("M")

    resumen = df.groupby("mes").agg({
        "valor": "sum",
        "valor_base": "sum",
        "comision": "sum"
    }).reset_index()

    st.dataframe(resumen)

    st.bar_chart(resumen.set_index("mes")[["valor", "valor_base", "comision"]])

# ========================
# App principal
# ========================
def main():
    st.title("📂 Gestión de Comisiones")

    menu = st.sidebar.radio("Navegación", ["Registrar Venta", "Pendientes", "Pagadas", "Dashboard"])

    if menu == "Registrar Venta":
        registrar_venta()
    elif menu == "Pendientes":
        listar_y_editar(pagadas=False)
    elif menu == "Pagadas":
        listar_y_editar(pagadas=True)
    elif menu == "Dashboard":
        dashboard()


if __name__ == "__main__":
    main()
