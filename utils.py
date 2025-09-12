import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "comprobantes"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ==============================================
# Subir comprobante
# ==============================================
def upload_comprobante(file, factura_numero: str) -> str:
    try:
        file_path = f"{factura_numero}/{file.name}"
        supabase.storage.from_(BUCKET).upload(file_path, file.getvalue(), {"upsert": True})
        return safe_get_public_url(file_path)
    except Exception as e:
        raise RuntimeError(f"Error subiendo comprobante: {e}")

# ==============================================
# Obtener URL pública
# ==============================================
def safe_get_public_url(path: str) -> str:
    try:
        return supabase.storage.from_(BUCKET).get_public_url(path)
    except Exception:
        return ""
