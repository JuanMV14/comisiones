"""
Script para exportar todas las referencias únicas de la base de datos a CSV
"""
import pandas as pd
from supabase import create_client
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def exportar_referencias_a_csv():
    """Exporta todas las referencias únicas de compras_clientes a CSV"""
    
    # Conectar a Supabase
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Faltan variables de entorno SUPABASE_URL o SUPABASE_KEY")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    print("Cargando todas las referencias de compras_clientes...")
    
    # Cargar todas las referencias únicas con paginación
    all_referencias = []
    page_size = 1000
    current_offset = 0
    
    # Primero obtener todas las referencias únicas
    referencias_unicas = set()
    
    while True:
        response = supabase.table("compras_clientes").select("cod_articulo, detalle").range(
            current_offset, current_offset + page_size - 1
        ).execute()
        
        if not response.data:
            break
        
        for item in response.data:
            cod_articulo = item.get('cod_articulo', '').strip() if item.get('cod_articulo') else ''
            detalle = item.get('detalle', '').strip() if item.get('detalle') else ''
            
            # Solo agregar si tiene código y detalle válidos
            if cod_articulo and cod_articulo != 'N/A' and detalle:
                # Usar tupla como clave para evitar duplicados
                clave = (cod_articulo, detalle)
                if clave not in referencias_unicas:
                    referencias_unicas.add(clave)
                    all_referencias.append({
                        'Artículo': cod_articulo,
                        'Descripción': detalle
                    })
        
        if len(response.data) < page_size:
            break
        
        current_offset += page_size
        print(f"   Procesadas {len(all_referencias)} referencias únicas...")
    
    if not all_referencias:
        print("No se encontraron referencias")
        return
    
    # Crear DataFrame y ordenar por código
    df = pd.DataFrame(all_referencias)
    df = df.sort_values('Artículo').reset_index(drop=True)
    
    # Eliminar duplicados exactos (por si acaso)
    df = df.drop_duplicates(subset=['Artículo', 'Descripción']).reset_index(drop=True)
    
    # Exportar a CSV
    archivo_csv = 'referencias_exportadas.csv'
    df.to_csv(archivo_csv, index=False, encoding='utf-8-sig')
    
    print(f"Exportadas {len(df)} referencias unicas a {archivo_csv}")
    print(f"   Primeras 5 referencias:")
    print(df.head().to_string(index=False))
    
    return df

if __name__ == "__main__":
    exportar_referencias_a_csv()
