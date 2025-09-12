import pandas as pd
from supabase import Client

def cargar_datos(supabase: Client):
    """Carga todas las comisiones desde Supabase y retorna un DataFrame limpio."""
    try:
        data = supabase.table("comisiones").select("*").execute()
        if not data.data:
            return pd.DataFrame()
        df = pd.DataFrame(data.data)

        # Columnas obligatorias
        for col in ["id", "referencia", "comprobante_url", "comprobante_file", "pagado"]:
            if col not in df.columns:
                df[col] = None if col == "id" else "" if "url" in col or "file" in col or "referencia" in col else False

        # Fechas
        for col in ["fecha", "fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real", "fecha_pago"]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Mes de factura
        if "fecha_factura" in df.columns:
            df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
        else:
            df["mes_factura"] = None

        return df
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return pd.DataFrame()

def insertar_venta(supabase: Client, data: dict):
    """Inserta una nueva venta en Supabase."""
    try:
        supabase.table("comisiones").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error insertando venta: {e}")
        return False

def actualizar_factura(supabase: Client, factura_id: int, updates: dict):
    """Actualiza los datos de una factura en Supabase por su ID."""
    try:
        supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
        return True
    except Exception as e:
        print(f"Error actualizando factura: {e}")
        return False
