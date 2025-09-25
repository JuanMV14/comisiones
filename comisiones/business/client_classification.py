import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Any, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

class ClientClassifier:
    """Sistema de clasificación de clientes con Machine Learning"""
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        self.pca = PCA(n_components=2)
        self.is_trained = False
        
    def entrenar_modelo(self, meses_historial: int = 12) -> Dict[str, Any]:
        """
        Entrena el modelo de clasificación de clientes
        
        Args:
            meses_historial: Meses de datos históricos para entrenar (recomendado: 12-18 meses)
        """
        try:
            # Obtener datos históricos
            df = self._obtener_datos_entrenamiento(meses_historial)
            
            if df.empty or len(df) < 10:
                return {
                    "success": False,
                    "message": f"No hay suficientes datos para entrenar (mínimo 10 clientes, encontrados: {len(df)})",
                    "recomendacion": "Esperar a tener más datos históricos o reducir meses_historial"
                }
            
            # Preparar features para ML
            features_df = self._preparar_features(df)
            
            # Entrenar modelo
            X_scaled = self.scaler.fit_transform(features_df)
            clusters = self.kmeans.fit_predict(X_scaled)
            
            # Reducir dimensionalidad para visualización
            X_pca = self.pca.fit_transform(X_scaled)
            
            # Analizar clusters
            cluster_analysis = self._analizar_clusters(df, clusters, features_df)
            
            # Guardar modelo entrenado
            self.is_trained = True
            
            return {
                "success": True,
                "clientes_entrenados": len(df),
                "meses_analizados": meses_historial,
                "clusters": cluster_analysis,
                "features_importantes": self._obtener_features_importantes(features_df.columns),
                "recomendacion_tiempo": self._recomendar_tiempo_entrenamiento(len(df))
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error entrenando modelo: {str(e)}",
                "recomendacion": "Verificar datos y configuración"
            }
    
    def _obtener_datos_entrenamiento(self, meses: int) -> pd.DataFrame:
        """Obtiene datos históricos para entrenamiento"""
        df = self.db_manager.cargar_datos()
        
        if df.empty:
            return pd.DataFrame()
        
        # Filtrar por fecha
        fecha_limite = date.today() - timedelta(days=meses * 30)
        df['fecha_factura'] = pd.to_datetime(df['fecha_factura'])
        df = df[df['fecha_factura'].dt.date >= fecha_limite]
        
        return df
    
    def _preparar_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para el modelo de ML"""
        # Agrupar por cliente
        client_features = df.groupby('cliente').agg({
            'valor': ['sum', 'mean', 'count', 'std'],
            'comision': ['sum', 'mean'],
            'dias_pago_real': ['mean', 'std'],
            'fecha_factura': ['min', 'max'],
            'cliente_propio': 'first',
            'descuento_adicional': 'mean'
        }).round(2)
        
        # Aplanar columnas
        client_features.columns = ['_'.join(col).strip() for col in client_features.columns]
        client_features = client_features.reset_index()
        
        # Calcular features adicionales
        client_features['frecuencia_compras'] = client_features['valor_count']
        client_features['ticket_promedio'] = client_features['valor_mean']
        client_features['volumen_total'] = client_features['valor_sum']
        client_features['puntualidad_pago'] = client_features['dias_pago_real_mean']
        client_features['variabilidad_pago'] = client_features['dias_pago_real_std'].fillna(0)
        client_features['antiguedad_cliente'] = (date.today() - pd.to_datetime(client_features['fecha_factura_min']).dt.date).dt.days
        client_features['ultima_compra_dias'] = (date.today() - pd.to_datetime(client_features['fecha_factura_max']).dt.date).dt.days
        client_features['es_cliente_propio'] = client_features['cliente_propio_first'].astype(int)
        client_features['descuento_promedio'] = client_features['descuento_adicional_mean'].fillna(0)
        
        # Seleccionar features para ML
        ml_features = [
            'frecuencia_compras', 'ticket_promedio', 'volumen_total',
            'puntualidad_pago', 'variabilidad_pago', 'antiguedad_cliente',
            'ultima_compra_dias', 'es_cliente_propio', 'descuento_promedio'
        ]
        
        features_df = client_features[ml_features].fillna(0)
        
        return features_df
    
    def _analizar_clusters(self, df: pd.DataFrame, clusters: np.ndarray, features_df: pd.DataFrame) -> Dict[str, Any]:
        """Analiza los clusters encontrados"""
        clientes = df.groupby('cliente').first().reset_index()
        clientes['cluster'] = clusters
        
        cluster_analysis = {}
        
        for cluster_id in range(4):
            cluster_data = clientes[clientes['cluster'] == cluster_id]
            
            if len(cluster_data) == 0:
                continue
                
            # Obtener estadísticas del cluster
            stats = {
                'cantidad_clientes': len(cluster_data),
                'porcentaje_total': len(cluster_data) / len(clientes) * 100,
                'caracteristicas': self._describir_cluster(cluster_data, features_df, cluster_id)
            }
            
            cluster_analysis[f'cluster_{cluster_id}'] = stats
        
        return cluster_analysis
    
    def _describir_cluster(self, cluster_data: pd.DataFrame, features_df: pd.DataFrame, cluster_id: int) -> Dict[str, Any]:
        """Describe las características de un cluster"""
        cluster_features = features_df.iloc[cluster_data.index]
        
        return {
            'nombre': self._asignar_nombre_cluster(cluster_id, cluster_features),
            'descripcion': self._generar_descripcion_cluster(cluster_features),
            'estrategia_recomendada': self._generar_estrategia_cluster(cluster_features),
            'productos_sugeridos': self._sugerir_productos_cluster(cluster_features),
            'metricas_promedio': {
                'frecuencia_compras': cluster_features['frecuencia_compras'].mean(),
                'ticket_promedio': cluster_features['ticket_promedio'].mean(),
                'volumen_total': cluster_features['volumen_total'].mean(),
                'puntualidad_pago': cluster_features['puntualidad_pago'].mean(),
                'antiguedad_dias': cluster_features['antiguedad_cliente'].mean()
            }
        }
    
    def _asignar_nombre_cluster(self, cluster_id: int, features: pd.DataFrame) -> str:
        """Asigna nombre descriptivo al cluster"""
        freq_avg = features['frecuencia_compras'].mean()
        ticket_avg = features['ticket_promedio'].mean()
        puntualidad_avg = features['puntualidad_pago'].mean()
        
        if freq_avg > 5 and ticket_avg > 1000000:
            return "🏆 Clientes VIP"
        elif freq_avg > 3 and puntualidad_avg < 40:
            return "⭐ Clientes Leales"
        elif ticket_avg > 500000:
            return "💰 Clientes de Alto Valor"
        else:
            return "📈 Clientes en Crecimiento"
    
    def _generar_descripcion_cluster(self, features: pd.DataFrame) -> str:
        """Genera descripción del cluster"""
        freq_avg = features['frecuencia_compras'].mean()
        ticket_avg = features['ticket_promedio'].mean()
        puntualidad_avg = features['puntualidad_pago'].mean()
        
        descripciones = []
        
        if freq_avg > 4:
            descripciones.append("Alta frecuencia de compras")
        elif freq_avg > 2:
            descripciones.append("Frecuencia media de compras")
        else:
            descripciones.append("Baja frecuencia de compras")
        
        if ticket_avg > 1000000:
            descripciones.append("tickets altos")
        elif ticket_avg > 500000:
            descripciones.append("tickets medios")
        else:
            descripciones.append("tickets bajos")
        
        if puntualidad_avg < 35:
            descripciones.append("muy puntuales en pagos")
        elif puntualidad_avg < 50:
            descripciones.append("puntuales en pagos")
        else:
            descripciones.append("pagos tardíos")
        
        return ", ".join(descripciones)
    
    def _generar_estrategia_cluster(self, features: pd.DataFrame) -> str:
        """Genera estrategia comercial para el cluster"""
        freq_avg = features['frecuencia_compras'].mean()
        ticket_avg = features['ticket_promedio'].mean()
        puntualidad_avg = features['puntualidad_pago'].mean()
        
        if freq_avg > 4 and ticket_avg > 1000000:
            return "Mantener relación premium, ofrecer productos exclusivos"
        elif freq_avg > 3 and puntualidad_avg < 40:
            return "Fidelización activa, programas de lealtad"
        elif ticket_avg > 500000:
            return "Upselling, productos complementarios de alto valor"
        else:
            return "Desarrollo de relación, aumentar frecuencia de compras"
    
    def _sugerir_productos_cluster(self, features: pd.DataFrame) -> List[str]:
        """Sugiere productos basado en características del cluster"""
        freq_avg = features['frecuencia_compras'].mean()
        ticket_avg = features['ticket_promedio'].mean()
        es_propio_avg = features['es_cliente_propio'].mean()
        
        productos = []
        
        if freq_avg > 4:
            productos.extend(["Productos de consumo frecuente", "Servicios de mantenimiento"])
        
        if ticket_avg > 1000000:
            productos.extend(["Productos premium", "Soluciones empresariales"])
        
        if es_propio_avg > 0.5:
            productos.extend(["Productos exclusivos", "Descuentos especiales"])
        
        if len(productos) == 0:
            productos = ["Productos básicos", "Ofertas de introducción"]
        
        return productos[:3]  # Máximo 3 sugerencias
    
    def _obtener_features_importantes(self, feature_names: List[str]) -> List[str]:
        """Identifica las features más importantes"""
        return [
            "Frecuencia de compras",
            "Ticket promedio", 
            "Volumen total",
            "Puntualidad de pago",
            "Antigüedad del cliente"
        ]
    
    def _recomendar_tiempo_entrenamiento(self, num_clientes: int) -> str:
        """Recomienda tiempo de entrenamiento basado en datos disponibles"""
        if num_clientes >= 50:
            return "12-18 meses (óptimo para modelos robustos)"
        elif num_clientes >= 20:
            return "6-12 meses (suficiente para clasificación básica)"
        else:
            return "3-6 meses (mínimo viable, considerar más datos)"
    
    def clasificar_cliente_nuevo(self, cliente_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clasifica un cliente nuevo basado en el modelo entrenado"""
        if not self.is_trained:
            return {
                "success": False,
                "message": "Modelo no entrenado. Ejecutar entrenar_modelo() primero"
            }
        
        try:
            # Preparar features del cliente nuevo
            features = self._preparar_features_cliente_nuevo(cliente_data)
            
            # Predecir cluster
            X_scaled = self.scaler.transform([features])
            cluster_pred = self.kmeans.predict(X_scaled)[0]
            
            return {
                "success": True,
                "cluster": cluster_pred,
                "caracteristicas": features,
                "recomendaciones": self._generar_recomendaciones_cliente_nuevo(cluster_pred, features)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error clasificando cliente: {str(e)}"
            }
    
    def _preparar_features_cliente_nuevo(self, cliente_data: Dict[str, Any]) -> List[float]:
        """Prepara features para un cliente nuevo"""
        # Valores por defecto para cliente nuevo
        return [
            cliente_data.get('frecuencia_estimada', 1),
            cliente_data.get('ticket_estimado', 500000),
            cliente_data.get('volumen_estimado', 500000),
            cliente_data.get('puntualidad_estimada', 45),
            0,  # variabilidad_pago (desconocida)
            0,  # antiguedad_cliente (nuevo)
            0,  # ultima_compra_dias (nuevo)
            cliente_data.get('es_cliente_propio', 0),
            cliente_data.get('descuento_estimado', 0)
        ]
    
    def _generar_recomendaciones_cliente_nuevo(self, cluster: int, features: List[float]) -> Dict[str, Any]:
        """Genera recomendaciones para cliente nuevo"""
        return {
            "estrategia_inicial": "Enfoque de desarrollo de relación",
            "productos_sugeridos": ["Productos básicos", "Ofertas de introducción"],
            "frecuencia_contacto": "Semanal",
            "descuentos_aplicables": "Descuentos estándar",
            "objetivo_primero": "Establecer confianza y primera compra"
        }
    
    def obtener_recomendaciones_importacion(self, cliente: str) -> Dict[str, Any]:
        """Obtiene recomendaciones específicas para importación de productos"""
        if not self.is_trained:
            return {"error": "Modelo no entrenado"}
        
        try:
            # Obtener datos del cliente
            df = self.db_manager.cargar_datos()
            cliente_data = df[df['cliente'] == cliente]
            
            if cliente_data.empty:
                return {"error": "Cliente no encontrado"}
            
            # Preparar features del cliente
            features_df = self._preparar_features(df)
            cliente_features = features_df[df.groupby('cliente').ngroup() == df[df['cliente'] == cliente].index[0]]
            
            # Predecir cluster
            X_scaled = self.scaler.transform([cliente_features.iloc[0]])
            cluster_pred = self.kmeans.predict(X_scaled)[0]
            
            # Generar recomendaciones específicas
            return {
                "cliente": cliente,
                "cluster": cluster_pred,
                "productos_recomendados": self._generar_productos_importacion(cluster_pred, cliente_features.iloc[0]),
                "mensaje_personalizado": self._generar_mensaje_importacion(cluster_pred, cliente_features.iloc[0]),
                "descuentos_aplicables": self._calcular_descuentos_importacion(cluster_pred),
                "prioridad_contacto": self._calcular_prioridad_contacto(cluster_pred, cliente_features.iloc[0])
            }
            
        except Exception as e:
            return {"error": f"Error generando recomendaciones: {str(e)}"}
    
    def _generar_productos_importacion(self, cluster: int, features: pd.Series) -> List[str]:
        """Genera lista de productos para importación basada en cluster"""
        productos_por_cluster = {
            0: ["Productos premium", "Soluciones empresariales", "Equipos especializados"],
            1: ["Productos de consumo frecuente", "Servicios de mantenimiento", "Repuestos"],
            2: ["Productos de alto valor", "Maquinaria industrial", "Sistemas completos"],
            3: ["Productos básicos", "Ofertas de introducción", "Equipos estándar"]
        }
        
        return productos_por_cluster.get(cluster, ["Productos generales"])
    
    def _generar_mensaje_importacion(self, cluster: int, features: pd.Series) -> str:
        """Genera mensaje personalizado para importación"""
        ticket_promedio = features['ticket_promedio']
        frecuencia = features['frecuencia_compras']
        
        if cluster == 0:  # VIP
            return f"Estimado cliente, tenemos nuevas importaciones premium que se alinean perfectamente con su perfil de alto valor (ticket promedio: ${ticket_promedio:,.0f})."
        elif cluster == 1:  # Leales
            return f"Como cliente frecuente (frecuencia: {frecuencia:.1f} compras), tenemos productos que complementan perfectamente sus necesidades regulares."
        elif cluster == 2:  # Alto valor
            return f"Basado en su historial de compras de alto valor, tenemos importaciones especiales que pueden interesarle."
        else:  # Crecimiento
            return f"Tenemos nuevas importaciones que pueden ser perfectas para expandir su portafolio de productos."
    
    def _calcular_descuentos_importacion(self, cluster: int) -> Dict[str, float]:
        """Calcula descuentos aplicables para importación"""
        descuentos_por_cluster = {
            0: {"descuento_base": 0.15, "descuento_adicional": 0.05},  # VIP
            1: {"descuento_base": 0.10, "descuento_adicional": 0.03},  # Leales
            2: {"descuento_base": 0.12, "descuento_adicional": 0.04},  # Alto valor
            3: {"descuento_base": 0.08, "descuento_adicional": 0.02}   # Crecimiento
        }
        
        return descuentos_por_cluster.get(cluster, {"descuento_base": 0.05, "descuento_adicional": 0.01})
    
    def _calcular_prioridad_contacto(self, cluster: int, features: pd.Series) -> str:
        """Calcula prioridad de contacto para importación"""
        if cluster == 0:  # VIP
            return "ALTA - Contactar en 24 horas"
        elif cluster == 2:  # Alto valor
            return "MEDIA-ALTA - Contactar en 48 horas"
        elif cluster == 1:  # Leales
            return "MEDIA - Contactar en 1 semana"
        else:  # Crecimiento
            return "BAJA - Contactar en 2 semanas"
