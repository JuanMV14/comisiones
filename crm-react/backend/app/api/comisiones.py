from fastapi import APIRouter, HTTPException
from typing import Dict, Any

router = APIRouter()

@router.get("")
async def get_comisiones():
    """
    Obtiene las comisiones del vendedor
    Reutiliza business/calculations.py y business/monthly_commission_calculator.py
    """
    try:
        # Reutilizar lógica existente
        return {"message": "Comisiones - implementar"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
