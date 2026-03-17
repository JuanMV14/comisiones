"""
Script para buscar el cliente ACEVEDO VILLADA JORGE IVAN y corregir su fecha
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def buscar_y_corregir():
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Buscar cliente por nombre
        print("Buscando cliente ACEVEDO VILLADA JORGE IVAN...")
        response = supabase.table("clientes_b2b").select("*").ilike("nombre", "%ACEVEDO%VILLADA%").execute()
        
        if response.data:
            print(f"\nEncontrados {len(response.data)} clientes:")
            for cliente in response.data:
                print(f"  ID: {cliente['id']}, Nombre: {cliente.get('nombre', 'N/A')}, NIT: {cliente.get('nit', 'N/A')}")
        
        # Buscar facturas relacionadas con este cliente
        print("\nBuscando facturas relacionadas...")
        
        # Buscar por NIT si lo tenemos
        if response.data and len(response.data) > 0:
            nit_cliente = response.data[0].get('nit', '')
            if nit_cliente:
                print(f"Buscando facturas con NIT: {nit_cliente}")
                facturas = supabase.table("comisiones").select("id, factura, fecha_factura, cliente").ilike("cliente", "%ACEVEDO%").execute()
                
                if facturas.data:
                    print(f"\nEncontradas {len(facturas.data)} facturas:")
                    for factura in facturas.data:
                        fecha_str = factura.get('fecha_factura', 'N/A')
                        print(f"  ID: {factura['id']}, Factura: {factura['factura']}, Fecha: {fecha_str}, Cliente: {factura.get('cliente', 'N/A')}")
                        
                        # Si la fecha es 2026-11-02 o similar, corregirla
                        if fecha_str and '2026-11-02' in str(fecha_str):
                            fecha_corregida = date(2026, 2, 11)
                            try:
                                supabase.table("comisiones").update({
                                    "fecha_factura": fecha_corregida.isoformat()
                                }).eq("id", factura['id']).execute()
                                print(f"    -> CORREGIDA a {fecha_corregida.isoformat()}")
                            except Exception as e:
                                print(f"    -> ERROR corrigiendo: {e}")
        
        # También buscar en todas las facturas de febrero 2026 que puedan estar mal
        print("\nBuscando facturas de febrero 2026 que puedan estar mal interpretadas...")
        todas_facturas = supabase.table("comisiones").select("id, factura, fecha_factura, cliente").gte("fecha_factura", "2026-01-01").lte("fecha_factura", "2026-12-31").execute()
        
        correcciones = 0
        for factura in todas_facturas.data:
            if factura.get('fecha_factura'):
                try:
                    fecha_actual = datetime.fromisoformat(factura['fecha_factura'].split('T')[0]).date()
                    # Si es noviembre 2026 y el día es 2, debería ser febrero 11
                    if fecha_actual.year == 2026 and fecha_actual.month == 11 and fecha_actual.day == 2:
                        fecha_corregida = date(2026, 2, 11)
                        supabase.table("comisiones").update({
                            "fecha_factura": fecha_corregida.isoformat()
                        }).eq("id", factura['id']).execute()
                        print(f"  Corregida factura ID {factura['id']} ({factura['factura']}): {fecha_actual} -> {fecha_corregida}")
                        correcciones += 1
                except Exception as e:
                    pass
        
        print(f"\nTotal de correcciones realizadas: {correcciones}")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    buscar_y_corregir()
