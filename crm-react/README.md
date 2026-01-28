# CRM React - Migración del Sistema Streamlit

Este proyecto migra tu CRM de Streamlit a **React + FastAPI**, manteniendo **TODAS las funcionalidades** existentes pero con un diseño moderno y profesional.

## 🎯 Estructura del Proyecto

```
crm-react/
├── frontend/          # React + Tailwind CSS + Vite
│   ├── src/
│   │   ├── components/   # Componentes reutilizables (Sidebar, etc.)
│   │   ├── pages/        # Páginas/vistas del CRM
│   │   ├── api/          # Cliente API para comunicarse con backend
│   │   └── utils/        # Utilidades
│   └── package.json
│
└── backend/           # FastAPI (reutiliza toda tu lógica Python)
    ├── app/
    │   ├── api/          # Endpoints REST
    │   └── services/     # Servicios (opcional)
    └── main.py
```

## ✨ Funcionalidades Migradas

### ✅ Completado:
- ✅ Estructura base React + Tailwind CSS
- ✅ Sidebar con navegación completa (15 opciones)
- ✅ Dashboard del Vendedor (estructura base)
- ✅ Vista de Clientes (tabla, búsqueda)
- ✅ Vista de Mensajes (diseño completo)
- ✅ Backend FastAPI básico
- ✅ Conexión con Supabase (reutiliza tu código existente)

### 🚧 En Desarrollo:
- Panel del Vendedor (métricas, mapa Colombia, gráficos)
- Nueva Venta Simple (productos editables, descuentos, comisiones)
- Catálogo
- Mis Comisiones
- Dashboard Ejecutivo
- Todas las vistas de gerencia

## 🚀 Cómo Usar

### 1. Instalar Frontend

```bash
cd crm-react/frontend
npm install
npm run dev
```

El frontend estará en: `http://localhost:3000`

### 2. Instalar Backend

```bash
cd crm-react/backend
pip install -r requirements.txt
python main.py
```

El backend estará en: `http://localhost:8000`

### 3. Configurar Variables de Entorno

Copia `crm-react/backend/env.example` a un archivo `.env` en el backend con tus credenciales de Supabase:

```env
SUPABASE_URL=tu_url
SUPABASE_KEY=tu_key
```

Opcional (frontend): copia `crm-react/frontend/env.example` a `crm-react/frontend/.env` si vas a:
- apuntar el frontend a un backend desplegado (define `VITE_API_URL`)
- o usar fallback directo a Supabase (`VITE_SUPABASE_URL` / `VITE_SUPABASE_ANON_KEY`)

## 🔄 Reutilización de Código

**El backend FastAPI reutiliza TODA tu lógica Python existente:**

- ✅ `database/queries.py` → Importado directamente
- ✅ `business/calculations.py` → Importado directamente
- ✅ `business/monthly_commission_calculator.py` → Importado directamente
- ✅ `database/client_purchases_manager.py` → Importado directamente
- ✅ Todos tus módulos de negocio → Sin cambios

**No necesitas reescribir nada**, solo crear endpoints API que llamen a tus funciones existentes.

## 📦 Próximos Pasos

### Para completar la migración:

1. **Implementar endpoints API restantes** en `backend/app/api/`:
   - Completar `dashboard.py` (métricas, gráficos, mapa)
   - Completar `clientes.py` (detalle de cliente con todas las pestañas)
   - Completar `ventas.py` (nueva venta con toda la lógica)
   - Crear `comisiones.py`, `catalogo.py`, etc.

2. **Implementar componentes React restantes**:
   - Panel del Vendedor completo (mapa Colombia con Plotly)
   - Nueva Venta Simple (productos editables, descuentos por escala)
   - Vista de Comisiones
   - Dashboard Ejecutivo
   - Todas las vistas de gerencia

3. **Integrar gráficos y mapas**:
   - Plotly para mapa de Colombia
   - Recharts para gráficos de ventas
   - Mismo diseño y funcionalidad que tu Streamlit actual

4. **Testing y Deployment**:
   - Frontend en Vercel (gratis)
   - Backend en Render/Railway (gratis con limitaciones)

## 🎨 Diseño

El diseño replica exactamente el código React que te gustó:
- **Sidebar oscuro** (`bg-slate-900`)
- **Cards con bordes sutiles** (`border-slate-700/50`)
- **Iconos Lucide React**
- **Tema oscuro corporativo**
- **Responsive**

## 📝 Notas

- **No pierdes funcionalidad**: Todo tu código Python se reutiliza
- **No pierdes datos**: Mismo Supabase, misma base de datos
- **Mejor UX**: Diseño moderno y profesional
- **Gratis**: Deployment en Vercel (frontend) y Render (backend)

## 🤝 Contribuir

Este es un proyecto en desarrollo. Para agregar funcionalidades:

1. Crear endpoint en `backend/app/api/` que reutilice tu código Python
2. Crear componente/página en `frontend/src/pages/`
3. Agregar llamada API en `frontend/src/api/`

¿Necesitas ayuda con alguna funcionalidad específica? ¡Pregunta!
