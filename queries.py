import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE = "comisiones"

# ==============================================
# Insertar Factura
# ==============================================
def insertar_factura(numero, cliente, valor_neto, fecha_factura, tiene_descuento):
    data = {
        "numero": numero,
        "cliente": cliente,
        "valor_neto": valor_neto,
        "fecha_factura": str(fecha_factura),
        "tiene_descuento": tiene_descuento,
        "estado": "pendiente",
        "comision": calcular_comision(valor_neto, tiene_descuento, fecha_factura),
    }
    supabase.table(TABLE).insert(data).execute()

# ==============================================
# Calcular Comisión
# ==============================================
def calcular_comision(valor_neto, tiene_descuento, fecha_factura):
    # Ejemplo: si tiene descuento no cambia nada,
    # si no, entonces la lógica de 35-45 días o >46 días
    # Por simplicidad dejamos 10% de comisión base
    return valor_neto * 0.10

# ==============================================
# Obtener todas las facturas
# ==============================================
def get_all_facturas():
    res = supabase.table(TABLE).select("*").execute()
    if res.data:
        return pd.DataFrame(res.data)
    return pd.DataFrame()

# ==============================================
# Actualizar factura
# ==============================================
def update_factura(id_factura, cliente, valor_neto, fecha_factura, tiene_descuento, comprobante_url=None):
    data = {
        "cliente": cliente,
        "valor_neto": valor_neto,
        "fecha_factura": str(fecha_factura),
        "tiene_descuento": tiene_descuento,
    }
    if comprobante_url:
        data["comprobante_url"] = comprobante_url
    supabase.table(TABLE).update(data).eq("id", id_factura).execute()

# ==============================================
# Marcar factura como pagada
# ==============================================
def marcar_factura_pagada(id_factura):
    supabase.table(TABLE).update({"estado": "pagada"}).eq("id", id_factura).execute()
