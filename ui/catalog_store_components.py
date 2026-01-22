import streamlit as st
import pandas as pd
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from database.catalog_manager import CatalogManager
from utils.formatting import format_currency

class CatalogStoreUI:
    """Interfaz tipo tienda para visualizar el catálogo de productos"""
    
    def __init__(self, catalog_manager: CatalogManager):
        self.catalog_manager = catalog_manager
    
    def render_catalog_store(self):
        """Renderiza la interfaz principal del catálogo tipo tienda"""
        st.header("🛒 Catálogo de Productos")
        st.markdown("---")
        
        # Estadísticas rápidas
        self._render_estadisticas()
        
        st.markdown("---")
        
        # Búsqueda y filtros
        col1, col2 = st.columns([3, 1])
        with col1:
            termino_busqueda = st.text_input(
                "🔍 Buscar producto",
                placeholder="Buscar por código, referencia, descripción o marca...",
                key="search_catalog"
            )
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Actualizar", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        
        # Filtros avanzados
        with st.expander("🔧 Filtros Avanzados", expanded=False):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                df_temp = self.catalog_manager.cargar_catalogo()
                marcas = ['Todas'] + sorted(df_temp['marca'].unique().tolist()) if not df_temp.empty else ['Todas']
                marca_filtro = st.selectbox("Marca", marcas)
            
            with col2:
                lineas = ['Todas'] + sorted(df_temp['linea'].unique().tolist()) if not df_temp.empty else ['Todas']
                linea_filtro = st.selectbox("Línea", lineas)
            
            with col3:
                precio_min = st.number_input("Precio Mínimo", min_value=0, value=0, step=1000)
            
            with col4:
                precio_max = st.number_input("Precio Máximo", min_value=0, value=0, step=1000)
        
        # Construir filtros
        filtros = {}
        if marca_filtro != 'Todas':
            filtros['marca'] = marca_filtro
        if linea_filtro != 'Todas':
            filtros['linea'] = linea_filtro
        if precio_min > 0:
            filtros['precio_min'] = precio_min
        if precio_max > 0:
            filtros['precio_max'] = precio_max
        
        # Buscar productos
        df_productos = self.catalog_manager.buscar_productos(termino_busqueda, filtros if filtros else None)
        
        # Mostrar resultados
        if not df_productos.empty:
            st.markdown(f"### 📦 {len(df_productos)} productos encontrados")
            
            # Opciones de visualización
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                vista = st.radio(
                    "Vista",
                    ["Tarjetas", "Tabla"],
                    horizontal=True,
                    key="vista_catalogo"
                )
            with col2:
                items_por_pagina = st.selectbox("Items por página", [12, 24, 48, 96], index=1)
            with col3:
                ordenar_por = st.selectbox("Ordenar por", ["Precio", "Marca", "Descripción"], index=0)
            
            # Ordenar
            if ordenar_por == "Precio":
                df_productos = df_productos.sort_values('precio', ascending=True)
            elif ordenar_por == "Marca":
                df_productos = df_productos.sort_values('marca', ascending=True)
            else:
                df_productos = df_productos.sort_values('descripcion', ascending=True)
            
            # Paginación
            total_paginas = (len(df_productos) - 1) // items_por_pagina + 1
            pagina_actual = st.session_state.get('pagina_catalogo', 1)
            
            if total_paginas > 1:
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    pagina_actual = st.selectbox(
                        f"Página (de {total_paginas})",
                        range(1, total_paginas + 1),
                        index=pagina_actual - 1,
                        key="pagina_selector"
                    )
                    st.session_state['pagina_catalogo'] = pagina_actual
            
            # Calcular rango de items a mostrar
            inicio = (pagina_actual - 1) * items_por_pagina
            fin = inicio + items_por_pagina
            df_pagina = df_productos.iloc[inicio:fin]
            
            st.markdown("---")
            
            # Renderizar según vista seleccionada
            if vista == "Tarjetas":
                self._render_tarjetas_productos(df_pagina)
            else:
                self._render_tabla_productos(df_pagina)
            
            # Botón de exportación
            st.markdown("---")
            col1, col2 = st.columns([1, 5])
            with col1:
                csv = df_productos.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar CSV",
                    data=csv,
                    file_name=f"catalogo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        else:
            st.info("🔍 No se encontraron productos con los criterios de búsqueda")
    
    def _render_estadisticas(self):
        """Renderiza estadísticas del catálogo"""
        stats = self.catalog_manager.obtener_estadisticas()
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Productos", stats['total_productos'])
        with col2:
            st.metric("Activos", stats['productos_activos'], delta=f"-{stats['productos_inactivos']} inactivos")
        with col3:
            st.metric("Marcas", stats['marcas'])
        with col4:
            st.metric("Líneas", stats['lineas'])
        with col5:
            st.metric("Precio Promedio", format_currency(stats['precio_promedio']))
    
    def _render_tarjetas_productos(self, df: pd.DataFrame):
        """Renderiza productos en formato de tarjetas tipo tienda"""
        # Calcular número de columnas según el ancho
        num_columnas = 4
        
        # Agrupar productos en filas
        productos_por_fila = []
        for i in range(0, len(df), num_columnas):
            productos_por_fila.append(df.iloc[i:i+num_columnas])
        
        # Renderizar cada fila
        for fila_productos in productos_por_fila:
            cols = st.columns(num_columnas)
            
            for idx, (col, (_, producto)) in enumerate(zip(cols, fila_productos.iterrows())):
                with col:
                    self._render_tarjeta_producto(producto)
    
    def _render_tarjeta_producto(self, producto: pd.Series):
        """Renderiza una tarjeta individual de producto con soporte para modo oscuro"""
        # Crear tarjeta con HTML/CSS
        precio = format_currency(producto.get('precio', 0))
        marca = producto.get('marca', 'N/A')
        linea = producto.get('linea', 'N/A')
        descripcion = producto.get('descripcion', 'Sin descripción')[:80] + "..." if len(str(producto.get('descripcion', ''))) > 80 else producto.get('descripcion', 'Sin descripción')
        
        # Usar contenedor de Streamlit para mejor compatibilidad con temas
        with st.container(border=True):
            st.markdown(f"### **{producto.get('cod_ur', 'N/A')}**")
            st.code(producto.get('referencia', 'N/A'), language=None)
            st.write(descripcion)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"🏭 **{marca}**")
            with col2:
                st.markdown(f"📦 **{linea}**")
            
            st.markdown(f"## 💰 **{precio}**")
    
    def _render_tabla_productos(self, df: pd.DataFrame):
        """Renderiza productos en formato de tabla"""
        # Seleccionar columnas a mostrar
        columnas_mostrar = ['cod_ur', 'referencia', 'descripcion', 'marca', 'linea', 'precio']
        columnas_disponibles = [col for col in columnas_mostrar if col in df.columns]
        
        df_mostrar = df[columnas_disponibles].copy()
        
        # Formatear precio
        if 'precio' in df_mostrar.columns:
            df_mostrar['precio'] = df_mostrar['precio'].apply(lambda x: format_currency(x))
        
        # Renombrar columnas para mejor visualización
        df_mostrar.columns = [col.replace('_', ' ').title() for col in df_mostrar.columns]
        
        st.dataframe(
            df_mostrar,
            use_container_width=True,
            height=400
        )
    
    def render_catalog_upload(self):
        """Renderiza la sección de carga/actualización del catálogo"""
        st.header("📤 Actualizar Catálogo")
        st.markdown("---")
        st.info("💡 **Instrucciones:** Sube el archivo Excel del catálogo. El sistema detectará automáticamente productos nuevos, actualizados o agotados.")
        
        # Opción 1: Cargar desde archivo
        uploaded_file = st.file_uploader(
            "Selecciona el archivo Excel del catálogo",
            type=['xlsx', 'xls'],
            help="El archivo debe contener las columnas: Cod_UR, Referencia, Descripcion, Precio, etc."
        )
        
        # Opción 2: Usar archivo del escritorio
        st.markdown("---")
        st.markdown("### O usar archivo del escritorio")
        ruta_escritorio = r"C:\Users\Contact Cemter UR\Desktop\Ctalogo.xlsx"
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.text_input("Ruta del archivo", value=ruta_escritorio, disabled=True)
        with col2:
            if st.button("📥 Cargar desde Escritorio", use_container_width=True):
                if os.path.exists(ruta_escritorio):
                    with st.spinner("Procesando catálogo..."):
                        resultado = self.catalog_manager.cargar_catalogo_desde_excel(ruta_escritorio)
                        
                        if "error" in resultado:
                            st.error(f"❌ {resultado['error']}")
                        else:
                            st.success("✅ Catálogo actualizado exitosamente!")
                            st.json(resultado)
                            
                            # Mostrar detalles
                            if resultado.get('productos_nuevos', 0) > 0:
                                st.info(f"🆕 {resultado['productos_nuevos']} productos nuevos agregados")
                                if resultado.get('detalle_nuevos'):
                                    st.write("Primeros productos nuevos:", resultado['detalle_nuevos'])
                            
                            if resultado.get('productos_actualizados', 0) > 0:
                                st.info(f"🔄 {resultado['productos_actualizados']} productos actualizados")
                            
                            if resultado.get('productos_desactivados', 0) > 0:
                                st.warning(f"⚠️ {resultado['productos_desactivados']} productos desactivados (agotados)")
                            
                        st.cache_data.clear()
                        st.rerun()
                else:
                    st.error(f"❌ No se encontró el archivo en: {ruta_escritorio}")
        
        # Si se subió un archivo
        if uploaded_file is not None:
            st.markdown("---")
            st.markdown(f"📄 Archivo seleccionado: **{uploaded_file.name}**")
            
            if st.button("📥 Procesar y Actualizar Catálogo", type="primary", use_container_width=True):
                # Guardar temporalmente
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                with st.spinner("Procesando catálogo..."):
                    resultado = self.catalog_manager.cargar_catalogo_desde_excel(tmp_path)
                    
                    # Limpiar archivo temporal
                    os.unlink(tmp_path)
                    
                    if "error" in resultado:
                        st.error(f"❌ {resultado['error']}")
                    else:
                        st.success("✅ Catálogo actualizado exitosamente!")
                        
                        # Mostrar resumen
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Productos", resultado.get('total_productos', 0))
                        with col2:
                            st.metric("Nuevos", resultado.get('productos_nuevos', 0))
                        with col3:
                            st.metric("Actualizados", resultado.get('productos_actualizados', 0))
                        with col4:
                            st.metric("Desactivados", resultado.get('productos_desactivados', 0))
                        
                        # Mostrar detalles
                        if resultado.get('productos_nuevos', 0) > 0:
                            with st.expander(f"🆕 Ver {resultado['productos_nuevos']} productos nuevos"):
                                if resultado.get('detalle_nuevos'):
                                    st.write(resultado['detalle_nuevos'])
                        
                        if resultado.get('productos_actualizados', 0) > 0:
                            with st.expander(f"🔄 Ver {resultado['productos_actualizados']} productos actualizados"):
                                if resultado.get('detalle_actualizados'):
                                    st.write(resultado['detalle_actualizados'])
                        
                        if resultado.get('productos_desactivados', 0) > 0:
                            with st.expander(f"⚠️ Ver {resultado['productos_desactivados']} productos desactivados"):
                                if resultado.get('detalle_desactivados'):
                                    st.write(resultado['detalle_desactivados'])
                        
                        # Botón para buscar un producto específico
                        st.markdown("---")
                        st.markdown("### 🔍 Verificar Producto")
                        codigo_verificar = st.text_input("Ingresa el código del producto a verificar (ej: MT08013)", key="verificar_producto")
                        if codigo_verificar:
                            df_verificar = self.catalog_manager.buscar_productos(codigo_verificar.upper().strip())
                            if not df_verificar.empty:
                                st.success(f"✅ Producto encontrado: {len(df_verificar)} resultado(s)")
                                st.dataframe(df_verificar[['cod_ur', 'referencia', 'descripcion', 'precio', 'activo']], use_container_width=True)
                            else:
                                st.warning(f"⚠️ No se encontró el producto '{codigo_verificar}'")
                                # Buscar en el catálogo completo (incluyendo inactivos)
                                df_completo = self.catalog_manager.cargar_catalogo_completo()
                                if not df_completo.empty:
                                    busqueda = df_completo[df_completo['cod_ur'].str.contains(codigo_verificar.upper().strip(), na=False, case=False)]
                                    if not busqueda.empty:
                                        st.info(f"ℹ️ Se encontró pero está inactivo:")
                                        st.dataframe(busqueda[['cod_ur', 'referencia', 'descripcion', 'precio', 'activo']], use_container_width=True)
                        
                        st.cache_data.clear()
                        st.rerun()

