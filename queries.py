# queries_organizadas.py
import pandas as pd
from supabase import Client
from datetime import datetime

def cargar_datos(supabase: Client):
    """Carga todas las ventas desde la tabla pedidos y relacionadas"""
    try:
        # Traer todos los pedidos con joins a las tablas relacionadas
        response = supabase.table("pedidos").select("""
            *,
            clientes:cliente_id(
                cliente_id,
                nombre_cliente,
                email_cliente,
                telefono_cliente,
                direccion_cliente,
                ciudad_cliente,
                pais_cliente,
                fecha_registro
            ),
            comercializadoras:comercializadora_id(
                comercializadora_id,
                nombre_comercializadora,
                email_comercializadora,
                telefono_comercializadora
            ),
            productos:producto_id(
                producto_id,
                nombre_producto,
                categoria_producto,
                precio_producto,
                stock_producto,
                descripcion_producto
            )
        """).execute()
        
        if not response.data:
            return pd.DataFrame()

        df = pd.DataFrame(response.data)

        # Mapear columnas de tu base de datos
        columnas_requeridas = {
            "pedido_id": None,
            "cliente_id": None,
            "comercializadora_id": None, 
            "producto_id": None,
            "cantidad_pedido": 0,
            "precio_unitario": 0,
            "total_pedido": 0,
            "fecha_pedido": None,
            "estado_pedido": "",
            "fecha_entrega": None,
            "direccion_entrega": "",
            "ciudad_entrega": "",
            "pais_entrega": "",
            "metodo_pago": "",
            "descuento_aplicado": 0,
            "iva_pedido": 0,
            "total_con_iva": 0,
            "observaciones_pedido": "",
            "created_at": None,
            "updated_at": None,
            # Campos calculados para comisiones
            "valor_neto": 0,
            "cliente_propio": False,
            "descuento_pie_factura": False,
            "condicion_especial": False,
            "dias_pago_real": None,
            "valor_devuelto": 0,
            "base_comision": 0,
            "comision": 0,
            "porcentaje": 0,
            "comision_ajustada": 0,
            "comision_perdida": False,
            "razon_perdida": "",
            "pagado": False,
            "fecha_pago_est": None,
            "fecha_pago_max": None,
            "fecha_pago_real": None,
            "comprobante_url": "",
            "referencia": ""
        }

        for col, default in columnas_requeridas.items():
            if col not in df.columns:
                df[col] = default

        # Calcular campos derivados
        df["valor_neto"] = df["total_pedido"] / 1.19  # Assuming IVA 19%
        df["total_con_iva"] = df.get("total_con_iva", df["total_pedido"])
        
        # Procesar fechas
        fecha_cols = ["fecha_pedido", "fecha_entrega", "fecha_pago_est", "fecha_pago_max", 
                     "fecha_pago_real", "created_at", "updated_at"]
        for col in fecha_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce")

        # Calcular mes del pedido y días de vencimiento
        df["mes_pedido"] = df["fecha_pedido"].dt.to_period("M").astype(str)
        hoy = pd.Timestamp.now()
        df["dias_vencimiento"] = (df["fecha_pago_max"] - hoy).dt.days

        # Determinar si cliente es propio (basado en comercializadora)
        # Esto lo puedes ajustar según tu lógica de negocio
        df["cliente_propio"] = df["comercializadora_id"].notna()

        # Calcular comisión automáticamente
        comisiones = df.apply(calcular_comision_automatica, axis=1)
        df["base_comision"] = [c["base_final"] for c in comisiones]
        df["comision"] = [c["comision"] for c in comisiones]
        df["porcentaje"] = [c["porcentaje"] for c in comisiones]
        df["comision_perdida"] = [c["perdida"] for c in comisiones]
        df["comision_ajustada"] = df["comision"]

        return df

    except Exception as e:
        print(f"Error cargando datos desde Supabase: {e}")
        return pd.DataFrame()


def calcular_comision_automatica(row):
    """Calcula comisión automáticamente basado en los datos de la fila"""
    valor_neto = row.get('valor_neto', row.get('total_pedido', 0) / 1.19 if row.get('total_pedido') else 0)
    cliente_propio = row.get('cliente_propio', False)
    descuento_pie_factura = row.get('descuento_pie_factura', False)
    descuento_aplicado = row.get('descuento_aplicado', 0)
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
    tiene_descuento_alto = descuento_aplicado > 15
    if cliente_propio:
        porcentaje = 1.5 if tiene_descuento_alto else 2.5
    else:
        porcentaje = 0.5 if tiene_descuento_alto else 1.0
    
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


def insertar_pedido(supabase: Client, data: dict):
    """Inserta un nuevo pedido con todos los campos"""
    try:
        # Mapear datos al esquema de pedidos
        pedido_data = {
            "cliente_id": data.get("cliente_id"),
            "comercializadora_id": data.get("comercializadora_id"),
            "producto_id": data.get("producto_id"),
            "cantidad_pedido": data.get("cantidad_pedido", 1),
            "precio_unitario": data.get("precio_unitario", 0),
            "total_pedido": data.get("total_pedido", 0),
            "fecha_pedido": data.get("fecha_pedido", datetime.now().date().isoformat()),
            "estado_pedido": data.get("estado_pedido", "pendiente"),
            "fecha_entrega": data.get("fecha_entrega"),
            "direccion_entrega": data.get("direccion_entrega", ""),
            "ciudad_entrega": data.get("ciudad_entrega", ""),
            "pais_entrega": data.get("pais_entrega", ""),
            "metodo_pago": data.get("metodo_pago", ""),
            "descuento_aplicado": data.get("descuento_aplicado", 0),
            "iva_pedido": data.get("iva_pedido", 0),
            "total_con_iva": data.get("total_con_iva", 0),
            "observaciones_pedido": data.get("observaciones_pedido", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("pedidos").insert(pedido_data).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"Error insertando pedido: {e}")
        return None


def actualizar_pedido(supabase: Client, pedido_id: int, updates: dict):
    """Actualiza un pedido existente"""
    try:
        updates["updated_at"] = datetime.now().isoformat()
        result = supabase.table("pedidos").update(updates).eq("pedido_id", pedido_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error actualizando pedido: {e}")
        return None


def cargar_clientes(supabase: Client):
    """Carga todos los clientes con sus datos completos"""
    try:
        response = supabase.table("clientes").select("""
            cliente_id,
            nombre_cliente,
            email_cliente,
            telefono_cliente,
            direccion_cliente,
            ciudad_cliente,
            pais_cliente,
            fecha_registro,
            created_at,
            updated_at
        """).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error cargando clientes: {e}")
        return []


def insertar_cliente(supabase: Client, cliente_data: dict):
    """Inserta un nuevo cliente"""
    try:
        data = {
            "nombre_cliente": cliente_data.get("nombre_cliente"),
            "email_cliente": cliente_data.get("email_cliente"),
            "telefono_cliente": cliente_data.get("telefono_cliente"),
            "direccion_cliente": cliente_data.get("direccion_cliente"),
            "ciudad_cliente": cliente_data.get("ciudad_cliente"),
            "pais_cliente": cliente_data.get("pais_cliente"),
            "fecha_registro": cliente_data.get("fecha_registro", datetime.now().date().isoformat()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("clientes").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error insertando cliente: {e}")
        return None


def actualizar_cliente(supabase: Client, cliente_id: int, updates: dict):
    """Actualiza un cliente existente"""
    try:
        updates["updated_at"] = datetime.now().isoformat()
        result = supabase.table("clientes").update(updates).eq("cliente_id", cliente_id).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error actualizando cliente: {e}")
        return None


def cargar_productos(supabase: Client):
    """Carga todos los productos"""
    try:
        response = supabase.table("productos").select("""
            producto_id,
            nombre_producto,
            categoria_producto,
            precio_producto,
            stock_producto,
            descripcion_producto,
            created_at,
            updated_at
        """).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error cargando productos: {e}")
        return []


def insertar_producto(supabase: Client, producto_data: dict):
    """Inserta un nuevo producto"""
    try:
        data = {
            "nombre_producto": producto_data.get("nombre_producto"),
            "categoria_producto": producto_data.get("categoria_producto"),
            "precio_producto": producto_data.get("precio_producto", 0),
            "stock_producto": producto_data.get("stock_producto", 0),
            "descripcion_producto": producto_data.get("descripcion_producto", ""),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        result = supabase.table("productos").insert(data).execute()
        return result.data[0] if result.data else None
    except Exception as e:
        print(f"Error insertando producto: {e}")
        return None


def cargar_comercializadoras(supabase: Client):
    """Carga todas las comercializadoras"""
    try:
        response = supabase.table("comercializadoras").select("""
            comercializadora_id,
            nombre_comercializadora,
            email_comercializadora,
            telefono_comercializadora,
            direccion_comercializadora,
            ciudad_comercializadora,
            pais_comercializadora,
            created_at,
            updated_at
        """).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error cargando comercializadoras: {e}")
        return []


def obtener_ventas_por_mes(supabase: Client, mes: str):
    """Obtiene todas las ventas de un mes específico"""
    try:
        # Convertir mes string a rango de fechas
        año, mes_num = mes.split('-')
        fecha_inicio = f"{año}-{mes_num}-01"
        
        # Calcular último día del mes
        if mes_num == '02':
            if int(año) % 4 == 0:
                fecha_fin = f"{año}-{mes_num}-29"
            else:
                fecha_fin = f"{año}-{mes_num}-28"
        elif mes_num in ['04', '06', '09', '11']:
            fecha_fin = f"{año}-{mes_num}-30"
        else:
            fecha_fin = f"{año}-{mes_num}-31"
        
        response = supabase.table("pedidos").select("*").gte("fecha_pedido", fecha_inicio).lte("fecha_pedido", fecha_fin).execute()
        
        return response.data if response.data else []
    except Exception as e:
        print(f"Error obteniendo ventas del mes: {e}")
        return []


def registrar_devolucion(supabase: Client, pedido_id: int, valor_devuelto: float, motivo: str):
    """Registra una devolución para un pedido"""
    try:
        # Si tienes tabla de devoluciones
        devolucion_data = {
            "pedido_id": pedido_id,
            "valor_devuelto": valor_devuelto,
            "motivo_devolucion": motivo,
            "fecha_devolucion": datetime.now().date().isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        result = supabase.table("devoluciones").insert(devolucion_data).execute()
        
        # Actualizar el pedido para recalcular comisión si es necesario
        return actualizar_pedido(supabase, pedido_id, {"valor_devuelto": valor_devuelto})
        
    except Exception as e:
        print(f"Error registrando devolución: {e}")
        return False


# Funciones auxiliares para reportes
def obtener_resumen_ventas_mes(supabase: Client, mes: str):
    """Obtiene un resumen de ventas del mes"""
    ventas = obtener_ventas_por_mes(supabase, mes)
    df = pd.DataFrame(ventas)
    
    if df.empty:
        return {
            "total_ventas": 0,
            "total_pedidos": 0,
            "ticket_promedio": 0,
            "clientes_unicos": 0
        }
    
    return {
        "total_ventas": df["total_pedido"].sum(),
        "total_pedidos": len(df),
        "ticket_promedio": df["total_pedido"].mean(),
        "clientes_unicos": df["cliente_id"].nunique()
    }


def obtener_top_productos(supabase: Client, mes: str = None, limit: int = 10):
    """Obtiene los productos más vendidos"""
    try:
        query = supabase.table("pedidos").select("""
            producto_id,
            productos:producto_id(nombre_producto),
            cantidad_pedido,
            total_pedido
        """)
        
        if mes:
            año, mes_num = mes.split('-')
            fecha_inicio = f"{año}-{mes_num}-01"
            query = query.gte("fecha_pedido", fecha_inicio)
        
        response = query.execute()
        df = pd.DataFrame(response.data)
        
        if df.empty:
            return []
        
        # Agrupar por producto
        top = df.groupby(['producto_id']).agg({
            'cantidad_pedido': 'sum',
            'total_pedido': 'sum'
        }).reset_index()
        
        return top.head(limit).to_dict('records')
        
    except Exception as e:
        print(f"Error obteniendo top productos: {e}")
        return []


# Aliases para compatibilidad con el código anterior
cargar_datos_completos = cargar_datos
insertar_venta = insertar_pedido
insertar_venta_completa = insertar_pedido
actualizar_factura = actualizar_pedido
actualizar_factura_completa = actualizar_pedido
