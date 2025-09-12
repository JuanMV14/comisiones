import pandas as pd
from datetime import datetime, timedelta

# ========================
# Funciones auxiliares
# ========================

def process_dataframe(data):
    if not data or not data.data:
        return pd.DataFrame()

    df = pd.DataFrame(data.data)

    if "id" not in df.columns:
        df["id"] = None

    for col in ["fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "fecha_factura" in df.columns:
        df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
    else:
        df["mes_factura"] = None

    return df


def calcular_fechas_pago(fecha_factura, condicion_especial):
    dias_pago = 60 if condicion_especial else 35
    dias_max = 60 if condicion_especial else 45

    fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
    fecha_pago_max = fecha_factura + timedelta(days=dias_max)

    return fecha_pago_est, fecha_pago_max


def calcular_comision(valor, porcentaje, tiene_descuento, fecha_pago_real=None, fecha_factura=None, devoluciones=0):
    """
    Regla de negocio:
    - Si tiene descuento a pie de factura → comisión normal sobre valor - devoluciones
    - Si NO tiene descuento:
        - Pago entre 35 y 45 días → aplica 15% descuento adicional
        - Pago desde día 46 en adelante → sin descuento
    """
    base = max(valor - devoluciones, 0)

    if tiene_descuento:
        return base * (porcentaje / 100)

    # Cliente SIN descuento
    if fecha_pago_real and fecha_factura:
        dias = (fecha_pago_real - fecha_factura).days
        if 35 <= dias <= 45:
            base = base * 0.85  # descuento 15%
    return base * (porcentaje / 100)
