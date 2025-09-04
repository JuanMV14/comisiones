import os
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client
from dotenv import load_dotenv

# ============================
# CONFIG
# ============================
st.set_page_config(page_title="💰 Control de Comisiones", layout="wide")
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================
# TRAER DATOS
# ============================
res = supabase.table("comisiones").select("*").execute()
df = pd.DataFrame(res.data)

# Parche columnas de valor
if "valor_factura" not in df.columns and "valor" in df.columns:
    df.rename(columns={"valor": "valor_factura"}, inplace=True)

if "valor_factura" not in df.columns:
    df["valor_factura"] = 0.0

df["valor_factura"] = df["valor_factura"].astype(float)

# Conversión segura de fechas
for col in ["fecha", "fecha_factura", "fecha_pago_estimada", "fecha_pago_max", "fecha_pago_real"]:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")

# ============================
# TABS
# ============================
tabs = st.tabs(["➕ Registrar venta", "📈 Dashboard", "⚠️ Alertas", "📋 Facturas"])

# ============================
# TAB 1: Registrar Venta
# ============================
with tabs[0]:
    st.header("➕ Registrar nueva venta")

    with st.form("nueva_venta"):
        numero_pedido = st.text_input("Número de pedido")
        cliente = st.text_input("Cliente")
        referencia = st.text_input("Referencia")
        valor_factura = st.number_input("Valor de la factura", min_value=0.0, step=1000.0)
        fecha_pedido = st.date_input("Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("Fecha de factura", value=date.today())
        condicion_especial = st.checkbox("¿Cliente con condición especial (60 días)?", value=False)

        # Cálculo automático de fechas de pago
        if condicion_especial:
            fecha_pago_estimada = fecha_factura + timedelta(days=60)
            fecha_pago_max = fecha_factura + timedelta(days=60)
        else:
            fecha_pago_estimada = fecha_factura + timedelta(days=35)
            fecha_pago_max = fecha_factura + timedelta(days=45)

        st.write(f"📅 Fecha estimada de pago: {fecha_pago_estimada}")
        st.write(f"📅 Fecha máxima de pago: {fecha_pago_max}")

        submitted = st.form_submit_button("Registrar venta")

        if submitted:
            try:
                data = {
                    "numero_pedido": numero_pedido,
                    "cliente": cliente,
                    "referencia": referencia,
                    "valor_factura": valor_factura,
                    "fecha": str(fecha_pedido),
                    "fecha_factura": str(fecha_factura),
                    "fecha_pago_estimada": str(fecha_pago_estimada),
                    "fecha_pago_max": str(fecha_pago_max),
                    "condicion_especial": condicion_especial,
                    "pagado": False,
                }
                resp = supabase.table("comisiones").insert(data).execute()
                st.success("✅ Venta registrada correctamente")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar la venta: {e}")

# ============================
# TAB 2: Dashboard
# ============================
with tabs[1]:
    st.header("📈 Dashboard")

    total_facturado = df["valor_factura"].sum()
    total_pagado = df[df["pagado"] == True]["valor_factura"].sum()
    total_pendiente = df[df["pagado"] == False]["valor_factura"].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total Facturado", f"${total_facturado:,.2f}")
    col2.metric("✅ Total Pagado", f"${total_pagado:,.2f}")
    col3.metric("⏳ Pendiente", f"${total_pendiente:,.2f}")

    st.subheader("🏆 Ranking de clientes por compras")
    ranking = df.groupby("cliente")["valor_factura"].sum().reset_index().sort_values("valor_factura", ascending=False)
    max_valor = ranking["valor_factura"].max() if not ranking.empty else 1

    for _, row in ranking.iterrows():
        porcentaje = (row["valor_factura"] / max_valor) * 100 if max_valor else 0
        st.markdown(f"""
            <div style='margin-bottom:10px;'>
                <b>{row['cliente']}</b> - ${row['valor_factura']:,.2f}
                <div style='background:#ddd; border-radius:10px; height:20px;'>
                    <div style='width:{porcentaje:.2f}%; background:#2ecc71; height:20px; border-radius:10px;'></div>
                </div>
            </div>
        """, unsafe_allow_html=True)

# ============================
# TAB 3: Alertas
# ============================
with tabs[2]:
    st.header("⚠️ Alertas de vencimiento")

    hoy = date.today()
    if "fecha_pago_max" in df.columns:
        vencimientos = df[
            (df["pagado"] == False) &
            (df["fecha_pago_max"].notna()) &
            (df["fecha_pago_max"].dt.date <= hoy + timedelta(days=5))
        ]
        if vencimientos.empty:
            st.success("🎉 No hay facturas próximas a vencer")
        else:
            st.warning("⚠️ Facturas próximas a vencer en los próximos 5 días:")
            st.dataframe(vencimientos, use_container_width=True)

# ============================
# TAB 4: Facturas
# ============================
with tabs[3]:
    st.header("📋 Facturas registradas")

    if df.empty:
        st.info("No hay facturas registradas aún.")
    else:
        for _, row in df.sort_values("fecha_factura", ascending=False).iterrows():
            with st.container():
                st.markdown("---")
                st.subheader(f"📌 Pedido {row['numero_pedido']} - {row['cliente']}")
                st.write(f"📅 Pedido: {row['fecha'].date() if pd.notnull(row['fecha']) else 'N/A'}")
                st.write(f"📅 Factura: {row['fecha_factura'].date() if pd.notnull(row['fecha_factura']) else 'N/A'}")
                st.write(f"📅 Pago estimado: {row['fecha_pago_estimada'].date() if pd.notnull(row['fecha_pago_estimada']) else 'N/A'}")
                st.write(f"📅 Pago máximo: {row['fecha_pago_max'].date() if pd.notnull(row['fecha_pago_max']) else 'N/A'}")
                st.write(f"💵 Valor: ${row['valor_factura']:,.2f}")
                st.write(f"✅ Pagado: {'Sí' if row['pagado'] else 'No'}")

                if row["pagado"]:
                    if row.get("comprobante_url"):
                        try:
                            signed = supabase.storage.from_(BUCKET).create_signed_url(row["comprobante_url"], 300)
                            st.markdown(f"[📄 Ver comprobante]({signed['signedURL']})")
                        except Exception:
                            st.error("⚠️ Error al generar link firmado del comprobante")
                else:
                    with st.form(f"pago_{row['id']}"):
                        comprobante = st.file_uploader("Subir comprobante de pago", type=["pdf", "jpg", "png"], key=f"comp_{row['id']}")
                        submitted_pago = st.form_submit_button("Marcar como pagada")
                        if submitted_pago and comprobante:
                            try:
                                file_bytes = comprobante.read()
                                file_name = f"{row['id']}_{comprobante.name}"
                                supabase.storage.from_(BUCKET).upload(file_name, file_bytes)
                                supabase.table("comisiones").update({
                                    "pagado": True,
                                    "fecha_pago_real": str(date.today()),
                                    "comprobante_url": file_name
                                }).eq("id", row["id"]).execute()
                                st.success("✅ Factura marcada como pagada")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error al subir comprobante: {e}")
