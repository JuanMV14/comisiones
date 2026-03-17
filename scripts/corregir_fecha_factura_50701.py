"""
Script para corregir las fechas de las compras de la factura 50701
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def corregir_fecha_factura():
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Buscar compras de la factura 50701
        print("Buscando compras de la factura 50701...")
        compras_response = supabase.table("compras_clientes").select("*").eq("num_documento", "50701").execute()
        
        if not compras_response.data:
            print("No se encontraron compras")
            return
        
        print(f"Encontradas {len(compras_response.data)} compras")
        
        # La fecha correcta debería ser 2026-02-07 (7 de febrero)
        fecha_corregida = date(2026, 2, 7)
        
        correcciones = 0
        for compra in compras_response.data:
            fecha_actual = compra.get('fecha', '')
            if fecha_actual:
                # Si la fecha es 2026-07-02, corregirla a 2026-02-07
                if '2026-07-02' in str(fecha_actual):
                    try:
                        supabase.table("compras_clientes").update({
                            "fecha": fecha_corregida.isoformat()
                        }).eq("id", compra['id']).execute()
                        print(f"  OK: Corregida compra ID {compra['id']}: {fecha_actual} -> {fecha_corregida.isoformat()}")
                        correcciones += 1
                    except Exception as e:
                        print(f"  ERROR corrigiendo compra ID {compra['id']}: {e}")
        
        print(f"\nTotal correcciones: {correcciones}")
        
        # También buscar otras compras con el mismo problema (mes y día intercambiados)
        print("\nBuscando otras compras con fechas mal interpretadas...")
        todas_compras = supabase.table("compras_clientes").select("id, num_documento, fecha").gte("fecha", "2026-01-01").lte("fecha", "2026-12-31").execute()
        
        correcciones_adicionales = 0
        for compra in todas_compras.data:
            fecha_str = compra.get('fecha', '')
            if fecha_str:
                try:
                    fecha_actual = datetime.fromisoformat(fecha_str.split('T')[0]).date()
                    # Si el mes es > 6 y el día es <= 12, podría estar intercambiado
                    # Por ejemplo: 2026-07-02 debería ser 2026-02-07
                    if fecha_actual.year == 2026 and fecha_actual.month > 6 and fecha_actual.day <= 12:
                        # Intercambiar mes y día
                        fecha_corregida = date(fecha_actual.year, fecha_actual.day, fecha_actual.month)
                        
                        # Solo corregir si la fecha corregida es razonable (no muy futura)
                        if fecha_corregida <= date(2026, 12, 31):
                            supabase.table("compras_clientes").update({
                                "fecha": fecha_corregida.isoformat()
                            }).eq("id", compra['id']).execute()
                            print(f"  OK: Corregida compra ID {compra['id']} (Doc: {compra.get('num_documento', 'N/A')}): {fecha_actual} -> {fecha_corregida}")
                            correcciones_adicionales += 1
                except:
                    pass
        
        print(f"\nTotal correcciones adicionales: {correcciones_adicionales}")
        print(f"Total general: {correcciones + correcciones_adicionales}")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    corregir_fecha_factura()
