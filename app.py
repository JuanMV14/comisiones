import os
import streamlit as st
from datetime import date
from dotenv import load_dotenv
from supabase import create_client, Client

# Importar módulos organizados
from comisiones.queries import DatabaseManager
from comisiones.ui.componentes import UIComponents
from comisiones.ui.tabs import TabRenderer
from comisiones.business.calculations import ComisionCalculator
from comisiones.business.ai_recommendations import AIRecommendations
from comisones.comisiones.utils.formatting import format_currency
from comisiones.config.settings import AppConfig

# ========================
# CONFIGURACIÓN INICIAL
# ========================
def initialize_app():
    """Inicializa la configuración de la aplicación"""
    load_dotenv()
    
    # Verificar variables de entorno
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        st.error("Faltan las variables de entorno SUPABASE_URL o SUPABASE_KEY.")
        st.stop()
    
    # Configurar Streamlit
    st.set_page_config(
        page_title="CRM Inteligente", 
        layout="wide",
        initial_sidebar_state="expanded",
        page_icon="🧠"
    )
    
    # Crear cliente Supabase
    supabase = create_client(supabase_url, supabase_key)
    
    return supabase

def load_css():
    """Carga estilos CSS personalizados"""
    st.markdown("""
    <style>
        .main .block-container {
            background-color: #0f1419 !important;
            color: #ffffff !important;
        }
        
        .stMarkdown, .stMarkdown p, .stMarkdown div, .stText, p, span, div {
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        h1, h2, h3, h4, h5, h6 {
            color: #ffffff !important;
            font-weight: 800 !important;
            text-shadow: 0 0 10px rgba(255,255,255,0.3) !important;
        }
        
        div[data-testid="metric-container"] {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid #ffffff !important;
            border-radius: 0.75rem !important;
            padding: 1.5rem !important;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px) !important;
        }
        
        div[data-testid="metric-container"] > div {
            color: #ffffff !important;
            font-weight: 800 !important;
            font-size: 16px !important;
        }
        
        .stButton > button {
            border-radius: 0.5rem !important;
            border: 2px solid #ffffff !important;
            font-weight: 800 !important;
            font-size: 14px !important;
            background-color: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            transition: all 0.2s ease !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stButton > button:hover {
            background-color: rgba(255, 255, 255, 0.2) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(255,255,255,0.2) !important;
        }
        
        .stButton > button[kind="primary"] {
            background-color: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            font-weight: 900 !important;
        }
        
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.1);
            padding: 0.5rem;
            border-radius: 0.75rem;
            border: 2px solid #ffffff;
            backdrop-filter: blur(10px);
        }
        
        .stTabs [data-baseweb="tab"] {
            background: rgba(255, 255, 255, 0.1) !important;
            border: 2px solid #ffffff !important;
            border-radius: 0.5rem !important;
            color: #ffffff !important;
            font-weight: 800 !important;
            padding: 0.75rem 1.5rem !important;
            backdrop-filter: blur(10px) !important;
        }
        
        .stTabs [aria-selected="true"] {
            background: #3b82f6 !important;
            color: #ffffff !important;
            border-color: #3b82f6 !important;
            font-weight: 900 !important;
        }
        
        .progress-bar {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 1rem;
            height: 1.5rem;
            overflow: hidden;
            width: 100%;
            border: 2px solid #ffffff;
            backdrop-filter: blur(10px);
        }
        
        .progress-fill {
            height: 100%;
            border-radius: 1rem;
            transition: width 0.3s ease;
        }
        
        .metric-card {
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid #ffffff;
            border-radius: 1rem;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: 0 6px 20px rgba(255,255,255,0.1);
            color: #ffffff;
            backdrop-filter: blur(15px);
        }
        
        .alert-high { 
            background: rgba(239, 68, 68, 0.2); 
            border: 2px solid #ef4444;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .alert-medium { 
            background: rgba(251, 146, 60, 0.2); 
            border: 2px solid #fb923c;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .alert-low { 
            background: rgba(34, 197, 94, 0.2); 
            border: 2px solid #22c55e;
            color: #ffffff !important;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: 1rem 0;
            font-weight: 600;
            backdrop-filter: blur(10px);
        }
        
        .recomendacion-card {
            background: linear-gradient(135deg, rgba(79, 70, 229, 0.3) 0%, rgba(124, 58, 237, 0.3) 100%);
            color: #ffffff;
            padding: 2rem;
            border-radius: 1rem;
            margin: 1rem 0;
            box-shadow: 0 8px 32px rgba(255,255,255,0.1);
            border: 2px solid #4f46e5;
            backdrop-filter: blur(20px);
        }
        
        .streamlit-expanderHeader {
            background: rgba(255, 255, 255, 0.1) !important;
            color: #ffffff !important;
            border: 2px solid #ffffff !important;
        }
        
        .streamlit-expanderContent {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 2px solid #ffffff !important;
            border-top: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    """Función principal de la aplicación"""
    # Inicializar aplicación
    supabase = initialize_app()
    load_css()
    
    # Inicializar managers
    db_manager = DatabaseManager(supabase)
    ui_components = UIComponents(db_manager)
    tab_renderer = TabRenderer(db_manager, ui_components)
    ai_recommendations = AIRecommendations(db_manager)
    
    # Variables de estado para la aplicación
    if 'show_meta_config' not in st.session_state:
        st.session_state.show_meta_config = False
    
    # ========================
    # SIDEBAR
    # ========================
    with st.sidebar:
        st.title("🧠 CRM Inteligente")
        st.markdown("---")
        
        # Configuración de meta mensual
        ui_components.render_sidebar_meta()
        
        st.markdown("---")
        
        # Filtros globales
        ui_components.render_sidebar_filters()
        
        # Botón de limpieza de estado
        if st.button("🔄 Limpiar Estados"):
            keys_to_delete = [key for key in st.session_state.keys() if key.startswith('show_')]
            for key in keys_to_delete:
                del st.session_state[key]
            st.cache_data.clear()
            st.rerun()
    
    # ========================
    # MODAL DE CONFIGURACIÓN DE META
    # ========================
    if st.session_state.show_meta_config:
        ui_components.render_meta_config_modal()
    
    # ========================
    # LAYOUT PRINCIPAL
    # ========================
    if not st.session_state.show_meta_config:
        st.title("🧠 CRM Inteligente")
        
        # Pestañas principales
        tabs = st.tabs([
            "Dashboard",
            "Comisiones", 
            "Nueva Venta",
            "Devoluciones",
            "Clientes",
            "IA & Alertas"
        ])
        
        # Renderizar cada pestaña
        with tabs[0]:
            tab_renderer.render_dashboard()
        
        with tabs[1]:
            tab_renderer.render_comisiones()
        
        with tabs[2]:
            tab_renderer.render_nueva_venta()
        
        with tabs[3]:
            tab_renderer.render_devoluciones()
        
        with tabs[4]:
            tab_renderer.render_clientes()
        
        with tabs[5]:
            tab_renderer.render_ia_alertas()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Error en la aplicación: {str(e)}")
        st.info("Por favor, recarga la página o contacta al administrador.")
