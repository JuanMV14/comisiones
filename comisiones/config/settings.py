import os
from typing import Dict, Any

class AppConfig:
    """Configuraciones centralizadas de la aplicación"""
    
    # Configuraciones de Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    SUPABASE_BUCKET_COMPROBANTES = os.getenv("SUPABASE_BUCKET_COMPROBANTES", "comprobantes")
    
    # Configuraciones de la aplicación
    APP_TITLE = "CRM Inteligente"
    APP_ICON = "🧠"
    PAGE_LAYOUT = "wide"
    
    # Configuraciones de negocio
    IVA_RATE = 0.19  # 19%
    DESCUENTO_AUTOMATICO = 0.15  # 15%
    
    # Días límite para diferentes condiciones
    DIAS_PAGO_NORMAL = 35
    DIAS_PAGO_ESPECIAL = 60
    DIAS_LIMITE_NORMAL = 45
    DIAS_LIMITE_ESPECIAL = 60
    DIAS_PERDIDA_COMISION = 80
    
    # Porcentajes de comisión
    COMISION_CLIENTE_PROPIO_NORMAL = 2.5
    COMISION_CLIENTE_PROPIO_DESCUENTO = 1.5
    COMISION_CLIENTE_EXTERNO_NORMAL = 1.0
    COMISION_CLIENTE_EXTERNO_DESCUENTO = 0.5
    
    # Configuraciones de cache
    CACHE_TTL_SECONDS = 300  # 5 minutos
    
    # Configuraciones de archivo
    MAX_FILE_SIZE_MB = 10
    ALLOWED_FILE_EXTENSIONS = ['pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx', 'xls', 'xlsx']
    
    # Configuraciones de alertas
    DIAS_ALERTA_VENCIMIENTO = 5
    DIAS_ALERTA_VENCIDO = -5
    PERCENTIL_COMISION_ALTA = 0.8
    
    # Configuraciones de IA y recomendaciones
    MAX_RECOMENDACIONES = 5
    MIN_PROBABILIDAD_RECOMENDACION = 20
    DIAS_CLIENTE_INACTIVO = 60
    DIAS_CLIENTE_RIESGO_ALTO = 90
    
    # Meta por defecto
    META_VENTAS_DEFAULT = 10000000  # 10 millones
    META_CLIENTES_NUEVOS_DEFAULT = 5
    BONO_PORCENTAJE = 0.005  # 0.5%
    
    # Formatos de fecha
    FORMATO_FECHA_DISPLAY = "%d/%m/%Y"
    FORMATO_FECHA_FILENAME = "%Y%m%d_%H%M%S"
    FORMATO_FECHA_ISO = "%Y-%m-%d"
    
    # Configuraciones de UI
    PROGRESS_BAR_COLORS = {
        "high": "#10b981",    # Verde
        "medium": "#f59e0b",  # Amarillo
        "low": "#ef4444"      # Rojo
    }
    
    ALERT_COLORS = {
        "success": "#10b981",
        "warning": "#f59e0b", 
        "error": "#ef4444",
        "info": "#3b82f6"
    }
    
    @classmethod
    def validate_environment(cls) -> Dict[str, Any]:
        """Valida que todas las variables de entorno necesarias estén configuradas"""
        errors = []
        warnings = []
        
        # Variables obligatorias
        required_vars = [
            ("SUPABASE_URL", cls.SUPABASE_URL),
            ("SUPABASE_KEY", cls.SUPABASE_KEY)
        ]
        
        for var_name, var_value in required_vars:
            if not var_value:
                errors.append(f"Variable de entorno faltante: {var_name}")
        
        # Variables opcionales
        optional_vars = [
            ("SUPABASE_BUCKET_COMPROBANTES", cls.SUPABASE_BUCKET_COMPROBANTES)
        ]
        
        for var_name, var_value in optional_vars:
            if not var_value or var_value == var_name.split("_")[-1].lower():
                warnings.append(f"Variable de entorno usando valor por defecto: {var_name}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    @classmethod
    def get_database_config(cls) -> Dict[str, str]:
        """Obtiene configuración de base de datos"""
        return {
            "url": cls.SUPABASE_URL,
            "key": cls.SUPABASE_KEY,
            "bucket": cls.SUPABASE_BUCKET_COMPROBANTES
        }
    
    @classmethod
    def get_business_rules(cls) -> Dict[str, Any]:
        """Obtiene reglas de negocio centralizadas"""
        return {
            "iva_rate": cls.IVA_RATE,
            "descuento_automatico": cls.DESCUENTO_AUTOMATICO,
            "dias_limites": {
                "pago_normal": cls.DIAS_PAGO_NORMAL,
                "pago_especial": cls.DIAS_PAGO_ESPECIAL,
                "limite_normal": cls.DIAS_LIMITE_NORMAL,
                "limite_especial": cls.DIAS_LIMITE_ESPECIAL,
                "perdida_comision": cls.DIAS_PERDIDA_COMISION
            },
            "comisiones": {
                "cliente_propio_normal": cls.COMISION_CLIENTE_PROPIO_NORMAL,
                "cliente_propio_descuento": cls.COMISION_CLIENTE_PROPIO_DESCUENTO,
                "cliente_externo_normal": cls.COMISION_CLIENTE_EXTERNO_NORMAL,
                "cliente_externo_descuento": cls.COMISION_CLIENTE_EXTERNO_DESCUENTO
            }
        }
    
    @classmethod
    def get_ui_config(cls) -> Dict[str, Any]:
        """Obtiene configuración de UI"""
        return {
            "title": cls.APP_TITLE,
            "icon": cls.APP_ICON,
            "layout": cls.PAGE_LAYOUT,
            "colors": {
                "progress": cls.PROGRESS_BAR_COLORS,
                "alerts": cls.ALERT_COLORS
            },
            "formats": {
                "fecha_display": cls.FORMATO_FECHA_DISPLAY,
                "fecha_filename": cls.FORMATO_FECHA_FILENAME,
                "fecha_iso": cls.FORMATO_FECHA_ISO
            }
        }
    
    @classmethod
    def get_file_config(cls) -> Dict[str, Any]:
        """Obtiene configuración de archivos"""
        return {
            "max_size_mb": cls.MAX_FILE_SIZE_MB,
            "allowed_extensions": cls.ALLOWED_FILE_EXTENSIONS,
            "bucket": cls.SUPABASE_BUCKET_COMPROBANTES
        }
    
    @classmethod
    def get_ai_config(cls) -> Dict[str, Any]:
        """Obtiene configuración de IA y recomendaciones"""
        return {
            "max_recomendaciones": cls.MAX_RECOMENDACIONES,
            "min_probabilidad": cls.MIN_PROBABILIDAD_RECOMENDACION,
            "dias_inactivo": cls.DIAS_CLIENTE_INACTIVO,
            "dias_riesgo_alto": cls.DIAS_CLIENTE_RIESGO_ALTO,
            "alertas": {
                "dias_vencimiento": cls.DIAS_ALERTA_VENCIMIENTO,
                "dias_vencido": cls.DIAS_ALERTA_VENCIDO,
                "percentil_comision_alta": cls.PERCENTIL_COMISION_ALTA
            }
        }

class DatabaseTables:
    """Nombres de tablas de la base de datos"""
    
    COMISIONES = "comisiones"
    DEVOLUCIONES = "devoluciones"
    METAS_MENSUALES = "metas_mensuales"
    CLIENTES = "clientes"
    PRODUCTOS = "productos"
    COMERCIALIZADORAS = "comercializadoras"
    PEDIDOS = "pedidos"

class SessionStateKeys:
    """Claves del estado de sesión de Streamlit"""
    
    SHOW_META_CONFIG = "show_meta_config"
    SHOW_META_DETAIL = "show_meta_detail"
    SHOW_NUEVA_DEVOLUCION = "show_nueva_devolucion"
    
    # Prefijos para estados dinámicos
    SHOW_EDIT_PREFIX = "show_edit_"
    SHOW_PAGO_PREFIX = "show_pago_"
    SHOW_DETAIL_PREFIX = "show_detail_"
    SHOW_COMPROBANTE_PREFIX = "show_comprobante_"

class FormKeys:
    """Claves para formularios de Streamlit"""
    
    # Nueva venta
    NUEVA_VENTA_PEDIDO = "nueva_venta_pedido"
    NUEVA_VENTA_CLIENTE = "nueva_venta_cliente"
    NUEVA_VENTA_FACTURA = "nueva_venta_factura"
    NUEVA_VENTA_FECHA = "nueva_venta_fecha"
    NUEVA_VENTA_VALOR = "nueva_venta_valor"
    NUEVA_VENTA_CONDICION = "nueva_venta_condicion"
    NUEVA_VENTA_CLIENTE_PROPIO = "nueva_venta_cliente_propio"
    NUEVA_VENTA_DESCUENTO_PIE = "nueva_venta_descuento_pie"
    NUEVA_VENTA_DESCUENTO_ADICIONAL = "nueva_venta_descuento_adicional"
    
    # Meta configuración
    CONFIG_META_VENTAS = "config_meta_ventas"
    CONFIG_META_CLIENTES = "config_meta_clientes"
    
    # Filtros
    COMISIONES_CLIENTE_FILTER = "comisiones_cliente_filter"
    DEVOLUCIONES_CLIENTE_FILTER = "devoluciones_cliente_filter"
    
    # Devoluciones
    DEVOLUCION_FACTURA_SELECT = "devolucion_factura_select"
    DEVOLUCION_VALOR = "devolucion_valor"
    DEVOLUCION_FECHA = "devolucion_fecha"
    DEVOLUCION_AFECTA = "devolucion_afecta"
    DEVOLUCION_MOTIVO = "devolucion_motivo"

class ErrorMessages:
    """Mensajes de error estandarizados"""
    
    # Base de datos
    DB_CONNECTION_ERROR = "Error de conexión con la base de datos"
    DB_INSERT_ERROR = "Error al insertar datos"
    DB_UPDATE_ERROR = "Error al actualizar datos"
    DB_DELETE_ERROR = "Error al eliminar datos"
    DB_QUERY_ERROR = "Error al consultar datos"
    
    # Validación
    REQUIRED_FIELD = "Este campo es obligatorio"
    INVALID_EMAIL = "El formato del email no es válido"
    INVALID_PHONE = "El formato del teléfono no es válido"
    INVALID_DATE = "La fecha no es válida"
    INVALID_AMOUNT = "El monto debe ser mayor a 0"
    INVALID_PERCENTAGE = "El porcentaje debe estar entre 0 y 100"
    
    # Archivos
    FILE_TOO_LARGE = "El archivo es demasiado grande"
    INVALID_FILE_TYPE = "Tipo de archivo no permitido"
    FILE_UPLOAD_ERROR = "Error al subir el archivo"
    
    # Negocio
    INVOICE_NOT_FOUND = "Factura no encontrada"
    INVOICE_ALREADY_PAID = "Esta factura ya está marcada como pagada"
    COMMISSION_LOST = "Comisión perdida por pago tardío"
    RETURN_EXCEEDS_INVOICE = "El valor a devolver no puede ser mayor al valor de la factura"

class SuccessMessages:
    """Mensajes de éxito estandarizados"""
    
    INVOICE_CREATED = "Factura creada exitosamente"
    INVOICE_UPDATED = "Factura actualizada exitosamente"
    PAYMENT_PROCESSED = "Pago procesado exitosamente"
    RETURN_REGISTERED = "Devolución registrada exitosamente"
    META_UPDATED = "Meta actualizada exitosamente"
    FILE_UPLOADED = "Archivo subido exitosamente"

class InfoMessages:
    """Mensajes informativos estandarizados"""
    
    NO_DATA_AVAILABLE = "No hay datos disponibles"
    NO_FILTERS_MATCH = "No hay registros que coincidan con los filtros"
    LOADING_DATA = "Cargando datos..."
    PROCESSING = "Procesando..."
    CALCULATING = "Calculando..."
