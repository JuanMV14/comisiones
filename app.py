import os
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
import altair as alt

# ========================
# Cargar variables de entorno
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Funciones auxiliares
# ========================
def subir_comprobante(file, pedido_id):
    if file is None:
        return None

    extension = os.path.splitext(file.name)[1]
    path = f"comprobantes/{pedido_id}{extension}"

    try:
        supabase.storage.from_(BUCKET).upload(
            path,
            file.read(),
            {"content-type": file.type},
            upsert=True
        )
        return path
    except Exception as e:
        st.error(f"❌ Error al subir comprobante: {e}")
        return None

def link_comprobante(path):
    try:
        url = supabase.storage.from_(BUCKET).get_public_url(path)
        return url
    except Exception:
        return None

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

        # Asegurar columna pagado
        if "pagado" not in df.columns:
            df["pagado"] = False

        # Recalcular fechas de pago si faltan
        for idx, row in df.iterrows():
            if pd.isna(row.get('fecha_pago_est')) or pd.isna(row.get('fecha_pago_max')):
                if pd.notna(row.get('fecha_factura')):
                    fecha_factura = row['fecha_factura']
                    if row.get('condicion_especial'):
                        df.at[idx, 'fecha_pago_est'] = fecha_factura + timedelta(days=60)
                        df.at[idx, 'fecha_pago_max'] = fecha_factura + timedelta(days=60)
                    else:
                        df.at[idx, 'fecha_pago_est'] = fecha_factura + timedelta(days=35)
                        df.at[idx, 'fecha_pago_max'] = fecha_factura + timedelta(days=45)
        return df
    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        return pd.DataFrame()

# ========================
# Layout principal
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")
tabs = st.tabs(["➕ Registrar Venta", "📌 Facturas Pendientes", "💸 Facturas Pagadas", "📈 Dashboard", "⚠️ Alertas"])

df = cargar_datos()

# ========================
# CONTROL GLOBAL DE MES (por Fecha Factura)
# ========================
if not df.empty:
    df["mes_factura"] = df["fecha_factura"].dt.strftime("%Y-%m")
    meses_disponibles = sorted(df["mes_factura"].dropna().unique())
else:
    meses_disponibles = []

if "mes_seleccionado" not in st.session_state:
    st.session_state["mes_seleccionado"] = "Todos"

st.selectbox(
    "Selecciona el mes a visualizar (Fecha Factura)",
    ["Todos"] + meses_disponibles,
    key="mes_seleccionado"
)

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
    st.header("📌 Facturas Pendientes")
    if df.empty:
        st.info("No hay facturas registradas todavía.")
    else:
        mes_seleccionado = st.session_state["mes_seleccionado"]
        df_mes = df.copy() if mes_seleccionado=="Todos" else df[df["mes_factura"]==mes_seleccionado]
        pendientes = df_mes[df_mes["pagado"]==False]
        if pendientes.empty:
            st.success("✅ No hay facturas pendientes")
        else:
            for _, row in pendientes.iterrows():
                with st.container():
                    st.write(f"🧾 Pedido: {row['pedido']} - Cliente: {row['cliente']}")
                    st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                    st.write(f"💰 Comisión: ${row.get('valor_comision',0):,.2f}")
                    st.write(f"📅 Fecha Factura: {row['fecha_factura'].date()}")
                    st.write(f"📅 Estimada Pago: {row['fecha_pago_est'].date()}")
                    st.write(f"📅 Máxima Pago: {row['fecha_pago_max'].date()}")
                    st.write(f"✅ Pagado: {'Sí' if row['pagado'] else 'No'}")

                    comprobante = st.file_uploader(
                        f"📎 Subir comprobante (Pedido {row['pedido']})",
                        type=["pdf","jpg","png"],
                        key=f"comp_{row['pedido']}"
                    )
                    if comprobante:
                        path = subir_comprobante(comprobante, row['pedido'])
                        if path:
                            supabase.table("comisiones").update({
                                "comprobante_url": path,
                                "pagado": True,
                                "fecha_pago_real": datetime.now().isoformat()
                            }).eq("id", row["id"]).execute()
                            st.success("📎 Comprobante cargado y factura marcada como pagada")
                            st.rerun()

# ========================
# TAB 3 - Facturas Pagadas
# ========================
with tabs[2]:
    st.header("💸 Facturas Pagadas")
    if df.empty:
        st.info("No hay facturas registradas todavía.")
    else:
        mes_seleccionado = st.session_state["mes_seleccionado"]
        df_mes = df.copy() if mes_seleccionado=="Todos" else df[df["mes_factura"]==mes_seleccionado]
        pagadas = df_mes[df_mes["pagado"]==True]
        if pagadas.empty:
            st.info("No hay facturas pagadas para este mes.")
        else:
            for _, row in pagadas.iterrows():
                with st.container():
                    st.write(f"🧾 Pedido: {row['pedido']} - Cliente: {row['cliente']}")
                    st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                    st.write(f"💰 Comisión: ${row.get('valor_comision',0):,.2f}")
                    if row.get("comprobante_url"):
                        url = link_comprobante(row["comprobante_url"])
                        if url:
                            st.markdown(f"[🔗 Ver comprobante]({url})", unsafe_allow_html=True)

# ========================
# TAB 4 - Dashboard Mejorado
# ========================
with tabs[3]:
    st.header("📈 Dashboard de Comisiones")
    if df.empty:
        st.info("No hay datos para mostrar en el dashboard.")
    else:
        mes_seleccionado = st.session_state["mes_seleccionado"]
        df_mes = df.copy() if mes_seleccionado=="Todos" else df[df["mes_factura"]==mes_seleccionado]

        total_facturado = df_mes["valor_factura"].sum()
        total_comisiones = df_mes.get("valor_comision", pd.Series([0])).sum()
        total_pagado = df_mes[df_mes["pagado"]]["valor_factura"].sum()

        col1,col2,col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

        # Ranking de Clientes
        st.subheader(f"🏆 Ranking de Clientes - {mes_seleccionado}")
        ranking = df_mes.groupby("cliente")["valor_factura"].sum().reset_index().sort_values(by="valor_factura", ascending=True)
        if not ranking.empty:
            chart_ranking = alt.Chart(ranking).mark_bar().encode(
                x=alt.X("valor_factura", title="Valor Facturado"),
                y=alt.Y("cliente", sort='-x', title="Cliente"),
                tooltip=["cliente","valor_factura"]
            )
            st.altair_chart(chart_ranking, use_container_width=True)

        # Flujo de Comisiones por Mes
        st.subheader(f"📅 Flujo de Comisiones - {mes_seleccionado}")
        flujo = df_mes.groupby("mes_factura")["valor_comision"].sum().reset_index().sort_values("mes_factura")
        if not flujo.empty:
            chart_flujo = alt.Chart(flujo).mark_bar(color="#FF7F0E").encode(
                x=alt.X("mes_factura", title="Mes (Fecha Factura)"),
                y=alt.Y("valor_comision", title="Comisiones"),
                tooltip=["mes_factura","valor_comision"]
            )
            st.altair_chart(chart_flujo, use_container_width=True)

# ========================
# TAB 5 - Alertas
# ========================
with tabs[4]:
    st.header("⚠️ Alertas de vencimiento")
    if df.empty:
        st.info("No hay datos de fechas de pago.")
    else:
        mes_seleccionado = st.session_state["mes_seleccionado"]
        df_mes = df.copy() if mes_seleccionado=="Todos" else df[df["mes_factura"]==mes_seleccionado]

        hoy = datetime.now()
        if "fecha_pago_max" in df_mes.columns:
            fechas_pago = pd.to_datetime(df_mes["fecha_pago_max"], errors="coerce")
            limite = hoy + timedelta(days=5)
            alertas = df_mes[(df_mes["pagado"]==False) & (fechas_pago <= limite)]
            if alertas.empty:
                st.success("✅ No hay facturas próximas a vencerse")
            else:
                for _, row in alertas.iterrows():
                    st.error(f"⚠️ Pedido {row['pedido']} ({row['cliente']}) vence el {row['fecha_pago_max'].date()}")

