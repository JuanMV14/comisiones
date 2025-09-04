import streamlit as st
import pandas as pd
from datetime import date, timedelta
from supabase import create_client, Client
import uuid
# ======================
# CONFIGURACIÓN SUPABASE
# ======================
SUPABASE_URL = "https://ihncwagxefayefcdngkw.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlobmN3YWd4ZWZheWVmY2RuZ2t3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTcwMDYwNDksImV4cCI6MjA3MjU4MjA0OX0.tzgjBgMJoZdSSw29661PDARz0wfQcdI2bNtZrOqwG54"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")
SIGNED_SECONDS = 300  # 5 minutos

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan variables de entorno SUPABASE_URL y/o SUPABASE_KEY")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# HELPERS
# =========================
def ensure_bucket_private(bucket_name: str):
    """
    Intenta crear el bucket si no existe. No falla si ya existe.
    No hace público el bucket.
    """
    try:
        # Si ya existe lanza error controlado, lo ignoramos
        supabase.storage.create_bucket(bucket_name, public=False)
    except Exception:
        pass

def upload_to_private_bucket(file, dest_path: str) -> str | None:
    """
    Sube archivo al bucket privado. Retorna la ruta (key) o None si falla.
    """
    try:
        # Nota: supabase-py acepta bytes
        file_bytes = file.getvalue()
        resp = supabase.storage.from_(BUCKET).upload(dest_path, file_bytes, {"content-type": file.type})
        # Si existe, a veces devuelve error conflict: para evitar, renombramos
        if isinstance(resp, dict) and resp.get("error"):
            unique = uuid.uuid4().hex[:8]
            alt_path = dest_path.replace(".", f"_{unique}.")
            supabase.storage.from_(BUCKET).upload(alt_path, file_bytes, {"content-type": file.type})
            return alt_path
        return dest_path
    except Exception as e:
        st.error(f"Error subiendo archivo: {e}")
        return None

def sign_private_url(path: str, seconds: int = SIGNED_SECONDS) -> str | None:
    try:
        signed = supabase.storage.from_(BUCKET).create_signed_url(path, seconds)
        if isinstance(signed, dict) and signed.get("signedURL"):
            return signed["signedURL"]
        # SDK alterno
        return signed
    except Exception as e:
        st.warning(f"No se pudo firmar el enlace: {e}")
        return None

def compute_payment_dates(fecha_factura: date, condicion_especial: bool) -> tuple[date, date]:
    """
    Devuelve (fecha_pago_estimado, fecha_pago_max) según regla:
    - Normal: 35 / 45 días
    - Condición especial: 60 / 60 días
    """
    if condicion_especial:
        dias_min = dias_max = 60
    else:
        dias_min, dias_max = 35, 45
    return (fecha_factura + timedelta(days=dias_min),
            fecha_factura + timedelta(days=dias_max))

def status_factura(pagado: bool, fecha_max: date) -> tuple[str, str]:
    """
    Retorna (etiqueta, color_hex) para mostrar estado.
    """
    if pagado:
        return ("Pagada", "#2ecc71")
    hoy = date.today()
    if hoy > fecha_max:
        return ("Vencida", "#e74c3c")
    if (fecha_max - hoy).days <= 5:
        return ("Próx. a vencer", "#f39c12")
    return ("Pendiente", "#3498db")

def fetch_comisiones(mes_filtro: str | None = None) -> pd.DataFrame:
    """
    Trae comisiones. Si mes_filtro = 'YYYY-MM' filtra por ese mes en fecha_factura.
    """
    try:
        q = supabase.table("comisiones").select("*").order("fecha_factura", desc=True)
        data = q.execute().data
        df = pd.DataFrame(data) if data else pd.DataFrame()
        if not df.empty:
            # Convertir fechas a datetime
            for col in ["fecha_pedido", "fecha_factura", "fecha_pago_estimado",
                        "fecha_pago_max", "fecha_pago_real", "created_at", "updated_at", "fecha"]:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors="coerce").dt.date
            if mes_filtro and "fecha_factura" in df.columns:
                df = df[df["fecha_factura"].astype(str).str[:7] == mes_filtro]
        return df
    except Exception as e:
        st.error(f"Error consultando comisiones: {e}")
        return pd.DataFrame()

def register_venta(payload: dict) -> bool:
    try:
        res = supabase.table("comisiones").insert(payload).execute()
        if getattr(res, "data", None) is not None:
            return True
        return False
    except Exception as e:
        st.error(f"❌ Error al registrar: {e}")
        return False

def marcar_pagada(row_id: int, fecha_pago_real: date, comprobante_path: str | None) -> bool:
    try:
        upd = {
            "pagado": True,
            "fecha_pago_real": fecha_pago_real,
            "updated_at": datetime.utcnow().isoformat()
        }
        if comprobante_path:
            upd["comprobante_path"] = comprobante_path
        res = supabase.table("comisiones").update(upd).eq("id", row_id).execute()
        return getattr(res, "data", None) is not None
    except Exception as e:
        st.error(f"❌ Error al actualizar pago: {e}")
        return False

def card_factura(row: pd.Series):
    """Pinta una tarjeta HTML para una factura."""
    etiqueta, color = status_factura(bool(row.get("pagado", False)), row.get("fecha_pago_max"))
    dias_restantes = None
    if not row.get("pagado", False) and row.get("fecha_pago_max"):
        dias_restantes = (row["fecha_pago_max"] - date.today()).days

    value = float(row.get("valor_total", 0) or 0)
    comision = float(row.get("comision_valor", 0) or 0)

    # Bloque tarjeta
    st.markdown(
        f"""
        <div style="
            border:1px solid #eee; border-radius:14px; padding:16px; margin-bottom:14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        ">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <div style="font-weight:700; font-size:18px;">📄 Factura #{row.get('factura_id','')}</div>
            <div style="background:{color}; color:white; padding:6px 10px; border-radius:10px;">
              {etiqueta}
            </div>
          </div>
          <div style="margin-top:8px; font-size:14px; color:#555;">
            <b>Cliente:</b> {row.get('cliente','')} &nbsp;&nbsp;|&nbsp;&nbsp;
            <b>Pedido:</b> {row.get('pedido_id','')} &nbsp;&nbsp;|&nbsp;&nbsp;
            <b>Emitida:</b> {row.get('fecha_factura','')} &nbsp;&nbsp;|&nbsp;&nbsp;
            <b>Pedido:</b> {row.get('fecha_pedido','')}
          </div>
          <div style="margin-top:8px; font-size:14px; color:#555;">
            <b>Pago estimado:</b> {row.get('fecha_pago_estimado','')} &nbsp;&nbsp;|&nbsp;&nbsp;
            <b>Fecha máxima:</b> {row.get('fecha_pago_max','')}
            {"&nbsp;&nbsp;|&nbsp;&nbsp;<b>Días restantes:</b> " + str(dias_restantes) if dias_restantes is not None else ""}
          </div>
          <div style="margin-top:12px; font-size:16px;">
            <b>Valor:</b> ${value:,.2f} &nbsp;&nbsp;|&nbsp;&nbsp;
            <b>Comisión:</b> ${comision:,.2f}
          </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Asegurar bucket
ensure_bucket_private(BUCKET)

# =========================
# UI — TABS (secciones)
# =========================
tab_registrar, tab_pendientes, tab_dashboard, tab_historial = st.tabs(
    ["📝 Registrar venta", "📬 Facturas pendientes", "📊 Dashboard", "🗂️ Historial"]
)

# -------------------------
# 📝 Registrar venta
# -------------------------
with tab_registrar:
    st.subheader("Registrar venta / comisión")

    with st.form("form_registro_venta", clear_on_submit=True):
        colA, colB, colC = st.columns([1.2, 1, 1])
        with colA:
            cliente = st.text_input("Cliente*", placeholder="Nombre del cliente")
            pedido_id = st.text_input("N° Pedido*", placeholder="Ej: 48847")
            factura_id = st.text_input("N° Factura*", placeholder="Ej: 42498")
        with colB:
            valor_total = st.number_input("Valor total*", min_value=0.0, step=1000.0, value=0.0)
            porcentaje = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, value=1.0)
            condicion_especial = st.toggle("Cliente con condición especial (60 días)", value=False)
        with colC:
            fecha_pedido = st.date_input("Fecha del pedido*", value=date.today())
            fecha_factura = st.date_input("Fecha de la factura*", value=date.today())

        comision_valor = (valor_total * porcentaje / 100.0) if valor_total else 0.0

        st.info(f"💰 Comisión calculada: **${comision_valor:,.2f}**")

        submitted = st.form_submit_button("Guardar venta", use_container_width=True)
        if submitted:
            if not (cliente and pedido_id and factura_id and valor_total and fecha_pedido and fecha_factura):
                st.error("Completa los campos obligatorios (*)")
            else:
                f_est, f_max = compute_payment_dates(fecha_factura, condicion_especial)
                payload = {
                    # Campo 'fecha' legacy: guardamos la fecha de creación para evitar NOT NULL
                    "fecha": date.today().isoformat(),
                    "pedido_id": str(pedido_id),
                    "cliente": cliente,
                    "factura_id": str(factura_id),
                    "valor_total": float(valor_total),
                    "porcentaje_comision": float(porcentaje),
                    "comision_valor": float(comision_valor),
                    "condicion_especial": bool(condicion_especial),
                    "created_at": datetime.utcnow().isoformat(),
                    "fecha_pedido": fecha_pedido.isoformat(),
                    "fecha_factura": fecha_factura.isoformat(),
                    "fecha_pago_estimado": f_est.isoformat(),
                    "fecha_pago_max": f_max.isoformat(),
                    "pagado": False,
                    "fecha_pago_real": None,
                    "comprobante_path": None
                }
                ok = register_venta(payload)
                if ok:
                    st.success("✅ Venta registrada correctamente")
                else:
                    st.error("❌ No se pudo registrar la venta")

# -------------------------
# 📬 Facturas pendientes (tarjetas + pago)
# -------------------------
with tab_pendientes:
    st.subheader("Facturas pendientes de pago")

    # Filtro por mes
    meses = st.selectbox(
        "Filtrar por mes (YYYY-MM)",
        options=["Todos"] + sorted({pd.to_datetime(x).strftime("%Y-%m") for x in
                                   fetch_comisiones().get("fecha_factura", []) if x}),
        index=0
    )
    mes_sel = None if meses == "Todos" else meses
    df = fetch_comisiones(mes_sel)

    if df.empty:
        st.info("No hay registros.")
    else:
        pend = df[df["pagado"] == False].sort_values("fecha_pago_max", ascending=True)
        if pend.empty:
            st.success("🎉 No hay facturas pendientes")
        else:
            for _, row in pend.iterrows():
                card_factura(row)

                # Acciones: marcar pagada + subir comprobante
                c1, c2, c3 = st.columns([1, 1, 2])
                with c1:
                    fecha_pago_real = st.date_input(
                        f"Fecha de pago real — Fact. {row['factura_id']}",
                        value=date.today(),
                        key=f"fecha_pago_real_{row['id']}"
                    )
                with c2:
                    archivo = st.file_uploader(
                        f"Comprobante — Fact. {row['factura_id']}",
                        type=["pdf", "jpg", "jpeg", "png"],
                        key=f"comprobante_{row['id']}"
                    )
                with c3:
                    if st.button(f"Marcar como pagada", key=f"pagar_{row['id']}", use_container_width=True):
                        ruta = None
                        if archivo is not None:
                            nombre = archivo.name
                            ext = nombre.split(".")[-1].lower()
                            # carpeta por cliente para orden
                            ruta = f"{row.get('cliente','generico').replace(' ', '_')}/{row['factura_id']}_{uuid.uuid4().hex[:6]}.{ext}"
                            subida = upload_to_private_bucket(archivo, ruta)
                            if not subida:
                                ruta = None
                        ok = marcar_pagada(int(row["id"]), fecha_pago_real, ruta)
                        if ok:
                            st.success("✅ Pago registrado correctamente")
                            st.experimental_rerun()
                        else:
                            st.error("❌ No se pudo registrar el pago")

# -------------------------
# 📊 Dashboard
# -------------------------
with tab_dashboard:
    st.subheader("Resumen y alertas")

    # Selector de mes
    todos_df = fetch_comisiones()
    meses_opts = sorted({pd.to_datetime(x).strftime("%Y-%m") for x in todos_df.get("fecha_factura", []) if x})
    mes_dashboard = st.selectbox("Mes (YYYY-MM)", options=["Todos"] + meses_opts, index=0)
    df_dash = fetch_comisiones(None if mes_dashboard == "Todos" else mes_dashboard)

    colA, colB = st.columns([1.2, 1])
    with colA:
        # Ranking por clientes (monto comprado)
        if not df_dash.empty:
            top = (df_dash.groupby("cliente", as_index=False)["valor_total"].sum()
                   .sort_values("valor_total", ascending=False).head(10))
            st.markdown("#### 🏆 Top clientes por compras")
            st.dataframe(top, use_container_width=True, hide_index=True)
            fig = px.bar(top, x="cliente", y="valor_total", title="Top clientes (valor total)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sin datos para graficar.")

    with colB:
        # Alertas de próximas a vencer
        if not df_dash.empty:
            hoy = date.today()
            proximas = df_dash[(df_dash["pagado"] == False) &
                               (df_dash["fecha_pago_max"] <= hoy + timedelta(days=5))]
            vencidas = df_dash[(df_dash["pagado"] == False) &
                               (df_dash["fecha_pago_max"] < hoy)]
            st.markdown("#### ⏰ Alertas")
            st.metric("Próx. a vencer (≤5 días)", len(proximas))
            st.metric("Vencidas", len(vencidas))
        else:
            st.info("Sin alertas.")

    # Ventas por mes
    st.markdown("---")
    st.markdown("#### 📅 Ventas por mes")
    if not todos_df.empty:
        dfm = todos_df.copy()
        dfm["mes"] = pd.to_datetime(dfm["fecha_factura"]).dt.to_period("M").astype(str)
        serie = dfm.groupby("mes", as_index=False)["valor_total"].sum()
        fig2 = px.line(serie, x="mes", y="valor_total", markers=True, title="Ventas por mes")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Sin ventas registradas.")

# -------------------------
# 🗂️ Historial
# -------------------------
with tab_historial:
    st.subheader("Historial completo")

    mes_hist = st.selectbox(
        "Filtrar por mes (YYYY-MM)",
        options=["Todos"] + meses_opts,
        index=0,
        key="mes_hist"
    )
    df_hist = fetch_comisiones(None if mes_hist == "Todos" else mes_hist)

    if df_hist.empty:
        st.info("No hay registros.")
    else:
        # Botón para generar links firmados al vuelo (solo si hay ruta)
        def link(row):
            p = row.get("comprobante_path")
            if p:
                url = sign_private_url(p, SIGNED_SECONDS)
                if url:
                    return f"[Ver comprobante]({url})"
            return ""
        if "comprobante_path" in df_hist.columns:
            df_hist["comprobante"] = df_hist.apply(link, axis=1)

        mostrar = ["id", "cliente", "pedido_id", "factura_id", "valor_total",
                   "porcentaje_comision", "comision_valor",
                   "fecha_pedido", "fecha_factura", "fecha_pago_estimado",
                   "fecha_pago_max", "pagado", "fecha_pago_real"]
        mostrar += ["comprobante"] if "comprobante" in df_hist.columns else []
        cols = [c for c in mostrar if c in df_hist.columns]

        st.dataframe(df_hist[cols], use_container_width=True, hide_index=True)
