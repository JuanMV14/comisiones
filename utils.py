# utils.py
import os
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY")

# Cliente compartido
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_comprobante(invoice_number: str, file_obj, folder: str = "") -> str:
    """
    Sube un archivo al bucket en la ruta:
      {folder}{invoice_number}/{timestamp}_{filename}
    Retorna la ruta (path) si subió ok, o None si falló.
    """
    try:
        original_name = getattr(file_obj, "name", "comprobante")
        timestamp = int(datetime.now().timestamp())
        # Sanitize invoice_number
        invoice_clean = str(invoice_number).replace("/", "_").replace(" ", "_")
        filename = f"{timestamp}_{original_name}"
        path = f"{folder}{invoice_clean}/{filename}" if folder else f"{invoice_clean}/{filename}"

        # file_obj can be an UploadedFile (has getbuffer) or bytes
        try:
            data = file_obj.getbuffer()
        except Exception:
            # If it's a stream-like object
            try:
                data = file_obj.read()
            except Exception:
                raise ValueError("No se pudo leer el archivo subido.")

        supabase.storage.from_(BUCKET).upload(path, data, {"content-type": getattr(file_obj, "type", None), "x-upsert": "true"})
        return path
    except Exception as e:
        print("Error upload_comprobante:", e)
        return None


def safe_get_public_url(bucket_path: str) -> str:
    """
    Dado el path dentro del bucket, devuelve la URL pública (o None).
    bucket_path: por ejemplo "12345/169000_file.jpg"
    """
    try:
        res = supabase.storage.from_(BUCKET).get_public_url(bucket_path)
        # supabase client may return a dict or string depending on version
        if isinstance(res, dict):
            # try common keys
            for k in ("publicUrl", "public_url", "publicURL", "url"):
                if k in res:
                    return res[k]
            # fallback to str
            return str(res)
        return res
    except Exception as e:
        print("Error safe_get_public_url:", e)
        return None
