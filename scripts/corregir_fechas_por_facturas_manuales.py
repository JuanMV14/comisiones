"""
Script para corregir fechas en compras_clientes basándose en las facturas manuales
Las facturas manuales tienen las fechas correctas, así que las usamos como referencia
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def corregir_fechas_por_referencia(dry_run=True):
    """
    Corrige fechas en compras_clientes comparándolas con las fechas correctas
    de las facturas manuales en comisiones
    """
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
            response = supabase.table("comisiones").select("id, factura, fecha_factura").range(current_offset, current_offset + page_size - 1).execute()
            
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
                    print(f"Error procesando factura {num_factura}: {e}")
                    continue
        
        print(f"Encontradas {len(facturas_correctas)} facturas manuales únicas con fechas correctas")
        
        # Ahora cargar compras_clientes
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
        
        if not compras_clientes:
            print("No se encontraron compras_clientes")
            return
        
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
                        fecha_actual_parsed = pd.to_datetime(fecha_actual, errors='coerce', dayfirst=True)
                        if pd.isna(fecha_actual_parsed):
                            continue
                        fecha_actual_date = fecha_actual_parsed.date()
                    else:
                        fecha_actual_date = fecha_actual
                    
                    # Comparar fechas
                    # Si la fecha actual es diferente a la correcta, necesita corrección
                    if fecha_actual_date != fecha_correcta:
                        # Verificar si es un intercambio de mes/día
                        año_actual = fecha_actual_date.year
                        mes_actual = fecha_actual_date.month
                        dia_actual = fecha_actual_date.day
                        
                        año_correcto = fecha_correcta.year
                        mes_correcto = fecha_correcta.month
                        dia_correcto = fecha_correcta.day
                        
                        # Si el año es el mismo y los valores están intercambiados
                        if año_actual == año_correcto:
                            # Verificar si es un intercambio simple de mes/día
                            if mes_actual == dia_correcto and dia_actual == mes_correcto:
                                correcciones.append({
                                    'id': compra['id'],
                                    'num_documento': num_documento,
                                    'fecha_actual': fecha_actual_date.isoformat(),
                                    'fecha_correcta': fecha_correcta.isoformat(),
                                    'tipo': 'intercambio_mes_dia'
                                })
                            # O si simplemente es diferente
                            elif abs((fecha_actual_date - fecha_correcta).days) < 365:
                                correcciones.append({
                                    'id': compra['id'],
                                    'num_documento': num_documento,
                                    'fecha_actual': fecha_actual_date.isoformat(),
                                    'fecha_correcta': fecha_correcta.isoformat(),
                                    'tipo': 'diferente'
                                })
                
                except Exception as e:
                    print(f"Error procesando compra ID {compra['id']}: {e}")
                    continue
        
        if not correcciones:
            print("\nNo se encontraron fechas que necesiten corrección")
            return
        
        print(f"\nEncontradas {len(correcciones)} compras que necesitan corrección:\n")
        
        # Mostrar correcciones
        for corr in correcciones[:20]:  # Mostrar primeras 20
            print(f"Compra ID {corr['id']}: Doc {corr['num_documento']}")
            print(f"  Fecha actual: {corr['fecha_actual']} ({datetime.fromisoformat(corr['fecha_actual']).strftime('%d/%m/%Y')})")
            print(f"  Fecha correcta: {corr['fecha_correcta']} ({datetime.fromisoformat(corr['fecha_correcta']).strftime('%d/%m/%Y')})")
            print(f"  Tipo: {corr['tipo']}")
            print()
        
        if len(correcciones) > 20:
            print(f"... y {len(correcciones) - 20} más\n")
        
        # Aplicar correcciones si no es dry_run
        if not dry_run:
            print(f"Aplicando {len(correcciones)} correcciones...")
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
        else:
            print("\nMODO DRY RUN: No se aplicaron correcciones")
            print("Para aplicar las correcciones, ejecuta con --apply")
        
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Corregir fechas en compras_clientes basándose en facturas manuales')
    parser.add_argument('--apply', action='store_true', help='Aplicar correcciones')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    if dry_run:
        print("MODO DRY RUN: Solo se mostraran las correcciones sin aplicarlas")
        print("Para aplicar las correcciones, ejecuta con --apply\n")
    else:
        print("MODO APLICAR: Se modificaran las fechas en compras_clientes")
        try:
            respuesta = input("Estas seguro? (escribe 'si' para continuar): ")
            if respuesta.lower() != 'si':
                print("Cancelado")
                sys.exit(0)
        except EOFError:
            print("Ejecutando automaticamente (modo no interactivo)...")
    
    corregir_fechas_por_referencia(dry_run=dry_run)
