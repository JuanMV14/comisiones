"""
Sistema de Gestión de Temas (Dark/Light Mode)
"""

import streamlit as st
from typing import Dict, Any

class ThemeManager:
    """Gestor de temas para la aplicación"""
    
    # Paleta de colores para Dark Mode
    DARK_THEME = {
        "primary": "#6366f1",           # Indigo
        "secondary": "#8b5cf6",         # Violet
        "success": "#10b981",           # Green
        "warning": "#f59e0b",           # Amber
        "error": "#ef4444",             # Red
        "info": "#3b82f6",              # Blue
        
        "background": "#0f172a",        # Slate 900
        "surface": "#1e293b",           # Slate 800
        "surface_light": "#334155",     # Slate 700
        
        "text_primary": "#f1f5f9",      # Slate 100
        "text_secondary": "#cbd5e1",    # Slate 300
        "text_tertiary": "#94a3b8",     # Slate 400
        
        "border": "#334155",            # Slate 700
        "border_light": "#475569",      # Slate 600
        
        "gradient_1": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "gradient_2": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "gradient_3": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "gradient_4": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "gradient_5": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    }
    
    # Paleta de colores para Light Mode
    LIGHT_THEME = {
        "primary": "#6366f1",
        "secondary": "#8b5cf6",
        "success": "#10b981",
        "warning": "#f59e0b",
        "error": "#ef4444",
        "info": "#3b82f6",
        
        "background": "#ffffff",
        "surface": "#f8fafc",           # Slate 50
        "surface_light": "#f1f5f9",     # Slate 100
        
        "text_primary": "#0f172a",      # Slate 900
        "text_secondary": "#334155",    # Slate 700
        "text_tertiary": "#64748b",     # Slate 500
        
        "border": "#e2e8f0",            # Slate 200
        "border_light": "#cbd5e1",      # Slate 300
        
        "gradient_1": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "gradient_2": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
        "gradient_3": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
        "gradient_4": "linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)",
        "gradient_5": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)",
    }
    
    @staticmethod
    def get_theme() -> Dict[str, str]:
        """Obtiene el tema actual desde session_state"""
        if "dark_mode" not in st.session_state:
            st.session_state.dark_mode = True  # Dark por defecto
        
        return ThemeManager.DARK_THEME if st.session_state.dark_mode else ThemeManager.LIGHT_THEME
    
    @staticmethod
    def toggle_theme():
        """Alterna entre dark y light mode"""
        st.session_state.dark_mode = not st.session_state.get("dark_mode", True)
    
    @staticmethod
    def render_theme_toggle():
        """Renderiza el toggle de tema en el sidebar"""
        theme = ThemeManager.get_theme()
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(
                f"""
                <div style='display: flex; align-items: center; gap: 10px;'>
                    <span style='color: {theme["text_secondary"]}; font-size: 14px;'>
                        {'🌙 Dark Mode' if st.session_state.get("dark_mode", True) else '☀️ Light Mode'}
                    </span>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        with col2:
            if st.button("🔄", key="toggle_theme", help="Cambiar tema"):
                ThemeManager.toggle_theme()
                st.rerun()
    
    @staticmethod
    def get_css() -> str:
        """Genera CSS personalizado según el tema actual"""
        theme = ThemeManager.get_theme()
        
        return f"""
        <style>
        /* ============================================
           TEMA PRINCIPAL
           ============================================ */
        
        /* Variables CSS */
        :root {{
            --primary: {theme['primary']};
            --secondary: {theme['secondary']};
            --success: {theme['success']};
            --warning: {theme['warning']};
            --error: {theme['error']};
            --info: {theme['info']};
            
            --bg-main: {theme['background']};
            --bg-surface: {theme['surface']};
            --bg-surface-light: {theme['surface_light']};
            
            --text-primary: {theme['text_primary']};
            --text-secondary: {theme['text_secondary']};
            --text-tertiary: {theme['text_tertiary']};
            
            --border: {theme['border']};
            --border-light: {theme['border_light']};
        }}
        
        /* Background principal */
        .stApp {{
            background: {theme['background']};
        }}
        
        /* ============================================
           GLASSMORPHISM CARDS
           ============================================ */
        
        .glass-card {{
            background: rgba(255, 255, 255, {'0.05' if st.session_state.get('dark_mode', True) else '0.8'});
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 16px;
            border: 1px solid {theme['border']};
            padding: 24px;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }}
        
        .glass-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.15);
        }}
        
        /* ============================================
           METRIC CARDS MODERNOS
           ============================================ */
        
        .modern-metric-card {{
            background: {theme['surface']};
            border-radius: 20px;
            padding: 24px;
            border: 1px solid {theme['border']};
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}
        
        .modern-metric-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: {theme['gradient_1']};
        }}
        
        .modern-metric-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
        }}
        
        .metric-title {{
            font-size: 14px;
            font-weight: 600;
            color: {theme['text_secondary']};
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
        }}
        
        .metric-value {{
            font-size: 36px;
            font-weight: 700;
            color: {theme['text_primary']};
            line-height: 1.2;
            margin-bottom: 8px;
        }}
        
        .metric-change {{
            font-size: 14px;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            padding: 4px 12px;
            border-radius: 12px;
        }}
        
        .metric-change.positive {{
            background: rgba(16, 185, 129, 0.1);
            color: {theme['success']};
        }}
        
        .metric-change.negative {{
            background: rgba(239, 68, 68, 0.1);
            color: {theme['error']};
        }}
        
        /* ============================================
           GRADIENTES
           ============================================ */
        
        .gradient-1 {{
            background: {theme['gradient_1']};
        }}
        
        .gradient-2 {{
            background: {theme['gradient_2']};
        }}
        
        .gradient-3 {{
            background: {theme['gradient_3']};
        }}
        
        .gradient-4 {{
            background: {theme['gradient_4']};
        }}
        
        .gradient-5 {{
            background: {theme['gradient_5']};
        }}
        
        /* ============================================
           BOTONES MODERNOS
           ============================================ */
        
        .stButton > button {{
            background: {theme['primary']};
            color: white;
            border: none;
            border-radius: 12px;
            padding: 12px 24px;
            font-weight: 600;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        }}
        
        /* ============================================
           INPUTS MODERNOS
           ============================================ */
        
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > select {{
            background: {theme['surface']};
            border: 2px solid {theme['border']};
            border-radius: 12px;
            padding: 12px 16px;
            color: {theme['text_primary']};
            transition: all 0.3s ease;
        }}
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus,
        .stSelectbox > div > div > select:focus {{
            border-color: {theme['primary']};
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
        }}
        
        /* ============================================
           TABLAS MODERNAS
           ============================================ */
        
        .dataframe {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
        }}
        
        .dataframe thead th {{
            background: {theme['surface_light']};
            color: {theme['text_primary']};
            font-weight: 600;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.5px;
            padding: 16px;
            border-bottom: 2px solid {theme['border']};
        }}
        
        .dataframe tbody tr {{
            transition: all 0.2s ease;
        }}
        
        .dataframe tbody tr:hover {{
            background: {theme['surface_light']};
        }}
        
        .dataframe tbody td {{
            padding: 14px 16px;
            color: {theme['text_secondary']};
            border-bottom: 1px solid {theme['border']};
        }}
        
        /* ============================================
           ANIMACIONES
           ============================================ */
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        .fade-in-up {{
            animation: fadeInUp 0.6s ease-out;
        }}
        
        @keyframes pulse {{
            0%, 100% {{
                opacity: 1;
            }}
            50% {{
                opacity: 0.5;
            }}
        }}
        
        .pulse {{
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }}
        
        /* ============================================
           PROGRESS BAR MODERNA
           ============================================ */
        
        .modern-progress {{
            width: 100%;
            height: 12px;
            background: {theme['surface']};
            border-radius: 10px;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.1);
        }}
        
        .modern-progress-bar {{
            height: 100%;
            background: {theme['gradient_1']};
            transition: width 1s ease-in-out;
            border-radius: 10px;
        }}
        
        /* ============================================
           BADGES
           ============================================ */
        
        .badge {{
            display: inline-flex;
            align-items: center;
            padding: 6px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
            gap: 4px;
        }}
        
        .badge-success {{
            background: rgba(16, 185, 129, 0.1);
            color: {theme['success']};
        }}
        
        .badge-warning {{
            background: rgba(245, 158, 11, 0.1);
            color: {theme['warning']};
        }}
        
        .badge-error {{
            background: rgba(239, 68, 68, 0.1);
            color: {theme['error']};
        }}
        
        .badge-info {{
            background: rgba(59, 130, 246, 0.1);
            color: {theme['info']};
        }}
        
        /* ============================================
           SIDEBAR MODERNA
           ============================================ */
        
        [data-testid="stSidebar"] {{
            background: {theme['surface']};
            border-right: 1px solid {theme['border']};
        }}
        
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {{
            color: {theme['text_primary']};
        }}
        
        /* ============================================
           SCROLLBAR MODERNA
           ============================================ */
        
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: {theme['surface']};
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {theme['border_light']};
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: {theme['text_tertiary']};
        }}
        
        /* ============================================
           TABS MODERNAS
           ============================================ */
        
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
            background: {theme['surface']};
            padding: 8px;
            border-radius: 12px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background: transparent;
            border-radius: 8px;
            color: {theme['text_secondary']};
            font-weight: 600;
            padding: 12px 24px;
            transition: all 0.3s ease;
        }}
        
        .stTabs [aria-selected="true"] {{
            background: {theme['primary']};
            color: white;
        }}
        
        /* ============================================
           TOOLTIPS
           ============================================ */
        
        .tooltip {{
            position: relative;
            display: inline-block;
        }}
        
        .tooltip .tooltiptext {{
            visibility: hidden;
            background-color: {theme['surface_light']};
            color: {theme['text_primary']};
            text-align: center;
            border-radius: 8px;
            padding: 8px 12px;
            position: absolute;
            z-index: 1;
            bottom: 125%;
            left: 50%;
            margin-left: -60px;
            opacity: 0;
            transition: opacity 0.3s;
            font-size: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }}
        
        .tooltip:hover .tooltiptext {{
            visibility: visible;
            opacity: 1;
        }}
        
        </style>
        """
    
    @staticmethod
    def apply_theme():
        """Aplica el tema actual a la aplicación"""
        st.markdown(ThemeManager.get_css(), unsafe_allow_html=True)

