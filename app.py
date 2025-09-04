import os
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from supabase import create_client, Client

# ======================
# CONFIGURACIÓN SUPABASE
# ======================
SUPABASE_URL = "https://ihncwagxefayefcdngkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlobmN3YWd4ZWZheWVmY2RuZ2t3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDYwNDksImV4cCI6MjA3MjU4MjA0OX0.tzgjBgMJoZdSSw29661PDARz0wfQcdI2bNtZrOqwG54"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# CONFIG STREAMLIT
# -----------------------------
st.set_page_config(page_title="📊 Comisiones", layout="wide")

# =============================
# REGISTRO DE VENTA
# =============================
st.header("📌 Registro de Venta")

with st.form("registro_venta"):
    factura = st.number_input("Número de Factura", min_value=1, step=1)
    cliente = st.text_input("Cliente")
    pedido = st.number_input("Número de Pedido", min_value=1, step=1)
    valor = st.number_input("Valor de la Venta", min_value=0.0, step=1000.0)
    porcentaje = st.number_input("Porcentaje de Comisión (%)", min_value=0.0, step=0.1, value=1.0)

    fecha_pedido = st.date_input("Fecha del Pedido", value=date.today())
    fecha_factura = st.date_input("Fecha de Facturación", value=date.today())

    condicion_especial = st.radio("¿Condición Especial de Pago?", ["No", "Sí"]) == "Sí"

    submitted = st.form_submit_button("Registrar Venta ✅")

    if submitted:
        try:
            comision = valor * (porcentaje / 100)

            if condicion_especial:
                fecha_pago_estimada = fecha_factura + timedelta(days=60)
                fecha_pago_max = fecha_factura + timedelta(days=60)
            else:
                fecha_pago_estimada = fecha_factura + timedelta(days=35)
                fecha_pago_max = fecha_factura + timedelta(days=45)

            resp = supabase.table("comisiones").insert({
                "fecha": str(date.today()),
                "factura": factura,
                "cliente": cliente,
                "pedido": pedido,
                "valor": valor,
                "porcentaje": porcentaje,
                "comision": comision,
                "condicion_especial": condicion_especial,
                "fecha_pedido": str(fecha_pedido),
                "fecha_factura": str(fecha_factura),
                "fecha_pago_estimada": str(fecha_pago_estimada),
                "fecha_pago_max": str(fecha_pago_max),
                "pagado": False
            }).execute()

            st.success("✅ Venta registrada exitosamente")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Error al registrar la venta: {e}")

st.markdown("---")

# =============================
# DASHBOARD
# =============================
st.header("📊 Dashboard de Comisiones")

data = supabase.table("comisiones").select("*").execute()
df = pd.DataFrame(data.data) if data.data else pd.DataFrame()

if not df.empty:
    # Ranking de clientes
    ranking = df.groupby("cliente")["valor"].sum().reset_index().sort_values("valor", ascending=False)
    st.subheader("🏆 Ranking de Clientes por Compras")
    st.dataframe(ranking, use_container_width=True)

    # Alertas de vencimiento (protegido contra columnas faltantes)
    if "fecha_pago_max" in df.columns and "pagado" in df.columns:
        hoy = date.today()
        vencimientos = df[
            (~df["pagado"]) &
            (pd.to_datetime(df["fecha_pago_max"]) <= pd.to_datetime(hoy + timedelta(days=5)))
        ]
        if not vencimientos.empty:
            st.warning("⚠️ Hay facturas próximas a vencer en los próximos 5 días")
            st.dataframe(
                vencimientos[["factura", "cliente", "fecha_factura", "fecha_pago_max"]],
                use_container_width=True
            )

    # Resumen de pagos
    total_comisiones = df["comision"].sum()
    comisiones_pendientes = df.loc[~df.get("pagado", False), "comision"].sum()
    comisiones_pagadas = df.loc[df.get("pagado", False), "comision"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Total Comisiones", f"${total_comisiones:,.2f}")
    col2.metric("⏳ Pendientes", f"${comisiones_pendientes:,.2f}")
    col3.metric("✅ Pagadas", f"${comisiones_pagadas:,.2f}")

else:
    st.info("Aún no hay ventas registradas.")

st.markdown("---")

# =============================
# HISTORIAL
# =============================
st.header("📑 Historial de Ventas y Pagos")

if not df.empty:
    for _, row in df.iterrows():
        with st.expander(f"📄 Factura {row['factura']} - {row['cliente']}"):
            st.write(f"**Valor Venta:** ${row['valor']:,.2f}")
            st.write(f"**Comisión:** ${row['comision']:,.2f}")
            st.write(f"**Fecha Factura:** {row['fecha_factura']}")
            st.write(f"**Fecha Estimada Pago:** {row.get('fecha_pago_estimada', 'N/A')}")
            st.write(f"**Fecha Máxima Pago:** {row.get('fecha_pago_max', 'N/A')}")
            st.write(f"**Pagado:** {'✅ Sí' if row.get('pagado') else '❌ No'}")

            # Si no está pagado, permitir marcar como pagado + comprobante
            if not row.get("pagado"):
                comprobante = st.file_uploader(
                    f"Subir comprobante de pago (opcional) para factura {row['factura']}",
                    type=["jpg", "png", "pdf"],
                    key=f"upload_{row['id']}"
                )

                if st.button(f"Marcar como Pagada", key=f"pago_{row['id']}"):
                    try:
                        url_comprobante = None
                        if comprobante:
                            file_name = f"{row['id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{comprobante.name}"
                            supabase.storage.from_("comprobantes").upload(file_name, comprobante.getvalue())
                            url_comprobante = f"{SUPABASE_URL}/storage/v1/object/public/comprobantes/{file_name}"

                        supabase.table("comisiones").update({
                            "pagado": True,
                            "fecha_pago_real": str(date.today()),
                            "comprobante_url": url_comprobante
                        }).eq("id", row["id"]).execute()

                        st.success("✅ Factura marcada como pagada y comprobante guardado")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al actualizar: {e}")
            else:
                if row.get("comprobante_url"):
                    st.markdown(f"📎 [Ver comprobante]({row['comprobante_url']})")
else:
    st.info("No hay registros en el historial todavía.")
