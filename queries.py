import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# ========================
# Conexión a Supabase
# ========================
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLE = "comisiones"


# ========================
# Consultas
# ========================
def get_all_comisiones():
    try:
        response = supabase.table(TABLE).select("*").execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"❌ Error al obtener comisiones: {e}")
        return []


def insert_comision(pedido, cliente, factura, valor, porcentaje,
                    comision, fecha_factura, tiene_descuento_factura):
    try:
        response = supabase.table(TABLE).insert({
            "pedido": pedido,
            "cliente": cliente,
            "factura": factura,
            "valor": valor,
            "porcentaje": porcentaje,
            "comision": comision,
            "fecha_factura": fecha_factura.isoformat(),
            "pagado": False,
            "tiene_descuento_factura": tiene_descuento_factura,
            "created_at": datetime.now().isoformat()
        }).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error al insertar comisión: {e}")
        return None


def update_comision(comision_id, updates: dict):
    try:
        response = supabase.table(TABLE).update(updates).eq("id", comision_id).execute()
        return response.data
    except Exception as e:
        print(f"❌ Error al actualizar comisión {comision_id}: {e}")
        return None
