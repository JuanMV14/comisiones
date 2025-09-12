def safe_get_public_url(supabase, bucket: str, path: str) -> str:
    """
    Obtiene la URL pública de un archivo en Supabase Storage.
    """
    try:
        return supabase.storage.from_(bucket).get_public_url(path)
    except Exception as e:
        print("Error obteniendo URL pública:", e)
        return None
