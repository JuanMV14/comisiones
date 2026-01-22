import pandas as pd
from datetime import datetime
from typing import Any, Optional, List, Dict

def format_currency(value: Any) -> str:
    """Formatea números como moneda colombiana"""
    if pd.isna(value) or value == 0 or value is None:
        return "$0"
    try:
        return f"${float(value):,.0f}".replace(",", ".")
    except (ValueError, TypeError):
        return "$0"

def format_percentage(value: Any, decimals: int = 1) -> str:
    """Formatea números como porcentaje"""
    if pd.isna(value) or value is None:
        return "0%"
    try:
        return f"{float(value):.{decimals}f}%"
    except (ValueError, TypeError):
        return "0%"

def format_date(date_value: Any, format_str: str = "%d/%m/%Y") -> str:
    """Formatea fechas de manera consistente"""
    if pd.isna(date_value) or date_value is None:
        return "N/A"
    
    try:
        if isinstance(date_value, str):
            parsed_date = pd.to_datetime(date_value)
        else:
            parsed_date = date_value
        
        return parsed_date.strftime(format_str)
    except:
        return "N/A"

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Convierte valores a float de manera segura"""
    if value in [None, "NULL", "null", "", "N/A"]:
        return default
    
    try:
        if isinstance(value, str):
            # Limpiar string antes de convertir
            cleaned = value.replace(",", "").replace("$", "").strip()
            if cleaned.replace('.', '').replace('-', '').isdigit():
                return float(cleaned)
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int_conversion(value: Any, default: int = 0) -> int:
    """Convierte valores a int de manera segura"""
    if value in [None, "NULL", "null", "", "N/A"]:
        return default
    
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def safe_string_conversion(value: Any, default: str = "") -> str:
    """Convierte valores a string de manera segura"""
    if value in [None, "NULL", "null"]:
        return default
    
    try:
        return str(value).strip()
    except:
        return default

def safe_bool_conversion(value: Any, default: bool = False) -> bool:
    """Convierte valores a bool de manera segura"""
    if value in [None, "NULL", "null", ""]:
        return default
    
    if isinstance(value, bool):
        return value
    
    if isinstance(value, str):
        return value.lower() in ['true', '1', 'yes', 'si', 'sí']
    
    try:
        return bool(int(value))
    except:
        return default

def calculate_days_between(start_date: Any, end_date: Any) -> Optional[int]:
    """Calcula días entre dos fechas de manera segura"""
    try:
        if pd.isna(start_date) or pd.isna(end_date):
            return None
        
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)
        
        return (end - start).days
    except:
        return None

def validate_email(email: str) -> bool:
    """Valida formato básico de email"""
    if not email or not isinstance(email, str):
        return False
    
    return "@" in email and "." in email.split("@")[-1]

def validate_phone(phone: str) -> bool:
    """Valida formato básico de teléfono"""
    if not phone or not isinstance(phone, str):
        return False
    
    # Remover espacios, guiones y paréntesis
    cleaned = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    
    # Verificar que solo contenga números y tenga longitud apropiada
    return cleaned.isdigit() and 7 <= len(cleaned) <= 15

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Trunca texto a longitud específica"""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def clean_numeric_string(value: str) -> str:
    """Limpia strings que representan números"""
    if not isinstance(value, str):
        return str(value)
    
    # Remover caracteres comunes que no son numéricos
    cleaned = value.replace(",", "").replace("$", "").replace("%", "").strip()
    
    return cleaned

def format_file_size(size_bytes: int) -> str:
    """Formatea tamaños de archivo"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def generate_unique_id(prefix: str = "") -> str:
    """Genera un ID único basado en timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return f"{prefix}_{timestamp}" if prefix else timestamp

def sanitize_filename(filename: str) -> str:
    """Sanitiza nombres de archivo"""
    if not filename:
        return "archivo"
    
    # Caracteres no permitidos en nombres de archivo
    invalid_chars = '<>:"/\\|?*'
    
    for char in invalid_chars:
        filename = filename.replace(char, "_")
    
    return filename.strip()

def parse_csv_row(row: str, delimiter: str = ",") -> List[str]:
    """Parsea una fila de CSV de manera segura"""
    try:
        # Manejo básico de CSV con comillas
        parts = []
        current_part = ""
        in_quotes = False
        
        for char in row:
            if char == '"':
                in_quotes = not in_quotes
            elif char == delimiter and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char
        
        parts.append(current_part.strip())
        return parts
    except:
        return row.split(delimiter)

def format_duration(seconds: int) -> str:
    """Formatea duración en segundos a formato legible"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def normalize_text(text: str) -> str:
    """Normaliza texto para comparaciones"""
    if not text:
        return ""
    
    # Convertir a minúsculas y remover espacios extra
    normalized = text.lower().strip()
    
    # Remover acentos básicos
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ñ': 'n', 'ü': 'u'
    }
    
    for accented, normal in replacements.items():
        normalized = normalized.replace(accented, normal)
    
    return normalized

def validate_monetary_amount(amount: Any, min_value: float = 0, max_value: float = float('inf')) -> bool:
    """Valida que un monto monetario esté en rango válido"""
    try:
        value = safe_float_conversion(amount)
        return min_value <= value <= max_value
    except:
        return False

def extract_numbers_from_string(text: str) -> List[float]:
    """Extrae todos los números de un string"""
    import re
    
    if not text:
        return []
    
    # Buscar patrones de números (incluyendo decimales)
    pattern = r'-?\d+(?:\.\d+)?'
    matches = re.findall(pattern, text)
    
    try:
        return [float(match) for match in matches]
    except:
        return []

def create_summary_dict(data: List[Dict], group_by: str, value_field: str) -> Dict[str, float]:
    """Crea un diccionario resumen agrupando datos"""
    summary = {}
    
    for item in data:
        if group_by in item and value_field in item:
            key = item[group_by]
            value = safe_float_conversion(item[value_field])
            
            if key in summary:
                summary[key] += value
            else:
                summary[key] = value
    
    return summary

def calculate_percentage_change(old_value: float, new_value: float) -> float:
    """Calcula el porcentaje de cambio entre dos valores"""
    if old_value == 0:
        return 100.0 if new_value > 0 else 0.0
    
    return ((new_value - old_value) / old_value) * 100

def format_percentage_change(old_value: float, new_value: float, show_sign: bool = True) -> str:
    """Formatea el cambio porcentual con signo"""
    change = calculate_percentage_change(old_value, new_value)
    
    if show_sign:
        sign = "+" if change > 0 else ""
        return f"{sign}{change:.1f}%"
    else:
        return f"{abs(change):.1f}%"

class CalculationHelpers:
    """Funciones helper para cálculos comunes y evitar duplicación de código"""
    
    @staticmethod
    def calcular_valor_neto_desde_total(valor_total: float, valor_flete: float = 0) -> float:
        """
        Calcula valor_neto desde valor_total considerando flete
        
        Args:
            valor_total: Valor total incluyendo IVA y flete
            valor_flete: Valor del flete (opcional)
        
        Returns:
            Valor neto (sin IVA, sin flete)
        """
        valor_sin_flete = valor_total - valor_flete
        return valor_sin_flete / 1.19
    
    @staticmethod
    def calcular_iva_desde_total(valor_total: float, valor_flete: float = 0) -> float:
        """
        Calcula IVA desde valor_total considerando flete
        
        Args:
            valor_total: Valor total incluyendo IVA y flete
            valor_flete: Valor del flete (opcional)
        
        Returns:
            Valor del IVA
        """
        valor_sin_flete = valor_total - valor_flete
        valor_neto = valor_sin_flete / 1.19
        return valor_sin_flete - valor_neto
    
    @staticmethod
    def calcular_valor_neto_ajustado_por_devoluciones(valor_neto: float, valor_devuelto: float) -> float:
        """
        Calcula valor_neto ajustado restando devoluciones
        (valor_devuelto incluye IVA, se divide por 1.19)
        
        Args:
            valor_neto: Valor neto original
            valor_devuelto: Valor devuelto (incluye IVA)
        
        Returns:
            Valor neto ajustado
        """
        return valor_neto - (valor_devuelto / 1.19)
    
    @staticmethod
    def validar_consistencia_valores(valor: float, valor_neto: float, iva: float, valor_flete: float = 0) -> bool:
        """
        Valida que valor = valor_neto + IVA + flete
        
        Args:
            valor: Valor total
            valor_neto: Valor neto
            iva: IVA
            valor_flete: Flete (opcional)
        
        Returns:
            True si son consistentes (diferencia <= 1), False en caso contrario
        """
        valor_calculado = valor_neto + iva + valor_flete
        diferencia = abs(valor - valor_calculado)
        return diferencia <= 1


class DataValidator:
    """Clase para validar estructuras de datos"""
    
    @staticmethod
    def validate_venta_data(data: Dict) -> List[str]:
        """Valida los datos de una venta"""
        errors = []
        
        # Campos obligatorios
        required_fields = ['pedido', 'cliente', 'valor']
        for field in required_fields:
            if not data.get(field):
                errors.append(f"Campo '{field}' es obligatorio")
        
        # Validaciones de tipo y rango
        if data.get('valor'):
            if not validate_monetary_amount(data['valor'], min_value=1):
                errors.append("El valor debe ser mayor a 0")
        
        if data.get('descuento_adicional'):
            descuento = safe_float_conversion(data['descuento_adicional'])
            if descuento < 0 or descuento > 100:
                errors.append("El descuento debe estar entre 0 y 100%")
        
        if data.get('email') and not validate_email(data['email']):
            errors.append("El formato del email no es válido")
        
        if data.get('telefono') and not validate_phone(data['telefono']):
            errors.append("El formato del teléfono no es válido")
        
        return errors
    
    @staticmethod
    def validate_cliente_data(data: Dict) -> List[str]:
        """Valida los datos de un cliente"""
        errors = []
        
        if not data.get('nombre'):
            errors.append("El nombre del cliente es obligatorio")
        
        if data.get('email') and not validate_email(data['email']):
            errors.append("El formato del email no es válido")
        
        if data.get('telefono') and not validate_phone(data['telefono']):
            errors.append("El formato del teléfono no es válido")
        
        return errors

# Constantes útiles
MONTHS_ES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
    5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
    9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}

DAYS_ES = {
    0: 'Lunes', 1: 'Martes', 2: 'Miércoles', 3: 'Jueves',
    4: 'Viernes', 5: 'Sábado', 6: 'Domingo'
}

# Aliases para compatibilidad con código anterior
calcular_comision_legacy = safe_float_conversion
format_money = format_currency
validate_required_fields = DataValidator.validate_venta_data
