import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
import uuid
# ======================
# CONFIGURACIÓN SUPABASE
# ======================
SUPABASE_URL = "https://ihncwagxefayefcdngkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlobmN3YWd4ZWZheWVmY2RuZ2t3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDYwNDksImV4cCI6MjA3MjU4MjA0OX0.tzgjBgMJoZdSSw29661PDARz0wfQcdI2bNtZrOqwG54"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

BUCKET = "comprobantes"  # bucket privado en Supabase Storage

# ==============================
# FORMULARIO DE REGISTRO DE VENTAS
# ==============================
st.title("📑 Registro de Comisiones")

with st.form("registro_venta"):
    pedido = st.number_input("Número de pedido", min_value=1, step=1)
    cliente = st.text_input("Cliente")
    factura = st.number_input("Número de factura", min_value=0, step=1)
    valor = st.number_input("Valor de la venta", min_value=0.0, step=1000.0)
    porcentaje = st.number_input("Porcentaje de comisión (%)", min_value=0.0, max_value=100.0, step=0.1)
    comision = valor * (porcentaje / 100)

    fecha_pedido = st.date_input("Fecha del pedido", value=date.today())
    fecha_factura = st.date_input("Fecha de la factura", value=date.today())

    condicion_especial = st.selectbox("¿Cliente con condición especial?", ["No", "Sí"]) == "Sí"

    # Fechas de pago calculadas
    dias = 60 if condicion_especial else 35
    fecha_pago = fecha_factura + timedelta(days=dias)
    fecha_pago_max = fecha_factura + timedelta(days=45 if not condicion_especial else 60)

    st.write(f"📅 Fecha estimada de pago: {fecha_pago}")
    st.write(f"📅 Fecha máxima de pago: {fecha_pago_max}")

    submitted = st.form_submit_button("Registrar venta")

    if submitted:
        try:
            data = {
                "fecha": fecha_pedido,
                "pedido": pedido,
                "cliente": cliente,
                "factura": factura,
                "valor": valor,
                "porcentaje": porcentaje,
                "comision": comision,
                "condicion_especial": condicion_especial,
                "fecha_pedido": fecha_pedido,
                "fecha_factura": fecha_factura,
                "fecha_pago": fecha_pago,
                "fecha_pago_max": fecha_pago_max,
                "pagado": False
            }
            resp = supabase.table("comisiones").insert(data).execute()
            st.success("✅ Venta registrada con éxito")
        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

# ==============================
# HISTORIAL Y PAGO DE FACTURAS
# ==============================
st.header("📊 Historial de Ventas")

data = supabase.table("comisiones").select("*").execute()
if data.data:
    df = pd.DataFrame(data.data)

    # Mostrar historial
    st.dataframe(df)

    # Ranking clientes
    ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
    st.subheader("🏆 Ranking de Clientes")
    st.table(ranking)

    # Alertas vencimientos
    hoy = date.today()
    if "fecha_pago_max" in df.columns:
        vencimientos = df[(~df["pagado"]) & (pd.to_datetime(df["fecha_pago_max"]) <= pd.to_datetime(hoy + timedelta(days=5)))]
        if not vencimientos.empty:
            st.warning("⚠️ Facturas próximas a vencer en 5 días:")
            st.dataframe(vencimientos)

    # Marcar pago + adjuntar comprobante
    st.subheader("💵 Registrar pago de factura")
    facturas_pend = df[df["pagado"] == False]
    if not facturas_pend.empty:
        factura_sel = st.selectbox("Selecciona factura a marcar como pagada", facturas_pend["factura"].astype(str).tolist())
        comprobante = st.file_uploader("Adjuntar comprobante de pago", type=["pdf", "jpg", "png"])

        if st.button("Confirmar pago ✅"):
            try:
                comprobante_file = None
                if comprobante:
                    # Guardar archivo en Supabase Storage
                    file_id = str(uuid.uuid4()) + "_" + comprobante.name
                    supabase.storage.from_(BUCKET).upload(file_id, comprobante.read())
                    comprobante_file = file_id

                # Actualizar registro
                supabase.table("comisiones").update({
                    "pagado": True,
                    "fecha_pago_real": hoy,
                    "comprobante_file": comprobante_file
                }).eq("factura", int(factura_sel)).execute()

                st.success("✅ Factura marcada como pagada con comprobante")
            except Exception as e:
                st.error(f"❌ Error al actualizar: {e}")

    # Ver comprobantes con link temporal
    st.subheader("📂 Ver comprobantes")
    comprobantes = df.dropna(subset=["comprobante_file"])
    if not comprobantes.empty:
        factura_ver = st.selectbox("Selecciona factura para ver comprobante", comprobantes["factura"].astype(str).tolist())
        if st.button("🔗 Generar link firmado"):
            try:
                comp_file = comprobantes[comprobantes["factura"].astype(str) == factura_ver]["comprobante_file"].values[0]
                signed_url = supabase.storage.from_(BUCKET).create_signed_url(comp_file, 300)  # 300s = 5 min
                st.success(f"Link válido por 5 min: {signed_url['signedURL']}")
            except Exception as e:
                st.error(f"❌ Error al generar link firmado: {e}")
else:
    st.info("No hay ventas registradas aún.")
