# CORRECCIONES PARA EL CRM - Agregar estas funciones y reemplazar las secciones problemáticas

# ========================
# FUNCIÓN PARA SUBIDA DE COMPROBANTES - NUEVA
# ========================

def subir_comprobante(supabase: Client, file, factura_id: int):
    """Sube un archivo de comprobante a Supabase Storage"""
    try:
        if file is not None:
            # Generar nombre único para el archivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_extension = file.name.split('.')[-1]
            file_name = f"comprobante_{factura_id}_{timestamp}.{file_extension}"
            
            # Subir archivo a Supabase Storage
            result = supabase.storage.from_(BUCKET).upload(file_name, file.getvalue())
            
            if result:
                # Obtener URL pública
                public_url = supabase.storage.from_(BUCKET).get_public_url(file_name)
                return public_url
            else:
                return None
    except Exception as e:
        print(f"Error subiendo comprobante: {e}")
        return None

# ========================
# FUNCIÓN CORREGIDA PARA CARDS DE FACTURAS
# ========================

def render_factura_card(factura, index):
    """Renderiza una card de factura con estilos corregidos"""
    
    # Determinar estado visual
    if factura.get("pagado"):
        estado_badge = "PAGADA"
        estado_color = "#10b981"
        estado_icon = "✅"
    elif factura.get("dias_vencimiento", 0) < 0:
        estado_badge = "VENCIDA"
        estado_color = "#ef4444"
        estado_icon = "⚠️"
    else:
        estado_badge = "PENDIENTE"
        estado_color = "#f59e0b"
        estado_icon = "⏳"
    
    # Card con colores corregidos
    card_html = f"""
    <div style="
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    ">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div>
                <h3 style="margin: 0; color: #1f2937; font-size: 18px; font-weight: 600;">
                    🧾 {factura.get('pedido', 'N/A')} - {factura.get('cliente', 'N/A')}
                </h3>
                <p style="margin: 4px 0 0 0; color: #6b7280; font-size: 14px;">
                    Factura: {factura.get('factura', 'N/A')}
                </p>
            </div>
            <span style="
                background: {estado_color};
                color: white;
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                white-space: nowrap;
            ">
                {estado_icon} {estado_badge}
            </span>
        </div>
        
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 16px;
            padding: 16px;
            background: #f9fafb;
            border-radius: 8px;
        ">
            <div style="color: #374151;">
                <strong style="color: #1f2937;">💰 Valor Neto:</strong><br>
                <span style="font-size: 16px; font-weight: 600; color: #059669;">
                    {format_currency(factura.get('valor_neto', 0))}
                </span>
            </div>
            <div style="color: #374151;">
                <strong style="color: #1f2937;">📊 Base Comisión:</strong><br>
                <span style="font-size: 16px; font-weight: 600; color: #0369a1;">
                    {format_currency(factura.get('base_comision', 0))}
                </span>
            </div>
            <div style="color: #374151;">
                <strong style="color: #1f2937;">🎯 Comisión:</strong><br>
                <span style="font-size: 16px; font-weight: 600; color: #dc2626;">
                    {format_currency(factura.get('comision', 0))}
                </span>
            </div>
            <div style="color: #374151;">
                <strong style="color: #1f2937;">📅 Fecha Factura:</strong><br>
                <span style="font-size: 14px; color: #6b7280;">
                    {factura.get('fecha_factura', 'N/A')}
                </span>
            </div>
        </div>
    </div>
    """
    
    st.markdown(card_html, unsafe_allow_html=True)

# ========================
# MODAL MEJORADO PARA MARCAR COMO PAGADO CON COMPROBANTE
# ========================

def mostrar_modal_pago(factura):
    """Modal para marcar factura como pagada con subida de comprobante"""
    
    with st.form(f"marcar_pagado_{factura.get('id')}"):
        st.markdown(f"### ✅ Marcar como Pagada - {factura.get('pedido', 'N/A')}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha_pago_real = st.date_input(
                "Fecha de Pago Real",
                value=date.today(),
                help="Fecha en que realmente se recibió el pago"
            )
            
            metodo_pago = st.selectbox(
                "Método de Pago",
                ["Transferencia", "Efectivo", "Cheque", "Tarjeta", "Otro"]
            )
        
        with col2:
            referencia_pago = st.text_input(
                "Referencia/Número de Transacción",
                help="Número de referencia del pago"
            )
            
            observaciones = st.text_area(
                "Observaciones",
                help="Notas adicionales sobre el pago"
            )
        
        st.markdown("#### 📎 Comprobante de Pago")
        comprobante_file = st.file_uploader(
            "Sube el comprobante de pago",
            type=['pdf', 'jpg', 'jpeg', 'png'],
            help="Formatos: PDF, JPG, PNG. Máximo 10MB"
        )
        
        if comprobante_file:
            st.success(f"📄 Archivo seleccionado: {comprobante_file.name}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.form_submit_button("✅ Confirmar Pago", type="primary"):
                # Calcular días de pago reales
                fecha_factura = pd.to_datetime(factura.get('fecha_factura'))
                dias_pago = (pd.to_datetime(fecha_pago_real) - fecha_factura).days
                
                # Subir comprobante si existe
                comprobante_url = None
                if comprobante_file:
                    comprobante_url = subir_comprobante(supabase, comprobante_file, factura.get('id'))
                
                # Actualizar factura
                updates = {
                    "pagado": True,
                    "fecha_pago_real": fecha_pago_real.isoformat(),
                    "dias_pago_real": dias_pago,
                    "metodo_pago": metodo_pago,
                    "referencia": referencia_pago,
                    "observaciones_pago": observaciones
                }
                
                if comprobante_url:
                    updates["comprobante_url"] = comprobante_url
                
                # Verificar si se pierde comisión por +80 días
                if dias_pago > 80:
                    updates["comision_perdida"] = True
                    updates["razon_perdida"] = f"Pago después de 80 días ({dias_pago} días)"
                    updates["comision_ajustada"] = 0
                    st.warning(f"⚠️ ATENCIÓN: La comisión se pierde por pago tardío ({dias_pago} días)")
                
                if actualizar_factura(supabase, factura.get('id'), updates):
                    st.success("✅ Factura marcada como pagada correctamente")
                    st.session_state[f"show_pago_{factura.get('id')}"] = False
                    st.rerun()
                else:
                    st.error("❌ Error al actualizar factura")
        
        with col2:
            if st.form_submit_button("❌ Cancelar"):
                st.session_state[f"show_pago_{factura.get('id')}"] = False
                st.rerun()

# ========================
# FUNCIÓN PARA MOSTRAR COMPROBANTE
# ========================

def mostrar_comprobante(comprobante_url):
    """Muestra el comprobante de pago"""
    if comprobante_url:
        if comprobante_url.lower().endswith('.pdf'):
            st.markdown(f"📄 [Ver Comprobante PDF]({comprobante_url})")
        else:
            try:
                st.image(comprobante_url, caption="Comprobante de Pago", width=300)
            except:
                st.markdown(f"🖼️ [Ver Comprobante]({comprobante_url})")
    else:
        st.info("📄 No hay comprobante subido")

# ========================
# REEMPLAZO PARA LA SECCIÓN DE COMISIONES (TAB 2)
# ========================

def render_tab_comisiones_corregida():
    """Renderiza el tab de comisiones con UI corregida"""
    
    st.header("💰 Gestión de Comisiones")
    
    # Filtros rápidos con mejor UI
    with st.container():
        st.markdown("### 🔍 Filtros")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            estado_filter = st.selectbox("📊 Estado", ["Todos", "Pendientes", "Pagadas", "Vencidas"])
        with col2:
            cliente_filter = st.text_input("🔎 Buscar cliente")
        with col3:
            monto_min = st.number_input("💰 Valor mínimo", min_value=0, value=0, step=100000)
        with col4:
            if st.button("📥 Exportar Excel", help="Exportar datos filtrados"):
                st.success("📊 Funcionalidad de exportación próximamente")
    
    # Cargar y filtrar datos
    df = cargar_datos(supabase)
    if not df.empty:
        df = agregar_campos_faltantes(df)
        
        # Aplicar filtros
        df_filtrado = df.copy()
        
        if estado_filter == "Pendientes":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == False]
        elif estado_filter == "Pagadas":
            df_filtrado = df_filtrado[df_filtrado["pagado"] == True]
        elif estado_filter == "Vencidas":
            df_filtrado = df_filtrado[df_filtrado["dias_vencimiento"] < 0]
        
        if cliente_filter:
            df_filtrado = df_filtrado[df_filtrado["cliente"].str.contains(cliente_filter, case=False, na=False)]
        
        if monto_min > 0:
            df_filtrado = df_filtrado[df_filtrado["valor"] >= monto_min]
    else:
        df_filtrado = pd.DataFrame()
    
    # Métricas de resumen
    if not df_filtrado.empty:
        st.markdown("### 📊 Resumen")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📋 Facturas", len(df_filtrado))
        with col2:
            st.metric("💰 Total Comisiones", format_currency(df_filtrado["comision"].sum()))
        with col3:
            st.metric("📈 Valor Promedio", format_currency(df_filtrado["valor"].mean()))
        with col4:
            pendientes = len(df_filtrado[df_filtrado["pagado"] == False])
            st.metric("⏳ Pendientes", pendientes, delta=f"-{len(df_filtrado)-pendientes}", delta_color="inverse")
    
    st.markdown("---")
    
    # Lista de facturas con UI corregida
    if not df_filtrado.empty:
        st.markdown("### 📋 Facturas Detalladas")
        
        for index, (_, factura) in enumerate(df_filtrado.iterrows()):
            # Renderizar card corregida
            render_factura_card(factura, index)
            
            # Botones de acción mejorados
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                if st.button("✏️", key=f"edit_{factura.get('id', 0)}", help="Editar factura"):
                    st.session_state[f"show_edit_{factura.get('id')}"] = True
            
            with col2:
                if not factura.get("pagado"):
                    if st.button("✅", key=f"pay_{factura.get('id', 0)}", help="Marcar como pagada"):
                        st.session_state[f"show_pago_{factura.get('id')}"] = True
            
            with col3:
                if factura.get("pagado"):
                    if st.button("🔄", key=f"dev_{factura.get('id', 0)}", help="Procesar devolución"):
                        st.session_state[f"show_devolucion_{factura.get('id')}"] = True
            
            with col4:
                if st.button("📄", key=f"detail_{factura.get('id', 0)}", help="Ver detalles completos"):
                    st.session_state[f"show_detail_{factura.get('id')}"] = True
            
            with col5:
                if factura.get("comprobante_url"):
                    if st.button("📎", key=f"comp_{factura.get('id', 0)}", help="Ver comprobante"):
                        st.session_state[f"show_comprobante_{factura.get('id')}"] = True
            
            with col6:
                if factura.get("dias_vencimiento", 0) < 0:
                    st.markdown("🚨", help=f"Vencida hace {abs(factura.get('dias_vencimiento', 0))} días")
            
            # Mostrar modales si están activos
            if st.session_state.get(f"show_pago_{factura.get('id')}", False):
                mostrar_modal_pago(factura)
            
            if st.session_state.get(f"show_comprobante_{factura.get('id')}", False):
                with st.expander(f"📎 Comprobante - {factura.get('pedido', 'N/A')}", expanded=True):
                    mostrar_comprobante(factura.get("comprobante_url"))
                    if st.button("❌ Cerrar", key=f"close_comp_{factura.get('id')}"):
                        st.session_state[f"show_comprobante_{factura.get('id')}"] = False
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("📭 No hay facturas que coincidan con los filtros aplicados")

# ========================
# CSS MEJORADO PARA CORREGIR PROBLEMAS VISUALES
# ========================

def aplicar_css_corregido():
    """Aplica CSS mejorado para corregir problemas visuales"""
    st.markdown("""
    <style>
        /* Corregir contraste en cards */
        .stMarkdown div[data-testid="metric-container"] {
            background: white !important;
            border: 1px solid #e5e7eb !important;
            padding: 1rem !important;
            border-radius: 0.5rem !important;
        }
        
        .stMarkdown div[data-testid="metric-container"] > div {
            color: #1f2937 !important;
        }
        
        /* Mejorar botones */
        .stButton > button {
            border-radius: 0.5rem !important;
            border: 1px solid #d1d5db !important;
            padding: 0.5rem 1rem !important;
        }
        
        /* Corregir selectbox y inputs */
        .stSelectbox > div > div {
            background-color: white !important;
            color: #1f2937 !important;
        }
        
        .stTextInput > div > div > input {
            background-color: white !important;
            color: #1f2937 !important;
        }
        
        /* Mejorar tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 1rem 1.5rem !important;
            border-radius: 0.5rem !important;
        }
        
        /* Ocultar elementos técnicos */
        .element-container:has(> .stMarkdown > div[data-testid="stMarkdownContainer"] > div > div) {
            display: none;
        }
        
        /* Mejorar alerts */
        .stAlert {
            border-radius: 0.5rem !important;
            border: none !important;
            padding: 1rem !important;
        }
    </style>
    """, unsafe_allow_html=True)
