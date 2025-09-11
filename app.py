# app.py
import os
from datetime import datetime, timedelta, date
import calendar
import streamlit as st
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# ========================
# Configuración
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("❌ Faltan SUPABASE_URL o SUPABASE_KEY en las variables de entorno.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Gestión de Comisiones", layout="wide")


# ========================
# Helpers
# ========================
def safe_get_public_url(bucket: str, path: str):
    """Obtiene URL pública del bucket (maneja distintos formatos de respuesta)."""
    try:
        res = supabase.storage.from_(bucket).get_public_url(path)
        # supabase-py puede devolver diccionario u objeto con keys distintas
        if isinstance(res, dict):
            for k in ("publicUrl", "public_url", "publicURL", "url"):
                if k in res:
                    return res[k]
            # fallback string
            return str(res)
        return res
    except Exception:
        return None


def add_one_month(d: date) -> date:
    """Suma un mes a una fecha, manejando fin de mes."""
    if d is None:
        return None
    year = d.year + (d.month // 12)
    month = d.month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def cargar_datos() -> pd.DataFrame:
    """Carga todos los registros de la tabla comisiones desde Supabase y normaliza tipos."""
    try:
        res = supabase.table("comisiones").select("*").execute()
        rows = res.data if getattr(res, "data", None) is not None else []
        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)

        # columnas opcionales que nos interesan - si no existen, crear con defaults
        expected_cols = {
            "id": None,
            "pedido": "",
            "cliente": "",
            "factura": "",
            "valor": 0.0,
            "devoluciones": 0.0,
            "tipo_cliente": "no_propio",  # opcional: no_propio|propio|propio_descuento
            "tiene_descuento_fac": False,
            "porcentaje_descuento": 15.0,
            "rango_descuento_ini": 35,
            "rango_descuento_fin": 45,
            "fecha_pedido": None,
            "fecha_factura": None,
            "fecha_pago_est": None,
            "fecha_pago_max": None,
            "fecha_pago_real": None,
            "pagado": False,
            "comprobante_url": None,
            "comprobante_file": None,
            "condicion_especial": False,
            "valor_base": None,
            "comision": None,
        }

        for c, default in expected_cols.items():
            if c not in df.columns:
                df[c] = default

        # convertir fechas
        for col in ["fecha_pedido", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.date

        # mes factura para filtros
        df["mes_factura"] = df["fecha_factura"].apply(lambda d: d.strftime("%Y-%m") if pd.notna(d) else None)

        return df

    except Exception as e:
        st.error(f"⚠️ Error al cargar datos: {e}")
        return pd.DataFrame()


# ========================
# Lógica de negocio: cálculo al vuelo
# ========================
def calcular_valor_y_comisiones_row(
    valor: float,
    devoluciones: float,
    tiene_descuento_fac: bool,
    porcentaje_descuento: float,
    rango_ini: int,
    rango_fin: int,
    fecha_factura,
    fecha_pago_real,
    tipo_cliente: str,
    descuento_default=0.15,
):
    """
    Retorna:
      valor_base_real, comision_real, valor_base_if_discount, comision_if_discount, valor_base_no_discount, comision_no_discount, mes_pago_comision (YYYY-MM or None)
    - valor_base_real & comision_real se calculan si hay fecha_pago_real (sino se dejan None o se asume valor actual)
    - valor_base_if_discount/comision_if_discount: estimación si se aplicara descuento por pronto pago
    - valor_base_no_discount/comision_no_discount: estimación sin descuento
    """
    valor = float(valor or 0.0)
    devoluciones = float(devoluciones or 0.0)
    base_sin_desc = max(0.0, valor - devoluciones)

    # valores estimados
    valor_base_if_discount = round(base_sin_desc * (1 - (porcentaje_descuento or descuento_default) / 100.0), 2)
    valor_base_no_discount = round(base_sin_desc, 2)

    # función para calcular comisión según tipo de cliente y si hay descuento en la base
    def comision_para_base(base, tiene_desc):
        if tipo_cliente == "no_propio":
            return round(base * 0.01, 2)
        elif tipo_cliente == "propio":
            # si tiene descuento a pie de factura o si aplica descuento por pronto pago, la regla del % de comision cambia:
            # según tus reglas: propio = 2.5%, propio + descuento adicional = 1.5%
            # consideramos "propio_descuento" si tipo_cliente == "propio_descuento"
            return round(base * 0.025, 2)
        elif tipo_cliente == "propio_descuento":
            return round(base * 0.015, 2)
        else:
            # fallback: usar porcentaje guardado en DB (no ideal)
            return round(base * 0.01, 2)

    # comisiones estimadas
    comision_if_discount = comision_para_base(valor_base_if_discount, True)
    comision_no_discount = comision_para_base(valor_base_no_discount, False)

    # calcular valores reales si hay fecha_pago_real
    valor_base_real = None
    comision_real = None
    mes_pago_comision = None

    if fecha_pago_real and fecha_factura:
        # días entre factura y pago
        dias = (fecha_pago_real - fecha_factura).days
        # decidir si aplica descuento
        if tiene_descuento_fac:
            valor_base_real = valor_base_if_discount
        else:
            # aplica descuento sólo si dias dentro del rango
            if rango_ini <= dias <= rango_fin:
                valor_base_real = valor_base_if_discount
            else:
                valor_base_real = valor_base_no_discount

        # calcular comision real
        # si tipo cliente es propio pero tiene descuento aplicado a pie de factura o se aplicó descuento en base, la regla cambia:
        if tipo_cliente == "propio" and tiene_descuento_fac:
            # si cliente es propio y hay descuento a pie, la regla que acordaste es 1.5%? (tu regla: cliente mio + descuento adicional -> 1.5%)
            # sin embargo definimos "propio_descuento" como tipo distinto; si aqui se usa tipo "propio" + tiene_descuento_fac == True, asumimos 1.5
            comision_real = round(valor_base_real * 0.015, 2)
        else:
            comision_real = comision_para_base(valor_base_real, tiene_descuento_fac)

        # mes pago comision = mes (fecha_pago_real) + 1 mes (mes vencido)
        pago_dt = fecha_pago_real
        mes_pago_dt = add_one_month(pago_dt)
        mes_pago_comision = mes_pago_dt.strftime("%Y-%m")
    else:
        # no hay fecha pago real -> no hay comision real aún
        valor_base_real = None
        comision_real = None

    return {
        "valor_base_real": valor_base_real,
        "comision_real": comision_real,
        "valor_base_if_discount": valor_base_if_discount,
        "comision_if_discount": comision_if_discount,
        "valor_base_no_discount": valor_base_no_discount,
        "comision_no_discount": comision_no_discount,
        "mes_pago_comision": mes_pago_comision,
    }


# ========================
# Registrar venta
# ========================
def registrar_venta_view():
    st.header("➕ Registrar Venta")
    with st.form("form_registrar"):
        pedido = st.text_input("Pedido")
        cliente = st.text_input("Cliente")
        factura = st.text_input("Factura")
        valor = st.number_input("Valor (base, antes de IVA)", min_value=0.0, step=1000.0)
        devoluciones = st.number_input("Devoluciones (si aplica)", min_value=0.0, step=100.0, value=0.0)
        tipo_cliente = st.selectbox("Tipo de cliente", ["no_propio", "propio", "propio_descuento"])
        tiene_descuento_fac = st.checkbox("¿Trae descuento a pie de factura (15%)?", value=False)
        porcentaje_descuento = st.number_input("Porcentaje descuento (si aplica)", value=15.0, min_value=0.0, max_value=100.0, step=0.5)
        rango_ini = st.number_input("Rango inicio días para descuento", value=35, min_value=0)
        rango_fin = st.number_input("Rango fin días para descuento", value=45, min_value=0)
        condicion_especial = st.selectbox("Condición especial (plazo 60 días)?", ["No", "Sí"])
        fecha_pedido = st.date_input("Fecha pedido", value=date.today())
        fecha_factura = st.date_input("Fecha factura", value=date.today())

        submit = st.form_submit_button("Registrar venta")

    if submit:
        try:
            # fechas estimadas según plazo
            dias_inicio = rango_ini
            dias_fin = rango_fin
            if condicion_especial == "Sí":
                dias_inicio = 60
                dias_fin = 60

            fecha_pago_est = fecha_factura + timedelta(days=dias_inicio)
            fecha_pago_max = fecha_factura + timedelta(days=dias_fin)

            payload = {
                "pedido": pedido,
                "cliente": cliente,
                "factura": factura,
                "valor": valor,
                "devoluciones": devoluciones,
                "tipo_cliente": tipo_cliente,
                "tiene_descuento_fac": tiene_descuento_fac,
                "porcentaje_descuento": porcentaje_descuento,
                "rango_descuento_ini": int(dias_inicio),
                "rango_descuento_fin": int(dias_fin),
                "condicion_especial": (condicion_especial == "Sí"),
                "fecha_pedido": fecha_pedido.isoformat(),
                "fecha_factura": fecha_factura.isoformat(),
                "fecha_pago_est": fecha_pago_est.isoformat(),
                "fecha_pago_max": fecha_pago_max.isoformat(),
                "pagado": False,
                "created_at": datetime.utcnow().isoformat(),
            }

            supabase.table("comisiones").insert(payload).execute()
            st.success("✅ Venta registrada")
        except Exception as e:
            st.error(f"❌ Error registrando venta: {e}")


# ========================
# Listado y edición (Pendientes / Pagadas)
# ========================
def listar_y_editar(pagadas=False):
    title = "✅ Facturas Pagadas" if pagadas else "📂 Facturas Pendientes"
    st.header(title)

    df = cargar_datos()
    if df.empty:
        st.info("No hay registros.")
        return

    # filtrar por pagado
    df_view = df[df["pagado"] == pagadas].copy()

    if df_view.empty:
        st.info("No hay facturas en esta vista.")
        return

    # Añadir cálculos estimados / reales al vuelo
    calc_cols = []
    for idx, row in df_view.iterrows():
        calc = calcular_valor_y_comisiones_row(
            valor=row.get("valor", 0),
            devoluciones=row.get("devoluciones", 0),
            tiene_descuento_fac=row.get("tiene_descuento_fac", False),
            porcentaje_descuento=row.get("porcentaje_descuento", 15.0),
            rango_ini=int(row.get("rango_descuento_ini", 35) or 35),
            rango_fin=int(row.get("rango_descuento_fin", 45) or 45),
            fecha_factura=row.get("fecha_factura"),
            fecha_pago_real=row.get("fecha_pago_real"),
            tipo_cliente=row.get("tipo_cliente", "no_propio"),
        )
        calc_cols.append(calc)

    # anexar columnas calculadas
    df_view = df_view.reset_index(drop=True)
    df_view["valor_base_real"] = [c["valor_base_real"] for c in calc_cols]
    df_view["comision_real"] = [c["comision_real"] for c in calc_cols]
    df_view["valor_base_if_discount"] = [c["valor_base_if_discount"] for c in calc_cols]
    df_view["comision_if_discount"] = [c["comision_if_discount"] for c in calc_cols]
    df_view["valor_base_no_discount"] = [c["valor_base_no_discount"] for c in calc_cols]
    df_view["comision_no_discount"] = [c["comision_no_discount"] for c in calc_cols]
    df_view["mes_pago_comision"] = [c["mes_pago_comision"] for c in calc_cols]

    # Orden sencillo
    df_view = df_view.sort_values(by=["fecha_factura", "cliente"], ascending=[False, True])

    # Mostrar lista y permitir edición por fila
    for _, row in df_view.iterrows():
        st.markdown("---")
        col1, col2, col3 = st.columns([3, 2, 2])
        with col1:
            st.write(f"**Pedido:** {row.get('pedido','')}")
            st.write(f"**Cliente:** {row.get('cliente','')}")
            st.write(f"**Factura:** {row.get('factura','')}")
            st.write(f"**Valor (base):** ${float(row.get('valor') or 0):,.2f}")
            st.write(f"**Devoluciones:** ${float(row.get('devoluciones') or 0):,.2f}")
            if pd.notna(row.get("valor_base_real")):
                st.write(f"**Valor base (real):** ${row['valor_base_real']:,.2f}")
                st.write(f"**Comisión (real):** ${row['comision_real']:,.2f}")
            else:
                st.write(f"**Valor base (estimado - si aplica descuento):** ${row['valor_base_if_discount']:,.2f}")
                st.write(f"**Comisión estimada (si aplica):** ${row['comision_if_discount']:,.2f}")
        with col2:
            st.write(f"📅 Fecha factura: {row['fecha_factura'] if pd.notna(row['fecha_factura']) else 'N/A'}")
            st.write(f"⏳ Fecha máxima pago: {row['fecha_pago_max'] if pd.notna(row['fecha_pago_max']) else 'N/A'}")
            st.write(f"📅 Fecha pago real: {row['fecha_pago_real'] if pd.notna(row['fecha_pago_real']) else 'N/A'}")
            st.write(f"Tipo cliente: {row.get('tipo_cliente','no_propio')}")
            st.write(f"Descuento a pie: {'Sí' if row.get('tiene_descuento_fac') else 'No'}")
        with col3:
            # comprobante link si existe
            if row.get("comprobante_url"):
                st.markdown(f"[🔗 Ver comprobante]({row.get('comprobante_url')})")

            # editar
            with st.expander("✏️ Editar"):
                with st.form(f"edit_{int(row['id'])}"):
                    v_valor = st.number_input("Valor", value=float(row.get("valor") or 0.0), key=f"valor_{row['id']}")
                    v_devol = st.number_input("Devoluciones", value=float(row.get("devoluciones") or 0.0), key=f"dev_{row['id']}")
                    v_tipo = st.selectbox("Tipo cliente", ["no_propio", "propio", "propio_descuento"], index=["no_propio", "propio", "propio_descuento"].index(row.get("tipo_cliente","no_propio")), key=f"tipo_{row['id']}")
                    v_desc_pie = st.checkbox("Descuento a pie (15%)", value=bool(row.get("tiene_descuento_fac")), key=f"pie_{row['id']}")
                    v_porcentaje_desc = st.number_input("Porcentaje descuento (%)", value=float(row.get("porcentaje_descuento") or 15.0), key=f"pdesc_{row['id']}")
                    v_rango_ini = st.number_input("Rango inicio días", value=int(row.get("rango_descuento_ini") or 35), key=f"rini_{row['id']}")
                    v_rango_fin = st.number_input("Rango fin días", value=int(row.get("rango_descuento_fin") or 45), key=f"rfin_{row['id']}")
                    v_pagado = st.checkbox("Marcar como pagado", value=bool(row.get("pagado")), key=f"pag_{row['id']}")
                    v_fecha_pago_real = st.date_input("Fecha pago real", value=(row.get("fecha_pago_real") if pd.notna(row.get("fecha_pago_real")) else date.today()), key=f"fpr_{row['id']}")
                    comprobante_file = st.file_uploader("Subir comprobante (opcional)", type=["pdf","jpg","png"], key=f"file_{row['id']}")
                    submit_row = st.form_submit_button("Guardar cambios")

                if submit_row:
                    try:
                        # calcular valores
                        calc = calcular_valor_y_comisiones_row(
                            valor=v_valor,
                            devoluciones=v_devol,
                            tiene_descuento_fac=v_desc_pie,
                            porcentaje_descuento=v_porcentaje_desc,
                            rango_ini=int(v_rango_ini),
                            rango_fin=int(v_rango_fin),
                            fecha_factura=row.get("fecha_factura"),
                            fecha_pago_real=v_fecha_pago_real if v_pagado else None,
                            tipo_cliente=v_tipo,
                        )

                        # subir comprobante si hay
                        comprobante_url = row.get("comprobante_url")
                        comprobante_file_name = row.get("comprobante_file")
                        if comprobante_file is not None:
                            try:
                                file_bytes = comprobante_file.read()
                            except Exception:
                                file_bytes = comprobante_file.getbuffer()

                            # generar nombre
                            factura_num = str(row.get("factura") or row.get("pedido") or int(row["id"]))
                            ext = str(comprobante_file.name).split(".")[-1]
                            fname = f"{factura_num}.{ext}"
                            path = f"{BUCKET}/{fname}"
                            try:
                                supabase.storage.from_(BUCKET).upload(path, file_bytes, {"content-type": comprobante_file.type, "x-upsert": "true"})
                                public_url = safe_get_public_url(BUCKET, path)
                                if public_url:
                                    comprobante_url = public_url
                                    comprobante_file_name = fname
                                else:
                                    st.warning("No se pudo obtener URL pública del comprobante.")
                            except Exception as e:
                                st.warning(f"No fue posible subir comprobante: {e}")

                        # preparar payload de update (incluimos valores calculados para comodidad)
                        update_payload = {
                            "valor": v_valor,
                            "devoluciones": v_devol,
                            "tipo_cliente": v_tipo,
                            "tiene_descuento_fac": v_desc_pie,
                            "porcentaje_descuento": v_porcentaje_desc,
                            "rango_descuento_ini": int(v_rango_ini),
                            "rango_descuento_fin": int(v_rango_fin),
                            "pagado": bool(v_pagado),
                            "fecha_pago_real": v_fecha_pago_real.isoformat() if v_pagado else None,
                            "valor_base": calc["valor_base_real"] if calc["valor_base_real"] is not None else None,
                            "comision": calc["comision_real"] if calc["comision_real"] is not None else None,
                            "comprobante_url": comprobante_url,
                            "comprobante_file": comprobante_file_name,
                            "updated_at": datetime.utcnow().isoformat(),
                        }

                        supabase.table("comisiones").update(update_payload).eq("id", int(row["id"])).execute()
                        st.success("✅ Factura actualizada")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"❌ Error actualizando factura: {e}")


# ========================
# Dashboard (con mes vencido)
# ========================
def dashboard_view():
    st.header("📈 Dashboard de Comisiones (Mes vencido)")

    df = cargar_datos()
    if df.empty:
        st.info("No hay datos.")
        return

    # calcular para cada fila
    rows_calc = []
    for _, row in df.iterrows():
        calc = calcular_valor_y_comisiones_row(
            valor=row.get("valor", 0),
            devoluciones=row.get("devoluciones", 0),
            tiene_descuento_fac=row.get("tiene_descuento_fac", False),
            porcentaje_descuento=row.get("porcentaje_descuento", 15.0),
            rango_ini=int(row.get("rango_descuento_ini", 35) or 35),
            rango_fin=int(row.get("rango_descuento_fin", 45) or 45),
            fecha_factura=row.get("fecha_factura"),
            fecha_pago_real=row.get("fecha_pago_real"),
            tipo_cliente=row.get("tipo_cliente", "no_propio"),
        )
        rows_calc.append(calc)

    df = df.reset_index(drop=True)
    df["valor_base_real"] = [c["valor_base_real"] for c in rows_calc]
    df["comision_real"] = [c["comision_real"] for c in rows_calc]
    df["valor_base_if_discount"] = [c["valor_base_if_discount"] for c in rows_calc]
    df["comision_if_discount"] = [c["comision_if_discount"] for c in rows_calc]
    df["valor_base_no_discount"] = [c["valor_base_no_discount"] for c in rows_calc]
    df["comision_no_discount"] = [c["comision_no_discount"] for c in rows_calc]
    df["mes_pago_comision"] = [c["mes_pago_comision"] for c in rows_calc]

    # Mes actual (YYYY-MM)
    hoy = date.today()
    mes_actual = hoy.strftime("%Y-%m")

    # Comisiones que se van a recibir en el mes actual (mes_pago_comision == mes_actual)
    comisiones_a_recibir_mes_actual = df[df["mes_pago_comision"] == mes_actual]["comision_real"].sum(skipna=True)

    # Comisiones ya liquidadas (todos los registros con comision_real no nulo)
    comisiones_liquidadas_total = df["comision_real"].sum(skipna=True)

    # Pendientes (sin fecha_pago_real) => estimaciones optimista/pesimista
    pendientes = df[df["fecha_pago_real"].isna()]
    est_opt = pendientes["comision_if_discount"].sum(skipna=True)
    est_pes = pendientes["comision_no_discount"].sum(skipna=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Comisión a recibir este mes (mes vencido)", f"${comisiones_a_recibir_mes_actual:,.2f}")
    col2.metric("Comisiones liquidadas (total)", f"${comisiones_liquidadas_total:,.2f}")
    col3.metric("Estimación pendientes (opt / pes)", f"${est_opt:,.2f} / ${est_pes:,.2f}")

    st.subheader("Detalle por cliente (Comisión real + estimaciones)")
    resumen = df.groupby("cliente").agg(
        total_valor=("valor", "sum"),
        comision_real_sum=("comision_real", lambda s: round(s.sum(skipna=True),2)),
        comision_estim_opt=("comision_if_discount", lambda s: round(s.sum(skipna=True),2)),
        comision_estim_pes=("comision_no_discount", lambda s: round(s.sum(skipna=True),2))
    ).reset_index().sort_values("comision_real_sum", ascending=False)

    st.dataframe(resumen, use_container_width=True)


# ========================
# Navegación principal
# ========================
def main():
    st.title("📊 Gestión de Comisiones")
    menu = st.sidebar.radio("Menú", ["Registrar Venta", "Pendientes", "Pagadas", "Dashboard"])

    if menu == "Registrar Venta":
        registrar_venta_view()
    elif menu == "Pendientes":
        listar_y_editar(pagadas=False)
    elif menu == "Pagadas":
        listar_y_editar(pagadas=True)
    elif menu == "Dashboard":
        dashboard_view()


if __name__ == "__main__":
    main()
