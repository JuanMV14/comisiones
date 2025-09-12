# queries.py
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, date

from utils import supabase  # importa el cliente compartido

TABLE = "comisiones"


def obtener_facturas() -> pd.DataFrame:
    """
    Retorna un DataFrame con las filas de la tabla comisiones.
    En caso de error o sin datos, retorna DataFrame() (vacío).
    """
    try:
        response = supabase.table(TABLE).select("*").execute()
        data = response.data
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)

        # Normalizar columnas de fecha a datetime donde existan
        for col in ["fecha_factura", "fecha_pago_real", "fecha_pago", "fecha_pago_est", "fecha_pago_max"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")
        return df
    except Exception as e:
        print("Error obtener_facturas:", e)
        return pd.DataFrame()


def insertar_factura(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Inserta una nueva fila. record es un dict con las claves necesarias.
    Devuelve la respuesta.data (registro insertado) o None si falla.
    """
    try:
        resp = supabase.table(TABLE).insert(record).execute()
        return resp.data
    except Exception as e:
        print("Error insertar_factura:", e)
        return None


def actualizar_factura(factura_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Actualiza la fila por id (actualizaciones parciales).
    """
    try:
        resp = supabase.table(TABLE).update(updates).eq("id", factura_id).execute()
        return resp.data
    except Exception as e:
        print("Error actualizar_factura:", e)
        return None


def marcar_pagada_con_comprobante(factura_id: int, public_url: str) -> Optional[Dict[str, Any]]:
    """
    Marca la factura como pagada, pone fecha_pago_real y guarda comprobante_url.
    """
    try:
        updates = {
            "pagado": True,
            "fecha_pago_real": datetime.now().isoformat(),
            "comprobante_url": public_url
        }
        resp = supabase.table(TABLE).update(updates).eq("id", factura_id).execute()
        return resp.data
    except Exception as e:
        print("Error marcar_pagada_con_comprobante:", e)
        return None
