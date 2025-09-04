import os
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
from dotenv import load_dotenv

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="📊 Control de Comisiones", layout="wide")

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================
# FUNCIONES AUXILIARES
# ==============================
def subir_comprobante(file, filename):
    try:
        path = f"{filename}"
        supabase.storage.from_(BUCKET).upload(file, path, {"upsert": True})
        return path
    except Exception as e:
        st.error(f"Error al subir comprobante: {e}")
        return None

def generar_link_temporal(path):
    try:
        url = supabase.storage.from_(BUCKET).create_signed_url(path, 300)
        return url
    except Exception as e:
        st.error(f"Error al generar link firmado: {e}")
        return None

# ==============================
# TABS
# ==============================
tabs = st.tabs(["📝 Registrar Venta", "📂 Facturas", "📈 Dashboard"])

# ==============================
# TAB 1: REGISTRO
# ==============================
with tabs[0]:
    st.header("📝 Registrar nueva venta")

    with st.form("form_venta"):
        pedido = st.text_input("Número de pedido")
        factura = st.text_input("Número de factura")
        cliente = st.text_input("Cliente")
        valor = st.number_input("Valor factura", min_value=0.0, step=1000.0)
        comision = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, step=0.5) / 100
        fecha_pedido = st.date_input("Fecha del pedido", value=date.today())
        fecha_factura = st.date_input("Fecha de la factura", value=date.today())

        condicion_especial = st.checkbox("Cliente con condición especial (60 días)")
        if condicion_especial:
            fecha_pago_min = fecha_factura + timedelta(days=60)
            fecha_pago_max = fecha_factura + timedelta(days=60)
        else:
            fecha_pago_min = fecha_factura + timedelta(days=35)
            fecha_pago_max = fecha_factura + timedelta(days=45)

        comprobante = st.file_uploader("Adjuntar comprobante de pago (opcional)", type=["pdf", "jpg", "png"])

        submitted = st.form_submit_button("💾 Guardar")
        if submitted:
            data = {
                "pedido": pedido,
                "factura": factura,
                "cliente": cliente,
                "valor_factura": valor,
                "comision": comision,
                "valor_comision": valor * comision,
                "pagado": False,
                "fecha_pedido": str(fecha_pedido),
                "fecha_factura": str(fecha_factura),
                "fecha_pago_min": str(fecha_pago_min),
                "fecha_pago_max": str(fecha_pago_max),
                "condicion_especial": condicion_especial,
            }

            # Subir comprobante si existe
            if comprobante:
                filename = f"{factura}_{comprobante.name}"
                path = subir_comprobante(comprobante, filename)
                if path:
                    data["comprobante_url"] = path

            try:
                supabase.table("comisiones").insert(data).execute()
                st.success("✅ Venta registrada exitosamente")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"❌ Error al registrar la venta: {e}")

# ==============================
# TAB 2: FACTURAS
# ==============================
with tabs[1]:
    st.header("📂 Facturas registradas")

    try:
        data = supabase.table("comisiones").select("*").execute()
        df = pd.DataFrame(data.data)
    except Exception as e:
        st.error(f"Error cargando datos: {e}")
        df = pd.DataFrame()

    if not df.empty:
        # Normalizar nombres de columnas
        if "valor_factura" not in df.columns and "valor" in df.columns:
            df = df.rename(columns={"valor": "valor_factura"})

        # Convertir fechas
        for col in ["fecha_factura", "fecha_pedido", "fecha_pago_min", "fecha_pago_max"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        for _, row in df.iterrows():
            with st.container():
                st.markdown(f"### 📄 Factura {row.get('factura', '')} - Cliente: {row.get('cliente', '')}")
                st.write(f"📅 Pedido: {row.get('fecha_pedido', '')}")
                st.write(f"🧾 Fecha factura: {row.get('fecha_factura', '')}")
                st.write(f"💵 Valor: ${row.get('valor_factura', 0):,.2f}")
                st.write(f"💰 Comisión: ${row.get('valor_comision', 0):,.2f}")
                st.write(f"⌛ Pago entre {row.get('fecha_pago_min', '')} y {row.get('fecha_pago_max', '')}")
                st.write(f"✅ Pagado: {row.get('pagado', False)}")

                # Mostrar comprobante si existe
                if row.get("comprobante_url"):
                    url = generar_link_temporal(row["comprobante_url"])
                    if url:
                        st.markdown(f"[📎 Ver comprobante]({url})", unsafe_allow_html=True)

                if not row.get("pagado", False):
                    if st.button(f"💵 Marcar como pagado ({row.get('factura','')})", key=f"pago_{row['id']}"):
                        try:
                            supabase.table("comisiones").update({"pagado": True, "fecha_pago_real": str(date.today())}).eq("id", row["id"]).execute()
                            st.success("Factura marcada como pagada ✅")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"Error al actualizar: {e}")

                st.markdown("---")
    else:
        st.info("No hay facturas registradas aún.")

# ==============================
# TAB 3: DASHBOARD
# ==============================
with tabs[2]:
    st.header("📈 Dashboard")

    if not df.empty:
        # Detectar columna valor
        if "valor_factura" in df.columns:
            col_valor = "valor_factura"
        elif "valor" in df.columns:
            col_valor = "valor"
        else:
            col_valor = None

        total_facturado = df[col_valor].sum() if col_valor else 0
        total_comisiones = df["valor_comision"].sum() if "valor_comision" in df.columns else 0
        total_pagado = df[df["pagado"] == True][col_valor].sum() if col_valor else 0
        pendientes = total_facturado - total_pagado

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("💵 Facturado", f"${total_facturado:,.2f}")
        col2.metric("💰 Comisiones", f"${total_comisiones:,.2f}")
        col3.metric("✅ Pagado", f"${total_pagado:,.2f}")
        col4.metric("⌛ Pendiente", f"${pendientes:,.2f}")

        # Ranking de clientes
        st.subheader("🏆 Clientes que más compraron")
        if col_valor:
            ranking = (
                df.groupby("cliente")[col_valor]
                .sum()
                .reset_index()
                .sort_values(by=col_valor, ascending=False)
            )
            max_val = ranking[col_valor].max()
            for _, row in ranking.iterrows():
                porcentaje = (row[col_valor] / max_val) * 100 if max_val else 0
                st.markdown(f"""
                    <div style='margin-bottom:10px;'>
                        <b>{row['cliente']}</b> - ${row[col_valor]:,.2f}
                        <div style='background:#ddd; border-radius:10px; height:20px;'>
                            <div style='width:{porcentaje:.2f}%; background:#3498db; height:20px; border-radius:10px;'></div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

        # Alertas
        st.subheader("⚠️ Facturas próximas a vencer")
        hoy = pd.to_datetime(date.today())
        if "fecha_pago_max" in df.columns:
            fechas_pago = pd.to_datetime(df["fecha_pago_max"], errors="coerce")
            vencimientos = df[
                (df["pagado"] == False) &
                (fechas_pago.dt.date <= hoy.date() + timedelta(days=5))
            ]
            if not vencimientos.empty:
                for _, row in vencimientos.iterrows():
                    st.write(f"Factura {row.get('factura','')} - Cliente {row.get('cliente','')} vence el {row['fecha_pago_max'].date()}")
            else:
                st.success("✅ No hay facturas próximas a vencer")
    else:
        st.info("No hay datos para mostrar en el dashboard.")
