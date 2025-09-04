import os
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# -------------------------
# CARGAR VARIABLES DE ENTORNO
# -------------------------
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# CONFIG STREAMLIT
# -------------------------
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

st.title("📊 Control de Comisiones")

# =========================
# FORMULARIO DE REGISTRO
# =========================
st.header("➕ Registrar nueva venta")

with st.form("registro_venta"):
    pedido = st.text_input("Número de pedido")
    cliente = st.text_input("Cliente")
    factura = st.text_input("Número de factura")
    valor = st.number_input("Valor de la factura", min_value=0.0, step=1000.0)
    porcentaje = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, step=0.1)
    comision = valor * (porcentaje / 100)

    fecha_pedido = st.date_input("Fecha de pedido", value=date.today())
    fecha_factura = st.date_input("Fecha de factura", value=date.today())

    condicion_especial = st.checkbox("¿Condición especial (60 días)?", value=False)

    dias_pago = 60 if condicion_especial else 35
    dias_max = 60 if condicion_especial else 45
    fecha_pago = fecha_factura + timedelta(days=dias_pago)
    fecha_maxima = fecha_factura + timedelta(days=dias_max)

    st.write(f"📅 Fecha estimada de pago: **{fecha_pago}**")
    st.write(f"📅 Fecha máxima de pago: **{fecha_maxima}**")

    submitted = st.form_submit_button("💾 Guardar venta")

    if submitted:
        try:
            data = {
                "pedido": pedido,
                "cliente": cliente,
                "factura": factura,
                "valor": valor,
                "porcentaje": porcentaje,
                "comision": comision,
                "pagado": False,
                "fecha_pedido": str(fecha_pedido),
                "fecha_factura": str(fecha_factura),
                "fecha_pago": str(fecha_pago),
                "fecha_maxima": str(fecha_maxima),
                "condicion_especial": condicion_especial,
            }
            resp = supabase.table("comisiones").insert(data).execute()
            st.success("✅ Venta registrada correctamente")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

# =========================
# CARGAR DATOS
# =========================
resp = supabase.table("comisiones").select("*").execute()
df = pd.DataFrame(resp.data) if resp.data else pd.DataFrame()

if not df.empty:
    # Convertir fechas a datetime
    for col in ["fecha_pedido", "fecha_factura", "fecha_pago", "fecha_maxima", "fecha_pago_real", "fecha_pago_max"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # =========================
    # DASHBOARD
    # =========================
    st.header("📈 Dashboard")

    total_valor = df["valor"].sum()
    total_comision = df["comision"].sum()
    pagadas = df[df["pagado"] == True]["valor"].sum()
    pendientes = df[df["pagado"] == False]["valor"].sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 Total facturado", f"${total_valor:,.2f}")
    col2.metric("💰 Total comisiones", f"${total_comision:,.2f}")
    col3.metric("✅ Pagado", f"${pagadas:,.2f}")
    col4.metric("⌛ Pendiente", f"${pendientes:,.2f}")

    # Ranking de clientes
    ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
    fig = px.bar(ranking, x="cliente", y="valor", title="🏆 Clientes que más compraron", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

    # =========================
    # ALERTAS
    # =========================
    hoy = date.today()
    alertas = df[(df["pagado"] == False) & (df["fecha_maxima"].dt.date <= hoy + timedelta(days=5))]

    st.header("⚠️ Alertas de vencimiento")
    if alertas.empty:
        st.success("✅ No hay facturas próximas a vencer")
    else:
        for _, row in alertas.iterrows():
            st.error(f"⚠️ Factura {row['factura']} del cliente {row['cliente']} vence el {row['fecha_maxima'].date()}")

    # =========================
    # HISTORIAL DE FACTURAS
    # =========================
    st.header("📋 Facturas registradas")

    for _, row in df.sort_values("fecha_factura", ascending=False).iterrows():
        with st.container():
            st.markdown(f"""
            ### 🧾 Factura {row['factura']} - {row['cliente']}
            - 📦 Pedido: **{row['pedido']}**
            - 💵 Valor: ${row['valor']:,.2f}
            - 💰 Comisión: ${row['comision']:,.2f} ({row['porcentaje']}%)
            - 📅 Pedido: {row['fecha_pedido'].date() if pd.notnull(row['fecha_pedido']) else 'N/A'}
            - 📅 Factura: {row['fecha_factura'].date() if pd.notnull(row['fecha_factura']) else 'N/A'}
            - 📅 Est. Pago: {row['fecha_pago'].date() if pd.notnull(row['fecha_pago']) else 'N/A'}
            - 📅 Máx. Pago: {row['fecha_maxima'].date() if pd.notnull(row['fecha_maxima']) else 'N/A'}
            - ✅ Estado: {"Pagada" if row["pagado"] else "Pendiente"}
            """)
            
            # Subir comprobante si está pendiente
            if not row["pagado"]:
                comp_file = st.file_uploader(f"📎 Adjuntar comprobante factura {row['factura']}", type=["pdf", "png", "jpg"], key=f"file_{row['id']}")
                if comp_file:
                    file_bytes = comp_file.read()
                    file_path = f"{row['factura']}/{comp_file.name}"
                    supabase.storage.from_(BUCKET).upload(file_path, file_bytes, {"upsert": True})
                    public_url = supabase.storage.from_(BUCKET).get_public_url(file_path)

                    supabase.table("comisiones").update({
                        "pagado": True,
                        "fecha_pago_real": str(date.today()),
                        "comprobante_url": public_url,
                        "comprobante_file": comp_file.name
                    }).eq("id", row["id"]).execute()
                    st.success("✅ Comprobante cargado y factura marcada como pagada")
                    st.rerun()

            # Mostrar comprobante si existe
            if row.get("comprobante_url"):
                st.markdown(f"[📂 Ver comprobante]({row['comprobante_url']})")

else:
    st.info("Aún no hay ventas registradas.")
