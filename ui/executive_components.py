"""
Componentes Visuales para Dashboard Ejecutivo
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from typing import Dict, Any, List
from utils.formatting import format_currency
from ui.theme_manager import ThemeManager

class ExecutiveComponents:
    """Componentes visuales para dashboard ejecutivo"""
    
    @staticmethod
    def render_executive_kpi_grid(kpis: Dict[str, Any]):
        """Renderiza grid de KPIs ejecutivos en formato 2x4"""
        
        theme = ThemeManager.get_theme()
        
        # Fila 1: KPIs Financieros
        st.markdown("### 💰 KPIs Financieros")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ExecutiveComponents._render_executive_metric(
                "Revenue Mes Actual",
                format_currency(kpis.get('revenue_actual', 0)),
                kpis.get('revenue_change', 0),
                "💵",
                theme['gradient_1']
            )
        
        with col2:
            ExecutiveComponents._render_executive_metric(
                "Comisiones Mes Actual",
                format_currency(kpis.get('commission_actual', 0)),
                kpis.get('commission_change', 0),
                "💰",
                theme['gradient_2']
            )
        
        with col3:
            ExecutiveComponents._render_executive_metric(
                "Ticket Promedio",
                format_currency(kpis.get('avg_ticket', 0)),
                kpis.get('avg_ticket_change', 0),
                "🎫",
                theme['gradient_3']
            )
        
        with col4:
            ExecutiveComponents._render_executive_metric(
                "Margen Comisión",
                f"{kpis.get('commission_margin', 0):.1f}%",
                None,
                "📊",
                theme['gradient_4']
            )
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Fila 2: KPIs YTD
        st.markdown("### 📅 Year-to-Date (YTD)")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            ExecutiveComponents._render_executive_metric(
                "Revenue YTD",
                format_currency(kpis.get('revenue_ytd', 0)),
                None,
                "📈",
                theme['gradient_5']
            )
        
        with col2:
            ExecutiveComponents._render_executive_metric(
                "Comisiones YTD",
                format_currency(kpis.get('commission_ytd', 0)),
                None,
                "💎",
                theme['gradient_1']
            )
        
        with col3:
            ExecutiveComponents._render_executive_metric(
                "Facturas Mes",
                str(kpis.get('invoices_count', 0)),
                kpis.get('invoices_change', 0),
                "📋",
                theme['gradient_2']
            )
        
        with col4:
            # Proyección del mes
            proyeccion = kpis.get('proyeccion_revenue', 0)
            ExecutiveComponents._render_executive_metric(
                "Proyección Mes",
                format_currency(proyeccion),
                None,
                "🔮",
                theme['gradient_3']
            )
    
    @staticmethod
    def render_operational_kpis(kpis: Dict[str, Any]):
        """Renderiza KPIs operacionales"""
        
        theme = ThemeManager.get_theme()
        
        st.markdown("### ⚙️ KPIs Operacionales")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            conversion = kpis.get('conversion_rate', 0)
            color = theme['success'] if conversion >= 80 else theme['warning'] if conversion >= 60 else theme['error']
            
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border-radius: 16px;
                    padding: 20px;
                    border-left: 4px solid {color};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                '>
                    <p style='margin: 0; font-size: 12px; color: {theme['text_secondary']};'>
                        🎯 Tasa de Conversión
                    </p>
                    <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: 700; color: {color};'>
                        {conversion:.1f}%
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            cycle = kpis.get('avg_sales_cycle', 0)
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border-radius: 16px;
                    padding: 20px;
                    border-left: 4px solid {theme['info']};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                '>
                    <p style='margin: 0; font-size: 12px; color: {theme['text_secondary']};'>
                        ⏱️ Ciclo de Venta
                    </p>
                    <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: 700; color: {theme['text_primary']};'>
                        {cycle:.0f} días
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col3:
            retention = kpis.get('retention_rate', 0)
            color = theme['success'] if retention >= 80 else theme['warning'] if retention >= 60 else theme['error']
            
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border-radius: 16px;
                    padding: 20px;
                    border-left: 4px solid {color};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                '>
                    <p style='margin: 0; font-size: 12px; color: {theme['text_secondary']};'>
                        🔁 Retención Clientes
                    </p>
                    <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: 700; color: {color};'>
                        {retention:.1f}%
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col4:
            nuevos = kpis.get('clientes_nuevos', 0)
            st.markdown(
                f"""
                <div style='
                    background: {theme['surface']};
                    border-radius: 16px;
                    padding: 20px;
                    border-left: 4px solid {theme['success']};
                    box-shadow: 0 4px 12px rgba(0,0,0,0.08);
                '>
                    <p style='margin: 0; font-size: 12px; color: {theme['text_secondary']};'>
                        ✨ Clientes Nuevos
                    </p>
                    <p style='margin: 8px 0 0 0; font-size: 32px; font-weight: 700; color: {theme['text_primary']};'>
                        {nuevos}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )
    
    @staticmethod
    def render_risk_panel(risk_data: Dict[str, Any]):
        """Renderiza panel de análisis de riesgo"""
        
        theme = ThemeManager.get_theme()
        risk_score = risk_data.get('risk_score', 0)
        
        # Determinar color y nivel
        if risk_score < 20:
            color = theme['success']
            nivel = "BAJO"
            emoji = "✅"
        elif risk_score < 40:
            color = theme['warning']
            nivel = "MEDIO"
            emoji = "⚠️"
        else:
            color = theme['error']
            nivel = "ALTO"
            emoji = "🚨"
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### 🎲 Análisis de Riesgo")
            
            # Risk score con gauge
            fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=risk_score,
                title={'text': f"{emoji} Nivel de Riesgo: {nivel}", 'font': {'size': 18}},
                gauge={
                    'axis': {'range': [None, 100]},
                    'bar': {'color': color},
                    'steps': [
                        {'range': [0, 20], 'color': 'rgba(16, 185, 129, 0.2)'},
                        {'range': [20, 40], 'color': 'rgba(245, 158, 11, 0.2)'},
                        {'range': [40, 100], 'color': 'rgba(239, 68, 68, 0.2)'}
                    ],
                    'threshold': {
                        'line': {'color': "white", 'width': 4},
                        'thickness': 0.75,
                        'value': 40
                    }
                },
                number={'suffix': "%", 'font': {'size': 40}}
            ))
            
            fig.update_layout(
                height=250,
                margin=dict(l=20, r=20, t=40, b=20),
                template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### 📊 Métricas")
            
            facturas_riesgo = risk_data.get('facturas_en_riesgo', 0)
            valor_riesgo = risk_data.get('valor_en_riesgo', 0)
            comision_riesgo = risk_data.get('comision_en_riesgo', 0)
            
            st.metric("Facturas en Riesgo", facturas_riesgo)
            st.metric("Valor en Riesgo", format_currency(valor_riesgo))
            st.metric("Comisión en Riesgo", format_currency(comision_riesgo))
        
        # Alertas
        alertas = risk_data.get('alertas', [])
        if alertas:
            st.markdown("### 🔔 Alertas")
            for alerta in alertas:
                st.warning(alerta)
    
    @staticmethod
    def render_trend_chart(trend_data: List[Dict[str, Any]]):
        """Renderiza gráfico de tendencia mensual"""
        
        if not trend_data:
            st.info("No hay suficientes datos para mostrar tendencias")
            return
        
        # Preparar datos
        meses = [d['mes'] for d in trend_data]
        revenue = [d['valor'] for d in trend_data]
        comision = [d['comision'] for d in trend_data]
        facturas = [d['facturas'] for d in trend_data]
        
        # Crear gráfico con subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('💰 Revenue y Comisiones', '📋 Número de Facturas'),
            vertical_spacing=0.15,
            row_heights=[0.6, 0.4]
        )
        
        # Revenue y comisiones
        fig.add_trace(
            go.Scatter(
                x=meses, y=revenue,
                name='Revenue',
                mode='lines+markers',
                line=dict(color='#6366f1', width=3),
                fill='tozeroy',
                fillcolor='rgba(99, 102, 241, 0.1)',
                marker=dict(size=10, line=dict(color='white', width=2))
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=meses, y=comision,
                name='Comisiones',
                mode='lines+markers',
                line=dict(color='#10b981', width=2, dash='dot'),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Facturas
        fig.add_trace(
            go.Bar(
                x=meses, y=facturas,
                name='Facturas',
                marker_color='#8b5cf6',
                showlegend=False
            ),
            row=2, col=1
        )
        
        # Layout
        fig.update_layout(
            height=600,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=80, b=20)
        )
        
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='rgba(148, 163, 184, 0.1)')
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def render_top_performers(top_data: Dict[str, List]):
        """Renderiza top performers en tabs"""
        
        tab1, tab2, tab3 = st.tabs(["💰 Top Valor", "💎 Top Comisiones", "🔁 Más Frecuentes"])
        
        with tab1:
            top_clientes = top_data.get('top_clientes', [])
            if top_clientes:
                for i, cliente in enumerate(top_clientes, 1):
                    ExecutiveComponents._render_top_item(
                        i, 
                        cliente['cliente'], 
                        format_currency(cliente['valor']),
                        "💰"
                    )
            else:
                st.info("No hay datos disponibles")
        
        with tab2:
            top_comisiones = top_data.get('top_comisiones', [])
            if top_comisiones:
                for i, cliente in enumerate(top_comisiones, 1):
                    ExecutiveComponents._render_top_item(
                        i,
                        cliente['cliente'],
                        format_currency(cliente['comision']),
                        "💎"
                    )
            else:
                st.info("No hay datos disponibles")
        
        with tab3:
            clientes_frecuentes = top_data.get('clientes_frecuentes', [])
            if clientes_frecuentes:
                for i, cliente in enumerate(clientes_frecuentes, 1):
                    ExecutiveComponents._render_top_item(
                        i,
                        cliente['cliente'],
                        f"{cliente['facturas']} facturas",
                        "🔁"
                    )
            else:
                st.info("No hay datos disponibles")
    
    @staticmethod
    def render_client_mix(comparativas: Dict[str, Any]):
        """Renderiza mix de clientes (propios vs externos)"""
        
        mix = comparativas.get('mix_clientes', {})
        
        # Donut chart
        labels = ['Clientes Propios', 'Clientes Externos']
        values = [mix.get('revenue_propios', 0), mix.get('revenue_externos', 0)]
        colors = ['#6366f1', '#8b5cf6']
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker=dict(colors=colors, line=dict(color='#1e293b', width=2)),
            textinfo='label+percent',
            textfont=dict(size=14),
            hovertemplate='<b>%{label}</b><br>%{value:,.0f}<br>%{percent}<extra></extra>'
        )])
        
        fig.update_layout(
            annotations=[dict(
                text=f"Mix<br>Clientes",
                x=0.5, y=0.5,
                font_size=18,
                showarrow=False
            )],
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            height=350,
            template='plotly_dark' if st.session_state.get('dark_mode', True) else 'plotly_white',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Cambios mes a mes
        col1, col2 = st.columns(2)
        with col1:
            cambio_propios = comparativas.get('cambio_propios', 0)
            st.metric(
                "Cambio Propios (MoM)",
                f"{cambio_propios:+.1f}%",
                delta=f"{cambio_propios:.1f}%"
            )
        with col2:
            cambio_externos = comparativas.get('cambio_externos', 0)
            st.metric(
                "Cambio Externos (MoM)",
                f"{cambio_externos:+.1f}%",
                delta=f"{cambio_externos:.1f}%"
            )
    
    @staticmethod
    def _render_executive_metric(
        title: str,
        value: str,
        change: float = None,
        icon: str = "📊",
        gradient: str = None
    ):
        """Renderiza métrica ejecutiva individual"""
        
        theme = ThemeManager.get_theme()
        
        change_html = ""
        if change is not None:
            change_color = theme['success'] if change >= 0 else theme['error']
            change_icon = "↗" if change >= 0 else "↘"
            change_html = f"""<div style='display: inline-flex; align-items: center; gap: 4px; padding: 4px 12px; border-radius: 12px; background: rgba({int(change_color[1:3], 16)}, {int(change_color[3:5], 16)}, {int(change_color[5:], 16)}, 0.15); color: {change_color}; font-size: 14px; font-weight: 600; margin-top: 8px;'>{change_icon} {abs(change):.1f}%</div>"""
        
        border_style = f"border-top: 4px solid transparent; border-image: {gradient} 1;" if gradient else f"border-top: 4px solid {theme['primary']};"
        
        # Construir HTML compacto (sin espacios problemáticos)
        html = f"""<div style='background: {theme['surface']}; border-radius: 16px; padding: 20px; {border_style} box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: all 0.3s ease; height: 160px; display: flex; flex-direction: column; justify-content: space-between;'><div><p style='margin: 0; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: {theme['text_tertiary']};'>{icon} {title}</p></div><div><p style='margin: 0; font-size: 28px; font-weight: 700; color: {theme['text_primary']};'>{value}</p>{change_html}</div></div>"""
        
        st.markdown(html, unsafe_allow_html=True)
    
    @staticmethod
    def _render_top_item(rank: int, name: str, value: str, icon: str):
        """Renderiza item de top performers"""
        
        theme = ThemeManager.get_theme()
        
        # Medallas para top 3
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        rank_display = medals.get(rank, f"#{rank}")
        
        # Colores para ranking
        colors = ['#FFD700', '#C0C0C0', '#CD7F32', '#6366f1', '#8b5cf6']
        color = colors[rank - 1] if rank <= len(colors) else theme['text_tertiary']
        
        st.markdown(
            f"""
            <div style='
                background: {theme['surface']};
                border-radius: 12px;
                padding: 16px 20px;
                margin-bottom: 12px;
                border-left: 4px solid {color};
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: all 0.2s ease;
            '>
                <div style='display: flex; align-items: center; gap: 16px;'>
                    <span style='font-size: 24px;'>{rank_display}</span>
                    <div>
                        <p style='margin: 0; font-weight: 600; color: {theme['text_primary']};'>{name}</p>
                    </div>
                </div>
                <div style='text-align: right;'>
                    <p style='margin: 0; font-size: 18px; font-weight: 700; color: {color};'>
                        {icon} {value}
                    </p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

