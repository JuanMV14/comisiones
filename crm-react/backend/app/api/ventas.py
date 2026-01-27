from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime, date, timedelta
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio raíz al path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
sys.path.insert(0, project_root)

load_dotenv()

router = APIRouter()

# Modelo para nueva venta
class NuevaVentaData(BaseModel):
    pedido: str
    cliente: str
    factura: Optional[str] = None
    fecha_factura: str  # ISO format
    valor_total: float
    condicion_especial: bool = False
    cliente_propio: bool = True
    descuento_pie_factura: bool = False
    descuento_adicional: float = 0.0
    ciudad_destino: str = "Resto"
    recogida_local: bool = False
    valor_flete: float = 0.0
    cliente_nit: Optional[str] = None
    referencia: Optional[str] = None

@router.post("/nueva-venta")
async def crear_nueva_venta(venta_data: NuevaVentaData):
    """
    Crea una nueva venta
    Reutiliza la lógica de ui/tabs.py _procesar_nueva_venta
    """
    try:
        from database.queries import DatabaseManager
        from business.calculations import ComisionCalculator
        from supabase import create_client
        from config.settings import AppConfig

        env_status = AppConfig.validate_environment()
        if not env_status["valid"]:
            raise HTTPException(status_code=500, detail="Faltan variables de entorno")

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        db_manager = DatabaseManager(supabase)
        comision_calc = ComisionCalculator()

        # Parsear fecha
        fecha_factura = datetime.fromisoformat(venta_data.fecha_factura.replace('Z', '+00:00')).date()
        
        # Calcular fechas de pago
        dias_pago = 60 if venta_data.condicion_especial else 35
        dias_max = 60 if venta_data.condicion_especial else 45
        fecha_pago_est = fecha_factura + timedelta(days=dias_pago)
        fecha_pago_max = fecha_factura + timedelta(days=dias_max)

        # Calcular valores
        valor_productos_con_iva = venta_data.valor_total - venta_data.valor_flete
        valor_neto_calculado = valor_productos_con_iva / 1.19
        iva_calculado = valor_productos_con_iva - valor_neto_calculado

        # Calcular comisión
        total_con_descuento_pie = valor_neto_calculado + iva_calculado
        tiene_descuento_adicional = venta_data.descuento_adicional > 0
        
        calc = comision_calc.calcular_comision_inteligente(
            total_con_descuento_pie,
            venta_data.cliente_propio,
            tiene_descuento_adicional,
            venta_data.descuento_pie_factura
        )

        # Preparar datos para insertar
        data = {
            "pedido": venta_data.pedido,
            "cliente": venta_data.cliente,
            "factura": venta_data.factura if venta_data.factura else f"FAC-{venta_data.pedido}",
            "valor": float(venta_data.valor_total),
            "valor_neto": float(valor_neto_calculado),
            "iva": float(iva_calculado),
            "base_comision": float(calc['base_comision']),
            "comision": float(calc['comision']),
            "porcentaje": float(calc['porcentaje']),
            "fecha_factura": fecha_factura.isoformat(),
            "fecha_pago_est": fecha_pago_est.isoformat(),
            "fecha_pago_max": fecha_pago_max.isoformat(),
            "cliente_propio": venta_data.cliente_propio,
            "descuento_pie_factura": venta_data.descuento_pie_factura,
            "descuento_adicional": float(venta_data.descuento_adicional),
            "condicion_especial": venta_data.condicion_especial,
            "ciudad_destino": venta_data.ciudad_destino,
            "recogida_local": venta_data.recogida_local,
            "valor_flete": float(venta_data.valor_flete),
            "pagado": False
        }

        # Agregar referencia si existe
        if venta_data.referencia:
            data["referencia"] = venta_data.referencia

        # Insertar venta
        venta_insertada = db_manager.insertar_venta(data)
        
        if not venta_insertada:
            raise HTTPException(status_code=400, detail="Error al insertar la venta")

        # Obtener ID de la factura insertada
        factura_response = supabase.table("comisiones").select("id").eq(
            "pedido", venta_data.pedido
        ).eq("cliente", venta_data.cliente).order("created_at", desc=True).limit(1).execute()

        factura_id = factura_response.data[0]['id'] if factura_response.data else None

        return {
            "success": True,
            "message": "Venta creada exitosamente",
            "venta_id": factura_id,
            "factura": data["factura"],
            "comision": float(calc['comision'])
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando venta: {str(e)}")
