from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

@router.get("")
async def get_clientes() -> List[Dict[str, Any]]:
    """
    Obtiene lista de todos los clientes
    Reutiliza database/queries.py y database/client_purchases_manager.py
    """
    try:
        from database.queries import DatabaseManager
        from database.client_purchases_manager import ClientPurchasesManager
        from supabase import create_client
        from config.settings import AppConfig
        import pandas as pd
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        # Obtener clientes de la tabla comisiones
        df_comisiones = db_manager.cargar_datos()
        clientes_comisiones = []
        
        if not df_comisiones.empty and 'cliente' in df_comisiones.columns:
            clientes_unicos = df_comisiones['cliente'].dropna().unique()
            for cliente in clientes_unicos:
                cliente_data = df_comisiones[df_comisiones['cliente'] == cliente].iloc[0]
                clientes_comisiones.append({
                    "id": hash(cliente) % 1000000,  # ID temporal
                    "nombre": cliente,
                    "contacto": cliente_data.get('cliente', ''),
                    "ciudad": cliente_data.get('ciudad_destino', 'N/A') if 'ciudad_destino' in cliente_data else 'N/A',
                    "estado": "activo"
                })
        
        # También obtener clientes B2B
        try:
            clientes_manager = ClientPurchasesManager(supabase)
            df_clientes_b2b = clientes_manager.listar_clientes()
            
            if not df_clientes_b2b.empty:
                for _, row in df_clientes_b2b.iterrows():
                    cliente_existe = any(c['nombre'] == row['nombre'] for c in clientes_comisiones)
                    if not cliente_existe:
                        clientes_comisiones.append({
                            "id": hash(row['nombre']) % 1000000,
                            "nombre": row['nombre'],
                            "contacto": row.get('contacto', ''),
                            "email": row.get('email', ''),
                            "telefono": row.get('telefono', ''),
                            "ciudad": row.get('ciudad', 'N/A'),
                            "credito": float(row.get('cupo_total', 0)) if pd.notna(row.get('cupo_total')) else 0,
                            "estado": "activo" if row.get('activo', True) else "inactivo"
                        })
        except:
            pass  # Si hay error con B2B, continuar solo con comisiones
        
        return clientes_comisiones
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo clientes: {str(e)}")

@router.get("/{cliente_id}")
async def get_cliente_by_id(cliente_id: int):
    """Obtiene un cliente por ID"""
    try:
        clientes = await get_clientes()
        cliente = next((c for c in clientes if c['id'] == cliente_id), None)
        if not cliente:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        return cliente
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/detalle")
async def get_cliente_detalle(nombre: str = Query(...)):
    """
    Obtiene el detalle completo de un cliente
    Reutiliza la lógica de ui/tabs.py render_clientes_vendedor
    """
    try:
        from database.queries import DatabaseManager
        from database.client_purchases_manager import ClientPurchasesManager
        from supabase import create_client
        from config.settings import AppConfig
        
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        # Obtener datos del cliente (reutilizar lógica existente)
        df = db_manager.cargar_datos()
        df_cliente = df[df['cliente'] == nombre] if not df.empty and 'cliente' in df.columns else pd.DataFrame()
        
        # Obtener cliente B2B si existe
        clientes_manager = ClientPurchasesManager(supabase)
        # ... más lógica de detalle de cliente
        
        return {
            "nombre": nombre,
            "compras": len(df_cliente) if not df_cliente.empty else 0,
            # ... más campos
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
