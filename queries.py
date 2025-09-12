import pandas as pd
from utils import supabase


def get_all_comisiones():
    try:
        response = supabase.table("comisiones").select("*").execute()
        data = response.data
        if data:
            return pd.DataFrame(data)
        return pd.DataFrame()
    except Exception as e:
        print("Error obteniendo comisiones:", e)
        return pd.DataFrame()


def insert_comision(data: dict):
    try:
        supabase.table("comisiones").insert(data).execute()
    except Exception as e:
        print("Error insertando comision:", e)


def update_comision(factura_id: int, data: dict):
    try:
        supabase.table("comisiones").update(data).eq("id", factura_id).execute()
    except Exception as e:
        print("Error actualizando comision:", e)
