# 🔍 Verificar Build Logs en Vercel

## Paso 1: Ver los Build Logs

1. Ve a [vercel.com/dashboard](https://vercel.com/dashboard)
2. Abre tu proyecto **frontend**
3. Ve a **Deployments**
4. Haz clic en el deployment más reciente
5. Haz clic en la pestaña **Build Logs** o **View Build Logs**

## Paso 2: Buscar VITE_API_URL en los Logs

En los Build Logs, busca si aparece `VITE_API_URL` o `VITE_`.

**Si NO aparece:**
- La variable no se está aplicando durante el build
- Ve al Paso 3

**Si SÍ aparece:**
- La variable está siendo leída
- El problema puede ser otro

## Paso 3: Verificar Configuración del Proyecto

1. Ve a **Settings** → **General**
2. Verifica:
   - **Framework Preset:** Debe ser "Vite"
   - **Build Command:** Debe ser `npm run build` o estar vacío
   - **Output Directory:** Debe ser `dist`
   - **Install Command:** Debe ser `npm install` o estar vacío

## Paso 4: Despliegue Manual desde Terminal

Si los Build Logs no muestran la variable, prueba desplegar manualmente:

```bash
cd crm-react/frontend
vercel --prod
```

Esto debería usar las variables configuradas en Vercel.
