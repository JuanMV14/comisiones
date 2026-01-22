import streamlit as st
import pandas as pd
from typing import Dict, Any
from datetime import datetime
from database.client_purchases_manager import ClientPurchasesManager
from utils.formatting import format_currency
import os


class ClientAnalysisUI:
    """Interfaz para análisis de clientes y sus compras"""
    
    def __init__(self, client_manager: ClientPurchasesManager, catalog_manager=None, sync_manager=None):
        self.client_manager = client_manager
        self.catalog_manager = catalog_manager
        if sync_manager:
            from ui.sync_components import SyncUI
            self.sync_ui = SyncUI(sync_manager)
    
    def render_gestion_clientes(self):
        """Renderiza la gestión de clientes B2B"""
        st.header("👥 Gestión de Clientes B2B")
        
        tab1, tab2, tab3 = st.tabs([
            "📋 Lista de Clientes", 
            "➕ Nuevo Cliente", 
            "📤 Cargar Compras"
        ])
        
        with tab1:
            self._render_lista_clientes()
        
        with tab2:
            self._render_formulario_cliente()
        
        with tab3:
            self._render_carga_compras()
    
    def _render_eliminar_todas_compras(self):
        """Renderiza la opción para eliminar todas las compras de un cliente"""
        st.subheader("🗑️ Eliminar Todas las Compras de un Cliente")
        st.markdown("---")
        st.error("⚠️ **ADVERTENCIA:** Esta acción eliminará TODAS las compras y devoluciones del cliente seleccionado. Esta acción NO se puede deshacer.")
        
        # Seleccionar cliente
        df_clientes = self.client_manager.listar_clientes()
        
        if df_clientes.empty:
            st.warning("⚠️ No hay clientes registrados")
            return
        
        opciones_clientes = {f"{row['nombre']} ({row['nit']})": row['nit'] for _, row in df_clientes.iterrows()}
        cliente_seleccionado = st.selectbox("Seleccionar Cliente", list(opciones_clientes.keys()), key="select_cliente_verificar")
        nit_seleccionado = opciones_clientes[cliente_seleccionado]
        
        # Obtener resumen antes de eliminar
        resumen = self.client_manager.obtener_resumen_compras_cliente(nit_seleccionado)
        
        if "error" not in resumen:
            st.markdown("---")
            st.info(f"📊 **Resumen actual:** {resumen['total_registros']} registros ({resumen['total_compras']} compras, {resumen['total_devoluciones']} devoluciones)")
        
        st.markdown("---")
        
        # Confirmación
        confirmacion = st.text_input(
            "Para confirmar, escribe 'ELIMINAR' en mayúsculas:",
            key="confirmacion_eliminar"
        )
        
        if st.button("🗑️ Eliminar TODAS las Compras", type="primary", disabled=(confirmacion != "ELIMINAR")):
            with st.spinner("Eliminando compras..."):
                resultado = self.client_manager.eliminar_todas_compras_cliente(nit_seleccionado)
            
            if "error" in resultado:
                st.error(f"❌ {resultado['error']}")
            else:
                st.success(f"✅ {resultado['mensaje']}")
                st.cache_data.clear()
                st.rerun()
    
    def _render_lista_clientes(self):
        """Lista de clientes registrados"""
        st.subheader("Clientes Registrados")
        
        df_clientes = self.client_manager.listar_clientes()
        
        if df_clientes.empty:
            st.info("No hay clientes registrados. Agrega el primer cliente en la pestaña 'Nuevo Cliente'.")
            return
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Clientes", len(df_clientes))
        with col2:
            cupo_total = df_clientes['cupo_total'].sum()
            st.metric("Cupo Total", format_currency(cupo_total))
        with col3:
            cupo_utilizado = df_clientes['cupo_utilizado'].sum()
            st.metric("Cupo Utilizado", format_currency(cupo_utilizado))
        with col4:
            cupo_disponible = cupo_total - cupo_utilizado
            st.metric("Cupo Disponible", format_currency(cupo_disponible))
        
        st.markdown("---")
        
        # Tabla de clientes
        for _, cliente in df_clientes.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.markdown(f"### {cliente['nombre']}")
                    st.write(f"**NIT:** {cliente['nit']} | **Ciudad:** {cliente.get('ciudad', 'N/A')}")
                
                with col2:
                    cupo_disp = cliente['cupo_total'] - cliente['cupo_utilizado']
                    pct_uso = (cliente['cupo_utilizado'] / cliente['cupo_total'] * 100) if cliente['cupo_total'] > 0 else 0
                    st.metric("Cupo Disponible", format_currency(cupo_disp), delta=f"-{pct_uso:.1f}% usado")
                
                with col3:
                    descuento_actual = cliente.get('descuento_predeterminado', 0) or 0
                    st.metric("Descuento", f"{descuento_actual:.2f}%")
                    st.metric("Plazo Pago", f"{cliente['plazo_pago']} días")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("📊 Ver Análisis", key=f"analisis_{cliente['nit']}", use_container_width=True):
                            st.session_state['cliente_analisis'] = cliente['nit']
                            st.rerun()
                    with col_btn2:
                        if st.button("✏️ Editar", key=f"editar_{cliente['nit']}", use_container_width=True):
                            st.session_state['cliente_editar'] = cliente['nit']
                            st.rerun()
                
                # Mostrar formulario de edición si este cliente está seleccionado
                if st.session_state.get('cliente_editar') == cliente['nit']:
                    st.markdown("---")
                    st.markdown("#### ✏️ Editar Cliente")
                    
                    with st.form(f"form_editar_{cliente['nit']}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            nuevo_descuento = st.number_input(
                                "Descuento Predeterminado (%)",
                                min_value=0.0,
                                max_value=100.0,
                                value=float(descuento_actual),
                                step=0.5,
                                key=f"edit_descuento_{cliente['nit']}"
                            )
                            nuevo_cupo_total = st.number_input(
                                "Cupo Total",
                                min_value=0,
                                value=int(cliente.get('cupo_total', 0)),
                                step=1000000,
                                key=f"edit_cupo_total_{cliente['nit']}"
                            )
                        
                        with col2:
                            nuevo_cupo_utilizado = st.number_input(
                                "Cupo Utilizado",
                                min_value=0,
                                value=int(cliente.get('cupo_utilizado', 0)),
                                step=100000,
                                key=f"edit_cupo_utilizado_{cliente['nit']}"
                            )
                            nuevo_plazo = st.selectbox(
                                "Plazo de Pago (días)",
                                [15, 30, 45, 60, 90],
                                index=[15, 30, 45, 60, 90].index(cliente.get('plazo_pago', 30)) if cliente.get('plazo_pago', 30) in [15, 30, 45, 60, 90] else 1,
                                key=f"edit_plazo_{cliente['nit']}"
                            )
                        
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.form_submit_button("💾 Guardar Cambios", type="primary", use_container_width=True):
                                resultado = self.client_manager.registrar_cliente({
                                    'nombre': cliente['nombre'],
                                    'nit': cliente['nit'],
                                    'cupo_total': nuevo_cupo_total,
                                    'cupo_utilizado': nuevo_cupo_utilizado,
                                    'plazo_pago': nuevo_plazo,
                                    'ciudad': cliente.get('ciudad', ''),
                                    'telefono': cliente.get('telefono', ''),
                                    'email': cliente.get('email', ''),
                                    'direccion': cliente.get('direccion', ''),
                                    'vendedor': cliente.get('vendedor', ''),
                                    'descuento_predeterminado': nuevo_descuento
                                })
                                
                                if "error" in resultado:
                                    st.error(f"❌ {resultado['error']}")
                                else:
                                    st.success(f"✅ Cliente actualizado: {cliente['nombre']}")
                                    st.session_state.pop('cliente_editar', None)
                                    st.cache_data.clear()
                                    st.rerun()
                        
                        with col_cancel:
                            if st.form_submit_button("❌ Cancelar", use_container_width=True):
                                st.session_state.pop('cliente_editar', None)
                                st.rerun()
        
        # Mostrar análisis si hay cliente seleccionado
        if 'cliente_analisis' in st.session_state:
            st.markdown("---")
            self.render_analisis_cliente(st.session_state['cliente_analisis'])
    
    def _render_formulario_cliente(self):
        """Formulario para registrar nuevo cliente"""
        st.subheader("Registrar Nuevo Cliente")
        
        with st.form("form_nuevo_cliente"):
            col1, col2 = st.columns(2)
            
            with col1:
                nombre = st.text_input("Nombre/Razón Social *", placeholder="EMPRESA S.A.S")
                nit = st.text_input("NIT *", placeholder="901234567")
                ciudad = st.text_input("Ciudad", placeholder="Bogotá")
                telefono = st.text_input("Teléfono", placeholder="3001234567")
            
            with col2:
                cupo_total = st.number_input("Cupo de Crédito", min_value=0, value=0, step=1000000)
                cupo_utilizado = st.number_input("Cupo Utilizado", min_value=0, value=0, step=100000)
                plazo_pago = st.selectbox("Plazo de Pago (días)", [15, 30, 45, 60, 90], index=1, key="select_plazo_pago")
                descuento_predeterminado = st.number_input(
                    "Descuento Predeterminado (%)", 
                    min_value=0.0, 
                    max_value=100.0, 
                    value=0.0, 
                    step=0.5,
                    key="descuento_predeterminado_nuevo",
                    help="Descuento que se aplicará por defecto a las ventas de este cliente"
                )
                email = st.text_input("Email", placeholder="contacto@empresa.com")
            
            direccion = st.text_area("Dirección", placeholder="Calle 123 # 45-67")
            vendedor = st.text_input("Vendedor Asignado", placeholder="Nombre del vendedor")
            
            submitted = st.form_submit_button("💾 Guardar Cliente", type="primary", use_container_width=True)
            
            if submitted:
                if not nombre or not nit:
                    st.error("❌ Nombre y NIT son obligatorios")
                else:
                    resultado = self.client_manager.registrar_cliente({
                        'nombre': nombre,
                        'nit': nit,
                        'cupo_total': cupo_total,
                        'cupo_utilizado': cupo_utilizado,
                        'plazo_pago': plazo_pago,
                        'ciudad': ciudad,
                        'telefono': telefono,
                        'email': email,
                        'direccion': direccion,
                        'vendedor': vendedor,
                        'descuento_predeterminado': descuento_predeterminado
                    })
                    
                    if "error" in resultado:
                        st.error(f"❌ {resultado['error']}")
                    else:
                        st.success(f"✅ {resultado['mensaje']}: {nombre}")
                        st.cache_data.clear()
                        st.rerun()
    
    def _render_carga_compras(self):
        """Carga de compras desde Excel"""
        st.subheader("Cargar Compras de Cliente")
        
        # Seleccionar cliente
        df_clientes = self.client_manager.listar_clientes()
        
        if df_clientes.empty:
            st.warning("⚠️ Primero debes registrar al menos un cliente")
            return
        
        opciones_clientes = {f"{row['nombre']} ({row['nit']})": row['nit'] for _, row in df_clientes.iterrows()}
        cliente_seleccionado = st.selectbox("Seleccionar Cliente", list(opciones_clientes.keys()), key="select_cliente_cargar")
        nit_seleccionado = opciones_clientes[cliente_seleccionado]
        
        st.markdown("---")
        
        # Opción 1: Subir archivo
        st.markdown("### 📁 Subir Archivo Excel")
        uploaded_file = st.file_uploader(
            "Selecciona el archivo de compras",
            type=['xlsx', 'xls'],
            help="El archivo debe contener las columnas: FUENTE, NUM_DCTO, FECHA, COD_ARTICULO, DETALLE, CANTIDAD, valor_Unitario, dcto, Total, FAMILIA, Marca, SUBGRUPO, GRUPO"
        )
        
        if uploaded_file:
            if st.button("📥 Procesar Archivo", type="primary"):
                import tempfile
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                with st.spinner("Procesando compras..."):
                    resultado = self.client_manager.cargar_compras_desde_excel(tmp_path, nit_seleccionado)
                
                os.unlink(tmp_path)
                
                if "error" in resultado:
                    st.error(f"❌ {resultado['error']}")
                else:
                    st.success(f"✅ Compras cargadas para {resultado['cliente']}")
                    st.json(resultado)
                    st.cache_data.clear()
        
        st.markdown("---")
        
        # Opción 2: Ruta de archivo
        st.markdown("### 📂 O usar ruta de archivo")
        ruta_archivo = st.text_input("Ruta del archivo", placeholder=r"C:\Users\...\archivo.xlsx")
        
        if ruta_archivo:
            if st.button("📥 Cargar desde Ruta"):
                if os.path.exists(ruta_archivo):
                    with st.spinner("Procesando compras..."):
                        resultado = self.client_manager.cargar_compras_desde_excel(ruta_archivo, nit_seleccionado)
                    
                    if "error" in resultado:
                        st.error(f"❌ {resultado['error']}")
                    else:
                        st.success(f"✅ Compras cargadas para {resultado['cliente']}")
                        st.json(resultado)
                        st.cache_data.clear()
                else:
                    st.error(f"❌ No se encontró el archivo: {ruta_archivo}")
    
    def render_analisis_cliente(self, nit_cliente: str):
        """Renderiza el análisis completo de un cliente"""
        st.header("📊 Análisis de Cliente")
        
        analisis = self.client_manager.analizar_cliente(nit_cliente)
        
        if "error" in analisis:
            st.error(f"❌ {analisis['error']}")
            return
        
        cliente = analisis['cliente']
        resumen = analisis['resumen']
        
        # Info del cliente
        with st.container(border=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            with col1:
                st.markdown(f"## {cliente['nombre']}")
                st.write(f"**NIT:** {cliente['nit']} | **Ciudad:** {cliente.get('ciudad', 'N/A')}")
            with col2:
                cupo_disp = cliente['cupo_total'] - cliente['cupo_utilizado']
                st.metric("Cupo Disponible", format_currency(cupo_disp))
            with col3:
                st.metric("Plazo Pago", f"{cliente['plazo_pago']} días")
        
        st.markdown("---")
        
        # Métricas principales
        st.subheader("📈 Resumen de Compras")
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Comprado", format_currency(resumen['total_compras']))
        with col2:
            st.metric("Devoluciones", format_currency(resumen.get('total_devoluciones', 0)), 
                     delta=f"-{resumen.get('num_devoluciones', 0)} docs")
        with col3:
            st.metric("Neto Compras", format_currency(resumen.get('neto_compras', resumen['total_compras'])))
        with col4:
            st.metric("Transacciones", resumen['num_transacciones'])
        with col5:
            st.metric("Ticket Promedio", format_currency(resumen['ticket_promedio']))
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Productos Diferentes", resumen['productos_diferentes'])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Frecuencia Compra", f"{resumen['frecuencia_dias']:.0f} días")
        with col2:
            st.metric("Días sin Comprar", resumen['dias_sin_comprar'])
        with col3:
            st.metric("Última Compra", resumen['ultima_compra'])
        with col4:
            st.metric("Descuento Promedio", f"{resumen['descuento_promedio']:.1f}%")
        
        st.markdown("---")
        
        # Análisis detallado en tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏭 Marcas", "📦 Categorías", "🛒 Productos Top", "💡 Recomendaciones"])
        
        with tab1:
            self._render_analisis_marcas(analisis['marcas_preferidas'])
        
        with tab2:
            self._render_analisis_categorias(analisis['grupos_preferidos'], analisis['subgrupos_preferidos'])
        
        with tab3:
            self._render_productos_top(analisis['productos_top'])
        
        with tab4:
            self._render_recomendaciones(nit_cliente)
    
    def _render_analisis_marcas(self, marcas: list):
        """Renderiza análisis de marcas preferidas"""
        st.subheader("🏭 Marcas Preferidas")
        
        if not marcas:
            st.info("No hay datos de marcas")
            return
        
        df = pd.DataFrame(marcas)
        
        # Top 5 marcas
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Top Marcas por Valor")
            for i, marca in enumerate(marcas[:5], 1):
                with st.container(border=True):
                    st.markdown(f"**{i}. {marca['marca']}**")
                    st.write(f"💰 {format_currency(marca['total'])} | 📦 {marca['cantidad']} unidades | 🧾 {marca['transacciones']} compras")
        
        with col2:
            st.markdown("#### Distribución de Compras")
            if 'total' in df.columns:
                st.bar_chart(df.set_index('marca')['total'].head(10))
    
    def _render_analisis_categorias(self, grupos: list, subgrupos: list):
        """Renderiza análisis de categorías"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📦 Grupos/Categorías")
            for grupo in grupos[:5]:
                with st.container(border=True):
                    st.markdown(f"**{grupo['grupo']}**")
                    st.write(f"💰 {format_currency(grupo['total'])} | 📦 {grupo['cantidad']} unidades")
        
        with col2:
            st.subheader("🔧 Subgrupos")
            for subgrupo in subgrupos[:5]:
                with st.container(border=True):
                    st.markdown(f"**{subgrupo['subgrupo']}**")
                    st.write(f"💰 {format_currency(subgrupo['total'])} | 📦 {subgrupo['cantidad']} unidades")
    
    def _render_productos_top(self, productos: list):
        """Renderiza productos más comprados"""
        st.subheader("🛒 Productos Más Comprados")
        
        if not productos:
            st.info("No hay datos de productos")
            return
        
        for i, prod in enumerate(productos[:10], 1):
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{i}. {prod['cod_articulo']}**")
                    st.write(prod['detalle'][:80] + "..." if len(prod['detalle']) > 80 else prod['detalle'])
                    st.caption(f"Marca: {prod['marca']}")
                with col2:
                    st.metric("Cantidad Total", prod['cantidad'])
                with col3:
                    st.metric("Veces Comprado", prod['veces_comprado'])
    
    def _render_recomendaciones(self, nit_cliente: str):
        """Renderiza recomendaciones de productos"""
        st.subheader("💡 Recomendaciones de Productos")
        
        if not self.catalog_manager:
            st.warning("⚠️ No hay catálogo disponible para generar recomendaciones")
            return
        
        if st.button("🔄 Generar Recomendaciones", type="primary"):
            with st.spinner("Analizando patrones de compra..."):
                recomendaciones = self.client_manager.generar_recomendaciones(nit_cliente, self.catalog_manager)
            
            if "error" in recomendaciones:
                st.error(f"❌ {recomendaciones['error']}")
                return
            
            st.success(f"✅ {recomendaciones['total_recomendaciones']} recomendaciones generadas")
            
            # Por marca
            if recomendaciones['recomendaciones']['por_marca']:
                st.markdown("#### 🏭 Basado en Marcas Preferidas")
                for rec in recomendaciones['recomendaciones']['por_marca'][:5]:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{rec['cod_ur']}** - {rec['descripcion'][:60]}...")
                            st.caption(f"Marca: {rec['marca']} | {rec['razon']}")
                        with col2:
                            st.metric("Precio", format_currency(rec['precio']))
            
            # Por categoría
            if recomendaciones['recomendaciones']['por_categoria']:
                st.markdown("#### 📦 Basado en Categorías")
                for rec in recomendaciones['recomendaciones']['por_categoria'][:5]:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{rec['cod_ur']}** - {rec['descripcion'][:60]}...")
                            st.caption(f"Marca: {rec['marca']} | {rec['razon']}")
                        with col2:
                            st.metric("Precio", format_currency(rec['precio']))
            
            # Recompra
            if recomendaciones['recomendaciones']['recompra']:
                st.markdown("#### 🔄 Sugerencias de Recompra")
                for rec in recomendaciones['recomendaciones']['recompra'][:5]:
                    with st.container(border=True):
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{rec['cod_articulo']}** - {rec['detalle'][:60]}...")
                            st.caption(f"Marca: {rec['marca']} | Compró {rec['cantidad_historica']} unidades")
                        with col2:
                            st.metric("Días sin Comprar", rec['dias_sin_comprar'])
    
    def _render_verificacion_compras(self):
        """Renderiza la verificación y limpieza de compras"""
        st.subheader("🔍 Verificar y Limpiar Compras de Cliente")
        st.markdown("---")
        st.warning("⚠️ **Importante:** Esta herramienta te permite revisar y eliminar compras incorrectas de un cliente")
        
        # Seleccionar cliente
        df_clientes = self.client_manager.listar_clientes()
        
        if df_clientes.empty:
            st.warning("⚠️ No hay clientes registrados")
            return
        
        # Buscar cliente específico o seleccionar
        col1, col2 = st.columns([2, 1])
        with col1:
            opciones_clientes = {f"{row['nombre']} ({row['nit']})": row['nit'] for _, row in df_clientes.iterrows()}
            cliente_seleccionado = st.selectbox("Seleccionar Cliente", list(opciones_clientes.keys()), key="select_cliente_verificar_compras")
            nit_seleccionado = opciones_clientes[cliente_seleccionado]
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔍 Verificar", type="primary", use_container_width=True):
                st.session_state['nit_verificacion'] = nit_seleccionado
        
        # Mostrar compras si hay cliente seleccionado
        if 'nit_verificacion' in st.session_state:
            nit_verificar = st.session_state['nit_verificacion']
            
            # Obtener resumen
            resumen = self.client_manager.obtener_resumen_compras_cliente(nit_verificar)
            
            if "error" in resumen:
                st.error(f"❌ {resumen['error']}")
                return
            
            # Mostrar resumen
            st.markdown("---")
            st.subheader("📊 Resumen de Compras")
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Registros", resumen['total_registros'])
            with col2:
                st.metric("Compras (FE)", resumen['total_compras'])
            with col3:
                st.metric("Devoluciones (DV)", resumen['total_devoluciones'])
            with col4:
                st.metric("Documentos Únicos", resumen['documentos_unicos'])
            with col5:
                st.metric("Valor Total", format_currency(resumen['total_valor_compras']))
            
            st.markdown("---")
            
            # Obtener todas las compras
            df_compras = self.client_manager.obtener_compras_cliente(nit_verificar, incluir_devoluciones=True)
            
            if not df_compras.empty:
                # Convertir fechas
                df_compras['fecha'] = pd.to_datetime(df_compras['fecha'])
                
                # Agrupar por documento para mejor visualización
                st.subheader("📋 Compras por Documento")
                
                documentos = df_compras.groupby(['num_documento', 'fuente', 'es_devolucion']).agg({
                    'fecha': 'first',
                    'total': 'sum',
                    'cantidad': 'sum',
                    'cod_articulo': 'count'
                }).reset_index()
                
                documentos = documentos.sort_values('fecha', ascending=False)
                
                # Mostrar cada documento
                compras_seleccionadas = []
                
                for _, doc in documentos.iterrows():
                    tipo = "🔄 Devolución" if doc['es_devolucion'] else "✅ Compra"
                    fuente = doc['fuente']
                    fecha = pd.to_datetime(doc['fecha']).strftime("%d/%m/%Y")
                    
                    with st.container(border=True):
                        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])
                        
                        with col1:
                            st.markdown(f"**Documento:** {doc['num_documento']}")
                            st.caption(f"{tipo} ({fuente}) | Fecha: {fecha}")
                        
                        with col2:
                            st.metric("Total", format_currency(abs(doc['total'])))
                        
                        with col3:
                            st.metric("Items", doc['cod_articulo'])
                        
                        with col4:
                            st.metric("Cantidad", doc['cantidad'])
                        
                        with col5:
                            # Obtener IDs de las compras de este documento
                            compras_doc = df_compras[
                                (df_compras['num_documento'] == doc['num_documento']) &
                                (df_compras['es_devolucion'] == doc['es_devolucion'])
                            ]
                            ids_doc = compras_doc['id'].tolist()
                            
                            if st.checkbox("Eliminar", key=f"eliminar_{doc['num_documento']}_{doc['es_devolucion']}"):
                                compras_seleccionadas.extend(ids_doc)
                            
                            # Mostrar detalles
                            with st.expander("Ver detalles"):
                                st.dataframe(compras_doc[['cod_articulo', 'detalle', 'cantidad', 'valor_unitario', 'total']], 
                                           use_container_width=True, hide_index=True)
                
                # Botón para eliminar seleccionadas
                if compras_seleccionadas:
                    st.markdown("---")
                    st.error(f"⚠️ **{len(compras_seleccionadas)} registros seleccionados para eliminar**")
                    
                    if st.button("🗑️ Eliminar Seleccionados", type="primary"):
                        with st.spinner("Eliminando compras..."):
                            resultado = self.client_manager.eliminar_compras(compras_seleccionadas)
                        
                        if "error" in resultado:
                            st.error(f"❌ {resultado['error']}")
                        else:
                            st.success(f"✅ {resultado['eliminadas']} compras eliminadas exitosamente")
                            if resultado['errores'] > 0:
                                st.warning(f"⚠️ {resultado['errores']} errores durante la eliminación")
                            st.cache_data.clear()
                            # Limpiar selección
                            if 'nit_verificacion' in st.session_state:
                                del st.session_state['nit_verificacion']
                            st.rerun()
            else:
                st.info("No hay compras registradas para este cliente")
