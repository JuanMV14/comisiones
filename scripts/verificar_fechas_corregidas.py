"""
Script para verificar si las fechas fueron corregidas correctamente
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def verificar_fechas():
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Verificar algunas facturas que deberían haberse corregido
        print("Verificando fechas en comisiones...")
        response = supabase.table("comisiones").select("id, factura, fecha_factura").order("id", desc=True).limit(50).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
            
            print(f"\nUltimas 50 facturas:")
            for idx, row in df.iterrows():
                if pd.notna(row['fecha_factura']):
                    print(f"ID {row['id']}: Factura {row['factura']} - Fecha: {row['fecha_factura'].strftime('%Y-%m-%d')} ({row['fecha_factura'].strftime('%d/%m/%Y')})")
        
        # Verificar fechas en compras_clientes también
        print("\n\nVerificando fechas en compras_clientes...")
        response_compras = supabase.table("compras_clientes").select("id, num_documento, fecha").order("id", desc=True).limit(50).execute()
        
        if response_compras.data:
            df_compras = pd.DataFrame(response_compras.data)
            df_compras['fecha'] = pd.to_datetime(df_compras['fecha'], errors='coerce', dayfirst=True)
            
            print(f"\nUltimas 50 compras:")
            for idx, row in df_compras.iterrows():
                if pd.notna(row['fecha']):
                    print(f"ID {row['id']}: Doc {row['num_documento']} - Fecha: {row['fecha'].strftime('%Y-%m-%d')} ({row['fecha'].strftime('%d/%m/%Y')})")
                    
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    verificar_fechas()
