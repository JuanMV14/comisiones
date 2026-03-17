"""
Script para corregir fechas mal interpretadas en la tabla comisiones
Este script identifica fechas que pueden estar guardadas incorrectamente
y las corrige basándose en lógica de negocio.

IMPORTANTE: Revisar los resultados antes de ejecutar las correcciones
"""

import sys
import os
from datetime import datetime, date
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

load_dotenv()

def corregir_fechas_facturas(dry_run=True):
    """
    Identifica y corrige fechas mal interpretadas en comisiones
    
    Args:
        dry_run: Si es True, solo muestra qué se corregiría sin hacer cambios
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
        
        # Obtener todas las facturas con fechas
        print("Cargando facturas...")
        response = supabase.table("comisiones").select("id, factura, fecha_factura, created_at").execute()
        
        if not response.data:
            print("No se encontraron facturas")
            return
        
        df = pd.DataFrame(response.data)
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'], errors='coerce')
        df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
        
        # Normalizar zonas horarias (convertir a naive si es necesario)
        if df['fecha_factura'].dt.tz is not None:
            df['fecha_factura'] = df['fecha_factura'].dt.tz_localize(None)
        if df['created_at'].dt.tz is not None:
            df['created_at'] = df['created_at'].dt.tz_localize(None)
        
        # Identificar fechas sospechosas
        # Fechas que están en el futuro muy lejano (más de 1 año desde created_at)
        df['diferencia_dias'] = (df['fecha_factura'] - df['created_at']).dt.days
        
        # Fechas sospechosas: creadas recientemente pero con fecha de factura muy futura
        fecha_actual = datetime.now()
        df['fecha_sospechosa'] = (
            (df['fecha_factura'] > fecha_actual) & 
            (df['diferencia_dias'] > 365)
        ) | (
            (df['fecha_factura'].dt.month > 8) &  # Mes > agosto
            (df['created_at'] < pd.Timestamp('2026-01-01'))  # Creadas antes de 2026
        )
        
        fechas_sospechosas = df[df['fecha_sospechosa']].copy()
        
        if fechas_sospechosas.empty:
            print("OK: No se encontraron fechas sospechosas")
            return
        
        print(f"\nATENCION: Se encontraron {len(fechas_sospechosas)} fechas sospechosas:\n")
        
        for idx, row in fechas_sospechosas.iterrows():
            fecha_original = row['fecha_factura']
            if pd.isna(fecha_original):
                continue
                
            # Intentar interpretar como DD/MM/YYYY si el mes es > 12
            # Si la fecha es "2026-09-02", podría ser "02/09/2026" = 9 de febrero
            año = fecha_original.year
            mes_original = fecha_original.month
            dia_original = fecha_original.day
            
            # Si el mes es > 12, ya está mal guardado
            # Si el mes es <= 12 pero el día es > 12, podría estar intercambiado
            if mes_original <= 12 and dia_original <= 12:
                # Posible intercambio: "2026-09-02" debería ser "2026-02-09"
                fecha_corregida = date(año, dia_original, mes_original)
                
                print(f"Factura ID {row['id']}: {row['factura']}")
                print(f"  Fecha original: {fecha_original.strftime('%Y-%m-%d')} ({fecha_original.strftime('%d/%m/%Y')})")
                print(f"  Fecha corregida: {fecha_corregida.strftime('%Y-%m-%d')} ({fecha_corregida.strftime('%d/%m/%Y')})")
                print(f"  Creada: {row['created_at']}")
                print()
                
                if not dry_run:
                    try:
                        supabase.table("comisiones").update({
                            "fecha_factura": fecha_corregida.isoformat()
                        }).eq("id", int(row['id'])).execute()
                        print(f"  OK: Corregida")
                    except Exception as e:
                        print(f"  ERROR corrigiendo: {e}")
                else:
                    print(f"  (Solo visualizacion - dry_run=True)")
        
        if dry_run:
            print("\nMODO DRY RUN: No se hicieron cambios")
            print("Para aplicar las correcciones, ejecuta con dry_run=False")
        else:
            print("\nOK: Correcciones aplicadas")
            
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        print(traceback.format_exc())

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Corregir fechas mal interpretadas en facturas')
    parser.add_argument('--apply', action='store_true', help='Aplicar correcciones (por defecto solo muestra)')
    
    args = parser.parse_args()
    
    dry_run = not args.apply
    
    if dry_run:
        print("MODO DRY RUN: Solo se mostraran las correcciones sin aplicarlas")
        print("Para aplicar las correcciones, ejecuta con --apply\n")
    else:
        print("MODO APLICAR: Se modificaran las fechas en la base de datos")
        # Si se ejecuta desde línea de comandos, proceder automáticamente
        try:
            respuesta = input("Estas seguro? (escribe 'si' para continuar): ")
            if respuesta.lower() != 'si':
                print("Cancelado")
                sys.exit(0)
        except EOFError:
            # Si no hay input disponible (ejecución no interactiva), proceder automáticamente
            print("Ejecutando automaticamente (modo no interactivo)...")
    
    corregir_fechas_facturas(dry_run=dry_run)
