import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Optional
from collections import Counter
import streamlit as st

class ClientProductRecommendations:
    """Sistema de recomendaciones de productos basado en historial de compras y catálogo de inventario"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.inventario_df = None
        self.historial_compras = None
    
    def cargar_inventario_csv(self, archivo_csv) -> Dict[str, Any]:
        """Carga el CSV de inventario con todas las referencias disponibles (método legacy)"""
        try:
            # Leer CSV
            df = pd.read_csv(archivo_csv)
            
            # Validar columnas mínimas requeridas
            columnas_requeridas = ['referencia']
            columnas_faltantes = [col for col in columnas_requeridas if col not in df.columns]
            
            if columnas_faltantes:
                return {
                    "error": f"El CSV debe contener al menos la columna 'referencia'. Faltan: {', '.join(columnas_faltantes)}"
                }
            
            # Normalizar nombres de columnas (case insensitive)
            df.columns = df.columns.str.strip().str.lower()
            
            # Normalizar referencia
            df['referencia'] = df['referencia'].astype(str).str.strip().str.upper()
            
            # Eliminar duplicados
            df = df.drop_duplicates(subset=['referencia'], keep='first')
            
            self.inventario_df = df
            
            return {
                "success": True,
                "total_referencias": len(df),
                "columnas_disponibles": list(df.columns)
            }
            
        except Exception as e:
            return {
                "error": f"Error cargando CSV: {str(e)}"
            }
    
    def cargar_inventario_desde_bd(self, catalog_manager) -> Dict[str, Any]:
        """Carga el inventario desde la base de datos"""
        try:
            df = catalog_manager.cargar_catalogo()
            
            if df.empty:
                return {
                    "error": "No hay productos en el catálogo. Por favor, actualiza el catálogo primero."
                }
            
            # Mapear columnas del catálogo
            if 'referencia' in df.columns:
                df['referencia'] = df['referencia'].astype(str).str.strip().str.upper()
            
            # Usar 'linea' como 'categoria' si existe
            if 'linea' in df.columns and 'categoria' not in df.columns:
                df['categoria'] = df['linea']
            
            self.inventario_df = df
            
            return {
                "success": True,
                "total_referencias": len(df),
                "columnas_disponibles": list(df.columns)
            }
            
        except Exception as e:
            return {
                "error": f"Error cargando inventario desde BD: {str(e)}"
            }
    
    def generar_recomendaciones_clientes(self) -> Dict[str, Any]:
        """Genera recomendaciones para todos los clientes basadas en historial y inventario"""
        try:
            # Validar que el inventario esté cargado
            if self.inventario_df is None or self.inventario_df.empty:
                return {
                    "error": "Debe cargar primero el CSV de inventario"
                }
            
            # Cargar historial de compras
            df_compras = self.db_manager.cargar_datos()
            
            if df_compras.empty:
                return {
                    "error": "No hay datos de compras disponibles"
                }
            
            # Validar que exista columna referencia
            if 'referencia' not in df_compras.columns:
                return {
                    "error": "La base de datos no contiene información de referencias de productos"
                }
            
            self.historial_compras = df_compras
            
            # Obtener lista de clientes
            clientes_unicos = df_compras['cliente'].unique()
            
            recomendaciones_todas = []
            
            for cliente in clientes_unicos:
                recomendaciones_cliente = self._generar_recomendaciones_cliente(cliente, df_compras)
                if recomendaciones_cliente:
                    recomendaciones_todas.extend(recomendaciones_cliente)
            
            # Ordenar por prioridad
            recomendaciones_todas.sort(key=lambda x: self._calcular_score_prioridad(x), reverse=True)
            
            return {
                "success": True,
                "total_recomendaciones": len(recomendaciones_todas),
                "total_clientes": len(clientes_unicos),
                "recomendaciones": recomendaciones_todas
            }
            
        except Exception as e:
            return {
                "error": f"Error generando recomendaciones: {str(e)}"
            }
    
    def _generar_recomendaciones_cliente(self, cliente: str, df_compras: pd.DataFrame) -> List[Dict[str, Any]]:
        """Genera recomendaciones para un cliente específico"""
        recomendaciones = []
        
        # Filtrar compras del cliente
        df_cliente = df_compras[df_compras['cliente'] == cliente].copy()
        
        if df_cliente.empty:
            return []
        
        # Convertir fecha_factura a datetime si no lo es
        if 'fecha_factura' in df_cliente.columns:
            df_cliente['fecha_factura'] = pd.to_datetime(df_cliente['fecha_factura'], errors='coerce')
        
        # Limpiar referencias
        df_cliente['referencia'] = df_cliente['referencia'].astype(str).str.strip().str.upper()
        df_cliente = df_cliente[df_cliente['referencia'].notna() & (df_cliente['referencia'] != 'NAN')]
        
        if df_cliente.empty:
            return []
        
        # 1. PRODUCTOS ABANDONADOS: Que compraba antes y ya no compra
        productos_abandonados = self._identificar_productos_abandonados(df_cliente)
        for producto in productos_abandonados:
            if producto['referencia'] in self.inventario_df['referencia'].values:
                recomendaciones.append({
                    "cliente": cliente,
                    "referencia": producto['referencia'],
                    "tipo_recomendacion": "Producto Abandonado",
                    "razon": producto['razon'],
                    "ultima_compra": producto['ultima_compra'],
                    "frecuencia_historica": producto['frecuencia'],
                    "valor_promedio": producto['valor_promedio'],
                    "prioridad": "Alta",
                    "categoria": self._obtener_categoria(producto['referencia']),
                    "dias_sin_comprar": producto['dias_sin_comprar']
                })
        
        # 2. PRODUCTOS COMPLEMENTARIOS: Basados en hábitos de compra
        productos_complementarios = self._identificar_productos_complementarios(df_cliente)
        for producto in productos_complementarios:
            if producto['referencia'] in self.inventario_df['referencia'].values:
                recomendaciones.append({
                    "cliente": cliente,
                    "referencia": producto['referencia'],
                    "tipo_recomendacion": "Producto Complementario",
                    "razon": producto['razon'],
                    "ultima_compra": None,
                    "frecuencia_historica": 0,
                    "valor_promedio": None,
                    "prioridad": producto['prioridad'],
                    "categoria": self._obtener_categoria(producto['referencia']),
                    "dias_sin_comprar": None
                })
        
        # 3. PRODUCTOS SIMILARES: Basados en categorías que compra
        productos_similares = self._identificar_productos_similares(df_cliente)
        for producto in productos_similares:
            if producto['referencia'] in self.inventario_df['referencia'].values:
                recomendaciones.append({
                    "cliente": cliente,
                    "referencia": producto['referencia'],
                    "tipo_recomendacion": "Producto Similar",
                    "razon": producto['razon'],
                    "ultima_compra": None,
                    "frecuencia_historica": 0,
                    "valor_promedio": None,
                    "prioridad": producto['prioridad'],
                    "categoria": self._obtener_categoria(producto['referencia']),
                    "dias_sin_comprar": None
                })
        
        return recomendaciones
    
    def _identificar_productos_abandonados(self, df_cliente: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identifica productos que el cliente compraba antes pero ya no compra"""
        productos_abandonados = []
        
        # Agrupar por referencia
        productos_historial = df_cliente.groupby('referencia').agg({
            'fecha_factura': ['max', 'min', 'count'],
            'valor': 'mean'
        }).reset_index()
        
        productos_historial.columns = ['referencia', 'ultima_compra', 'primera_compra', 'frecuencia', 'valor_promedio']
        
        # Calcular días desde última compra
        fecha_hoy = date.today()
        productos_historial['dias_sin_comprar'] = productos_historial['ultima_compra'].apply(
            lambda x: (fecha_hoy - x.date()).days if pd.notna(x) else 999
        )
        
        # Calcular frecuencia promedio de compra
        productos_historial['dias_entre_compras'] = (
            productos_historial['ultima_compra'] - productos_historial['primera_compra']
        ).dt.days / productos_historial['frecuencia']
        
        # Identificar productos abandonados (más de 2 veces la frecuencia promedio sin comprar)
        for _, row in productos_historial.iterrows():
            dias_esperados = row['dias_entre_compras'] * 2 if row['dias_entre_compras'] > 0 else 60
            dias_sin_comprar = row['dias_sin_comprar']
            
            if dias_sin_comprar > dias_esperados and row['frecuencia'] >= 2:
                razon = f"Compraba cada {int(row['dias_entre_compras'])} días aproximadamente, lleva {dias_sin_comprar} días sin comprar"
                productos_abandonados.append({
                    "referencia": row['referencia'],
                    "ultima_compra": row['ultima_compra'],
                    "frecuencia": int(row['frecuencia']),
                    "valor_promedio": float(row['valor_promedio']),
                    "dias_sin_comprar": int(dias_sin_comprar),
                    "razon": razon
                })
        
        return productos_abandonados
    
    def _identificar_productos_complementarios(self, df_cliente: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identifica productos complementarios basados en patrones de compra"""
        productos_complementarios = []
        
        # Obtener referencias que el cliente compra frecuentemente
        referencias_frecuentes = df_cliente['referencia'].value_counts().head(10).index.tolist()
        
        # Buscar productos relacionados en el inventario
        if 'categoria' in self.inventario_df.columns:
            # Si hay categorías, buscar productos de las mismas categorías
            categorias_cliente = self.inventario_df[
                self.inventario_df['referencia'].isin(referencias_frecuentes)
            ]['categoria'].unique() if 'categoria' in self.inventario_df.columns else []
            
            productos_relacionados = self.inventario_df[
                (self.inventario_df['categoria'].isin(categorias_cliente)) &
                (~self.inventario_df['referencia'].isin(df_cliente['referencia'].unique()))
            ]
            
            for _, producto in productos_relacionados.head(5).iterrows():
                productos_complementarios.append({
                    "referencia": producto['referencia'],
                    "razon": f"Producto complementario en categoría {producto.get('categoria', 'N/A')} que compra frecuentemente",
                    "prioridad": "Media"
                })
        else:
            # Si no hay categorías, sugerir productos del inventario que no ha comprado
            referencias_cliente = set(df_cliente['referencia'].unique())
            productos_disponibles = self.inventario_df[
                ~self.inventario_df['referencia'].isin(referencias_cliente)
            ]
            
            for _, producto in productos_disponibles.head(5).iterrows():
                productos_complementarios.append({
                    "referencia": producto['referencia'],
                    "razon": "Producto disponible que podría complementar sus compras habituales",
                    "prioridad": "Baja"
                })
        
        return productos_complementarios
    
    def _identificar_productos_similares(self, df_cliente: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identifica productos similares basados en lo que compra"""
        productos_similares = []
        
        # Obtener referencias más compradas
        referencias_top = df_cliente['referencia'].value_counts().head(5).index.tolist()
        
        # Buscar productos similares en inventario
        referencias_cliente = set(df_cliente['referencia'].unique())
        productos_disponibles = self.inventario_df[
            ~self.inventario_df['referencia'].isin(referencias_cliente)
        ]
        
        # Si hay descripción o nombre, buscar similitudes
        if 'descripcion' in self.inventario_df.columns or 'nombre' in self.inventario_df.columns:
            col_desc = 'descripcion' if 'descripcion' in self.inventario_df.columns else 'nombre'
            
            # Obtener palabras clave de productos que compra
            palabras_clave = []
            for ref in referencias_top:
                producto_inv = self.inventario_df[self.inventario_df['referencia'] == ref]
                if not producto_inv.empty:
                    desc = str(producto_inv[col_desc].iloc[0]).lower()
                    palabras_clave.extend(desc.split()[:3])  # Primeras 3 palabras
            
            # Buscar productos con palabras similares
            for _, producto in productos_disponibles.iterrows():
                desc = str(producto.get(col_desc, '')).lower()
                palabras_comunes = sum(1 for palabra in palabras_clave if palabra in desc)
                
                if palabras_comunes >= 1:
                    productos_similares.append({
                        "referencia": producto['referencia'],
                        "razon": f"Producto similar a los que suele comprar",
                        "prioridad": "Media"
                    })
                    
                    if len(productos_similares) >= 5:
                        break
        
        return productos_similares
    
    def _obtener_categoria(self, referencia: str) -> str:
        """Obtiene la categoría de un producto del inventario"""
        if self.inventario_df is None or self.inventario_df.empty:
            return "N/A"
        
        producto = self.inventario_df[self.inventario_df['referencia'] == referencia]
        if not producto.empty and 'categoria' in producto.columns:
            return str(producto['categoria'].iloc[0])
        return "N/A"
    
    def _calcular_score_prioridad(self, recomendacion: Dict[str, Any]) -> int:
        """Calcula un score numérico para ordenar por prioridad"""
        score = 0
        
        # Prioridad Alta = 30, Media = 20, Baja = 10
        prioridades = {"Alta": 30, "Media": 20, "Baja": 10}
        score += prioridades.get(recomendacion.get('prioridad', 'Baja'), 10)
        
        # Productos abandonados tienen más peso
        if recomendacion.get('tipo_recomendacion') == "Producto Abandonado":
            score += 20
            # Más días sin comprar = más urgente
            dias = recomendacion.get('dias_sin_comprar', 0)
            if dias:
                score += min(dias // 30, 10)  # Máximo 10 puntos adicionales
        
        # Productos con mayor frecuencia histórica
        frecuencia = recomendacion.get('frecuencia_historica', 0)
        if frecuencia:
            score += min(frecuencia, 10)  # Máximo 10 puntos
        
        return score

