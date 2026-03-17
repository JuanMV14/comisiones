"""
Script para verificar la factura 50833 del cliente ACEVEDO VILLADA
"""

import sys
import os
from datetime import datetime
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def verificar_factura():
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        # Buscar factura 50833
        print("Buscando factura 50833...")
        response = supabase.table("comisiones").select("*").eq("factura", "50833").execute()
        
        if response.data:
            factura = response.data[0]
            print(f"\nFactura encontrada:")
            print(f"  ID: {factura['id']}")
            print(f"  Factura: {factura['factura']}")
            print(f"  Cliente: {factura.get('cliente', 'N/A')}")
            print(f"  fecha_factura: {factura.get('fecha_factura', 'N/A')}")
            print(f"  fecha_pago_est: {factura.get('fecha_pago_est', 'N/A')}")
            print(f"  fecha_pago_max: {factura.get('fecha_pago_max', 'N/A')}")
            
            # Si fecha_pago_max es 2026-11-02, corregirla
            fecha_pago_max = factura.get('fecha_pago_max', '')
            if fecha_pago_max and '2026-11-02' in str(fecha_pago_max):
                print(f"\nCORRIGIENDO fecha_pago_max de {fecha_pago_max} a 2026-02-11...")
                
                # Calcular la fecha correcta basada en fecha_factura
                fecha_factura_str = factura.get('fecha_factura', '')
                if fecha_factura_str:
                    try:
                        fecha_factura = datetime.fromisoformat(fecha_factura_str.split('T')[0]).date()
                        condicion_especial = factura.get('condicion_especial', False)
                        dias_max = 60 if condicion_especial else 45
                        fecha_pago_max_corregida = fecha_factura + timedelta(days=dias_max)
                        
                        print(f"  fecha_factura: {fecha_factura}")
                        print(f"  condicion_especial: {condicion_especial}")
                        print(f"  dias_max: {dias_max}")
                        print(f"  fecha_pago_max_corregida: {fecha_pago_max_corregida}")
                        
                        # Actualizar
                        supabase.table("comisiones").update({
                            "fecha_pago_max": fecha_pago_max_corregida.isoformat()
                        }).eq("id", factura['id']).execute()
                        
                        print(f"\nOK: Factura actualizada")
                    except Exception as e:
                        print(f"ERROR calculando fecha: {e}")
            elif fecha_pago_max and '2026-02-11' in str(fecha_pago_max):
                print(f"\nLa fecha_pago_max ya está correcta: {fecha_pago_max}")
            else:
                print(f"\nFecha_pago_max actual: {fecha_pago_max}")
        else:
            print("No se encontró la factura 50833")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    from datetime import timedelta
    verificar_factura()
