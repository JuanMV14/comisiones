"""
Sistema de Machine Learning y Analytics Avanzado
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
import warnings
warnings.filterwarnings('ignore')

@dataclass
class PredictionResult:
    """Resultado de predicción"""
    fecha: date
    valor_predicho: float
    confianza: float
    intervalo_inferior: float
    intervalo_superior: float

class MLAnalytics:
    """Sistema de Machine Learning y Analytics Avanzado"""
    
    def __init__(self, db_manager=None):
        self.db_manager = db_manager
    
    # ========================================
    # PREDICCIÓN DE VENTAS
    # ========================================
    
    def predict_sales(
        self,
        df: pd.DataFrame,
        periods: int = 30,
        confidence: float = 0.95
    ) -> Dict[str, Any]:
        """
        Predice ventas futuras usando regresión lineal y tendencias
        
        Args:
            df: DataFrame con histórico de ventas
            periods: Días a predecir
            confidence: Nivel de confianza (0-1)
            
        Returns:
            Dict con predicciones y métricas
        """
        if df.empty:
            return self._empty_prediction()
        
        try:
            # Preparar datos
            df_prep = df[df['pagado'] == True].copy()
            df_prep['fecha_pago_real'] = pd.to_datetime(df_prep['fecha_pago_real'])
            
            # Agrupar por día
            daily = df_prep.groupby(df_prep['fecha_pago_real'].dt.date)['valor'].sum().reset_index()
            daily.columns = ['fecha', 'valor']
            daily['fecha'] = pd.to_datetime(daily['fecha'])
            
            if len(daily) < 30:
                return {
                    "error": "Insuficientes datos históricos (mínimo 30 días)",
                    "dias_disponibles": len(daily)
                }
            
            # Crear features
            daily['dia_num'] = (daily['fecha'] - daily['fecha'].min()).dt.days
            
            # Modelo simple: Regresión lineal
            from sklearn.linear_model import LinearRegression
            from sklearn.metrics import r2_score, mean_absolute_error
            
            X = daily[['dia_num']].values
            y = daily['valor'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            # Predecir en datos históricos (para métricas)
            y_pred_hist = model.predict(X)
            r2 = r2_score(y, y_pred_hist)
            mae = mean_absolute_error(y, y_pred_hist)
            
            # Predecir futuro
            ultimo_dia = daily['dia_num'].max()
            futuro_dias = np.array([[ultimo_dia + i] for i in range(1, periods + 1)])
            predicciones_futuro = model.predict(futuro_dias)
            
            # Calcular intervalo de confianza
            std_error = np.std(y - y_pred_hist)
            z_score = 1.96 if confidence == 0.95 else 2.576  # 95% o 99%
            
            predicciones_lista = []
            fecha_inicio = daily['fecha'].max() + timedelta(days=1)
            
            for i, pred in enumerate(predicciones_futuro):
                fecha_pred = fecha_inicio + timedelta(days=i)
                intervalo = z_score * std_error
                
                predicciones_lista.append({
                    "fecha": fecha_pred.date(),
                    "valor_predicho": max(0, pred),
                    "intervalo_inferior": max(0, pred - intervalo),
                    "intervalo_superior": pred + intervalo,
                    "confianza": confidence
                })
            
            # Tendencia
            tendencia = "Creciente" if model.coef_[0] > 0 else "Decreciente"
            cambio_diario = model.coef_[0]
            
            # Suma total predicha
            total_predicho = sum(p["valor_predicho"] for p in predicciones_lista)
            
            return {
                "predicciones": predicciones_lista,
                "total_predicho": total_predicho,
                "tendencia": tendencia,
                "cambio_diario": cambio_diario,
                "r2_score": r2,
                "mae": mae,
                "datos_historicos": len(daily),
                "modelo": "Regresión Lineal",
                "confianza_modelo": "Alta" if r2 > 0.7 else "Media" if r2 > 0.4 else "Baja"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # ANÁLISIS RFM
    # ========================================
    
    def rfm_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Análisis RFM (Recency, Frequency, Monetary) de clientes
        
        Returns:
            Dict con segmentación RFM de clientes
        """
        if df.empty:
            return {"error": "No hay datos disponibles"}
        
        try:
            # Filtrar solo pagadas
            df_pagadas = df[df['pagado'] == True].copy()
            df_pagadas['fecha_pago_real'] = pd.to_datetime(df_pagadas['fecha_pago_real'])
            
            # Calcular métricas RFM
            hoy = pd.Timestamp.now()
            
            rfm = df_pagadas.groupby('cliente').agg({
                'fecha_pago_real': lambda x: (hoy - x.max()).days,  # Recency
                'id': 'count',  # Frequency
                'valor': 'sum'  # Monetary
            })
            
            rfm.columns = ['Recency', 'Frequency', 'Monetary']
            
            # Calcular scores (1-5, donde 5 es mejor)
            rfm['R_Score'] = pd.qcut(rfm['Recency'], q=5, labels=[5, 4, 3, 2, 1], duplicates='drop')
            rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            rfm['M_Score'] = pd.qcut(rfm['Monetary'], q=5, labels=[1, 2, 3, 4, 5], duplicates='drop')
            
            # Score total
            rfm['RFM_Score'] = rfm['R_Score'].astype(int) + rfm['F_Score'].astype(int) + rfm['M_Score'].astype(int)
            
            # Segmentación
            def segment_cliente(row):
                r, f, m = int(row['R_Score']), int(row['F_Score']), int(row['M_Score'])
                
                if r >= 4 and f >= 4 and m >= 4:
                    return "Champions"  # Mejores clientes
                elif r >= 4 and f >= 3:
                    return "Loyal Customers"  # Leales
                elif r >= 4 and f <= 2:
                    return "Promising"  # Prometedores
                elif r >= 3 and f >= 3 and m >= 3:
                    return "Potential Loyalists"  # Potencial leales
                elif r >= 3 and f <= 2 and m <= 2:
                    return "New Customers"  # Nuevos
                elif r <= 2 and f >= 3 and m >= 3:
                    return "At Risk"  # En riesgo
                elif r <= 2 and f >= 4 and m >= 4:
                    return "Can't Lose Them"  # No perderlos
                elif r <= 2:
                    return "Lost"  # Perdidos
                else:
                    return "Need Attention"  # Necesitan atención
            
            rfm['Segmento'] = rfm.apply(segment_cliente, axis=1)
            
            # Estadísticas por segmento
            segmentos = rfm.groupby('Segmento').agg({
                'Recency': 'mean',
                'Frequency': ['mean', 'count'],
                'Monetary': 'sum'
            }).round(2)
            
            segmentos.columns = ['Recency_Avg', 'Frequency_Avg', 'Clientes', 'Revenue_Total']
            segmentos = segmentos.reset_index()
            
            # Convertir a lista de diccionarios
            segmentos_list = segmentos.to_dict('records')
            
            # Top clientes por segmento
            top_champions = rfm[rfm['Segmento'] == 'Champions'].nlargest(5, 'Monetary')
            at_risk = rfm[rfm['Segmento'] == 'At Risk'].nlargest(5, 'Monetary')
            
            return {
                "rfm_data": rfm.reset_index().to_dict('records'),
                "segmentos": segmentos_list,
                "top_champions": top_champions.reset_index().to_dict('records'),
                "at_risk": at_risk.reset_index().to_dict('records'),
                "total_clientes": len(rfm),
                "descripcion_segmentos": {
                    "Champions": "Mejores clientes: compran recientemente, frecuentemente y gastan mucho",
                    "Loyal Customers": "Clientes leales: compran regularmente",
                    "At Risk": "En riesgo: antes eran buenos, ahora no compran",
                    "Can't Lose Them": "No perderlos: grandes gastadores que no han comprado recientemente",
                    "Lost": "Perdidos: hace mucho no compran",
                    "Promising": "Prometedores: compradores recientes con potencial",
                    "New Customers": "Clientes nuevos: compraron recientemente pero poco",
                    "Potential Loyalists": "Potencial leales: buenos clientes a desarrollar",
                    "Need Attention": "Necesitan atención: por debajo del promedio"
                }
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # DETECCIÓN DE ANOMALÍAS
    # ========================================
    
    def detect_anomalies(
        self,
        df: pd.DataFrame,
        threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detecta anomalías en ventas usando Z-Score
        
        Args:
            df: DataFrame con ventas
            threshold: Umbral de Z-Score (default: 2.0 = outliers moderados)
            
        Returns:
            Dict con anomalías detectadas
        """
        if df.empty:
            return {"error": "No hay datos disponibles"}
        
        try:
            df_pagadas = df[df['pagado'] == True].copy()
            
            # Calcular estadísticas
            mean_valor = df_pagadas['valor'].mean()
            std_valor = df_pagadas['valor'].std()
            
            # Calcular Z-Score
            df_pagadas['z_score'] = (df_pagadas['valor'] - mean_valor) / std_valor
            
            # Identificar anomalías
            anomalias = df_pagadas[abs(df_pagadas['z_score']) > threshold].copy()
            anomalias = anomalias.sort_values('z_score', ascending=False)
            
            # Clasificar anomalías
            anomalias['tipo'] = anomalias['z_score'].apply(
                lambda x: 'Valor Extremadamente Alto' if x > threshold 
                else 'Valor Extremadamente Bajo'
            )
            
            return {
                "total_anomalias": len(anomalias),
                "anomalias_altas": len(anomalias[anomalias['z_score'] > threshold]),
                "anomalias_bajas": len(anomalias[anomalias['z_score'] < -threshold]),
                "anomalias": anomalias[[
                    'cliente', 'factura', 'valor', 'fecha_factura', 'z_score', 'tipo'
                ]].to_dict('records'),
                "mean_valor": mean_valor,
                "std_valor": std_valor,
                "threshold": threshold
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # CLUSTERING DE CLIENTES
    # ========================================
    
    def cluster_clients(
        self,
        df: pd.DataFrame,
        n_clusters: int = 4
    ) -> Dict[str, Any]:
        """
        Agrupa clientes automáticamente usando K-Means
        
        Args:
            df: DataFrame con ventas
            n_clusters: Número de clusters a crear
            
        Returns:
            Dict con clusters y características
        """
        if df.empty:
            return {"error": "No hay datos disponibles"}
        
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            
            # Preparar datos
            df_pagadas = df[df['pagado'] == True].copy()
            
            # Agregar por cliente
            cliente_features = df_pagadas.groupby('cliente').agg({
                'valor': ['sum', 'mean', 'count'],
                'comision': 'sum'
            })
            
            cliente_features.columns = ['_'.join(col).strip() for col in cliente_features.columns.values]
            cliente_features.columns = ['Total_Ventas', 'Ticket_Promedio', 'Num_Compras', 'Total_Comision']
            
            # Normalizar datos
            scaler = StandardScaler()
            features_scaled = scaler.fit_transform(cliente_features)
            
            # K-Means
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cliente_features['Cluster'] = kmeans.fit_predict(features_scaled)
            
            # Características de cada cluster
            cluster_stats = cliente_features.groupby('Cluster').agg({
                'Total_Ventas': 'mean',
                'Ticket_Promedio': 'mean',
                'Num_Compras': 'mean',
                'Total_Comision': 'mean'
            }).round(2)
            
            # Nombrar clusters
            cluster_stats['Nombre'] = [
                "Clientes Premium" if row['Total_Ventas'] > cluster_stats['Total_Ventas'].median() * 1.5
                else "Clientes Frecuentes" if row['Num_Compras'] > cluster_stats['Num_Compras'].median()
                else "Clientes Alto Ticket" if row['Ticket_Promedio'] > cluster_stats['Ticket_Promedio'].median()
                else "Clientes Estándar"
                for _, row in cluster_stats.iterrows()
            ]
            
            cluster_stats['Clientes'] = cliente_features.groupby('Cluster').size().values
            
            return {
                "n_clusters": n_clusters,
                "cluster_stats": cluster_stats.reset_index().to_dict('records'),
                "clientes_por_cluster": cliente_features.reset_index().to_dict('records'),
                "total_clientes": len(cliente_features)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # PREDICCIÓN DE CHURN
    # ========================================
    
    def predict_churn(
        self,
        df: pd.DataFrame,
        dias_inactivo: int = 60
    ) -> Dict[str, Any]:
        """
        Predice qué clientes están en riesgo de abandonar
        
        Args:
            df: DataFrame con ventas
            dias_inactivo: Días sin comprar para considerar en riesgo
            
        Returns:
            Dict con clientes en riesgo
        """
        if df.empty:
            return {"error": "No hay datos disponibles"}
        
        try:
            df_pagadas = df[df['pagado'] == True].copy()
            df_pagadas['fecha_pago_real'] = pd.to_datetime(df_pagadas['fecha_pago_real'])
            
            # Última compra por cliente
            ultima_compra = df_pagadas.groupby('cliente').agg({
                'fecha_pago_real': 'max',
                'valor': ['sum', 'count'],
                'comision': 'sum'
            })
            
            ultima_compra.columns = ['Ultima_Compra', 'Total_Comprado', 'Num_Compras', 'Total_Comision']
            
            # Días desde última compra
            hoy = pd.Timestamp.now()
            ultima_compra['Dias_Inactivo'] = (hoy - ultima_compra['Ultima_Compra']).dt.days
            
            # Calcular promedio de días entre compras
            compras_por_cliente = df_pagadas.groupby('cliente')['fecha_pago_real'].apply(
                lambda x: x.diff().dt.days.mean()
            )
            ultima_compra['Promedio_Dias_Entre_Compras'] = compras_por_cliente
            
            # Score de riesgo de churn (0-100)
            ultima_compra['Churn_Score'] = np.clip(
                (ultima_compra['Dias_Inactivo'] / ultima_compra['Promedio_Dias_Entre_Compras'] * 50) +
                (50 if ultima_compra['Dias_Inactivo'] > dias_inactivo else 0),
                0, 100
            )
            
            # Clasificar riesgo
            ultima_compra['Riesgo'] = pd.cut(
                ultima_compra['Churn_Score'],
                bins=[0, 30, 60, 100],
                labels=['Bajo', 'Medio', 'Alto']
            )
            
            # Clientes en riesgo alto
            alto_riesgo = ultima_compra[ultima_compra['Riesgo'] == 'Alto'].copy()
            alto_riesgo = alto_riesgo.nlargest(20, 'Total_Comprado')  # Top 20 por valor
            
            # Clientes en riesgo medio
            medio_riesgo = ultima_compra[ultima_compra['Riesgo'] == 'Medio'].copy()
            medio_riesgo = medio_riesgo.nlargest(20, 'Total_Comprado')
            
            return {
                "total_clientes": len(ultima_compra),
                "alto_riesgo_count": len(ultima_compra[ultima_compra['Riesgo'] == 'Alto']),
                "medio_riesgo_count": len(ultima_compra[ultima_compra['Riesgo'] == 'Medio']),
                "bajo_riesgo_count": len(ultima_compra[ultima_compra['Riesgo'] == 'Bajo']),
                "alto_riesgo": alto_riesgo.reset_index().to_dict('records'),
                "medio_riesgo": medio_riesgo.reset_index().to_dict('records'),
                "valor_en_riesgo": alto_riesgo['Total_Comprado'].sum(),
                "dias_inactivo_threshold": dias_inactivo
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # ANÁLISIS DE TENDENCIAS
    # ========================================
    
    def trend_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Análisis de tendencias de ventas (semanal, mensual, trimestral)
        
        Returns:
            Dict con análisis de tendencias
        """
        if df.empty:
            return {"error": "No hay datos disponibles"}
        
        try:
            df_pagadas = df[df['pagado'] == True].copy()
            df_pagadas['fecha_pago_real'] = pd.to_datetime(df_pagadas['fecha_pago_real'])
            
            # Tendencia semanal
            df_pagadas['semana'] = df_pagadas['fecha_pago_real'].dt.to_period('W')
            semanal = df_pagadas.groupby('semana')['valor'].sum().reset_index()
            semanal['semana'] = semanal['semana'].astype(str)
            
            # Tendencia mensual
            df_pagadas['mes'] = df_pagadas['fecha_pago_real'].dt.to_period('M')
            mensual = df_pagadas.groupby('mes')['valor'].sum().reset_index()
            mensual['mes'] = mensual['mes'].astype(str)
            
            # Calcular crecimiento
            if len(mensual) >= 2:
                ultimo_mes = mensual.iloc[-1]['valor']
                penultimo_mes = mensual.iloc[-2]['valor']
                crecimiento_mensual = ((ultimo_mes - penultimo_mes) / penultimo_mes * 100) if penultimo_mes > 0 else 0
            else:
                crecimiento_mensual = 0
            
            # Mejor mes
            if not mensual.empty:
                mejor_mes = mensual.loc[mensual['valor'].idxmax()]
            else:
                mejor_mes = {"mes": "N/A", "valor": 0}
            
            return {
                "semanal": semanal.to_dict('records'),
                "mensual": mensual.to_dict('records'),
                "crecimiento_mensual": crecimiento_mensual,
                "mejor_mes": mejor_mes.to_dict(),
                "promedio_semanal": semanal['valor'].mean() if not semanal.empty else 0,
                "promedio_mensual": mensual['valor'].mean() if not mensual.empty else 0
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    # ========================================
    # UTILIDADES
    # ========================================
    
    def _empty_prediction(self) -> Dict:
        """Retorna estructura vacía de predicción"""
        return {
            "predicciones": [],
            "total_predicho": 0,
            "tendencia": "N/A",
            "error": "No hay datos suficientes"
        }
    
    def install_dependencies(self) -> Dict[str, bool]:
        """
        Verifica e instala dependencias de ML
        
        Returns:
            Dict con estado de cada librería
        """
        libs = {
            "sklearn": False,
            "numpy": False,
            "pandas": False
        }
        
        try:
            import sklearn
            libs["sklearn"] = True
        except ImportError:
            pass
        
        try:
            import numpy
            libs["numpy"] = True
        except ImportError:
            pass
        
        try:
            import pandas
            libs["pandas"] = True
        except ImportError:
            pass
        
        return libs

