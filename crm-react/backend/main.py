from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
from dotenv import load_dotenv

# Agregar el directorio actual (backend) al path para que Python encuentre 'app'
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Agregar el directorio raíz del proyecto original al path
# Esto permite importar los módulos existentes (database, config, etc.)
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
# Importante: NO ponerlo en sys.path[0] porque en la raíz existe un `app.py`
# que colisiona con el paquete `app/` del backend (FastAPI).
sys.path.append(project_root)

from app.api import dashboard, clientes, ventas, comisiones, analytics, devoluciones, catalogo, presupuestos
from config.settings import AppConfig

# Cargar variables de entorno (busca .env si existe; en este repo se recomienda usar env.example como plantilla)
load_dotenv()

app = FastAPI(
    title="CRM API",
    description="API para el sistema CRM - Reutiliza toda la lógica Python existente",
    version="1.0.0"
)

# CORS - Permitir llamadas desde el frontend React
# Detectar si estamos en producción (Vercel)
is_production = os.getenv("VERCEL") == "1" or os.getenv("ENVIRONMENT") == "production"

# Obtener URL del frontend desde variable de entorno o usar valores por defecto
frontend_urls_str = os.getenv("FRONTEND_URLS", "http://localhost:3000,http://localhost:5173")
frontend_urls = [url.strip() for url in frontend_urls_str.split(",") if url.strip()]

# Agregar URLs de Vercel automáticamente si estamos en Vercel
vercel_url = os.getenv("VERCEL_URL")
if vercel_url:
    frontend_urls.append(f"https://{vercel_url}")

# Agregar URL específica del frontend si está configurada
frontend_prod_url = os.getenv("FRONTEND_PROD_URL")
if frontend_prod_url:
    frontend_urls.append(frontend_prod_url.strip())

# En desarrollo, permitir todos los orígenes para evitar problemas de CORS
# En producción, usar solo los orígenes específicos + permitir todos temporalmente para facilitar despliegue
if is_production:
    # En producción, permitir los orígenes específicos + wildcard para facilitar despliegue inicial
    # TODO: Restringir a solo los orígenes específicos una vez que tengas la URL definitiva
    allow_origins = ["*"]  # Cambiar a frontend_urls cuando tengas la URL definitiva
else:
    allow_origins = ["*"]

print(f"🌐 CORS configurado. Modo: {'PRODUCCIÓN' if is_production else 'DESARROLLO'}")
print(f"🌐 Orígenes permitidos: {allow_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Incluir routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["clientes"])
app.include_router(ventas.router, prefix="/api/ventas", tags=["ventas"])
app.include_router(comisiones.router, prefix="/api/comisiones", tags=["comisiones"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(devoluciones.router, prefix="/api/devoluciones", tags=["devoluciones"])
app.include_router(catalogo.router, prefix="/api/catalogo", tags=["catalogo"])
app.include_router(presupuestos.router, prefix="/api/presupuestos", tags=["presupuestos"])

@app.get("/")
def root():
    return {"message": "CRM API - Sistema de Gestión", "version": "1.0.0"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/health/db")
def health_check_db():
    """
    Verifica conexión a Supabase con una consulta mínima.
    Útil para diagnosticar si el problema es de variables de entorno / credenciales / red.
    """
    env_status = AppConfig.validate_environment()
    if not env_status["valid"]:
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Faltan variables de entorno para conectar a Supabase.",
                "errors": env_status["errors"],
            },
        )

    try:
        from supabase import create_client

        supabase = create_client(AppConfig.SUPABASE_URL, AppConfig.SUPABASE_KEY)
        # Consulta mínima: 1 fila de la tabla comisiones (si no existe, igual sirve para ver el tipo de error)
        res = supabase.table("comisiones").select("id").limit(1).execute()
        return {"status": "ok", "supabase": "connected", "sample_rows": len(res.data or [])}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "supabase": "not_connected", "detail": str(e)},
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
