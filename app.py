import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client

# ======================
# CONFIGURACIÓN SUPABASE
# ======================
SUPABASE_URL = "https://ihncwagxefayefcdngkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlobmN3YWd4ZWZheWVmY2RuZ2t3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDYwNDksImV4cCI6MjA3MjU4MjA0OX0.tzgjBgMJoZdSSw29661PDARz0wfQcdI2bNtZrOqwG54"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==========================
# CONFIG STREAMLIT
# ==========================
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

st.title("📊 Control de Comisiones")

# ==========================
# FORMULARIO DE REGISTRO DE VENTA
# ==========================
with st.form("registro_venta"):
    st.subheader("📝 Registrar nueva venta")
    pedido = st.text_input("Número de Pedido")
    cliente = st.text_input("Cliente")
    factura = st.text_input("Número de Factura")
    valor = st.number_input("Valor de la venta", min_value=0.0, step=1000.0)
    porcentaje = st.number_input("Porcentaje de comisión (%)", min_value=0.0, max_value=100.0, value=5.0)
    comision = valor * (porcentaje / 100)

    fecha_pedido = st.date_input("Fecha del Pedido", value=date.today())
    fecha_factura = st.date_input("Fecha de la Factura", value=date.today())

    condicion_especial = st.checkbox("¿Cliente con condición especial (60 días)?", value=False)

    submitted = st.form_submit_button("Guardar Venta")

    if submitted:
        try:
            # Calcular fechas de pago estimadas según condición
            if condicion_especial:
                fecha_pago = fecha_factura + timedelta(days=60)
                fecha_maxima = fecha_factura + timedelta(days=60)
            else:
                fecha_pago = fecha_factura + timedelta(days=35)
                fecha_maxima = fecha_factura + timedelta(days=45)

            # Insertar en Supabase
            resp = supabase.table("comisiones").insert({
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
                "condicion_especial": condicion_especial
            }).execute()

            st.success("✅ Venta registrada con éxito")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

# ==========================
# TABLA DE VENTAS
# ==========================
st.subheader("📋 Ventas registradas")

try:
    data = supabase.table("comisiones").select("*").execute()
    if data.data:
        df = pd.DataFrame(data.data)
        df["valor"] = df["valor"].astype(float)
        df["comision"] = df["comision"].astype(float)

        st.dataframe(df, use_container_width=True)

        # ==========================
        # ALERTAS DE VENCIMIENTO
        # ==========================
        hoy = date.today()
        df["fecha_maxima"] = pd.to_datetime(df["fecha_maxima"]).dt.date
        proximos_vencimientos = df[(df["pagado"] == False) & (df["fecha_maxima"] <= hoy + timedelta(days=5))]

        if not proximos_vencimientos.empty:
            st.warning("⚠️ Facturas próximas a vencerse en los próximos 5 días:")
            st.dataframe(proximos_vencimientos[["cliente", "factura", "fecha_maxima"]])

        # ==========================
        # RANKING DE CLIENTES
        # ==========================
        st.subheader("🏆 Ranking de Clientes por Compras")
        ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
        st.bar_chart(ranking.set_index("cliente"))

    else:
        st.info("No hay ventas registradas aún.")

except Exception as e:
    st.error(f"❌ Error al cargar los datos: {e}")
