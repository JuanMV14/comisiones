import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# =========================
# Conexión a Supabase
# =========================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "comprobantes"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# Manejo de archivos
# =========================
def upload_comprobante(file, factura_numero: str) -> str:
    """Sube un comprobante al bucket 'comprobantes/{factura_numero}/' y devuelve la URL pública"""
    try:
        file_path = f"{factura_numero}/{file.name}"
        supabase.storage.from_(BUCKET).upload(file_path, file.getvalue(), {"upsert": True})
        return safe_get_public_url(file_path)
    except Exception as e:
        raise RuntimeError(f"Error subiendo comprobante: {e}")

def safe_get_public_url(path: str) -> str:
    """Devuelve la URL pública de un archivo en el bucket"""
    try:
        return supabase.storage.from_(BUCKET).get_public_url(path)
    except Exception:
        return ""
