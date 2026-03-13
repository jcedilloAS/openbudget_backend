# OpenBudget Backend API

Backend API para OpenBudget usando FastAPI con mejores prácticas.

## Características

- ⚡ FastAPI - Framework moderno y rápido
- 🗃️ SQLAlchemy - ORM potente y flexible
- 🔄 Alembic - Migraciones de base de datos
- ✅ Pydantic - Validación de datos
- 🏗️ Arquitectura limpia con separación de capas
- 📝 Documentación automática (Swagger/ReDoc)

## Estructura del Proyecto

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── endpoints/
│   │       └── router.py
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── crud/
│   ├── models/
│   ├── schemas/
│   └── main.py
├── alembic/
├── .env.example
├── requirements.txt
└── README.md
```

## Instalación

### Opción 1: Con Docker (Recomendado) 🐳

1. **Desarrollo:**
```bash
# Iniciar todos los servicios (API + PostgreSQL + pgAdmin)
make up

# O manualmente
docker-compose up -d
```

La API estará disponible en:
- **API**: http://localhost:8000
- **Documentación Swagger**: http://localhost:8000/docs
- **pgAdmin**: http://localhost:5050 (admin@openbudget.com / admin)

2. **Producción:**
```bash
# Configurar variables de entorno
cp .env.prod.example .env.prod
# Editar .env.prod con valores de producción

# Iniciar servicios de producción
make up-prod

# O manualmente
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Opción 2: Instalación Local

1. Crear entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

3. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus credenciales
```

4. Crear base de datos y ejecutar migraciones:
```bash
alembic upgrade head
```

5. Ejecutar el servidor:
```bash
uvicorn app.main:app --reload
```

La API estará disponible en: http://localhost:8000

## Documentación

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

### Accounts

- `GET /api/v1/accounts/` - Listar todas las cuentas
- `GET /api/v1/accounts/{id}` - Obtener cuenta por ID
- `POST /api/v1/accounts/` - Crear nueva cuenta
- `PUT /api/v1/accounts/{id}` - Actualizar cuenta
- `DELETE /api/v1/accounts/{id}` - Eliminar cuenta

## Desarrollo

### Crear nueva migración
```bash
alembic revision --autogenerate -m "description"
```

### Aplicar migraciones
```bash
alembic upgrade head
```

### Revertir migración
```bash
alembic downgrade -1
```
