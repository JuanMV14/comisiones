"""
Sistema de validación de flete según reglas de envío
"""

from typing import Dict, Any, Tuple

class FreightValidator:
    """Validador de flete según ciudad y valor base"""
    
    # Umbrales para flete gratis
    UMBRAL_MEDELLIN = 1_500_000
    UMBRAL_BOGOTA = 2_000_000
    UMBRAL_RESTO = 4_000_000
    
    @staticmethod
    def debe_tener_flete(base_comision: float, ciudad_destino: str, recogida_local: bool = False) -> Tuple[bool, str]:
        """
        Determina si un pedido debe tener flete según las reglas
        
        Args:
            base_comision: Valor base del pedido (sin IVA)
            ciudad_destino: "Medellín", "Bogotá", o "Resto"
            recogida_local: Si es recogida local (solo aplica para Medellín)
        
        Returns:
            Tupla (debe_tener_flete, razon)
        """
        # Recogida local NUNCA paga flete
        if recogida_local and ciudad_destino == "Medellín":
            return False, "Recogida local - Sin flete"
        
        # Validar según ciudad
        if ciudad_destino == "Medellín":
            if base_comision >= FreightValidator.UMBRAL_MEDELLIN:
                return False, f"Base ≥ ${FreightValidator.UMBRAL_MEDELLIN:,.0f} - Sin flete"
            else:
                return True, f"Base < ${FreightValidator.UMBRAL_MEDELLIN:,.0f} - Con flete"
        
        elif ciudad_destino == "Bogotá":
            if base_comision >= FreightValidator.UMBRAL_BOGOTA:
                return False, f"Base ≥ ${FreightValidator.UMBRAL_BOGOTA:,.0f} - Sin flete"
            else:
                return True, f"Base < ${FreightValidator.UMBRAL_BOGOTA:,.0f} - Con flete"
        
        else:  # Resto del país
            if base_comision >= FreightValidator.UMBRAL_RESTO:
                return False, f"Base ≥ ${FreightValidator.UMBRAL_RESTO:,.0f} - Sin flete"
            else:
                return True, f"Base < ${FreightValidator.UMBRAL_RESTO:,.0f} - Con flete"
    
    @staticmethod
    def validar_factura(factura: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida si una factura cumple con las reglas de flete
        
        Args:
            factura: Diccionario con datos de la factura
        
        Returns:
            Diccionario con resultado de validación
        """
        base_comision = factura.get('base_comision', 0)
        ciudad_destino = factura.get('ciudad_destino', 'Resto')
        recogida_local = factura.get('recogida_local', False)
        
        debe_tener, razon = FreightValidator.debe_tener_flete(
            base_comision, 
            ciudad_destino, 
            recogida_local
        )
        
        return {
            'debe_tener_flete': debe_tener,
            'razon': razon,
            'ciudad_destino': ciudad_destino,
            'recogida_local': recogida_local,
            'base_comision': base_comision,
            'alerta': FreightValidator._generar_alerta(debe_tener, ciudad_destino, base_comision)
        }
    
    @staticmethod
    def _generar_alerta(debe_tener_flete: bool, ciudad: str, base: float) -> str:
        """Genera mensaje de alerta informativo"""
        if debe_tener_flete:
            return f"⚠️ Este pedido debe incluir flete ({ciudad})"
        else:
            return f"✅ Este pedido NO debe tener flete ({ciudad})"
    
    @staticmethod
    def obtener_umbral_ciudad(ciudad_destino: str) -> float:
        """Retorna el umbral de flete gratis para una ciudad"""
        if ciudad_destino == "Medellín":
            return FreightValidator.UMBRAL_MEDELLIN
        elif ciudad_destino == "Bogotá":
            return FreightValidator.UMBRAL_BOGOTA
        else:
            return FreightValidator.UMBRAL_RESTO
    
    @staticmethod
    def calcular_faltante_flete_gratis(base_comision: float, ciudad_destino: str) -> Dict[str, Any]:
        """
        Calcula cuánto falta para obtener flete gratis
        
        Returns:
            Diccionario con información del faltante
        """
        umbral = FreightValidator.obtener_umbral_ciudad(ciudad_destino)
        
        if base_comision >= umbral:
            return {
                'tiene_flete_gratis': True,
                'faltante': 0,
                'porcentaje_alcanzado': 100
            }
        else:
            faltante = umbral - base_comision
            porcentaje = (base_comision / umbral) * 100
            
            return {
                'tiene_flete_gratis': False,
                'faltante': faltante,
                'porcentaje_alcanzado': porcentaje,
                'umbral': umbral
            }

