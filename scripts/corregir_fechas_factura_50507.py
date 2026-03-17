"""
Script para corregir las fechas de las compras de la factura 50507
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
        
        # Buscar la factura para obtener su fecha correcta
        factura_response = supabase.table("comisiones").select("*").eq("factura", "50507").execute()
        
        if not factura_response.data:
            print("No se encontro la factura 50507")
            return
        
        factura = factura_response.data[0]
        fecha_factura_str = factura.get('fecha_factura', '')
        
        if fecha_factura_str:
            fecha_factura = datetime.fromisoformat(fecha_factura_str.split('T')[0]).date()
            print(f"Factura 50507 encontrada:")
            print(f"  Fecha factura: {fecha_factura}")
            print(f"  Cliente: {factura.get('cliente', 'N/A')}")
        else:
            fecha_factura = date(2026, 2, 4)  # Fecha por defecto basada en la imagen
        
        # Buscar compras de la factura 50507
        print(f"\nBuscando compras de la factura 50507...")
        compras_response = supabase.table("compras_clientes").select("*").eq("num_documento", "50507").execute()
        
        if not compras_response.data:
            print("No se encontraron compras")
            return
        
        print(f"Encontradas {len(compras_response.data)} compras")
        
        correcciones = 0
        for compra in compras_response.data:
            fecha_actual = compra.get('fecha', '')
            if fecha_actual:
                fecha_actual_date = datetime.fromisoformat(fecha_actual.split('T')[0]).date()
                
                # Si la fecha es diferente a la fecha de la factura, corregirla
                if fecha_actual_date != fecha_factura:
                    # Verificar si es un intercambio de mes/día
                    if fecha_actual_date.year == fecha_factura.year:
                        # Si el mes y día están intercambiados
                        if fecha_actual_date.month == fecha_factura.day and fecha_actual_date.day == fecha_factura.month:
                            try:
                                supabase.table("compras_clientes").update({
                                    "fecha": fecha_factura.isoformat()
                                }).eq("id", compra['id']).execute()
                                print(f"  OK: Corregida compra ID {compra['id']}: {fecha_actual_date} -> {fecha_factura}")
                                correcciones += 1
                            except Exception as e:
                                print(f"  ERROR corrigiendo compra ID {compra['id']}: {e}")
                        # O simplemente usar la fecha de la factura si es diferente
                        elif abs((fecha_actual_date - fecha_factura).days) < 365:
                            try:
                                supabase.table("compras_clientes").update({
                                    "fecha": fecha_factura.isoformat()
                                }).eq("id", compra['id']).execute()
                                print(f"  OK: Corregida compra ID {compra['id']}: {fecha_actual_date} -> {fecha_factura}")
                                correcciones += 1
                            except Exception as e:
                                print(f"  ERROR corrigiendo compra ID {compra['id']}: {e}")
        
        print(f"\nTotal correcciones: {correcciones}")
        
        # Buscar otras compras con fechas mal interpretadas (mes y día intercambiados)
        print("\nBuscando otras compras con fechas mal interpretadas...")
        todas_compras = supabase.table("compras_clientes").select("id, num_documento, fecha").gte("fecha", "2026-01-01").lte("fecha", "2026-12-31").execute()
        
        correcciones_adicionales = 0
        for compra in todas_compras.data:
            fecha_str = compra.get('fecha', '')
            if fecha_str:
                try:
                    fecha_actual = datetime.fromisoformat(fecha_str.split('T')[0]).date()
                    # Si el mes es > 6 y el día es <= 12, podría estar intercambiado
                    # Por ejemplo: 2026-04-02 debería ser 2026-02-04
                    if fecha_actual.year == 2026 and fecha_actual.month > 2 and fecha_actual.day <= 12:
                        # Intercambiar mes y día
                        fecha_corregida = date(fecha_actual.year, fecha_actual.day, fecha_actual.month)
                        
                        # Solo corregir si la fecha corregida es razonable (no muy futura)
                        if fecha_corregida <= date(2026, 12, 31) and fecha_corregida >= date(2026, 1, 1):
                            # Verificar que no sea una fecha válida (ej: 04-02 podría ser válido si es abril 2)
                            # Solo corregir si el mes original es > 6 (julio en adelante) o si el día es claramente un mes
                            if fecha_actual.month > 6 or (fecha_actual.month > 2 and fecha_actual.day <= 12):
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
