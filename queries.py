import pandas as pd

# ========================
# Obtener facturas
# ========================
def get_facturas_pendientes(supabase):
    response = supabase.table("comisiones").select("*").eq("pagado", False).execute()
    data = response.data or []
    return pd.DataFrame(data)


def get_facturas_pagadas(supabase):
    response = supabase.table("comisiones").select("*").eq("pagado", True).execute()
    data = response.data or []
    return pd.DataFrame(data)


# ========================
# Insertar nueva factura
# ========================
def insert_factura(supabase, data):
    supabase.table("comisiones").insert(data).execute()


# ========================
# Actualizar factura
# ========================
def update_factura(supabase, factura_id, data):
    supabase.table("comisiones").update(data).eq("id", factura_id).execute()
