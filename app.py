import os
from datetime import datetime, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# ========================
# Configuración Supabase
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "comprobantes"  # bucket en Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ========================
# Funciones de acceso a datos
# ========================
def get_all_comisiones():
    res = supabase.table("comisiones").select("*").execute()
    return res.data if res.data else []


def insert_comision(factura: str, pedido: str, cliente: str, valor: float,
                    fecha: date, descuento: bool):
    data = {
        "factura": factura,
        "pedido": pedido,
        "cliente": cliente,
        "valor": valor,
        "fecha": str(fecha),
        "tiene_descuento": descuento,
        "pagado": False,
        "comprobante_url": None,
    }
    supabase.table("comisiones").insert(data).execute()


def update_comision(comision_id: int, data_update: dict):
    supabase.table("comisiones").update(data_update).eq("id", comision_id).execute()


# ========================
# Función para subir comprobante
# ========================
def subir_comprobante(factura_numero: str, file) -> str:
    extension = file.name.split(".")[-1]
    filename = f"{factura_numero}_{int(datetime.now().timestamp())}.{extension}"

    res = supabase.storage.from_(BUCKET).upload(filename, file.getbuffer(), {"upsert": True})

    if res is not None:
        url = supabase.storage.from_(BUCKET).get_public_url(filename)
        return url
    else:
        st.error("❌ Error al subir el comprobante")
        return None


# ========================
# Interfaz Streamlit
# ========================
def main():
    st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
    st.title("📊 Gestión de Comisiones")

    menu = ["Dashboard", "Facturas Pendientes", "Facturas Pagadas", "Registrar Venta"]
    choice = st.sidebar.selectbox("Menú", menu)

    comisiones = get_all_comisiones()
    df = pd.DataFrame(comisiones) if comisiones else pd.DataFrame()

    if choice == "Dashboard":
        mostrar_dashboard(df)

    elif choice == "Facturas Pendientes":
        mostrar_facturas(df, pagadas=False)

    elif choice == "Facturas Pagadas":
        mostrar_facturas(df, pagadas=True)

    elif choice == "Registrar Venta":
        registrar_venta()


# ========================
# Dashboard con métricas
# ========================
def mostrar_dashboard(df: pd.DataFrame):
    st.subheader("📌 Resumen General")

    if df.empty:
        st.info("No hay facturas registradas todavía.")
        return

    # Totales
    total_facturado = df["valor"].sum()
    total_pagado = df[df["pagado"] == True]["valor"].sum()
    total_pendiente = df[df["pagado"] == False]["valor"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Facturado", f"${total_facturado:,.0f}")
    col2.metric("✅ Pagado", f"${total_pagado:,.0f}")
    col3.metric("⏳ Pendiente", f"${total_pendiente:,.0f}")

    # Ranking clientes
    st.subheader("🏆 Ranking por cliente")
    ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
    st.dataframe(ranking)

    # Alertas
    st.subheader("⚠️ Alertas")
    df["fecha"] = pd.to_datetime(df["fecha"])
    hoy = pd.to_datetime(date.today())
    df["dias_transcurridos"] = (hoy - df["fecha"]).dt.days

    alertas = df[(df["pagado"] == False) & (df["dias_transcurridos"] > 35)]
    if alertas.empty:
        st.success("✅ No hay facturas vencidas.")
    else:
        st.error("❌ Facturas vencidas:")
        st.dataframe(alertas[["factura", "cliente", "valor", "fecha", "dias_transcurridos"]])


# ========================
# Mostrar facturas
# ========================
def mostrar_facturas(df: pd.DataFrame, pagadas: bool):
    estado = "Pagadas" if pagadas else "Pendientes"
    st.subheader(f"📂 Facturas {estado}")

    if df.empty:
        st.info("No hay facturas registradas todavía.")
        return

    data = df[df["pagado"] == pagadas]
    if data.empty:
        st.info(f"No hay facturas {estado.lower()}.")
        return

    st.dataframe(data)

    factura_id = st.selectbox(f"Selecciona una factura {estado.lower()} para editar", data["id"])
    if factura_id:
        factura = next((c for c in data.to_dict("records") if c["id"] == factura_id), None)
        if factura:
            editar_factura(factura)


# ========================
# Registrar venta
# ========================
def registrar_venta():
    st.subheader("📝 Registrar nueva venta")

    with st.form("form_venta"):
        factura = st.text_input("Número de factura")
        pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        valor = st.number_input("Valor (neto, antes de IVA)", min_value=0.0, format="%.2f")
        fecha = st.date_input("Fecha", value=date.today())
        descuento = st.selectbox("¿Tiene descuento a pie de factura?", ["Sí", "No"])
        submit = st.form_submit_button("Guardar")

    if submit:
        insert_comision(
            factura,
            pedido,
            cliente,
            valor,
            fecha,
            descuento == "Sí"
        )
        st.success("✅ Venta registrada con éxito")


# ========================
# Editar factura
# ========================
def editar_factura(factura):
    st.subheader(f"✏️ Editar factura {factura['factura']}")

    nuevo_valor_factura = st.text_input("Número de factura", factura["factura"])
    nuevo_pedido = st.text_input("Número de pedido", factura["pedido"])
    nuevo_cliente = st.text_input("Cliente", factura["cliente"])
    nuevo_valor = st.number_input("Valor", value=float(factura["valor"]))
    comprobante_file = st.file_uploader("Subir comprobante de pago", type=["jpg", "jpeg", "png", "pdf"])

    if st.button("Guardar cambios"):
        data_update = {
            "factura": nuevo_valor_factura,
            "pedido": nuevo_pedido,
            "cliente": nuevo_cliente,
            "valor": nuevo_valor,
        }

        if comprobante_file:
            comprobante_url = subir_comprobante(nuevo_valor_factura, comprobante_file)
            if comprobante_url:
                data_update["comprobante_url"] = comprobante_url
                data_update["pagado"] = True

        update_comision(factura["id"], data_update)
        st.success("✅ Factura actualizada con éxito")


# ========================
# Run
# ========================
if __name__ == "__main__":
    main()
