import os
from datetime import date, timedelta, datetime
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

from queries import cargar_datos, insertar_venta, actualizar_factura
from utils import safe_get_public_url, calcular_comision, format_currency, now_iso

# ========================
# Configuración
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Layout principal
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")

df_tmp = cargar_datos(supabase)
meses_disponibles = ["Todos"] + (sorted(df_tmp["mes_factura"].dropna().unique().tolist()) if not df_tmp.empty else [])

if "mes_global" not in st.session_state:
    st.session_state["mes_global"] = "Todos"

if st.session_state["mes_global"] not in meses_disponibles:
    st.session_state["mes_global"] = "Todos"

st.session_state["mes_global"] = st.selectbox(
    "📅 Filtrar por mes (Fecha Factura)",
    meses_disponibles,
    index=meses_disponibles.index(st.session_state["mes_global"]) if st.session_state["mes_global"] in meses_disponibles else 0
)

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
        factura = st.text_input("Factura")
        valor = st.number_input("Valor Factura", min_value=0.0, step=1000.0)
        porcentaje_input = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, step=0.5)
        fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        condicion_especial = st.selectbox("Condición Especial?", ["No", "Sí"])
        submit = st.form_submit_button("💾 Registrar")

    if submit:
        dias_pago = 60 if condicion_especial == "Sí" else 35
        dias_max = 60 if condicion_especial == "Sí" else 45
        fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
        fecha_pago_max = fecha_factura + timedelta(days=dias_max)
        comision = calcular_comision(valor, porcentaje_input)

        data = {
            "pedido": pedido,
            "cliente": cliente,
            "factura": factura,
            "valor": valor,
            "comision": comision,
            "porcentaje": porcentaje_input,
            "fecha_factura": fecha_factura.isoformat(),
            "fecha_pago_est": fecha_pago_est.isoformat(),
            "fecha_pago_max": fecha_pago_max.isoformat(),
            "condicion_especial": (condicion_especial == "Sí"),
            "pagado": False,
        }

        if insertar_venta(supabase, data):
            st.success("✅ Venta registrada correctamente")
            st.rerun()
        else:
            st.error("❌ Error al registrar la venta")

# ========================
# TAB 2 - Facturas Pendientes
# ========================
with tabs[1]:
    st.header("📂 Facturas Pendientes")
    df = cargar_datos(supabase)
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pendientes = df[df["pagado"] == False]
        if st.session_state["mes_global"] != "Todos":
            df_pendientes = df_pendientes[df_pendientes["mes_factura"] == st.session_state["mes_global"]]

        if df_pendientes.empty:
            st.success("✅ No hay facturas pendientes")
        else:
            for _, row in df_pendientes.iterrows():
                st.write(f"**Pedido:** {row.get('pedido', '')}")
                st.write(f"**Cliente:** {row.get('cliente', '')}")
                st.write(f"**Factura:** {row.get('factura', 'N/A') if row.get('factura') else 'N/A'}")
                st.write(f"**Valor Factura:** {format_currency(row.get('valor', 0))}")
                st.write(f"**Fecha Factura:** {row['fecha_factura'].date() if pd.notna(row.get('fecha_factura')) else 'N/A'}")
                st.write(f"**Fecha Máxima Pago:** {row['fecha_pago_max'].date() if pd.notna(row.get('fecha_pago_max')) else 'N/A'}")
                st.divider()

# ========================
# TAB 3 - Facturas Pagadas
# ========================
with tabs[2]:
    st.header("✅ Facturas Pagadas")
    df = cargar_datos(supabase)
    if df.empty:
        st.info("No hay facturas registradas.")
    else:
        df_pagadas = df[df["pagado"] == True]
        if st.session_state["mes_global"] != "Todos":
            df_pagadas = df_pagadas[df_pagadas["mes_factura"] == st.session_state["mes_global"]]

        if df_pagadas.empty:
            st.info("No hay facturas pagadas todavía.")
        else:
            for _, row in df_pagadas.iterrows():
                st.write(f"**Pedido:** {row.get('pedido', '')}")
                st.write(f"**Cliente:** {row.get('cliente','')}")
                st.write(f"**Factura:** {row.get('factura','N/A')}")
                st.write(f"**Valor Factura:** {format_currency(row.get('valor',0))}")
                st.write(f"**Fecha Factura:** {row['fecha_factura'].date() if pd.notna(row.get('fecha_factura')) else 'N/A'}")
                st.write(f"**Fecha Pago Real:** {row['fecha_pago_real'].date() if pd.notna(row.get('fecha_pago_real')) else 'N/A'}")
                if row.get("comprobante_url"):
                    st.markdown(f"[🔗 Ver comprobante]({row.get('comprobante_url')})", unsafe_allow_html=True)
                st.divider()

# ========================
# TAB 4 - Dashboard
# ========================
with tabs[3]:
    st.header("📈 Dashboard de Comisiones")
    df = cargar_datos(supabase)
    if df.empty:
        st.info("No hay datos para mostrar.")
    else:
        if st.session_state["mes_global"] != "Todos":
            df = df[df["mes_factura"] == st.session_state["mes_global"]]

        total_facturado = df["valor"].sum()
        total_comisiones = df.get("comision", pd.Series([0])).sum()
        total_pagado = df[df["pagado"]]["valor"].sum()

        col1, col2, col3 = st.columns(3)
        col1.metric("💵 Total Facturado", format_currency(total_facturado))
        col2.metric("💰 Total Comisiones", format_currency(total_comisiones))
        col3.metric("✅ Total Pagado", format_currency(total_pagado))

        st.subheader("🏆 Ranking de Clientes")
        if not df.empty:
            ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
            for _, row in ranking.iterrows():
                st.write(f"**{row['cliente']}** - 💵 {format_currency(row['valor'])}")
                st.progress(min(1.0, row["valor"] / total_facturado) if total_facturado else 0)
        else:
            st.info("No hay ventas registradas en este mes.")

# ========================
# TAB 5 - Alertas
# ========================
with tabs[4]:
    st.header("⚠️ Alertas de vencimiento")
    df = cargar_datos(supabase)
    if not df.empty and "fecha_pago_max" in df.columns:
        hoy = datetime.now()
        fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
        limite = hoy + timedelta(days=5)
        alertas = df[(df["pagado"] == False) & (fechas_pago <= limite)]

        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencerse")
        else:
            for _, row in alertas.iterrows():
                st.error(f"⚠️ Pedido {row.get('pedido','')} ({row.get('cliente','')}) vence el {row['fecha_pago_max'].date()}")
    else:
        st.info("No hay datos de fechas de pago.")

# ========================
# TAB 6 - Editar Facturas
# ========================
with tabs[5]:
    st.header("✏️ Editar Facturas")
    df = cargar_datos(supabase)
    if df.empty:
        st.info("No hay facturas registradas todavía.")
    else:
        df_filtrado = df[df["pagado"].isin([True, False])]
        if st.session_state["mes_global"] != "Todos":
            df_filtrado = df_filtrado[df_filtrado["mes_factura"] == st.session_state["mes_global"]]

        if df_filtrado.empty:
            st.info("No hay facturas en este mes para editar.")
        else:
            opciones = df_filtrado.apply(
                lambda r: f"{r['pedido']} - {r.get('cliente','')} (id:{r['id']})", axis=1
            ).tolist()
            seleccion = st.selectbox("Selecciona la factura a editar", opciones)
            selected_id = opciones[opciones.index(seleccion)].split("(id:")[-1].rstrip(")")
            try:
                id_val = int(selected_id)
                factura = df_filtrado[df_filtrado["id"] == id_val].iloc[0]
            except Exception:
                pedido_sel = seleccion.split(" - ")[0]
                factura = df_filtrado[df_filtrado["pedido"].astype(str) == pedido_sel].iloc[0]

            st.write(f"Cliente: {factura.get('cliente','')}")
            valor = st.number_input("Valor Factura", value=float(factura.get("valor", 0.0)))
            porcentaje = st.number_input(
                "Porcentaje Comisión (%)",
                value=float(factura.get("comision",0)/valor*100 if valor else 0),
                min_value=0.0, max_value=100.0, step=0.1
            )
            pagado = st.selectbox("Pagado?", ["No","Sí"], index=0 if not factura.get("pagado", False) else 1)
            fecha_pago_real = st.date_input(
                "Fecha de Pago Real",
                value=(factura["fecha_pago_real"].date() if pd.notna(factura.get("fecha_pago_real")) else date.today())
            )
            comprobante_file = st.file_uploader("Subir comprobante de pago (PDF/JPG/PNG)", type=["pdf","jpg","png"])

            if st.button("💾 Guardar cambios"):
                if "id" not in factura or pd.isna(factura["id"]):
                    st.error("⚠️ No se encontró un ID válido para esta factura; no se puede actualizar en Supabase.")
                else:
                    comision = calcular_comision(valor, porcentaje)
                    comprobante_url = factura.get("comprobante_url", "")
                    comprobante_file_name = factura.get("comprobante_file","")

                    if comprobante_file is not None:
                        try:
                            file_bytes = comprobante_file.read()
                        except Exception:
                            file_bytes = comprobante_file.getbuffer()

                        if "factura" in factura and pd.notna(factura.get("factura")) and str(factura.get("factura")).strip() != "":
                            factura_num = str(factura.get("factura")).strip()
                        elif pd.notna(factura.get("pedido")) and str(factura.get("pedido")).strip() != "":
                            factura_num = str(factura.get("pedido")).strip()
                        else:
                            factura_num = str(int(factura["id"]))

                        extension = str(comprobante_file.name).split(".")[-1]
                        file_name = f"{factura_num}.{extension}"
                        file_path = f"{BUCKET}/{file_name}"

                        try:
                            supabase.storage.from_(BUCKET).upload(
                                file_path,
                                file_bytes,
                                {"content-type": comprobante_file.type, "x-upsert": "true"}
                            )
                            public_url = safe_get_public_url(supabase, BUCKET, file_path)
                            if public_url:
                                comprobante_url = public_url
                                comprobante_file_name = file_name
                            else:
                                st.warning("⚠️ No se pudo obtener URL pública del archivo.")
                        except Exception as e:
                            st.error(f"❌ Error subiendo archivo: {e}")

                    updates = {
                        "valor": valor,
                        "comision": comision,
                        "porcentaje": porcentaje,
                        "pagado": (pagado == "Sí"),
                        "fecha_pago_real": fecha_pago_real.isoformat() if pagado=="Sí" else None,
                        "comprobante_url": comprobante_url if comprobante_url else None,
                        "comprobante_file": comprobante_file_name if comprobante_file_name else None,
                        "updated_at": now_iso()
                    }

                    if actualizar_factura(supabase, int(factura["id"]), updates):
                        st.success("✅ Cambios guardados correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error actualizando la factura")
