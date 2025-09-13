# queries_mejoradas.py
import pandas as pd
from supabase import Client
from datetime import datetime

def cargar_datos(supabase: Client):
    """Carga todas las ventas con cálculos automáticos"""
    try:
        data = supabase.table("comisiones").select("*").execute()
        
        if not data.data:
            return pd.DataFrame()

        df = pd.DataFrame(data.data)

        # Normalizar nombres de columnas si tu tabla usa otros
        if "monto" in df.columns and "valor" not in df.columns:
            df.rename(columns={"monto": "valor"}, inplace=True)

        if "fecha" in df.columns and "fecha_factura" not in df.columns:
            df.rename(columns={"fecha": "fecha_factura"}, inplace=True)

        # Agregar columnas faltantes
        columnas_requeridas = {
            "id": None, "pedido": "", "cliente": "", "factura": "", 
            "valor": 0, "valor_neto": 0, "iva": 0,
            "cliente_propio": False, "descuento_pie_factura": False, 
            "descuento_adicional": 0, "condicion_especial": False,
            "dias_pago_real": None, "valor_devuelto": 0,
            "base_comision": 0, "comision": 0, "porcentaje": 0,
            "comision_ajustada": 0, "comision_perdida": False,
            "razon_perdida": "", "pagado": False,
            "fecha_factura": None, "fecha_pago_est": None, 
            "fecha_pago_max": None, "fecha_pago_real": None,
            "comprobante_url": "", "comprobante_file": "",
            "referencia": "", "created_at": None, "updated_at": None
        }
        
        for col, default_val in columnas_requeridas.items():
            if col not in df.columns:
                df[col] = default_val

        # Procesar fechas
        fecha_cols = ["fecha_factura", "fecha_pago_est", "fecha_pago_max", "fecha_pago_real", "created_at", "updated_at"]
        for col in fecha_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calcular campo mes y días de vencimiento
        df["mes_factura"] = df["fecha_factura"].dt.to_period("M").astype(str)
        hoy = pd.Timestamp.now()
        df["dias_vencimiento"] = (df["fecha_pago_max"] - hoy).dt.days

        return df

    except Exception as e:
        print(f"Error cargando datos: {e}")
        return pd.DataFrame()


def calcular_comision_automatica(row):
    """Calcula comisión automáticamente basado en los datos de la fila"""
    valor_neto = row.get('valor_neto', row.get('valor', 0) / 1.19 if row.get('valor') else 0)
    cliente_propio = row.get('cliente_propio', False)
    descuento_pie_factura = row.get('descuento_pie_factura', False)
    descuento_adicional = row.get('descuento_adicional', 0)
    dias_pago = row.get('dias_pago_real')
    condicion_especial = row.get('condicion_especial', False)
    valor_devuelto = row.get('valor_devuelto', 0)
    
    # 1. Calcular base inicial
    if descuento_pie_factura:
        base = valor_neto
    else:
        limite_dias = 60 if condicion_especial else 45
        if not dias_pago or dias_pago <= limite_dias:
            base = valor_neto * 0.85
        else:
            base = valor_neto
    
    # 2. Restar devoluciones
    base_final = base - valor_devuelto
    
    # 3. Determinar porcentaje
    tiene_descuento_adicional = descuento_adicional > 15
    if cliente_propio:
        porcentaje = 1.5 if tiene_descuento_adicional else 2.5
    else:
        porcentaje = 0.5 if tiene_descuento_adicional else 1.0
    
    # 4. Verificar pérdida por +80 días
    if dias_pago and dias_pago > 80:
        return {
            'comision': 0,
            'base_final': 0,
            'porcentaje': 0,
            'perdida': True
        }
    
    comision = base_final * (porcentaje / 100)
    
    return {
        'comision': comision,
        'base_final': base_final,
        'porcentaje': porcentaje,
        'perdida': False
    }

def insertar_venta(supabase: Client, data: dict):
    """Inserta una nueva venta con todos los campos mejorados"""
    try:
        # Agregar timestamp
        data["created_at"] = datetime.now().isoformat()
        data["updated_at"] = datetime.now().isoformat()
        
        result = supabase.table("comisiones").insert(data).execute()
        
        # También actualizar cliente si no existe
        if data.get("cliente"):
            upsert_cliente(supabase, {
                "nombre": data["cliente"],
                "es_propio": data.get("cliente_propio", False),
                "ultima_compra": data.get("fecha_factura"),
                "ticket_promedio": data.get("valor_neto", 0),
                "descuento_habitual": data.get("descuento_adicional", 0)
            })
        
        return True
    except Exception as e:
        print(f"Error insertando venta completa: {e}")
        return False

def actualizar_factura(supabase: Client, factura_id: int, updates: dict):
    """Actualiza una factura con recálculo automático de comisiones"""
    try:
        # Obtener datos actuales
        current = supabase.table("comisiones").select("*").eq("id", factura_id).execute()
        if not current.data:
            return False
        
        current_data = current.data[0]
        
        # Merge de datos
        merged_data = {**current_data, **updates}
        
        # Recalcular comisión si es necesario
        if any(key in updates for key in ["valor_neto", "dias_pago_real", "valor_devuelto", "descuento_adicional"]):
            comision_calc = calcular_comision_automatica(merged_data)
            updates.update({
                "base_comision": comision_calc["base_final"],
                "comision": comision_calc["comision"],
                "comision_ajustada": comision_calc["comision"],
                "porcentaje": comision_calc["porcentaje"],
                "comision_perdida": comision_calc["perdida"]
            })
        
        updates["updated_at"] = datetime.now().isoformat()
        
        supabase.table("comisiones").update(updates).eq("id", factura_id).execute()
        return True
    except Exception as e:
        print(f"Error actualizando factura completa: {e}")
        return False

def registrar_devolucion(supabase: Client, factura_id: int, valor_devuelto: float, motivo: str):
    """Registra una devolución y recalcula comisiones"""
    try:
        # Insertar en tabla de devoluciones
        devolucion_data = {
            "factura_id": factura_id,
            "valor_devuelto": valor_devuelto,
            "motivo": motivo,
            "fecha_devolucion": datetime.now().date().isoformat()
        }
        
        supabase.table("devoluciones").insert(devolucion_data).execute()
        
        # Actualizar factura con valor devuelto acumulado
        current = supabase.table("comisiones").select("valor_devuelto").eq("id", factura_id).execute()
        valor_actual = current.data[0]["valor_devuelto"] if current.data else 0
        nuevo_total = valor_actual + valor_devuelto
        
        # Actualizar con recálculo automático
        return actualizar_factura_completa(supabase, factura_id, {"valor_devuelto": nuevo_total})
        
    except Exception as e:
        print(f"Error registrando devolución: {e}")
        return False

def cargar_clientes(supabase: Client):
    """Carga todos los clientes"""
    try:
        data = supabase.table("clientes").select("*").execute()
        return data.data if data.data else []
    except Exception as e:
        print(f"Error cargando clientes: {e}")
        return []

def upsert_cliente(supabase: Client, cliente_data: dict):
    """Inserta o actualiza un cliente"""
    try:
        cliente_data["updated_at"] = datetime.now().isoformat()
        
        # Verificar si existe
        existing = supabase.table("clientes").select("id").eq("nombre", cliente_data["nombre"]).execute()
        
        if existing.data:
            # Actualizar
            cliente_id = existing.data[0]["id"]
            supabase.table("clientes").update(cliente_data).eq("id", cliente_id).execute()
        else:
            # Insertar
            cliente_data["created_at"] = datetime.now().isoformat()
            supabase.table("clientes").insert(cliente_data).execute()
        
        return True
    except Exception as e:
        print(f"Error en upsert cliente: {e}")
        return False

def obtener_meta_mes(supabase: Client, mes: str):
    """Obtiene la meta del mes especificado"""
    try:
        data = supabase.table("metas_mensuales").select("*").eq("mes", mes).execute()
        return data.data[0] if data.data else None
    except Exception as e:
        print(f"Error obteniendo meta del mes: {e}")
        return None

def upsert_meta_mes(supabase: Client, mes: str, meta_ventas: float, meta_clientes_nuevos: int):
    """Inserta o actualiza la meta del mes"""
    try:
        meta_data = {
            "mes": mes,
            "meta_ventas": meta_ventas,
            "meta_clientes_nuevos": meta_clientes_nuevos,
            "updated_at": datetime.now().isoformat()
        }
        
        existing = supabase.table("metas_mensuales").select("id").eq("mes", mes).execute()
        
        if existing.data:
            supabase.table("metas_mensuales").update(meta_data).eq("mes", mes).execute()
        else:
            meta_data["created_at"] = datetime.now().isoformat()
            supabase.table("metas_mensuales").insert(meta_data).execute()
        
        return True
    except Exception as e:
        print(f"Error en upsert meta: {e}")
        return False

def actualizar_progreso_meta(supabase: Client, mes: str):
    """Actualiza el progreso actual de la meta del mes"""
    try:
        # Calcular ventas actuales del mes
        df = cargar_datos_completos(supabase)
        df_mes = df[df["mes_factura"] == mes]
        
        ventas_actuales = df_mes[df_mes["pagado"] == True]["valor_neto"].sum()
        
        # Contar clientes nuevos (esto necesitaría lógica adicional)
        clientes_nuevos = len(df_mes["cliente"].unique())  # Simplificado
        
        updates = {
            "ventas_actuales": ventas_actuales,
            "clientes_nuevos_actuales": clientes_nuevos,
            "updated_at": datetime.now().isoformat()
        }
        
        supabase.table("metas_mensuales").update(updates).eq("mes", mes).execute()
        return True
    except Exception as e:
        print(f"Error actualizando progreso meta: {e}")
        return False


# Aliases para compatibilidad
cargar_datos_completos = cargar_datos
insertar_venta_completa = insertar_venta
actualizar_factura_completa = actualizar_factura

