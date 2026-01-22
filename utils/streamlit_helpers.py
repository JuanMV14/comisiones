"""
Utilidades para Streamlit - Funciones helper para evitar errores comunes
"""
import streamlit as st
import time
from typing import Optional


def safe_rerun(delay: float = 0.15, max_retries: int = 3):
    """
    Ejecuta st.rerun() de manera segura, evitando múltiples llamadas simultáneas.
    
    Esto previene el error 'NotFoundError: Failed to execute removeChild on Node'
    que ocurre cuando múltiples reruns se ejecutan al mismo tiempo.
    
    Args:
        delay: Tiempo de espera en segundos antes de ejecutar el rerun (default: 0.15)
        max_retries: Número máximo de intentos si hay un rerun en progreso (default: 3)
    """
    # Verificar si ya hay un rerun en progreso
    if st.session_state.get("_rerunning", False):
        # Si hay un rerun en progreso, esperar un poco y verificar de nuevo
        for _ in range(max_retries):
            time.sleep(delay)
            if not st.session_state.get("_rerunning", False):
                break
        else:
            # Si después de los reintentos sigue habiendo un rerun, no hacer nada
            return
    
    # Marcar que hay un rerun en progreso
    st.session_state["_rerunning"] = True
    
    # Pequeño delay para asegurar que el estado se guarde
    time.sleep(delay)
    
    try:
        st.rerun()
    except Exception:
        # Si hay un error, asegurarse de limpiar el flag
        st.session_state["_rerunning"] = False
        raise





