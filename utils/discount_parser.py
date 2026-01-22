import re
from typing import Dict, Optional, List


class DiscountParser:
    """Parser para interpretar descuentos por volumen desde DetalleDescuento"""
    
    @staticmethod
    def parse_detalle_descuento(detalle: str) -> Dict[int, float]:
        """
        Parsea el detalle de descuento y retorna un diccionario {cantidad: porcentaje}
        
        Ejemplo:
        "1 UND +10,00%; 12 UND +5,00%;" -> {1: 10.0, 12: 5.0}
        """
        if not detalle or not isinstance(detalle, str):
            return {}
        
        descuentos = {}
        
        # Buscar patrones: número UND +porcentaje%
        # Ejemplo: "1 UND +10,00%; 12 UND +5,00%;"
        pattern = r'(\d+)\s*UND\s*\+?([\d,]+)\s*%'
        matches = re.findall(pattern, detalle, re.IGNORECASE)
        
        for cantidad_str, porcentaje_str in matches:
            try:
                cantidad = int(cantidad_str)
                # Reemplazar coma por punto para decimales
                porcentaje = float(porcentaje_str.replace(',', '.'))
                descuentos[cantidad] = porcentaje
            except ValueError:
                continue
        
        return descuentos
    
    @staticmethod
    def calcular_descuento_por_cantidad(detalle: str, cantidad: int) -> float:
        """
        Calcula el descuento aplicable según la cantidad comprada
        
        Args:
            detalle: String con el detalle de descuento (ej: "1 UND +10,00%; 12 UND +5,00%;")
            cantidad: Cantidad de productos a comprar
        
        Returns:
            Porcentaje de descuento aplicable (0 si no hay descuento)
        """
        descuentos = DiscountParser.parse_detalle_descuento(detalle)
        
        if not descuentos:
            return 0.0
        
        # Buscar el descuento más alto que aplique para la cantidad
        # Si compras 12 unidades, aplica el descuento de 12, no el de 1
        descuento_aplicable = 0.0
        
        for cantidad_min, porcentaje in sorted(descuentos.items(), reverse=True):
            if cantidad >= cantidad_min:
                descuento_aplicable = porcentaje
                break
        
        return descuento_aplicable
    
    @staticmethod
    def obtener_info_descuentos(detalle: str) -> List[Dict[str, any]]:
        """
        Obtiene información formateada de los descuentos disponibles
        
        Returns:
            Lista de diccionarios con {cantidad: int, descuento: float, descripcion: str}
        """
        descuentos = DiscountParser.parse_detalle_descuento(detalle)
        
        if not descuentos:
            return []
        
        info = []
        for cantidad, porcentaje in sorted(descuentos.items()):
            info.append({
                'cantidad': cantidad,
                'descuento': porcentaje,
                'descripcion': f"{cantidad} unidad{'es' if cantidad > 1 else ''}: {porcentaje}%"
            })
        
        return info
