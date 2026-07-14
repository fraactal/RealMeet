# Backend Rules — RealMeet

## Configuración

- Todas las variables deben estar declaradas en `.env.example`.
- No asumir que variables tipo lista llegan en formato JSON válido.
- Para variables de lista, aceptar:
  1. JSON: `["http://localhost:5173"]`
  2. CSV: `http://localhost:5173,http://127.0.0.1:5173`
- Validar configuración al inicio y fallar con mensajes claros.
- Nunca imprimir passwords, JWT secrets, URLs completas con credenciales ni tokens.

## Inicio de servicios

- El backend no debe ejecutar migraciones hasta que PostgreSQL esté disponible.
- Docker Compose debe usar healthchecks para DB y backend.
- Exponer `GET /health` y `GET /ready`.
- `/health` indica que el proceso FastAPI está vivo.
- `/ready` valida conectividad mínima con PostgreSQL.

## Logging

- Usar logging estructurado.
- Registrar:
  - inicio de aplicación;
  - ambiente;
  - conexión a base de datos;
  - migraciones;
  - seed;
  - errores inesperados;
  - request id cuando sea posible.
- No ocultar excepciones.
- Errores de autenticación deben registrarse sin password ni token.

## API Errors

- Usar respuestas consistentes:
  - 401: credenciales inválidas o token inválido;
  - 403: permiso insuficiente;
  - 422: validación;
  - 500: error no controlado;
  - 503: dependencia no disponible.
- Incluir un código de error estable para frontend.
- No devolver tracebacks en producción.

## Pruebas mínimas obligatorias

Antes de considerar una tarea backend terminada:
- probar carga de Settings;
- probar /health;
- probar /ready;
- probar login exitoso y fallido;
- probar CORS desde frontend local;
- ejecutar migraciones en una base vacía.