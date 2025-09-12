# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
from utils import upload_comprobante, safe_get_public_url, supabase
from queries import obtener_facturas, insertar_factura, actualizar_factura, marcar_pagada_con_comprobante

st.set_page_config(page_title="Gestión de Comisiones", layout="wide")

# ---------- Helpers internos ----------
def safe_col(df: pd.DataFrame, col: str, default):
    """Devuelve la columna si existe o una serie con valor default."""
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def format_money(v):
    try:
        return f"${v:,.0f}"
    except Exception:
        return str(v)


# ---------- UI Sections ----------
def dashboard_view(df: pd.DataFrame):
    st.header("📈 Dashboard")

    if df.empty:
        st.info("No hay datos para mostrar en el dashboard.")
        return

    # asegurar fecha_factura y comision, valor
    if "fecha_factura" in df.columns:
        df["mes"] = df["fecha_factura"].dt.to_period("M").astype(str)
    else:
        df["mes"] = "sin_fecha"

    total_ventas = safe_col(df, "valor", 0).sum()
    total_comisiones = safe_col(df, "comision", 0).sum()
    total_pagadas = int(safe_col(df, "pagado", False).sum())
    total_pendientes = len(df) - total_pagadas

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💵 Total Ventas Netas", format_money(total_ventas))
    c2.metric("🏦 Total Comisiones", format_money(total_comisiones))
    c3.metric("✅ Facturas Pagadas", str(total_pagadas))
    c4.metric("⏳ Facturas Pendientes", str(total_pendientes))

    st.markdown("---")
    st.subheader("🏆 Ranking de clientes (ventas netas acumuladas por mes)")

    # Agrupar por cliente y mes y calcular acumulado progresivo por cliente
    if "cliente" not in df.columns:
        st.info("No hay columna 'cliente' en los datos.")
    else:
        # pivot: filas=mes, columnas=cliente, valores=sum(valor)
        pivot = df.groupby(["mes", "cliente"])["valor"].sum().reset_index()
        # construir acumulado por cliente mes a mes
        pivot_sorted = pivot.sort_values("mes")
        # create a DataFrame where index months, columns clients, values cumulative
        months = sorted(pivot_sorted["mes"].unique())
        clients = sorted(pivot_sorted["cliente"].unique())
        accum = pd.DataFrame(0, index=months, columns=clients)
        for m in months:
            row = pivot_sorted[pivot_sorted["mes"] == m]
            for _, r in row.iterrows():
                accum.loc[m, r["cliente"]] += r["valor"]
            # cumulative
            if months.index(m) > 0:
                accum.loc[m] = accum.loc[m] + accum.loc[months[months.index(m)-1]]

        # melt for plotly
        accum_reset = accum.reset_index().melt(id_vars="index", var_name="cliente", value_name="ventas_acumuladas")
        accum_reset.rename(columns={"index": "mes"}, inplace=True)
        fig_bar = px.bar(accum_reset, x="mes", y="ventas_acumuladas", color="cliente",
                         title="Ventas netas acumuladas por cliente (progresivo mes a mes)",
                         labels={"ventas_acumuladas": "Ventas acumuladas", "mes": "Mes"})
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Evolución de comisiones (mensual)")
    # Line of commissions per month
    comm = df.groupby("mes")["comision"].sum().reset_index() if "mes" in df.columns else pd.DataFrame()
    if comm.empty:
        st.info("No hay datos de comisiones por mes.")
    else:
        fig_line = px.area(comm.sort_values("mes"), x="mes", y="comision",
                           title="Evolución mensual de comisiones",
                           labels={"comision": "Comisiones", "mes": "Mes"})
        st.plotly_chart(fig_line, use_container_width=True)


def render_invoice_card(row: pd.Series, allow_edit=True):
    """Muestra la 'card' de la factura y retorna si el usuario pulsó editar."""
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    with col1:
        st.markdown(f"**Factura:** {row.get('factura', 'N/A')}")
        st.write(f"**Cliente:** {row.get('cliente', '')}")
        st.write(f"**Pedido:** {row.get('pedido', '')}")
        st.write(f"**Valor:** {format_money(row.get('valor', 0))}")
        st.write(f"**Comisión:** {format_money(row.get('comision', 0))}")
        if row.get("fecha_factura") is not None:
            st.write(f"**Fecha factura:** {row.get('fecha_factura').date() if hasattr(row.get('fecha_factura'), 'date') else row.get('fecha_factura')}")
        if row.get("pagado"):
            if row.get("comprobante_url"):
                st.markdown(f"[🔗 Ver comprobante]({row.get('comprobante_url')})")
    with col2:
        if allow_edit:
            return st.button("✏️ Editar", key=f"edit_{row.get('id')}")
        else:
            return False


def invoices_view(df: pd.DataFrame, pagadas: bool):
    title = "Facturas Pagadas" if pagadas else "Facturas Pendientes"
    st.header(f"📂 {title}")

    if df.empty:
        st.info("No hay facturas registradas.")
        return

    # filter pagado column (boolean) — tolerate missing column
    if "pagado" in df.columns:
        sub = df[df["pagado"] == True] if pagadas else df[df["pagado"] == False]
    else:
        # If 'pagado' doesn't exist treat all as pendientes if pagadas==False
        sub = pd.DataFrame() if pagadas else df.copy()

    if sub.empty:
        st.info("No hay facturas en este estado.")
        return

    # Optionally filter by month selection
    if "mes_global" in st.session_state and st.session_state["mes_global"] != "Todos" and "mes" in sub.columns:
        sub = sub[sub["mes"] == st.session_state["mes_global"]]

    # Render each as a card
    for _, row in sub.iterrows():
        edit_pressed = render_invoice_card(row, allow_edit=True)
        if edit_pressed:
            # show edit form in an expander to avoid immediate rerun
            with st.expander(f"Editar factura {row.get('factura')}"):
                with st.form(f"form_edit_{row.get('id')}"):
                    new_factura = st.text_input("Factura", value=str(row.get("factura", "")))
                    new_pedido = st.text_input("Pedido", value=str(row.get("pedido", "")))
                    new_cliente = st.text_input("Cliente", value=str(row.get("cliente", "")))
                    new_valor = st.number_input("Valor", value=float(row.get("valor", 0.0)))
                    new_porcentaje = st.number_input("Porcentaje comisión (%)", value=float(row.get("porcentaje", row.get("comision", 0) / (row.get("valor",1)) * 100 if row.get("valor",0) else 0)))
                    # fecha pago real (optional)
                    fecha_pago_real = None
                    try:
                        if row.get("fecha_pago_real") is not None and not pd.isna(row.get("fecha_pago_real")):
                            fecha_pago_real = st.date_input("Fecha Pago Real", value=row.get("fecha_pago_real").date())
                        else:
                            fecha_pago_real = st.date_input("Fecha Pago Real", value=date.today())
                    except Exception:
                        fecha_pago_real = st.date_input("Fecha Pago Real", value=date.today())

                    comprobante_file = st.file_uploader("Subir comprobante (jpg/png/pdf)", key=f"file_{row.get('id')}")
                    submit = st.form_submit_button("Guardar")

                    if submit:
                        # prepare update
                        new_comision = round(new_valor * (new_porcentaje / 100), 2)
                        updates = {
                            "factura": new_factura,
                            "pedido": new_pedido,
                            "cliente": new_cliente,
                            "valor": new_valor,
                            "porcentaje": new_porcentaje,
                            "comision": new_comision
                        }
                        # handle comprobante upload
                        if comprobante_file:
                            path = upload_comprobante(new_factura, comprobante_file, folder="")
                            if path:
                                public_url = safe_get_public_url(path)
                                # mark pagado + save url + fecha_pago_real
                                updates["comprobante_url"] = public_url
                                updates["pagado"] = True
                                updates["fecha_pago_real"] = pd.to_datetime(fecha_pago_real).isoformat()
                                # update in DB
                                marcar_pagada_con_comprobante(int(row.get("id")), public_url)
                                st.success("Comprobante subido y factura marcada como pagada.")
                            else:
                                st.error("Error subiendo comprobante.")
                                # still save other updates
                                actualizar_factura(int(row.get("id")), updates)
                                st.success("Cambios guardados (sin comprobante).")
                        else:
                            # if user didn't upload file but updated values, just update fields
                            if fecha_pago_real:
                                updates["fecha_pago_real"] = pd.to_datetime(fecha_pago_real).isoformat()
                            actualizar_factura(int(row.get("id")), updates)
                            st.success("Cambios guardados.")
                        st.experimental_rerun()


def alerts_view(df: pd.DataFrame):
    st.header("⚠️ Alertas")
    if df.empty:
        st.info("No hay facturas registradas.")
        return
    # identify overdue: unpaid and fecha_pago_max or fecha_factura+dias
    now = pd.to_datetime(date.today())
    df2 = df.copy()
    # Prefer fecha_pago_max if exists, else compute from fecha_factura + 45 days
    if "fecha_pago_max" in df2.columns:
        df2["fecha_pago_max_dt"] = pd.to_datetime(df2["fecha_pago_max"], errors="coerce")
    else:
        if "fecha_factura" in df2.columns:
            df2["fecha_pago_max_dt"] = pd.to_datetime(df2["fecha_factura"], errors="coerce") + pd.Timedelta(days=45)
        else:
            df2["fecha_pago_max_dt"] = pd.NaT

    overdue = df2[(df2.get("pagado", False) == False) & (df2["fecha_pago_max_dt"].notna()) & (df2["fecha_pago_max_dt"] <= now)]
    if overdue.empty:
        st.success("✅ No hay facturas próximas a vencerse o vencidas.")
        return

    for _, r in overdue.iterrows():
        st.markdown("---")
        st.subheader(f"Factura {r.get('factura')} — {r.get('cliente')}")
        st.write(f"Valor: {format_money(r.get('valor',0))}")
        st.write(f"Vencimiento: {r.get('fecha_pago_max_dt').date() if not pd.isna(r.get('fecha_pago_max_dt')) else 'N/A'}")
        if r.get("comprobante_url"):
            st.markdown(f"[🔗 Ver comprobante]({r.get('comprobante_url')})")


# ---------- APP entry ----------
def main():
    st.title("📊 Gestión de Comisiones (v2)")

    # obtener facturas
    df = obtener_facturas()

    # normalize df if None
    if df is None:
        df = pd.DataFrame()

    # create month filter dropdown
    if not df.empty and "fecha_factura" in df.columns:
        df["mes"] = df["fecha_factura"].dt.to_period("M").astype(str)
        months = ["Todos"] + sorted(df["mes"].dropna().unique().tolist())
    else:
        months = ["Todos"]
        df["mes"] = None

    if "mes_global" not in st.session_state:
        st.session_state["mes_global"] = "Todos"

    st.sidebar.markdown("### Filtros")
    st.session_state["mes_global"] = st.sidebar.selectbox("Filtrar por mes (fecha_factura)", months, index=months.index(st.session_state["mes_global"]) if st.session_state["mes_global"] in months else 0)

    menu = st.sidebar.radio("Navegación", ["Dashboard", "Facturas Pendientes", "Facturas Pagadas", "Alertas", "Registrar Factura"])

    if menu == "Dashboard":
        dashboard_view(df)
    elif menu == "Facturas Pendientes":
        invoices_view(df, pagadas=False)
    elif menu == "Facturas Pagadas":
        invoices_view(df, pagadas=True)
    elif menu == "Alertas":
        alerts_view(df)
    elif menu == "Registrar Factura":
        st.header("📝 Registrar Factura")
        with st.form("form_registrar"):
            pedido = st.text_input("Pedido")
            cliente = st.text_input("Cliente")
            factura = st.text_input("Factura")
            valor = st.number_input("Valor (neto)", min_value=0.0, step=1000.0)
            porcentaje = st.number_input("Porcentaje comisión (%)", min_value=0.0, max_value=100.0, step=0.1, value=10.0)
            fecha_factura = st.date_input("Fecha factura", value=date.today())
            condicion_especial = st.selectbox("Condición especial?", ["No","Sí"])
            tiene_descuento = st.selectbox("Descuento a pie de factura?", ["No","Sí"])
            submit = st.form_submit_button("Registrar")

        if submit:
            try:
                record = {
                    "pedido": pedido,
                    "cliente": cliente,
                    "factura": factura,
                    "valor": float(valor),
                    "porcentaje": float(porcentaje),
                    "comision": round(float(valor) * (float(porcentaje) / 100), 2),
                    "fecha_factura": pd.to_datetime(fecha_factura).isoformat(),
                    "condicion_especial": True if condicion_especial == "Sí" else False,
                    # try to be compatible with multiple possible column names
                    "tiene_descuento_factura": True if tiene_descuento == "Sí" else False,
                    "descuento_factura": True if tiene_descuento == "Sí" else False,
                    "pagado": False
                }
                insertar_factura(record)
                st.success("Factura registrada ✅")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error registrando factura: {e}")


if __name__ == "__main__":
    main()
