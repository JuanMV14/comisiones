from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path para importar módulos existentes
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

@router.get("/metrics")
async def get_dashboard_metrics() -> Dict[str, Any]:
    """
    Obtiene las métricas principales del dashboard del vendedor
    Reutiliza la lógica de business/calculations.py y database/queries.py
    """
    try:
        # Importar los módulos existentes
        from database.queries import DatabaseManager
        from supabase import create_client
        from config.settings import AppConfig
        
        # Inicializar conexión a Supabase
        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        
        # Obtener datos y calcular métricas (reutilizar tu lógica existente)
        df = db_manager.cargar_datos()
        
        # Calcular métricas (ejemplo - ajustar según tu lógica)
        total_ventas = df['valor'].sum() if not df.empty and 'valor' in df.columns else 0
        comisiones = df['comision'].sum() if not df.empty and 'comision' in df.columns else 0
        clientes_activos = df['cliente'].nunique() if not df.empty and 'cliente' in df.columns else 0
        
        # Calcular pedidos del mes (ejemplo)
        from datetime import datetime
        df_mes = df[df['fecha_factura'].dt.month == datetime.now().month] if not df.empty else df
        pedidos_mes = len(df_mes) if not df_mes.empty else 0
        
        return {
            "totalVentas": float(total_ventas),
            "comisiones": float(comisiones),
            "clientesActivos": int(clientes_activos),
            "pedidosMes": int(pedidos_mes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo métricas: {str(e)}")

@router.get("/sales-chart")
async def get_sales_chart():
    """Obtiene datos para el gráfico de ventas mensuales"""
    try:
        # Reutilizar lógica de business/calculations.py
        return {"message": "Sales chart data - implementar"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/colombia-map")
async def get_colombia_map():
    """Obtiene datos para el mapa de Colombia"""
    try:
        # Reutilizar lógica de análisis geográfico
        return {"message": "Colombia map data - implementar"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
