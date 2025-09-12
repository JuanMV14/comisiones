import streamlit as st
import pandas as pd
from datetime import datetime

from queries import update_factura

# ========================
# Cálculo de comisión
# ========================
def calcular_comision(
    valor_base,
    porcentaje,
    fecha_factura,
    fecha_pago,
    tiene_descuento,
    porcentaje_descuento=15,
    rango_ini=35,
    rango_fin=45,
):
    comision_inicial = valor_base * (porcentaje / 100)

    if tiene_descuento:
        # Cliente con descuento a pie de factura → comisión directa
        return round(comision_inicial, 2)

    dias = (fecha_pago - fecha_factura).days
    if rango_ini <= dias <= rango_fin:
        valor_ajustado = valor_base * (1 - porcentaje_descuento / 100)
    elif dias > rango_fin:
        valor_ajustado = valor_base
    else:
        valor_ajustado = 0

    return round(comision_inicial * (valor_ajustado / valor_base), 2)


# ========================
# Renderizar tablas
# ========================
def render_table(df: pd.DataFrame, supabase, editable=False):
    if editable:
        edited_df = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{df.shape[0]}",
        )

        if st.button("💾 Guardar cambios", key=f"save_{df.shape[0]}"):
            for i, row in edited_df.iterrows():
                try:
                    fecha_factura = (
                        datetime.strptime(row["fecha_factura"], "%Y-%m-%d").date()
                        if isinstance(row["fecha_factura"], str)
                        else row["fecha_factura"]
                    )
                    fecha_pago_real = (
                        datetime.strptime(row["fecha_pago_real"], "%Y-%m-%d").date()
                        if isinstance(row["fecha_pago_real"], str)
                        else row["fecha_pago_real"]
                    )

                    comision = calcular_comision(
                        row["valor_base"],
                        row["porcentaje"],
                        fecha_factura,
                        fecha_pago_real or fecha_factura,
                        row["tiene_descuento_factura"],
                        row.get("porcentaje_descuento", 15),
                        row.get("rango_descuento_ini", 35),
                        row.get("rango_descuento_fin", 45),
                    )

                    row_dict = row.to_dict()
                    row_dict["comision"] = comision

                    update_factura(supabase, row["id"], row_dict)

                except Exception as e:
                    st.error(f"Error al guardar factura {row['id']}: {e}")

            st.success("✅ Cambios guardados correctamente")
    else:
        st.dataframe(df, use_container_width=True)


# ========================
# Dashboard
# ========================
def mostrar_dashboard(facturas_pend, facturas_pag):
    total_pendientes = facturas_pend["valor"].sum() if not facturas_pend.empty else 0
    total_pagadas = facturas_pag["valor"].sum() if not facturas_pag.empty else 0
    comisiones_pend = facturas_pend["comision"].sum() if not facturas_pend.empty else 0
    comisiones_pag = facturas_pag["comision"].sum() if not facturas_pag.empty else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("💵 Pendiente por Cobrar", f"${total_pendientes:,.0f}")
    col2.metric("✅ Cobrado", f"${total_pagadas:,.0f}")
    col3.metric("🕒 Comisión Pendiente", f"${comisiones_pend:,.0f}")
    col4.metric("🏦 Comisión Pagada", f"${comisiones_pag:,.0f}")
