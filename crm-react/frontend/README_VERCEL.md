# Guía de Despliegue en Vercel

Este proyecto está configurado para desplegarse en Vercel.

## Configuración

### Archivos de Configuración

1. **vercel.json**: Configuración de Vercel para el proyecto Vite
   - Framework: Vite
   - Output Directory: `dist`
   - Rewrites: Configurado para SPA (Single Page Application)

2. **package.json**: Ya incluye los scripts necesarios:
   - `npm run build`: Construye la aplicación para producción
   - `npm run dev`: Inicia el servidor de desarrollo

## Pasos para Desplegar en Vercel

### Opción 1: Desde la CLI de Vercel

1. Instala Vercel CLI globalmente:
```bash
npm i -g vercel
```

2. Navega a la carpeta del frontend:
```bash
cd crm-react/frontend
```

3. Inicia sesión en Vercel:
```bash
vercel login
```

4. Despliega el proyecto:
```bash
vercel
```

5. Para producción:
```bash
vercel --prod
```

### Opción 2: Desde el Dashboard de Vercel

1. Ve a [vercel.com](https://vercel.com) e inicia sesión
2. Haz clic en "Add New Project"
3. Conecta tu repositorio de GitHub/GitLab/Bitbucket
4. Configura el proyecto:
   - **Framework Preset**: Vite
   - **Root Directory**: `crm-react/frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`
5. Haz clic en "Deploy"

## Variables de Entorno

Si necesitas variables de entorno (por ejemplo, para la API del backend), agrégalas en:
- Dashboard de Vercel → Project Settings → Environment Variables

Ejemplo:
```
VITE_API_URL=https://tu-api.com
```

## Rutas Disponibles

- `/crm` - Componente CRM Corporativo (nuevo diseño)
- `/` - Dashboard principal (con Sidebar)
- `/panel-vendedor` - Panel del vendedor
- `/clientes` - Vista de clientes
- `/nueva-venta` - Nueva venta
- Y más rutas según la aplicación...

## Notas Importantes

- El proyecto usa React Router para navegación SPA
- Vercel detecta automáticamente proyectos Vite
- El archivo `vercel.json` configura los rewrites para que todas las rutas apunten a `index.html`
- Asegúrate de que el backend esté desplegado y accesible desde el frontend

## Solución de Problemas

### Error: Cannot find module
- Ejecuta `npm install` en la carpeta `crm-react/frontend`
- Verifica que todas las dependencias estén en `package.json`

### Error: Build failed
- Verifica que el comando `npm run build` funcione localmente
- Revisa los logs de build en Vercel para más detalles

### Rutas no funcionan en producción
- Verifica que `vercel.json` tenga la configuración de rewrites correcta
- Asegúrate de que todas las rutas estén configuradas en React Router
