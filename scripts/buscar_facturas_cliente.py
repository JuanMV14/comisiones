"""
Script para buscar facturas de un cliente específico
"""

import sys
import os
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def buscar_facturas_cliente(nombre_cliente):
    try:
        from supabase import create_client
        from config.settings import AppConfig
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        print(f"Buscando facturas del cliente: {nombre_cliente}\n")
        
        # Buscar facturas
        facturas_response = supabase.table("comisiones").select("*").ilike("cliente", f"%{nombre_cliente}%").order("fecha_factura", desc=True).limit(10).execute()
        
        if not facturas_response.data:
            print("No se encontraron facturas")
            return
        
        print(f"Encontradas {len(facturas_response.data)} facturas:\n")
        
        for factura in facturas_response.data:
            print(f"Factura: {factura.get('factura', 'N/A')}")
            print(f"  Fecha: {factura.get('fecha_factura', 'N/A')}")
            print(f"  Valor: {factura.get('valor', 0)}")
            print()
            
            # Buscar compras relacionadas
            num_factura = factura.get('factura', '')
            if num_factura:
                compras_response = supabase.table("compras_clientes").select("id, marca, total, fecha").eq("num_documento", str(num_factura)).eq("es_devolucion", False).execute()
                
                if compras_response.data:
                    print(f"  Compras relacionadas: {len(compras_response.data)}")
                    marcas = {}
                    for compra in compras_response.data:
                        marca = compra.get('marca', 'N/A')
                        total = compra.get('total', 0)
                        fecha = compra.get('fecha', 'N/A')
                        if marca not in marcas:
                            marcas[marca] = 0
                        marcas[marca] += total
                        print(f"    - Marca: {marca}, Total: {total}, Fecha: {fecha}")
                    
                    print(f"  Total por marca:")
                    for marca, total in marcas.items():
                        print(f"    {marca}: ${total:,.2f}")
                else:
                    print(f"  No se encontraron compras relacionadas")
                print()
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Buscar facturas de un cliente')
    parser.add_argument('--cliente', type=str, default='VASQUEZ ZULUAGA', help='Nombre del cliente')
    
    args = parser.parse_args()
    
    buscar_facturas_cliente(args.cliente)
