import pandas as pd
from datetime import date

# ========================
# Consultar facturas
# ========================
def obtener_facturas(supabase):
    response = supabase.table("comisiones").select("*").execute()
    data = response.data

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Asegurar que fecha_factura esté como datetime
    if "fecha_factura" in df.columns:
        df["fecha_factura"] = pd.to_datetime(df["fecha_factura"], errors="coerce").dt.date

    return df


# ========================
# Insertar factura
# ========================
def insertar_factura(supabase, nueva_factura: dict):
    supabase.table("comisiones").insert(nueva_factura).execute()


# ========================
# Marcar como pagada
# ========================
def marcar_factura_pagada(supabase, factura_id: int, comprobante_url: str):
    hoy = date.today().isoformat()
    supabase.table("comisiones").update({
        "pagado": True,
        "fecha_pago_real": hoy,
        "comprobante_url": comprobante_url
    }).eq("id", factura_id).execute()
