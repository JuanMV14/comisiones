from datetime import datetime

def safe_get_public_url(supabase, bucket: str, path: str):
    """Obtiene la URL pública de un archivo en Supabase Storage."""
    try:
        res = supabase.storage.from_(bucket).get_public_url(path)
        if isinstance(res, dict):
            for key in ("publicUrl", "public_url", "publicURL", "publicurl", "url"):
                if key in res:
                    return res[key]
            return str(res)
        return res
    except Exception:
        return None

def calcular_comision(valor, porcentaje):
    """Calcula la comisión según valor y porcentaje."""
    return valor * (porcentaje / 100)

def format_currency(value):
    """Formatea un número a pesos colombianos con separador de miles."""
    return f"${value:,.2f}"

def now_iso():
    """Devuelve la fecha y hora actual en formato ISO."""
    return datetime.now().isoformat()
