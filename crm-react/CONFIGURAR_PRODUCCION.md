# 🚀 Configuración Rápida para Producción

## Problema Actual

Tu aplicación funciona perfectamente en local pero en producción (Vercel) muestra errores porque el frontend no puede conectarse al backend.

## Solución en 3 Pasos

### ✅ Paso 1: Verificar que el Backend esté Desplegado

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Busca un proyecto llamado algo como `crm-backend` o `comisiones-backend`
3. Si **NO existe**, despliégalo ahora:
   ```bash
   cd crm-react/backend
   vercel login
   vercel
   ```
   - Cuando te pregunte el nombre, usa: `crm-backend` o `comisiones-backend`
   - Anota la URL que te da (ej: `https://crm-backend-xxxxx.vercel.app`)

4. Si **SÍ existe**, abre el proyecto y copia la URL de producción

### ✅ Paso 2: Configurar Variable de Entorno en el Frontend

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Abre tu proyecto **frontend** (el que muestra el error)
3. Ve a **Settings** → **Environment Variables**
4. Haz clic en **Add New**
5. Completa:
   - **Key:** `VITE_API_URL`
   - **Value:** `https://tu-backend-xxxxx.vercel.app/api`
     (Reemplaza `tu-backend-xxxxx.vercel.app` con la URL real de tu backend del Paso 1)
   - **Environment:** Selecciona las tres opciones:
     - ☑ Production
     - ☑ Preview  
     - ☑ Development
6. Haz clic en **Save**

### ✅ Paso 3: Redesplegar el Frontend

**⚠️ IMPORTANTE:** Después de agregar variables de entorno, SIEMPRE debes redesplegar:

**Opción A: Desde Vercel Dashboard (Recomendado)**
1. Ve a **Deployments**
2. Haz clic en el deployment más reciente (el que está arriba)
3. Haz clic en **...** (tres puntos) en la esquina superior derecha
4. Selecciona **Redeploy**
5. Espera 1-2 minutos a que termine

**Opción B: Desde Terminal**
```bash
cd crm-react/frontend
vercel --prod
```

## ✅ Verificación

Después de redesplegar:

1. Abre tu aplicación en el navegador
2. Abre la consola del navegador (F12 → pestaña Console)
3. Deberías ver:
   ```
   🌐 Entorno: PRODUCCIÓN
   🌐 API URL: https://tu-backend-xxxxx.vercel.app/api
   ```
4. Si ves `⚠️ VITE_API_URL no configurada`, vuelve al Paso 2

## 🔍 Troubleshooting

### Error: "Network Error" o "Failed to fetch"

**Causa:** El frontend no puede conectarse al backend.

**Solución:**
1. Verifica que el backend esté desplegado (Paso 1)
2. Verifica que `VITE_API_URL` esté configurada correctamente (Paso 2)
3. Verifica que hayas redesplegado después de agregar la variable (Paso 3)

### Error: "CORS policy"

**Causa:** El backend no permite el origen del frontend.

**Solución:**
1. Ve al proyecto backend en Vercel
2. Settings → Environment Variables
3. Agrega: `FRONTEND_URLS=https://tu-frontend.vercel.app`
   (Reemplaza con la URL real de tu frontend)
4. Redesplegar el backend

### La variable está configurada pero sigue sin funcionar

**Causa:** No redesplegaste después de agregar la variable.

**Solución:** 
- Las variables de entorno de Vite solo están disponibles en **build time**
- Debes **redesplegar** después de agregar o cambiar variables
- Ve al Paso 3 y redesplegar

## 📋 Checklist Final

- [ ] Backend desplegado en Vercel
- [ ] URL del backend anotada
- [ ] Variable `VITE_API_URL` agregada en el frontend
- [ ] Variable configurada para Production, Preview y Development
- [ ] Frontend redesplegado después de agregar la variable
- [ ] Verificado en la consola del navegador que la URL está configurada

## 🎯 Resultado Esperado

Después de completar estos pasos:
- ✅ El Panel del Vendedor debería mostrar todos los datos
- ✅ El Dashboard Ejecutivo debería funcionar
- ✅ Todas las vistas deberían cargar correctamente
- ✅ No deberías ver más errores de conexión

---

**¿Necesitas ayuda?** Abre la consola del navegador (F12) y comparte los mensajes que ves allí.
