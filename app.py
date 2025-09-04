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

# ======================
# FUNCIONES BD
# ======================
def insertar_comision(fecha, pedido, cliente, factura, valor, porcentaje, comision,
                      pagado, fecha_pedido, fecha_factura, fecha_pago, fecha_maxima, condicion_especial):
    data = {
        "fecha": str(fecha),
        "pedido": pedido,
        "cliente": cliente,
        "factura": factura,
        "valor": valor,
        "porcentaje": porcentaje,
        "comision": comision,
        "pagado": pagado,
        "fecha_pedido": str(fecha_pedido),
        "fecha_factura": str(fecha_factura),
        "fecha_pago": str(fecha_pago),
        "fecha_maxima": str(fecha_maxima),
        "condicion_especial": condicion_especial
    }
    return supabase.table("comisiones").insert(data).execute()

def actualizar_pago(id_registro, fecha_pago_real):
    return supabase.table("comisiones").update({"pagado": True, "fecha_pago_real": str(fecha_pago_real)}).eq("id", id_registro).execute()

def obtener_comisiones():
    res = supabase.table("comisiones").select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()

# ======================
# APP STREAMLIT
# ======================
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

st.title("📊 Control de Comisiones")

tabs = st.tabs(["➕ Nueva Comisión", "📈 Dashboard", "📑 Historial"])

# ======================
# TAB 1: NUEVA COMISIÓN
# ======================
with tabs[0]:
    st.header("➕ Registrar nueva comisión")
    with st.form("form_comision"):
        # Fechas principales
        fecha_pedido = st.date_input("📅 Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("📅 Fecha de la factura", value=date.today())

        # Condición especial
        condicion_especial = st.checkbox("¿Cliente con condición especial?", value=False)

        if condicion_especial:
            fecha_pago = st.date_input("📅 Fecha de pago (manual)")
            fecha_maxima = st.date_input("📅 Fecha máxima (manual)")
        else:
            fecha_pago = fecha_factura + timedelta(days=35)
            fecha_maxima = fecha_factura + timedelta(days=45)
            st.info(f"✅ Fecha de pago estimada: {fecha_pago.strftime('%Y-%m-%d')} | "
                    f"⏳ Fecha máxima: {fecha_maxima.strftime('%Y-%m-%d')}")

        # Datos del pedido
        pedido = st.text_input("N° Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("N° Factura")
        valor = st.number_input("Valor venta", min_value=0.0, format="%.2f")
        porcentaje = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, format="%.2f")
        comision = valor * (porcentaje / 100)
        pagado = st.checkbox("¿Pagado?", value=False)

        submitted = st.form_submit_button("Guardar")
        if submitted:
            insertar_comision(
                fecha=date.today(),
                pedido=pedido,
                cliente=cliente,
                factura=factura,
                valor=valor,
                porcentaje=porcentaje,
                comision=comision,
                pagado=pagado,
                fecha_pedido=fecha_pedido,
                fecha_factura=fecha_factura,
                fecha_pago=fecha_pago,
                fecha_maxima=fecha_maxima,
                condicion_especial=condicion_especial
            )
            st.success("✅ Comisión registrada correctamente")

# ======================
# TAB 2: DASHBOARD
# ======================
with tabs[1]:
    st.header("📈 Dashboard mensual")

    df = obtener_comisiones()
    if df.empty:
        st.info("Aún no tienes comisiones registradas.")
    else:
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"])
        df["fecha_maxima"] = pd.to_datetime(df["fecha_maxima"])
        df["mes"] = df["fecha_factura"].dt.to_period("M").astype(str)

        mes_sel = st.selectbox("Selecciona el mes", sorted(df["mes"].unique()), index=len(df["mes"].unique())-1)
        df_mes = df[df["mes"] == mes_sel]

        total_ventas = df_mes["valor"].sum()
        total_comisiones = df_mes["comision"].sum()
        pagado = df_mes[df_mes["pagado"] == True]["comision"].sum()
        pendiente = total_comisiones - pagado

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💰 Ventas", f"${total_ventas:,.2f}")
        col2.metric("📊 Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Pagado", f"${pagado:,.2f}")
        col4.metric("⏳ Pendiente", f"${pendiente:,.2f}")

        # Ranking clientes
        st.subheader("🏆 Ranking de clientes por compras")
        ranking = df_mes.groupby("cliente")["valor"].sum().sort_values(ascending=False).reset_index()
        st.table(ranking)

        # Alertas de vencimiento
        st.subheader("⚠️ Facturas próximas a vencerse")
        hoy = date.today()
        alertas = df_mes[(df_mes["pagado"] == False) & ((df_mes["fecha_maxima"] - pd.to_datetime(hoy)).dt.days <= 5)]
        if alertas.empty:
            st.success("✅ No hay facturas próximas a vencerse")
        else:
            st.error("⚠️ Facturas próximas a vencerse")
            st.dataframe(alertas[["cliente", "factura", "fecha_factura", "fecha_maxima", "valor"]])

# ======================
# TAB 3: HISTORIAL
# ======================
with tabs[2]:
    st.header("📑 Historial de comisiones")

    df = obtener_comisiones()
    if df.empty:
        st.info("No hay registros aún.")
    else:
        for _, row in df.iterrows():
            with st.expander(f"📄 {row['cliente']} - Factura {row['factura']}"):
                st.write(f"Pedido: {row['pedido']}")
                st.write(f"Valor: ${row['valor']:,.2f}")
                st.write(f"Comisión: ${row['comision']:,.2f}")
                st.write(f"Fecha factura: {row['fecha_factura']}")
                st.write(f"Fecha máxima: {row['fecha_maxima']}")
                st.write(f"Pagado: {'✅ Sí' if row['pagado'] else '❌ No'}")

                if not row["pagado"]:
                    if st.button(f"Marcar como pagado ({row['factura']})", key=f"pago_{row['id']}"):
                        actualizar_pago(row["id"], date.today())
                        st.success("✅ Pago registrado")
                        st.rerun()

