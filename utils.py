import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = "comprobantes"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_file(file, filename: str) -> str:
    """Sube un archivo al bucket y devuelve la ruta."""
    try:
        supabase.storage.from_(BUCKET).upload(filename, file, {"upsert": True})
        return filename
    except Exception as e:
        raise Exception(f"Error subiendo archivo: {e}")


def safe_get_public_url(filename: str) -> str:
    """Devuelve la URL pública de un archivo en Supabase Storage."""
    try:
        return supabase.storage.from_(BUCKET).get_public_url(filename)
    except Exception as e:
        return f"Error obteniendo URL pública: {e}"
