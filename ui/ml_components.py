"""
Componentes UI para Machine Learning y Analytics
"""

import streamlit as st
from typing import Dict, Any, List
import plotly.graph_objects as go
import plotly.express as px
from business.ml_analytics import MLAnalytics
from ui.theme_manager import ThemeManager
from utils.formatting import format_currency
import pandas as pd

class MLComponentsUI:
    """Interfaz de usuario para ML y Analytics"""
    
    def __init__(self, ml_analytics: MLAnalytics):
        self.ml = ml_analytics
    
    def render_ml_dashboard(self, df: pd.DataFrame):
        """Renderiza el dashboard completo de ML & Analytics"""
        
        theme = ThemeManager.get_theme()
        
        # Título
        st.markdown(
            f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1 style='
                    font-size: 2.5rem;
                    font-weight: 800;
                    background: {theme['gradient_4']};
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 0.5rem;
                '>
                    🤖 IA y Analytics Avanzado
                </h1>
                <p style='color: {theme['text_secondary']}; font-size: 1rem;'>
                    Machine Learning · Predicciones · Análisis Inteligente
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Verificar dependencias
        deps = self.ml.install_dependencies()
        if not all(deps.values()):
            st.error("⚠️ Faltan dependencias de ML. Instala: `pip install scikit-learn`")
            return
        
        # Tabs principales
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📈 Predicción Ventas",
            "🎯 Análisis RFM",
            "🔍 Anomalías",
            "🏷️ Clustering",
            "⚠️ Predicción Churn",
            "📊 Tendencias"
        ])
        
        with tab1:
            self._render_sales_prediction(df)
        
        with tab2:
            self._render_rfm_analysis(df)
        
        with tab3:
            self._render_anomaly_detection(df)
        
        with tab4:
            self._render_clustering(df)
        
        with tab5:
            self._render_churn_prediction(df)
        
        with tab6:
            self._render_trend_analysis(df)
    
    def _render_sales_prediction(self, df: pd.DataFrame):
        """Renderiza predicción de ventas"""
        
        st.markdown("### 📈 Predicción de Ventas con Machine Learning")
        st.info("🤖 Usamos regresión lineal para predecir ventas futuras basadas en histórico")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            st.markdown("#### ⚙️ Configuración")
            
            periods = st.slider(
                "Días a Predecir",
                min_value=7,
                max_value=90,
                value=30,
                key="pred_periods"
            )
            
            confidence = st.select_slider(
                "Nivel de Confianza",
                options=[0.90, 0.95, 0.99],
                value=0.95,
                format_func=lambda x: f"{x*100:.0f}%",
                key="pred_confidence"
            )
            
            if st.button("🚀 Generar Predicción", type="primary", use_container_width=True):
                with st.spinner("Entrenando modelo..."):
                    result = self.ml.predict_sales(df, periods, confidence)
                    st.session_state['prediction_result'] = result
        
        with col2:
            st.markdown("#### 📊 Resultados de la Predicción")
            
            if 'prediction_result' not in st.session_state:
                st.info("👈 Configura los parámetros y genera la predicción")
                return
            
            result = st.session_state['prediction_result']
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                if "dias_disponibles" in result:
                    st.warning(f"⚠️ Solo hay {result['dias_disponibles']} días de datos históricos")
                return
            
            # Métricas principales
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Predicho",
                    format_currency(result['total_predicho']),
                    help=f"Ventas estimadas para {periods} días"
                )
            
            with col2:
                st.metric(
                    "Tendencia",
                    result['tendencia'],
                    delta=format_currency(result['cambio_diario']) + "/día",
                    help="Cambio promedio diario"
                )
            
            with col3:
                st.metric(
                    "R² Score",
                    f"{result['r2_score']:.3f}",
                    help="Calidad del modelo (0-1, mayor es mejor)"
                )
            
            with col4:
                st.metric(
                    "Confianza Modelo",
                    result['confianza_modelo'],
                    help="Basado en R² score"
                )
            
            # Gráfico de predicción
            st.markdown("---")
            self._render_prediction_chart(result)
            
            # Tabla de predicciones
            with st.expander("📋 Ver Tabla de Predicciones Detallada"):
                pred_df = pd.DataFrame(result['predicciones'])
                pred_df['fecha'] = pd.to_datetime(pred_df['fecha'])
                pred_df['valor_predicho'] = pred_df['valor_predicho'].apply(format_currency)
                pred_df['intervalo_inferior'] = pred_df['intervalo_inferior'].apply(format_currency)
                pred_df['intervalo_superior'] = pred_df['intervalo_superior'].apply(format_currency)
                st.dataframe(pred_df, use_container_width=True)
    
    def _render_rfm_analysis(self, df: pd.DataFrame):
        """Renderiza análisis RFM"""
        
        st.markdown("### 🎯 Análisis RFM de Clientes")
        st.info("📊 RFM = Recency (Recencia), Frequency (Frecuencia), Monetary (Monetario)")
        
        with st.spinner("Analizando clientes..."):
            result = self.ml.rfm_analysis(df)
        
        if "error" in result:
            st.error(f"❌ {result['error']}")
            return
        
        # Métricas generales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Clientes", result['total_clientes'])
        
        with col2:
            champions = len([s for s in result['segmentos'] if s['Segmento'] == 'Champions'])
            st.metric("Champions", champions, help="Mejores clientes")
        
        with col3:
            at_risk = len([s for s in result['segmentos'] if s['Segmento'] == 'At Risk'])
            st.metric("En Riesgo", at_risk, delta=f"-{at_risk}", delta_color="inverse")
        
        with col4:
            lost = len([s for s in result['segmentos'] if s['Segmento'] == 'Lost'])
            st.metric("Perdidos", lost, delta=f"-{lost}", delta_color="inverse")
        
        st.markdown("---")
        
        # Gráfico de segmentos
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Distribución de Segmentos")
            self._render_rfm_segments_chart(result['segmentos'])
        
        with col2:
            st.markdown("#### 💰 Revenue por Segmento")
            self._render_rfm_revenue_chart(result['segmentos'])
        
        st.markdown("---")
        
        # Tabla de segmentos
        st.markdown("### 📋 Detalles por Segmento")
        
        segmentos_df = pd.DataFrame(result['segmentos'])
        segmentos_df['Revenue_Total'] = segmentos_df['Revenue_Total'].apply(format_currency)
        segmentos_df['Recency_Avg'] = segmentos_df['Recency_Avg'].apply(lambda x: f"{x:.0f} días")
        segmentos_df['Frequency_Avg'] = segmentos_df['Frequency_Avg'].apply(lambda x: f"{x:.1f}")
        
        st.dataframe(segmentos_df, use_container_width=True)
        
        # Champions y At Risk
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🏆 Top 5 Champions")
            if result['top_champions']:
                for champion in result['top_champions'][:5]:
                    with st.expander(f"👑 {champion['cliente']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Recencia", f"{champion['Recency']} días")
                            st.metric("Frecuencia", champion['Frequency'])
                        with col_b:
                            st.metric("Monetario", format_currency(champion['Monetary']))
                            st.metric("Score RFM", champion['RFM_Score'])
            else:
                st.info("No hay champions aún")
        
        with col2:
            st.markdown("### ⚠️ Top 5 En Riesgo")
            if result['at_risk']:
                for at_risk_client in result['at_risk'][:5]:
                    with st.expander(f"⚠️ {at_risk_client['cliente']}"):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("Recencia", f"{at_risk_client['Recency']} días")
                            st.metric("Frecuencia", at_risk_client['Frequency'])
                        with col_b:
                            st.metric("Monetario", format_currency(at_risk_client['Monetary']))
                            st.warning("💡 Acción requerida: Contactar pronto")
            else:
                st.success("✅ No hay clientes en riesgo")
        
        # Descripción de segmentos
        with st.expander("📖 ¿Qué significan los segmentos?"):
            for seg, desc in result['descripcion_segmentos'].items():
                st.markdown(f"**{seg}**: {desc}")
    
    def _render_anomaly_detection(self, df: pd.DataFrame):
        """Renderiza detección de anomalías"""
        
        st.markdown("### 🔍 Detección de Anomalías en Ventas")
        st.info("⚡ Identificamos ventas inusuales (muy altas o muy bajas) usando análisis estadístico")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            threshold = st.slider(
                "Sensibilidad",
                min_value=1.5,
                max_value=3.0,
                value=2.0,
                step=0.5,
                help="Z-Score threshold (menor = más sensible)",
                key="anomaly_threshold"
            )
            
            if st.button("🔍 Detectar Anomalías", type="primary", use_container_width=True):
                with st.spinner("Analizando..."):
                    result = self.ml.detect_anomalies(df, threshold)
                    st.session_state['anomaly_result'] = result
        
        with col2:
            if 'anomaly_result' not in st.session_state:
                st.info("👈 Ajusta la sensibilidad y detecta anomalías")
                return
            
            result = st.session_state['anomaly_result']
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                return
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Anomalías", result['total_anomalias'])
            
            with col2:
                st.metric(
                    "Valores Altos",
                    result['anomalias_altas'],
                    delta="↗️ Inusual",
                    help="Ventas extremadamente altas"
                )
            
            with col3:
                st.metric(
                    "Valores Bajos",
                    result['anomalias_bajas'],
                    delta="↘️ Inusual",
                    delta_color="inverse",
                    help="Ventas extremadamente bajas"
                )
            
            with col4:
                st.metric("Threshold", f"{threshold} σ", help="Z-Score usado")
            
            # Tabla de anomalías
            if result['anomalias']:
                st.markdown("---")
                st.markdown("### 📋 Anomalías Detectadas")
                
                anomalias_df = pd.DataFrame(result['anomalias'])
                anomalias_df['valor'] = anomalias_df['valor'].apply(format_currency)
                anomalias_df['z_score'] = anomalias_df['z_score'].apply(lambda x: f"{x:.2f}")
                
                st.dataframe(anomalias_df, use_container_width=True)
            else:
                st.success("✅ No se detectaron anomalías con este threshold")
    
    def _render_clustering(self, df: pd.DataFrame):
        """Renderiza clustering de clientes"""
        
        st.markdown("### 🏷️ Clustering Automático de Clientes")
        st.info("🤖 Agrupamos clientes similares automáticamente usando K-Means")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            n_clusters = st.slider(
                "Número de Grupos",
                min_value=2,
                max_value=6,
                value=4,
                key="n_clusters"
            )
            
            if st.button("🏷️ Agrupar Clientes", type="primary", use_container_width=True):
                with st.spinner("Agrupando..."):
                    result = self.ml.cluster_clients(df, n_clusters)
                    st.session_state['cluster_result'] = result
        
        with col2:
            if 'cluster_result' not in st.session_state:
                st.info("👈 Selecciona el número de grupos y ejecuta")
                return
            
            result = st.session_state['cluster_result']
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                return
            
            # Métricas
            st.metric("Total Clientes Agrupados", result['total_clientes'])
            
            # Características de clusters
            st.markdown("---")
            st.markdown("### 📊 Características de cada Grupo")
            
            cluster_df = pd.DataFrame(result['cluster_stats'])
            cluster_df['Total_Ventas'] = cluster_df['Total_Ventas'].apply(format_currency)
            cluster_df['Ticket_Promedio'] = cluster_df['Ticket_Promedio'].apply(format_currency)
            cluster_df['Total_Comision'] = cluster_df['Total_Comision'].apply(format_currency)
            cluster_df['Num_Compras'] = cluster_df['Num_Compras'].apply(lambda x: f"{x:.1f}")
            
            st.dataframe(cluster_df, use_container_width=True)
            
            # Gráfico de clusters
            st.markdown("---")
            self._render_cluster_chart(result['cluster_stats'])
    
    def _render_churn_prediction(self, df: pd.DataFrame):
        """Renderiza predicción de churn"""
        
        st.markdown("### ⚠️ Predicción de Churn (Abandono de Clientes)")
        st.info("🎯 Identificamos clientes en riesgo de abandonar basándose en su comportamiento")
        
        col1, col2 = st.columns([1, 3])
        
        with col1:
            dias_inactivo = st.slider(
                "Días de Inactividad",
                min_value=30,
                max_value=180,
                value=60,
                step=15,
                help="Días sin comprar para considerar en riesgo",
                key="churn_days"
            )
            
            if st.button("⚠️ Analizar Churn", type="primary", use_container_width=True):
                with st.spinner("Analizando..."):
                    result = self.ml.predict_churn(df, dias_inactivo)
                    st.session_state['churn_result'] = result
        
        with col2:
            if 'churn_result' not in st.session_state:
                st.info("👈 Configura el umbral y analiza")
                return
            
            result = st.session_state['churn_result']
            
            if "error" in result:
                st.error(f"❌ {result['error']}")
                return
            
            # Métricas
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Clientes", result['total_clientes'])
            
            with col2:
                pct_alto = result['alto_riesgo_count'] / result['total_clientes'] * 100
                st.metric(
                    "Riesgo Alto",
                    result['alto_riesgo_count'],
                    delta=f"{pct_alto:.1f}%",
                    delta_color="inverse"
                )
            
            with col3:
                pct_medio = result['medio_riesgo_count'] / result['total_clientes'] * 100
                st.metric(
                    "Riesgo Medio",
                    result['medio_riesgo_count'],
                    delta=f"{pct_medio:.1f}%",
                    delta_color="inverse"
                )
            
            with col4:
                st.metric(
                    "Valor en Riesgo",
                    format_currency(result['valor_en_riesgo']),
                    help="Valor histórico de clientes en riesgo alto"
                )
            
            # Gráfico de distribución
            st.markdown("---")
            self._render_churn_distribution_chart(result)
            
            # Clientes en riesgo alto
            st.markdown("---")
            st.markdown("### 🚨 Clientes en Riesgo Alto (Top 20)")
            
            if result['alto_riesgo']:
                alto_riesgo_df = pd.DataFrame(result['alto_riesgo'])
                alto_riesgo_df['Total_Comprado'] = alto_riesgo_df['Total_Comprado'].apply(format_currency)
                alto_riesgo_df['Total_Comision'] = alto_riesgo_df['Total_Comision'].apply(format_currency)
                alto_riesgo_df['Churn_Score'] = alto_riesgo_df['Churn_Score'].apply(lambda x: f"{x:.0f}")
                
                st.dataframe(alto_riesgo_df[['cliente', 'Dias_Inactivo', 'Churn_Score', 'Total_Comprado', 'Num_Compras']], use_container_width=True)
                
                st.warning("💡 **Acción Recomendada**: Contactar a estos clientes con oferta especial o recordatorio")
            else:
                st.success("✅ No hay clientes en riesgo alto")
    
    def _render_trend_analysis(self, df: pd.DataFrame):
        """Renderiza análisis de tendencias"""
        
        st.markdown("### 📊 Análisis de Tendencias")
        
        with st.spinner("Analizando tendencias..."):
            result = self.ml.trend_analysis(df)
        
        if "error" in result:
            st.error(f"❌ {result['error']}")
            return
        
        # Métricas principales
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Mejor Mes", result['mejor_mes']['mes'])
        
        with col2:
            st.metric("Valor Mejor Mes", format_currency(result['mejor_mes']['valor']))
        
        with col3:
            st.metric(
                "Crecimiento Mensual",
                f"{result['crecimiento_mensual']:.1f}%",
                delta=f"{result['crecimiento_mensual']:.1f}%"
            )
        
        with col4:
            st.metric("Promedio Mensual", format_currency(result['promedio_mensual']))
        
        # Gráficos
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📅 Tendencia Semanal")
            self._render_trend_chart(result['semanal'], 'semana', "Semana")
        
        with col2:
            st.markdown("#### 📆 Tendencia Mensual")
            self._render_trend_chart(result['mensual'], 'mes', "Mes")
    
    # ========================================
    # GRÁFICOS
    # ========================================
    
    def _render_prediction_chart(self, result: Dict):
        """Renderiza gráfico de predicción"""
        
        pred_df = pd.DataFrame(result['predicciones'])
        
        fig = go.Figure()
        
        # Predicción
        fig.add_trace(go.Scatter(
            x=pred_df['fecha'],
            y=pred_df['valor_predicho'],
            mode='lines+markers',
            name='Predicción',
            line=dict(color='#6366f1', width=3),
            marker=dict(size=6)
        ))
        
        # Intervalo de confianza
        fig.add_trace(go.Scatter(
            x=pred_df['fecha'],
            y=pred_df['intervalo_superior'],
            mode='lines',
            name='Intervalo Superior',
            line=dict(width=0),
            showlegend=False
        ))
        
        fig.add_trace(go.Scatter(
            x=pred_df['fecha'],
            y=pred_df['intervalo_inferior'],
            mode='lines',
            name='Intervalo Inferior',
            line=dict(width=0),
            fillcolor='rgba(99, 102, 241, 0.2)',
            fill='tonexty',
            showlegend=True
        ))
        
        fig.update_layout(
            title="Predicción de Ventas",
            xaxis_title="Fecha",
            yaxis_title="Valor",
            height=400,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_rfm_segments_chart(self, segmentos: List[Dict]):
        """Renderiza gráfico de segmentos RFM"""
        
        seg_df = pd.DataFrame(segmentos)
        
        fig = go.Figure(data=[go.Pie(
            labels=seg_df['Segmento'],
            values=seg_df['Clientes'],
            hole=0.4
        )])
        
        fig.update_layout(
            height=350,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_rfm_revenue_chart(self, segmentos: List[Dict]):
        """Renderiza gráfico de revenue por segmento"""
        
        seg_df = pd.DataFrame(segmentos)
        
        fig = go.Figure(data=[go.Bar(
            x=seg_df['Segmento'],
            y=seg_df['Revenue_Total'],
            marker_color='#10b981'
        )])
        
        fig.update_layout(
            height=350,
            yaxis_title="Revenue Total",
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_cluster_chart(self, cluster_stats: List[Dict]):
        """Renderiza gráfico de clusters"""
        
        cluster_df = pd.DataFrame(cluster_stats)
        
        fig = go.Figure(data=[go.Bar(
            x=cluster_df['Nombre'],
            y=cluster_df['Clientes'],
            text=cluster_df['Clientes'],
            textposition='auto',
            marker_color='#8b5cf6'
        )])
        
        fig.update_layout(
            title="Distribución de Clientes por Cluster",
            height=400,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_churn_distribution_chart(self, result: Dict):
        """Renderiza distribución de churn"""
        
        labels = ['Bajo Riesgo', 'Riesgo Medio', 'Alto Riesgo']
        values = [
            result['bajo_riesgo_count'],
            result['medio_riesgo_count'],
            result['alto_riesgo_count']
        ]
        colors = ['#10b981', '#f59e0b', '#ef4444']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            marker=dict(colors=colors),
            hole=0.4
        )])
        
        fig.update_layout(
            title="Distribución de Riesgo de Churn",
            height=350,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_trend_chart(self, data: List[Dict], x_col: str, x_label: str):
        """Renderiza gráfico de tendencia"""
        
        df = pd.DataFrame(data)
        
        fig = go.Figure(data=[go.Scatter(
            x=df[x_col],
            y=df['valor'],
            mode='lines+markers',
            line=dict(color='#6366f1', width=2),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)'
        )])
        
        fig.update_layout(
            xaxis_title=x_label,
            yaxis_title="Valor",
            height=300,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)

