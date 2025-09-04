import os
import streamlit as st
import pandas as pd
from datetime import date, datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# ==============================
# CONFIGURACIÓN INICIAL
# ==============================
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gestión de Comisiones", layout="wide")

# ==============================
# FUNCIÓN PARA SUBIR COMPROBANTE
# ==============================
def subir_comprobante(file, nombre_archivo):
    try:
        supabase.storage.from_(BUCKET).upload(nombre_archivo, file.getbuffer(), {"upsert": True})
        return True
    except Exception as e:
        st.error(f"❌ Error al subir comprobante: {e}")
        return False

def obtener_url_firmada(nombre_archivo, segundos=300):
    try:
        url = supabase.storage.from_(BUCKET).create_signed_url(nombre_archivo, segundos)
        return url
    except Exception:
        return None

# ==============================
# CARGAR DATOS
# ==============================
res = supabase.table("comisiones").select("*").execute()
df = pd.DataFrame(res.data)

# Normalizar columna de valor
if "valor_factura" not in df.columns and "valor" in df.columns:
    df.rename(columns={"valor": "valor_factura"}, inplace=True)
if "valor_factura" not in df.columns:
    df["valor_factura"] = 0.0
df["valor_factura"] = df["valor_factura"].astype(float)

# Convertir fechas
for col in ["fecha_pedido", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# ==============================
# UI PRINCIPAL
# ==============================
st.title("📊 Gestión de Comisiones y Facturas")

tabs = st.tabs(["➕ Registrar Venta", "📋 Facturas", "📈 Dashboard", "⚠️ Alertas"])

# ==============================
# TAB 1: REGISTRAR VENTA
# ==============================
with tabs[0]:
    st.header("➕ Registrar Venta")
    with st.form("nueva_venta"):
        pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        valor = st.number_input("Valor factura", min_value=0.0)
        comision = st.number_input("Porcentaje comisión", min_value=0.0, max_value=1.0, value=0.1)
        condicion_especial = st.checkbox("¿Cliente con condición especial (60 días)?", value=False)

        fecha_pedido = st.date_input("Fecha del pedido", date.today())
        fecha_factura = st.date_input("Fecha de factura", date.today())

        if condicion_especial:
            fecha_pago_est = fecha_factura + timedelta(days=60)
            fecha_pago_max = fecha_factura + timedelta(days=60)
        else:
            fecha_pago_est = fecha_factura + timedelta(days=35)
            fecha_pago_max = fecha_factura + timedelta(days=45)

        st.write(f"📅 Fecha estimada de pago: {fecha_pago_est}")
        st.write(f"📅 Fecha máxima de pago: {fecha_pago_max}")

        submitted = st.form_submit_button("Guardar")

        if submitted:
            comision_valor = valor * comision
            data = {
                "pedido": pedido,
                "cliente": cliente,
                "valor_factura": valor,
                "comision": comision,
                "valor_comision": comision_valor,
                "condicion_especial": condicion_especial,
                "fecha_pedido": str(fecha_pedido),
                "fecha_factura": str(fecha_factura),
                "fecha_pago_est": str(fecha_pago_est),
                "fecha_pago_max": str(fecha_pago_max),
                "pagado": False,
            }
            try:
                supabase.table("comisiones").insert(data).execute()
                st.success("✅ Venta registrada correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar la venta: {e}")

# ==============================
# TAB 2: FACTURAS
# ==============================
with tabs[1]:
    st.header("📋 Facturas registradas")

    if df.empty:
        st.info("No hay facturas registradas aún.")
    else:
        for _, row in df.iterrows():
            with st.container():
                st.subheader(f"📌 Pedido #{row['pedido']} - {row['cliente']}")
                st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                st.write(f"💰 Comisión: ${row['valor_comision']:,.2f}")
                st.write(f"📅 Factura emitida: {row['fecha_factura'].date() if pd.notna(row['fecha_factura']) else 'N/A'}")
                st.write(f"📅 Pago estimado: {row['fecha_pago_est'].date() if pd.notna(row['fecha_pago_est']) else 'N/A'}")
                st.write(f"📅 Pago máximo: {row['fecha_pago_max'].date() if pd.notna(row['fecha_pago_max']) else 'N/A'}")
                st.write(f"✅ Pagado: {'Sí' if row.get('pagado', False) else 'No'}")

                if not row.get("pagado", False):
                    if st.button(f"Registrar pago #{row['id']}", key=f"pago_{row['id']}"):
                        supabase.table("comisiones").update({"pagado": True, "fecha_pago_real": str(date.today())}).eq("id", row["id"]).execute()
                        st.success("✅ Pago registrado")
                        st.rerun()

                comp = st.file_uploader(f"📎 Subir comprobante #{row['id']}", type=["pdf", "jpg", "png"], key=f"comp_{row['id']}")
                if comp:
                    nombre_archivo = f"comprobante_{row['id']}_{comp.name}"
                    if subir_comprobante(comp, nombre_archivo):
                        supabase.table("comisiones").update({"comprobante_url": nombre_archivo}).eq("id", row["id"]).execute()
                        st.success("📎 Comprobante subido")
                        st.rerun()

                if row.get("comprobante_url"):
                    url = obtener_url_firmada(row["comprobante_url"])
                    if url:
                        st.markdown(f"[🔗 Ver comprobante]({url})", unsafe_allow_html=True)

                st.markdown("---")

# ==============================
# TAB 3: DASHBOARD
# ==============================
with tabs[2]:
    st.header("📈 Dashboard")

    total_facturado = df["valor_factura"].sum()
    total_comisiones = df["valor_comision"].sum()
    st.metric("💵 Total facturado", f"${total_facturado:,.2f}")
    st.metric("💰 Total comisiones", f"${total_comisiones:,.2f}")

    st.subheader("🏆 Ranking de clientes")
    ranking = df.groupby("cliente")["valor_factura"].sum().sort_values(ascending=False)
    max_val = ranking.max() if not ranking.empty else 1

    for cliente, valor in ranking.items():
        pct = (valor / max_val) * 100
        st.markdown(f"""
        <div style="margin-bottom:10px;">
            <b>{cliente}</b> - ${valor:,.2f}
            <div style='background:#eee; border-radius:8px; height:18px;'>
                <div style='width:{pct}%; background:#3498db; height:18px; border-radius:8px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ==============================
# TAB 4: ALERTAS
# ==============================
with tabs[3]:
    st.header("⚠️ Facturas por vencer")

    hoy = date.today()
    if "fecha_pago_max" in df.columns:
        df["fecha_pago_max"] = pd.to_datetime(df["fecha_pago_max"], errors="coerce")

        vencimientos = df[
            (df["pagado"] == False) &
            (df["fecha_pago_max"].notna()) &
            (df["fecha_pago_max"].dt.date <= hoy + timedelta(days=5))
        ]

        if vencimientos.empty:
            st.info("✅ No hay facturas próximas a vencer.")
        else:
            for _, row in vencimientos.iterrows():
                st.error(f"⚠️ Factura de {row['cliente']} (Pedido {row['pedido']}) vence el {row['fecha_pago_max'].date()}")
