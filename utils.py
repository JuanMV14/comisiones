from datetime import date

# ========================
# Cálculo de días de pago
# ========================
def calcular_dias_pago(fecha_factura, fecha_pago):
    if not fecha_factura or not fecha_pago:
        return None
    if isinstance(fecha_factura, str):
        fecha_factura = date.fromisoformat(fecha_factura)
    if isinstance(fecha_pago, str):
        fecha_pago = date.fromisoformat(fecha_pago)
    return (fecha_pago - fecha_factura).days


# ========================
# Cálculo de comisión
# ========================
def calcular_comision(valor, porcentaje, tiene_descuento_factura, dias_pago=None):
    """
    Regla:
    - Si tiene descuento a pie de factura → comisión normal sobre valor.
    - Si NO tiene descuento:
        - Pago entre 35 y 45 días → aplica 15% de descuento sobre valor.
        - Pago desde 46 días → comisión sobre el valor pleno.
    """
    if dias_pago is None:  # registrar venta (sin fecha de pago aún)
        base = valor
    else:
        if tiene_descuento_factura:
            base = valor
        else:
            if 35 <= dias_pago <= 45:
                base = valor * 0.85  # descuento 15%
            else:
                base = valor

    return round(base * (porcentaje / 100), 2)
