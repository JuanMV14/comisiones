"""
Script para corregir fechas mal interpretadas en la tabla compras_clientes
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def corregir_fechas_compras(dry_run=True):
    """
    Identifica y corrige fechas mal interpretadas en compras_clientes
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
        
        # Obtener todas las compras con fechas
        print("Cargando compras_clientes...")
        
        all_compras = []
        page_size = 1000
        current_offset = 0
        
        while True:
            response = supabase.table("compras_clientes").select("id, num_documento, fecha").range(current_offset, current_offset + page_size - 1).execute()
            
            if not response.data:
                break
            
            all_compras.extend(response.data)
            
            if len(response.data) < page_size:
                break
            
            current_offset += page_size
        
        if not all_compras:
            print("No se encontraron compras")
            return
        
        df = pd.DataFrame(all_compras)
        df['fecha'] = pd.to_datetime(df['fecha'], errors='coerce', dayfirst=True)
        
        # Normalizar zonas horarias
        if df['fecha'].dt.tz is not None:
            df['fecha'] = df['fecha'].dt.tz_localize(None)
        
        # Filtrar fechas válidas
        df = df[df['fecha'].notna()].copy()
        
        # Identificar fechas sospechosas
        fecha_actual = datetime.now()
        
        # Fechas sospechosas: fechas muy futuras (más de 1 año desde ahora) o fechas con mes > 8 en 2025
        df['fecha_sospechosa'] = (
            (df['fecha'] > fecha_actual + pd.Timedelta(days=365))
        ) | (
            (df['fecha'].dt.year == 2025) & (df['fecha'].dt.month > 8)
        ) | (
            (df['fecha'].dt.year == 2026) & (df['fecha'].dt.month > 2) & (df['fecha'] < pd.Timestamp('2026-02-01'))
        )
        
        fechas_sospechosas = df[df['fecha_sospechosa']].copy()
        
        if fechas_sospechosas.empty:
            print("OK: No se encontraron fechas sospechosas en compras_clientes")
            return
        
        print(f"\nATENCION: Se encontraron {len(fechas_sospechosas)} fechas sospechosas en compras_clientes:\n")
        
        correcciones = 0
        for idx, row in fechas_sospechosas.iterrows():
            fecha_original = row['fecha']
            if pd.isna(fecha_original):
                continue
                
            año = fecha_original.year
            mes_original = fecha_original.month
            dia_original = fecha_original.day
            
            # Si el mes es <= 12 y el día es <= 12, posible intercambio
            if mes_original <= 12 and dia_original <= 12:
                fecha_corregida = date(año, dia_original, mes_original)
                
                # Solo corregir si la fecha corregida es más razonable (no muy futura)
                fecha_corregida_obj = pd.Timestamp(fecha_corregida)
                if fecha_corregida_obj <= fecha_actual + pd.Timedelta(days=90):  # No más de 3 meses en el futuro
                    print(f"Compra ID {row['id']}: Doc {row['num_documento']}")
                    print(f"  Fecha original: {fecha_original.strftime('%Y-%m-%d')} ({fecha_original.strftime('%d/%m/%Y')})")
                    print(f"  Fecha corregida: {fecha_corregida.strftime('%Y-%m-%d')} ({fecha_corregida.strftime('%d/%m/%Y')})")
                    print()
                else:
                    continue
                
                if not dry_run:
                    try:
                        supabase.table("compras_clientes").update({
                            "fecha": fecha_corregida.isoformat()
                        }).eq("id", int(row['id'])).execute()
                        correcciones += 1
                        print(f"  OK: Corregida")
                    except Exception as e:
                        print(f"  ERROR corrigiendo: {e}")
                else:
                    print(f"  (Solo visualizacion - dry_run=True)")
        
        if dry_run:
            print("\nMODO DRY RUN: No se hicieron cambios")
            print("Para aplicar las correcciones, ejecuta con --apply")
        else:
            print(f"\nOK: {correcciones} correcciones aplicadas en compras_clientes")
            
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Corregir fechas mal interpretadas en compras_clientes')
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
    
    corregir_fechas_compras(dry_run=dry_run)
