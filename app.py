import os
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

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
def cargar_datos():
    """Carga los datos desde Supabase y calcula fechas de pago si faltan"""
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

        # Columna auxiliar para filtros de mes
        if "fecha_factura" in df.columns:
            df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)

        return df
    except Exception as e:
        st.error(f"⚠️ Error cargando datos: {e}")
        return pd.DataFrame()

# ========================
# Layout principal
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")

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
    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        mes_seleccionado = st.selectbox(
            "📅 Filtrar por mes (Fecha Factura)",
            ["Todos"] + sorted(df["mes_factura"].dropna().unique())
        )
        df_pendientes = df[df["pagado"] == False]
        if mes_seleccionado != "Todos":
            df_pendientes = df_pendientes[df_pendientes["mes_factura"] == mes_seleccionado]

        if df_pendientes.empty:
            st.success("✅ No hay facturas pendientes")
        else:
            columnas = [c for c in ["pedido", "cliente", "valor_factura", "fecha_factura", "fecha_pago_max", "valor_comision"] if c in df_pendientes.columns]
            st.dataframe(df_pendientes[columnas])

# ========================
# TAB 3 - Facturas Pagadas
# ========================
with tabs[2]:
    st.header("✅ Facturas Pagadas")
    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        mes_seleccionado = st.selectbox(
            "📅 Filtrar por mes (Fecha Factura)",
            ["Todos"] + sorted(df["mes_factura"].dropna().unique()),
            key="mes_pagadas"
        )
        df_pagadas = df[df["pagado"] == True]
        if mes_seleccionado != "Todos":
            df_pagadas = df_pagadas[df_pagadas["mes_factura"] == mes_seleccionado]

        if df_pagadas.empty:
            st.info("No hay facturas pagadas todavía.")
        else:
            columnas = [c for c in ["pedido", "cliente", "valor_factura", "fecha_factura", "fecha_pago_real", "valor_comision"] if c in df_pagadas.columns]
            st.dataframe(df_pagadas[columnas])

# ========================
# TAB 4 - Dashboard
# ========================
with tabs[3]:
    st.header("📈 Dashboard de Comisiones")
    df = cargar_datos()
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        total_facturado = df["valor_factura"].sum()
        total_comisiones = df.get("valor_comision", pd.Series([0])).sum()
        total_pagado = df[df["pagado"]]["valor_factura"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

        st.subheader("🏆 Ranking de Clientes")
        ranking = df.groupby("cliente")["valor_factura"].sum().reset_index().sort_values(by="valor_factura", ascending=False)
        for _, row in ranking.iterrows():
            st.write(f"**{row['cliente']}** - 💵 ${row['valor_factura']:,.2f}")
            st.progress(min(1.0, row["valor_factura"] / total_facturado))

# ========================
# TAB 5 - Alertas
# ========================
with tabs[4]:
    st.header("⚠️ Alertas de vencimiento")
    df = cargar_datos()
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
    else:
        st.info("No hay datos de fechas de pago.")

# ========================
# TAB 6 - Editar Facturas
# ========================
with tabs[5]:
    st.header("✏️ Editar Facturas")
    df = cargar_datos()
    if df.empty:
        st.info("No hay facturas registradas todavía.")
    else:
        mes_seleccionado = st.selectbox(
            "📅 Selecciona el mes (Fecha Factura)",
            ["Todos"] + sorted(df["mes_factura"].dropna().unique()),
            key="mes_editar"
        )
        df_mes = df.copy() if mes_seleccionado == "Todos" else df[df["mes_factura"] == mes_seleccionado]

        if df_mes.empty:
            st.info("No hay facturas en este mes.")
        else:
            pedido_seleccionado = st.selectbox(
                "Selecciona la factura a editar",
                df_mes["pedido"].astype(str).tolist()
            )
            factura = df_mes[df_mes["pedido"] == pedido_seleccionado].iloc[0]

            st.write(f"Cliente: {factura['cliente']}")
            valor_factura = st.number_input("Valor Factura", value=float(factura["valor_factura"]))
            porcentaje = st.number_input("Porcentaje Comisión (%)",
                                         value=float(factura.get("valor_comision", 0) / valor_factura * 100 if valor_factura else 0),
                                         min_value=0.0, max_value=100.0, step=0.1)
            pagado = st.selectbox("Pagado?", ["No", "Sí"], index=0 if not factura["pagado"] else 1)
            fecha_pago_real = st.date_input(
                "Fecha de Pago Real",
                value=factura["fecha_pago_real"].date() if pd.notna(factura.get("fecha_pago_real")) else date.today()
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
