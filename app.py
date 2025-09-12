import os
from datetime import datetime, timedelta, date
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv
from queries import get_all_comisiones, insert_comision, update_comision
from utils import safe_get_public_url

# ========================
# Configuración
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "comprobantes"

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================
# Layout principal
# ========================
st.set_page_config(page_title="Gestión de Comisiones", layout="wide")
st.title("📊 Gestión de Comisiones")

def main():
    df = get_all_comisiones()
    if not df.empty and "fecha_factura" in df.columns:
        df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
    else:
        df["mes_factura"] = None

    meses_disponibles = ["Todos"] + (sorted(df["mes_factura"].dropna().unique().tolist()) if not df.empty else [])
    if "mes_global" not in st.session_state:
        st.session_state["mes_global"] = "Todos"

    if st.session_state["mes_global"] not in meses_disponibles:
        st.session_state["mes_global"] = "Todos"

    st.session_state["mes_global"] = st.selectbox(
        "📅 Filtrar por mes (Fecha Factura)",
        meses_disponibles,
        index=meses_disponibles.index(st.session_state["mes_global"]) if st.session_state["mes_global"] in meses_disponibles else 0
    )

    # Tabs
    tabs = st.tabs([
        "➕ Registrar Venta",
        "📂 Facturas Pendientes",
        "✅ Facturas Pagadas",
        "📈 Dashboard",
        "⚠️ Alertas"
    ])

    with tabs[0]:
        registrar_venta()

    with tabs[1]:
        mostrar_facturas(df, pagadas=False)

    with tabs[2]:
        mostrar_facturas(df, pagadas=True)

    with tabs[3]:
        mostrar_dashboard(df)

    with tabs[4]:
        mostrar_alertas(df)


# ========================
# Registrar Venta
# ========================
def registrar_venta():
    st.header("➕ Registrar nueva venta")

    with st.form("form_venta"):
        pedido = st.text_input("Número de Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Factura")
        valor = st.number_input("Valor Factura (neto, sin IVA)", min_value=0.0, step=1000.0)
        porcentaje_input = st.number_input("Porcentaje Comisión (%)", min_value=0.0, max_value=100.0, step=0.5)
        fecha_factura = st.date_input("Fecha de Factura", value=date.today())
        condicion_especial = st.selectbox("Condición Especial?", ["No", "Sí"])
        descuento_factura = st.selectbox("¿Tiene descuento a pie de factura?", ["Sí", "No"])
        submit = st.form_submit_button("💾 Registrar")

    if submit:
        try:
            comision = valor * (porcentaje_input / 100)
            porcentaje = porcentaje_input
            dias_pago = 60 if condicion_especial == "Sí" else 35
            dias_max = 60 if condicion_especial == "Sí" else 45

            fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
            fecha_pago_max = fecha_factura + timedelta(days=dias_max)

            data = {
                "pedido": pedido,
                "cliente": cliente,
                "factura": factura,
                "valor": valor,
                "comision": comision,
                "porcentaje": porcentaje,
                "fecha_factura": fecha_factura.isoformat(),
                "fecha_pago_est": fecha_pago_est.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "condicion_especial": (condicion_especial == "Sí"),
                "descuento_factura": (descuento_factura == "Sí"),
                "pagado": False,
            }

            insert_comision(data)
            st.success("✅ Venta registrada correctamente")
            st.rerun()

        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")


# ========================
# Mostrar Facturas
# ========================
def mostrar_facturas(df, pagadas=False):
    tipo = "Pagadas" if pagadas else "Pendientes"
    st.header(f"{'✅' if pagadas else '📂'} Facturas {tipo}")

    if df.empty:
        st.info("No hay facturas registradas.")
        return

    df_filtrado = df[df["pagado"] == pagadas]
    if st.session_state["mes_global"] != "Todos":
        df_filtrado = df_filtrado[df_filtrado["mes_factura"] == st.session_state["mes_global"]]

    if df_filtrado.empty:
        st.info(f"No hay facturas {tipo.lower()} en este mes.")
        return

    for _, row in df_filtrado.iterrows():
        with st.expander(f"📄 Pedido: {row.get('pedido', '')} - Cliente: {row.get('cliente', '')}"):
            st.write(f"**Factura:** {row.get('factura', 'N/A')}")
            st.write(f"**Valor Factura:** ${row.get('valor', 0):,.2f}")
            st.write(f"**Comisión:** ${row.get('comision', 0):,.2f}")
            st.write(f"**Fecha Factura:** {row['fecha_factura'].date() if pd.notna(row.get('fecha_factura')) else 'N/A'}")
            if pagadas:
                st.write(f"**Fecha Pago Real:** {row['fecha_pago_real'].date() if pd.notna(row.get('fecha_pago_real')) else 'N/A'}")
                if row.get("comprobante_url"):
                    st.markdown(f"[🔗 Ver comprobante]({row.get('comprobante_url')})", unsafe_allow_html=True)
            else:
                st.write(f"**Fecha Máxima Pago:** {row['fecha_pago_max'].date() if pd.notna(row.get('fecha_pago_max')) else 'N/A'}")

            if st.button(f"✏️ Editar factura {row['id']}", key=f"edit_{row['id']}"):
                editar_factura(row)


# ========================
# Editar Factura
# ========================
def editar_factura(factura):
    st.subheader(f"✏️ Editar Factura {factura.get('factura','')}")
    valor = st.number_input("Valor Factura", value=float(factura.get("valor", 0.0)))
    porcentaje = st.number_input(
        "Porcentaje Comisión (%)",
        value=float(factura.get("comision", 0) / valor * 100 if valor else 0),
        min_value=0.0, max_value=100.0, step=0.1
    )
    pagado = st.selectbox("Pagado?", ["No", "Sí"], index=0 if not factura.get("pagado", False) else 1)
    fecha_pago_real = st.date_input(
        "Fecha de Pago Real",
        value=(factura["fecha_pago_real"].date() if pd.notna(factura.get("fecha_pago_real")) else date.today())
    )
    comprobante_file = st.file_uploader("Subir comprobante de pago (PDF/JPG/PNG)", type=["pdf", "jpg", "png"])

    if st.button("💾 Guardar cambios", key=f"save_{factura['id']}"):
        comision = valor * (porcentaje / 100)
        comprobante_url = factura.get("comprobante_url", "")
        comprobante_file_name = factura.get("comprobante_file", "")

        if comprobante_file is not None:
            try:
                file_bytes = comprobante_file.read()
            except Exception:
                file_bytes = comprobante_file.getbuffer()

            factura_num = str(factura.get("factura") or factura.get("pedido") or factura["id"])
            extension = str(comprobante_file.name).split(".")[-1]
            file_name = f"{factura_num}.{extension}"
            file_path = f"{file_name}"

            supabase.storage.from_(BUCKET).upload(
                file_path,
                file_bytes,
                {"content-type": comprobante_file.type, "x-upsert": "true"}
            )
            public_url = safe_get_public_url(BUCKET, file_path)
            if public_url:
                comprobante_url = public_url
                comprobante_file_name = file_name
            else:
                st.warning("⚠️ No se pudo obtener URL pública del archivo.")

        update_comision(factura["id"], {
            "valor": valor,
            "comision": comision,
            "porcentaje": porcentaje,
            "pagado": (pagado == "Sí"),
            "fecha_pago_real": fecha_pago_real.isoformat() if pagado == "Sí" else None,
            "comprobante_url": comprobante_url if comprobante_url else None,
            "comprobante_file": comprobante_file_name if comprobante_file_name else None,
            "updated_at": datetime.now().isoformat()
        })
        st.success("✅ Cambios guardados correctamente")
        st.rerun()


# ========================
# Dashboard
# ========================
def mostrar_dashboard(df):
    st.header("📈 Dashboard de Comisiones")

    if df.empty:
        st.info("No hay datos para mostrar.")
        return

    if st.session_state["mes_global"] != "Todos":
        df = df[df["mes_factura"] == st.session_state["mes_global"]]

    total_facturado = df["valor"].sum()
    total_comisiones = df.get("comision", pd.Series([0])).sum()
    total_pagado = df[df["pagado"]]["valor"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
    col2.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
    col3.metric("✅ Total Pagado", f"${total_pagado:,.2f}")

    st.subheader("🏆 Ranking de Clientes")
    ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values(by="valor", ascending=False)
    for _, row in ranking.iterrows():
        st.write(f"**{row['cliente']}** - 💵 ${row['valor']:,.2f}")
        st.progress(min(1.0, row["valor"] / total_facturado) if total_facturado else 0)


# ========================
# Alertas
# ========================
def mostrar_alertas(df):
    st.header("⚠️ Alertas de vencimiento")
    if df.empty or "fecha_pago_max" not in df.columns:
        st.info("No hay datos de fechas de pago.")
        return

    hoy = datetime.now()
    fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
    limite = hoy + timedelta(days=5)
    alertas = df[(df["pagado"] == False) & (fechas_pago <= limite)]

    if alertas.empty:
        st.success("✅ No hay facturas próximas a vencerse")
    else:
        for _, row in alertas.iterrows():
            st.error(f"⚠️ Pedido {row.get('pedido', '')} ({row.get('cliente','')}) vence el {row['fecha_pago_max'].date()}")


if __name__ == "__main__":
    main()
