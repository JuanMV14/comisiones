import os
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# ========================
# Configuración inicial
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Funciones auxiliares
# ========================
def cargar_datos():
    try:
        data = supabase.table("comisiones").select("*").execute()
        if not data.data:
            return pd.DataFrame()
        df = pd.DataFrame(data.data)

        # Normalizar columnas
        if "valor" in df.columns and "valor_factura" not in df.columns:
            df.rename(columns={"valor": "valor_factura"}, inplace=True)
        if "comision" in df.columns and "valor_comision" not in df.columns:
            df.rename(columns={"comision": "valor_comision"}, inplace=True)

        # Convertir fechas
        for col in ["fecha", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Columna auxiliar de mes
        if "fecha_factura" in df.columns:
            df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)

        # Asegurar columna pagado
        if "pagado" not in df.columns:
            df["pagado"] = False

        return df
    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        return pd.DataFrame()

def subir_comprobante(file, pedido_id):
    """Sube comprobante al bucket y actualiza registro"""
    try:
        file_name = f"{pedido_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.name}"
        file_path = f"{pedido_id}/{file_name}"

        supabase.storage.from_(BUCKET).upload(file_path, file.getvalue())
        url = supabase.storage.from_(BUCKET).get_public_url(file_path)

        supabase.table("comisiones").update({
            "pagado": True,
            "fecha_pago_real": datetime.now().isoformat(),
            "comprobante_url": url
        }).eq("id", pedido_id).execute()

        return url
    except Exception as e:
        st.error(f"❌ Error subiendo comprobante: {e}")
        return None

# ========================
# Layout principal
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")

df = cargar_datos()

# Filtro global de mes
if not df.empty:
    if "mes_filtrado" not in st.session_state:
        st.session_state["mes_filtrado"] = "Todos"

    meses = ["Todos"] + sorted(df["mes_factura"].dropna().unique())
    st.session_state["mes_filtrado"] = st.selectbox(
        "📅 Seleccionar mes (Fecha Factura)",
        meses,
        index=meses.index(st.session_state["mes_filtrado"]) if st.session_state["mes_filtrado"] in meses else 0
    )

    if st.session_state["mes_filtrado"] != "Todos":
        df = df[df["mes_factura"] == st.session_state["mes_filtrado"]]

# ========================
# Tabs
# ========================
tabs = st.tabs([
    "➕ Registrar Venta",
    "📂 Facturas Pendientes",
    "✅ Facturas Pagadas",
    "📈 Dashboard",
    "⚠️ Alertas",
    "✏️ Editar Facturas"
])

# ========================
# TAB 1 - Registrar Venta
# ========================
with tabs[0]:
    st.header("➕ Registrar nueva venta")

    with st.form("form_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        referencia = st.text_input("Referencia")
        valor_factura = st.number_input("Valor Factura", min_value=0.0, step=1000.0)
        comision = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, step=0.5)
        fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        condicion_especial = st.selectbox("Condición Especial?", ["No", "Sí"])
        submit = st.form_submit_button("💾 Registrar")

    if submit:
        try:
            valor_comision = valor_factura * (comision / 100)
            dias_pago = 60 if condicion_especial == "Sí" else 35
            dias_max = 60 if condicion_especial == "Sí" else 45

            fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
            fecha_pago_max = fecha_factura + timedelta(days=dias_max)

            data = {
                "pedido": pedido,
                "cliente": cliente,
                "referencia": referencia,
                "valor_factura": valor_factura,
                "valor_comision": valor_comision,
                "fecha": datetime.now().isoformat(),
                "fecha_factura": fecha_factura.isoformat(),
                "fecha_pago_est": fecha_pago_est.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "condicion_especial": (condicion_especial == "Sí"),
                "pagado": False,
            }
            supabase.table("comisiones").insert(data).execute()
            st.success("✅ Venta registrada correctamente")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

# ========================
# TAB 2 - Facturas Pendientes
# ========================
with tabs[1]:
    st.header("📂 Facturas Pendientes")
    df_pendientes = df[df["pagado"] == False]
    if df_pendientes.empty:
        st.success("✅ No hay facturas pendientes")
    else:
        for _, row in df_pendientes.iterrows():
            with st.expander(f"📌 Pedido {row['pedido']} - {row['cliente']} (${row['valor_factura']:,.0f})"):
                st.write(f"**Referencia:** {row['referencia']}")
                st.write(f"**Fecha Factura:** {row['fecha_factura'].date()}")
                st.write(f"**Fecha Máxima de Pago:** {row['fecha_pago_max'].date() if pd.notna(row['fecha_pago_max']) else 'N/A'}")
                st.write(f"**Comisión:** ${row['valor_comision']:,.0f}")

                file = st.file_uploader("📤 Subir comprobante de pago", type=["pdf", "jpg", "png"], key=f"upload_{row['id']}")
                if file and st.button("✅ Confirmar pago", key=f"btn_{row['id']}"):
                    url = subir_comprobante(file, row["id"])
                    if url:
                        st.success(f"💾 Pago registrado. Comprobante: {url}")
                        st.rerun()

# ========================
# TAB 3 - Facturas Pagadas
# ========================
with tabs[2]:
    st.header("✅ Facturas Pagadas")
    df_pagadas = df[df["pagado"] == True]
    if df_pagadas.empty:
        st.info("No hay facturas pagadas todavía.")
    else:
        for _, row in df_pagadas.iterrows():
            with st.expander(f"💰 Pedido {row['pedido']} - {row['cliente']} (${row['valor_factura']:,.0f})"):
                st.write(f"**Referencia:** {row['referencia']}")
                st.write(f"**Fecha Factura:** {row['fecha_factura'].date()}")
                st.write(f"**Fecha Pago Real:** {row['fecha_pago_real'].date() if pd.notna(row['fecha_pago_real']) else 'N/A'}")
                st.write(f"**Comisión:** ${row['valor_comision']:,.0f}")
                if "comprobante_url" in row and row["comprobante_url"]:
                    st.markdown(f"[📎 Ver comprobante]({row['comprobante_url']})")
                else:
                    st.warning("⚠️ No hay comprobante registrado.")

# ========================
# TAB 4 - Dashboard
# ========================
with tabs[3]:
    st.header("📈 Dashboard de Comisiones")
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        total_facturado = df["valor_factura"].sum()
        total_comisiones = df["valor_comision"].sum()
        total_pagado = df[df["pagado"]]["valor_factura"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

# ========================
# TAB 5 - Alertas
# ========================
with tabs[4]:
    st.header("⚠️ Alertas de vencimiento")
    if not df.empty and "fecha_pago_max" in df.columns:
        hoy = datetime.now()
        fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
        limite = hoy + timedelta(days=5)
        alertas = df[(df["pagado"] == False) & (fechas_pago <= limite)]

        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencerse")
        else:
            for _, row in alertas.iterrows():
                st.error(f"⚠️ Pedido {row['pedido']} ({row['cliente']}) vence el {row['fecha_pago_max'].date()}")

# ========================
# TAB 6 - Editar Facturas
# ========================
with tabs[5]:
    st.header("✏️ Editar Facturas")
    if df.empty:
        st.info("No hay facturas registradas todavía.")
    else:
        pedido_seleccionado = st.selectbox(
            "Selecciona el pedido a editar",
            df["pedido"].astype(str).tolist()
        )
        factura = df[df["pedido"] == pedido_seleccionado].iloc[0]

        st.write(f"Cliente: {factura['cliente']}")
        valor_factura = st.number_input("Valor Factura", value=float(factura["valor_factura"]))
        porcentaje = st.number_input(
            "Porcentaje Comisión (%)",
            value=float(factura["valor_comision"] / factura["valor_factura"] * 100 if factura["valor_factura"] else 0),
            min_value=0.0, max_value=100.0, step=0.1
        )
        pagado = st.selectbox("Pagado?", ["No", "Sí"], index=1 if factura["pagado"] else 0)
        fecha_pago_real = st.date_input(
            "Fecha de Pago Real",
            value=factura["fecha_pago_real"].date() if pd.notna(factura["fecha_pago_real"]) else date.today()
        )

        if st.button("💾 Guardar cambios"):
            valor_comision = valor_factura * (porcentaje / 100)
            supabase.table("comisiones").update({
                "valor_factura": valor_factura,
                "valor_comision": valor_comision,
                "pagado": (pagado == "Sí"),
                "fecha_pago_real": fecha_pago_real.isoformat() if pagado == "Sí" else None
            }).eq("id", factura["id"]).execute()
            st.success("✅ Cambios guardados correctamente")
            st.rerun()
