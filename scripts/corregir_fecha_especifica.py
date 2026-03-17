"""
Script para corregir una fecha específica: 02/11/2026 -> 11/02/2026
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def corregir_fecha_especifica():
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Buscar en comisiones donde fecha_factura = 2026-11-02 (que debería ser 2026-02-11)
        print("Buscando facturas con fecha 2026-11-02...")
        response = supabase.table("comisiones").select("id, factura, fecha_factura, cliente").eq("fecha_factura", "2026-11-02").execute()
        
        if response.data:
            print(f"\nEncontradas {len(response.data)} facturas con fecha 2026-11-02:")
            for factura in response.data:
                print(f"  ID: {factura['id']}, Factura: {factura['factura']}, Cliente: {factura.get('cliente', 'N/A')}")
            
            # Corregir todas
            fecha_corregida = date(2026, 2, 11)
            for factura in response.data:
                try:
                    supabase.table("comisiones").update({
                        "fecha_factura": fecha_corregida.isoformat()
                    }).eq("id", factura['id']).execute()
                    print(f"  OK: Corregida factura ID {factura['id']} ({factura['factura']})")
                except Exception as e:
                    print(f"  ERROR corrigiendo factura ID {factura['id']}: {e}")
        else:
            print("No se encontraron facturas con fecha 2026-11-02")
        
        # También buscar en compras_clientes
        print("\nBuscando compras con fecha 2026-11-02...")
        response_compras = supabase.table("compras_clientes").select("id, num_documento, fecha").eq("fecha", "2026-11-02").execute()
        
        if response_compras.data:
            print(f"\nEncontradas {len(response_compras.data)} compras con fecha 2026-11-02:")
            for compra in response_compras.data:
                print(f"  ID: {compra['id']}, Doc: {compra['num_documento']}")
            
            # Corregir todas
            fecha_corregida = date(2026, 2, 11)
            for compra in response_compras.data:
                try:
                    supabase.table("compras_clientes").update({
                        "fecha": fecha_corregida.isoformat()
                    }).eq("id", compra['id']).execute()
                    print(f"  OK: Corregida compra ID {compra['id']} (Doc: {compra['num_documento']})")
                except Exception as e:
                    print(f"  ERROR corrigiendo compra ID {compra['id']}: {e}")
        else:
            print("No se encontraron compras con fecha 2026-11-02")
        
        # Buscar también fechas que puedan estar mal interpretadas (mes 11, día 2)
        print("\nBuscando otras fechas que puedan estar mal (mes=11, día=2)...")
        response_otras = supabase.table("comisiones").select("id, factura, fecha_factura, cliente").execute()
        
        correcciones = 0
        for factura in response_otras.data:
            if factura.get('fecha_factura'):
                try:
                    fecha_actual = datetime.fromisoformat(factura['fecha_factura']).date()
                    # Si es noviembre 2026 y el día es 2, podría ser febrero 11
                    if fecha_actual.year == 2026 and fecha_actual.month == 11 and fecha_actual.day == 2:
                        fecha_corregida = date(2026, 2, 11)
                        supabase.table("comisiones").update({
                            "fecha_factura": fecha_corregida.isoformat()
                        }).eq("id", factura['id']).execute()
                        print(f"  OK: Corregida factura ID {factura['id']} ({factura['factura']}): {fecha_actual} -> {fecha_corregida}")
                        correcciones += 1
                except:
                    pass
        
        print(f"\nOK: Total de correcciones: {correcciones}")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    corregir_fecha_especifica()
