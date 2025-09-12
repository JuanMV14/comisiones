from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_all_comisiones():
    return supabase.table("comisiones").select("*").execute()


def insert_comision(data: dict):
    return supabase.table("comisiones").insert(data).execute()


def update_comision(id_val: int, data: dict):
    return supabase.table("comisiones").update(data).eq("id", id_val).execute()
