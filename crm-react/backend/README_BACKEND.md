# Backend CRM - Guía de Inicio

## Inicio Rápido

### 1. Instalar dependencias
```bash
cd crm-react/backend
pip install -r requirements.txt
```

### 2. Configurar variables de entorno
Copia `crm-react/backend/env.example` a un archivo `.env` en `crm-react/backend/` (o configura estas variables en tu entorno) con:
```
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_key_de_supabase
```

### 3. Iniciar el servidor
```bash
python main.py
```

O usando uvicorn directamente:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

El backend estará disponible en: `http://localhost:8000`

## Endpoints disponibles

- `GET /` - Información de la API
- `GET /api/health` - Health check
- `GET /api/dashboard/metrics` - Métricas del dashboard
- `GET /api/clientes` - Lista de clientes
- `GET /api/clientes/{id}` - Cliente por ID
- `GET /api/comisiones` - Comisiones

## Para desarrollo local con frontend

1. Inicia el backend en una terminal
2. En otra terminal, inicia el frontend:
   ```bash
   cd crm-react/frontend
   npm run dev
   ```
3. El frontend se conectará automáticamente a `http://localhost:8000/api`
