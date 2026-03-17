"""
Script para corregir TODAS las fechas de compras_clientes basándose en las fechas correctas
de las facturas manuales. Compara num_documento con factura y ajusta la fecha.
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def corregir_todas_fechas():
    try:
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        
        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            print("ERROR: Faltan variables de entorno")
            return
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        
        print("Cargando facturas manuales (comisiones)...")
        # Obtener todas las facturas manuales
        facturas_manuales = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response = supabase.table("comisiones").select("id, factura, fecha_factura, cliente").range(current_offset, current_offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            facturas_manuales.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size
        
        if not facturas_manuales:
            print("No se encontraron facturas manuales")
            return
        
        # Crear un diccionario: num_factura -> fecha_correcta
        facturas_correctas = {}
        for factura in facturas_manuales:
            num_factura = str(factura.get('factura', '')).strip()
            fecha_factura = factura.get('fecha_factura')
            
            if num_factura and num_factura != 'N/A' and fecha_factura:
                try:
                    # Parsear fecha correcta
                    if isinstance(fecha_factura, str):
                        fecha_correcta = datetime.fromisoformat(fecha_factura.split('T')[0]).date()
                    else:
                        fecha_correcta = fecha_factura
                    
                    # Guardar la fecha más reciente si hay múltiples facturas con el mismo número
                    if num_factura not in facturas_correctas:
                        facturas_correctas[num_factura] = fecha_correcta
                    else:
                        # Si hay múltiples, usar la más reciente
                        if fecha_correcta > facturas_correctas[num_factura]:
                            facturas_correctas[num_factura] = fecha_correcta
                except Exception as e:
                    continue
        
        print(f"Encontradas {len(facturas_correctas)} facturas manuales unicas con fechas correctas")
        
        # Ahora cargar todas las compras_clientes
        print("\nCargando compras_clientes...")
        compras_clientes = []
        current_offset = 0
        
        while True:
            response = supabase.table("compras_clientes").select("id, num_documento, fecha").range(current_offset, current_offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            compras_clientes.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size
        
        print(f"Encontradas {len(compras_clientes)} compras_clientes")
        
        # Comparar y corregir
        correcciones = []
        
        for compra in compras_clientes:
            num_documento = str(compra.get('num_documento', '')).strip()
            fecha_actual = compra.get('fecha')
            
            if not num_documento or not fecha_actual:
                continue
            
            # Buscar si hay una factura manual con este número
            if num_documento in facturas_correctas:
                fecha_correcta = facturas_correctas[num_documento]
                
                try:
                    # Parsear fecha actual en compras_clientes
                    if isinstance(fecha_actual, str):
                        fecha_actual_parsed = pd.to_datetime(fecha_actual, errors='coerce', dayfirst=False)
                        if pd.isna(fecha_actual_parsed):
                            continue
                        fecha_actual_date = fecha_actual_parsed.date()
                    else:
                        fecha_actual_date = fecha_actual
                    
                    # Comparar fechas
                    # Si la fecha actual es diferente a la correcta, necesita corrección
                    if fecha_actual_date != fecha_correcta:
                        correcciones.append({
                            'id': compra['id'],
                            'num_documento': num_documento,
                            'fecha_actual': fecha_actual_date.isoformat(),
                            'fecha_correcta': fecha_correcta.isoformat()
                        })
                
                except Exception as e:
                    continue
        
        if not correcciones:
            print("\nNo se encontraron fechas que necesiten correccion")
            return
        
        print(f"\nEncontradas {len(correcciones)} compras que necesitan correccion")
        
        # Mostrar algunas correcciones
        print("\nPrimeras 20 correcciones:")
        for corr in correcciones[:20]:
            print(f"  Doc {corr['num_documento']}: {corr['fecha_actual']} -> {corr['fecha_correcta']}")
        
        if len(correcciones) > 20:
            print(f"... y {len(correcciones) - 20} mas\n")
        
        # Aplicar correcciones
        print(f"\nAplicando {len(correcciones)} correcciones...")
        exitosas = 0
        errores = 0
        
        for corr in correcciones:
            try:
                supabase.table("compras_clientes").update({
                    "fecha": corr['fecha_correcta']
                }).eq("id", corr['id']).execute()
                exitosas += 1
            except Exception as e:
                print(f"Error corrigiendo compra ID {corr['id']}: {e}")
                errores += 1
        
        print(f"\nOK: {exitosas} correcciones aplicadas")
        if errores > 0:
            print(f"ERRORES: {errores} correcciones fallaron")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    corregir_todas_fechas()
