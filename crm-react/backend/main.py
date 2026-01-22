from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os

# Agregar el directorio raíz del proyecto original al path
# Esto permite importar los módulos existentes
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app.api import dashboard, clientes, ventas, comisiones

app = FastAPI(
    title="CRM API",
    description="API para el sistema CRM - Reutiliza toda la lógica Python existente",
    version="1.0.0"
)

# CORS - Permitir llamadas desde el frontend React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(clientes.router, prefix="/api/clientes", tags=["clientes"])
app.include_router(ventas.router, prefix="/api/ventas", tags=["ventas"])
app.include_router(comisiones.router, prefix="/api/comisiones", tags=["comisiones"])

@app.get("/")
def root():
    return {"message": "CRM API - Sistema de Gestión", "version": "1.0.0"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
