"""
Componentes UI Modernos con Glassmorphism y Animaciones
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Any, List, Optional
from utils.formatting import format_currency
import pandas as pd

class ModernComponents:
    """Componentes visuales modernos para el CRM"""
    
    @staticmethod
    def render_metric_card(
        title: str,
        value: str,
        change: Optional[float] = None,
        icon: str = "📊",
        gradient_class: str = "gradient-1"
    ):
        """
        Renderiza una tarjeta de métrica moderna
        
        Args:
            title: Título de la métrica
            value: Valor principal
            change: Cambio porcentual (opcional)
            icon: Emoji del icono
            gradient_class: Clase CSS del gradiente
        """
        change_html = ""
        if change is not None:
            change_class = "positive" if change >= 0 else "negative"
            change_icon = "↗️" if change >= 0 else "↘️"
            change_html = f"""
            <div class="metric-change {change_class}">
                {change_icon} {abs(change):.1f}%
            </div>
            """
        
        st.markdown(
            f"""
            <div class="modern-metric-card fade-in-up">
                <div class="metric-title">
                    {icon} {title}
                </div>
                <div class="metric-value">
                    {value}
                </div>
                {change_html}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_progress_bar(
        value: float,
        max_value: float,
        title: str = "",
        show_percentage: bool = True
    ):
        """
        Renderiza una barra de progreso moderna
        
        Args:
            value: Valor actual
            max_value: Valor máximo
            title: Título opcional
            show_percentage: Mostrar porcentaje
        """
        percentage = min((value / max_value * 100), 100) if max_value > 0 else 0
        
        title_html = f"<p style='margin-bottom: 8px; font-weight: 600;'>{title}</p>" if title else ""
        percentage_text = f"{percentage:.1f}%" if show_percentage else ""
        
        st.markdown(
            f"""
            <div>
                {title_html}
                <div class="modern-progress">
                    <div class="modern-progress-bar" style="width: {percentage}%"></div>
                </div>
                <div style='display: flex; justify-content: space-between; margin-top: 8px; font-size: 12px;'>
                    <span>{format_currency(value)}</span>
                    <span>{percentage_text}</span>
                    <span>{format_currency(max_value)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_badge(text: str, type: str = "info"):
        """
        Renderiza un badge moderno
        
        Args:
            text: Texto del badge
            type: Tipo (success, warning, error, info)
        """
        icons = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        icon = icons.get(type, "ℹ️")
        
        return f"""
        <span class="badge badge-{type}">
            {icon} {text}
        </span>
        """
    
    @staticmethod
    def render_glass_card(content: str, title: Optional[str] = None):
        """
        Renderiza una tarjeta con efecto glassmorphism
        
        Args:
            content: Contenido HTML de la tarjeta
            title: Título opcional
        """
        title_html = f"<h3 style='margin-top: 0;'>{title}</h3>" if title else ""
        
        st.markdown(
            f"""
            <div class="glass-card">
                {title_html}
                {content}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def create_modern_chart_revenue_trend(df: pd.DataFrame):
        """
        Crea un gráfico moderno de tendencia de ingresos
        
        Args:
            df: DataFrame con datos de ventas
        """
        # Preparar datos
        df_copy = df.copy()
        df_copy['fecha_factura'] = pd.to_datetime(df_copy['fecha_factura'])
        
        # Agrupar por mes
        df_monthly = df_copy.groupby(df_copy['fecha_factura'].dt.to_period('M')).agg({
            'valor': 'sum',
            'comision': 'sum'
        }).reset_index()
        
        df_monthly['fecha_factura'] = df_monthly['fecha_factura'].astype(str)
        
        # Crear gráfico con Plotly
        fig = go.Figure()
        
        # Línea de ventas con área
        fig.add_trace(go.Scatter(
            x=df_monthly['fecha_factura'],
            y=df_monthly['valor'],
            mode='lines+markers',
            name='Ventas',
            line=dict(color='#6366f1', width=3),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
            marker=dict(size=10, color='#6366f1', line=dict(color='white', width=2))
        ))
        
        # Línea de comisiones
        fig.add_trace(go.Scatter(
            x=df_monthly['fecha_factura'],
            y=df_monthly['comision'],
            mode='lines+markers',
            name='Comisiones',
            line=dict(color='#10b981', width=3, dash='dot'),
            marker=dict(size=8, color='#10b981')
        ))
        
        # Actualizar layout
        fig.update_layout(
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family="Inter, sans-serif", size=12),
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
        )
        
        fig.update_xaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            title_text=""
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            title_text=""
        )
        
        return fig
    
    @staticmethod
    def create_donut_chart(labels: List[str], values: List[float], title: str):
        """
        Crea un gráfico de dona moderno
        
        Args:
            labels: Etiquetas de las categorías
            values: Valores de cada categoría
            title: Título del gráfico
        """
        colors = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(colors=colors, line=dict(color='#1e293b', width=2)),
            textinfo='label+percent',
            textfont=dict(size=12, family="Inter, sans-serif"),
            hovertemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            annotations=[dict(text=title, x=0.5, y=0.5, font_size=16, showarrow=False)],
            margin=dict(l=20, r=20, t=40, b=20),
            height=350
        )
        
        return fig
    
    @staticmethod
    def create_bar_chart_comparison(
        categories: List[str],
        values1: List[float],
        values2: List[float],
        name1: str,
        name2: str,
        title: str
    ):
        """
        Crea un gráfico de barras comparativo
        
        Args:
            categories: Categorías del eje X
            values1: Valores de la primera serie
            values2: Valores de la segunda serie
            name1: Nombre de la primera serie
            name2: Nombre de la segunda serie
            title: Título del gráfico
        """
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values1,
            name=name1,
            marker_color='#6366f1',
            marker_line=dict(width=0),
            hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            x=categories,
            y=values2,
            name=name2,
            marker_color='#10b981',
            marker_line=dict(width=0),
            hovertemplate='<b>%{x}</b><br>%{y:,.0f}<extra></extra>'
        ))
        
        fig.update_layout(
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            title=dict(text=title, x=0.5, xanchor='center'),
            barmode='group',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=60, b=20),
            height=350
        )
        
        fig.update_xaxes(
            showgrid=False,
            title_text=""
        )
        
        fig.update_yaxes(
            showgrid=True,
            gridwidth=1,
            gridcolor='rgba(148, 163, 184, 0.1)',
            title_text=""
        )
        
        return fig
    
    @staticmethod
    def create_gauge_chart(value: float, max_value: float, title: str):
        """
        Crea un gráfico de gauge (medidor)
        
        Args:
            value: Valor actual
            max_value: Valor máximo
            title: Título del gauge
        """
        percentage = (value / max_value * 100) if max_value > 0 else 0
        
        # Determinar color según porcentaje
        if percentage >= 90:
            color = "#10b981"  # Verde
        elif percentage >= 70:
            color = "#f59e0b"  # Amarillo
        else:
            color = "#ef4444"  # Rojo
        
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=percentage,
            title={'text': title, 'font': {'size': 20}},
            delta={'reference': 100, 'increasing': {'color': "#10b981"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkgray"},
                'bar': {'color': color},
                'bgcolor': "rgba(0,0,0,0)",
                'borderwidth': 2,
                'bordercolor': "rgba(148, 163, 184, 0.2)",
                'steps': [
                    {'range': [0, 50], 'color': 'rgba(239, 68, 68, 0.1)'},
                    {'range': [50, 75], 'color': 'rgba(245, 158, 11, 0.1)'},
                    {'range': [75, 100], 'color': 'rgba(16, 185, 129, 0.1)'}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 100
                }
            },
            number={'suffix': "%", 'font': {'size': 40}}
        ))
        
        fig.update_layout(
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=60, b=20),
            height=300
        )
        
        return fig
    
    @staticmethod
    def render_alert_card(message: str, type: str = "info", icon: str = None):
        """
        Renderiza una tarjeta de alerta moderna
        
        Args:
            message: Mensaje de la alerta
            type: Tipo (success, warning, error, info)
            icon: Icono personalizado (opcional)
        """
        icons = {
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "info": "ℹ️"
        }
        
        alert_icon = icon if icon else icons.get(type, "ℹ️")
        
        colors = {
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "info": "#3b82f6"
        }
        
        color = colors.get(type, "#3b82f6")
        
        st.markdown(
            f"""
            <div style='
                background: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:], 16)}, 0.1);
                border-left: 4px solid {color};
                border-radius: 12px;
                padding: 16px 20px;
                margin: 16px 0;
                display: flex;
                align-items: center;
                gap: 12px;
                animation: fadeInUp 0.5s ease-out;
            '>
                <span style='font-size: 24px;'>{alert_icon}</span>
                <span style='font-size: 14px; font-weight: 500;'>{message}</span>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    @staticmethod
    def render_stat_row(stats: List[Dict[str, Any]]):
        """
        Renderiza una fila de estadísticas
        
        Args:
            stats: Lista de diccionarios con {title, value, icon, change}
        """
        cols = st.columns(len(stats))
        
        for i, stat in enumerate(stats):
            with cols[i]:
                ModernComponents.render_metric_card(
                    title=stat.get('title', ''),
                    value=stat.get('value', '0'),
                    change=stat.get('change'),
                    icon=stat.get('icon', '📊'),
                    gradient_class=f"gradient-{(i % 5) + 1}"
                )

