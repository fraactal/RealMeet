# Diseno tecnico del Modulo 2

## Flujo de autenticacion

```text
POST /api/v1/auth/login
-> AuthService busca usuario por email normalizado
-> valida existencia, password e is_active con respuesta 401 generica
-> emite JWT HS256 con sub y exp
-> frontend guarda token con mecanismo actual
```

`GET /api/v1/auth/me` usa `get_current_user`, valida token, carga usuario desde DB, rechaza usuario inexistente o inactivo y serializa con contrato seguro.

## JWT

Se mantiene el contrato compatible actual:

- `sub`: id de usuario como string.
- `exp`: expiracion.
- algoritmo: `HS256`.

No se agregan datos de rol, password, hash, notas, secretos ni informacion clinica al token. La autorizacion se decide consultando el usuario actual en DB.

## Errores

- `401`: token ausente, invalido, vencido, payload sin `sub` valido, usuario inexistente, usuario inactivo o credenciales invalidas.
- `403`: usuario autenticado sin rol permitido.
- `404`: se conserva donde el patron actual evita revelar recursos inexistentes o ajenos.

## Autorizacion backend

Se conserva `get_current_user` como dependencia de autenticacion y `require_roles` como dependencia de autorizacion. Si se agregan helpers de rol, deben envolver ese mecanismo sin duplicar logica.

Rutas observadas:

| Endpoint | Rol actual | Observacion M2 |
| --- | --- | --- |
| `POST /auth/login` | publico | Debe rechazar usuario inactivo. |
| `GET /auth/me` | autenticado | Debe usar contrato seguro. |
| `GET /users/me` | autenticado | Debe usar contrato seguro. |
| `PATCH /users/me` | autenticado | Usa `UserSelfUpdate`; impide `is_active` y campos admin. |
| `GET /users/me/profile` | client | Perfil cliente propio. |
| `PATCH /users/me/profile` | client | Actualizacion segura de perfil cliente propio. |
| `/admin/*` | admin | Router protegido por `require_roles(admin)`. |
| `POST /professionals/profile` | professional | Usa contrato propio restringido del Modulo 2. |
| `GET /professionals/me/profile` | professional | Usa contrato propio restringido del Modulo 2. |
| `PATCH /professionals/me/profile` | professional | Usa contrato propio restringido del Modulo 2. |
| `/professional/metrics` | professional | Mantener proteccion existente. |
| `/admin/metrics` | admin | Mantener proteccion existente. |
| `/appointments` protegidos | client/professional/authenticated segun accion | No ampliar reservas en M2. |

## Perfil cliente

Se usaran campos existentes:

- Datos de usuario propios: `first_name`, `last_name`, `phone`.
- Datos de `ClientProfile`: `birth_date`, `notes`.

No se agregan datos clinicos ni nuevas columnas. La actualizacion se realiza en `ProfileService` y no permite `role`, `is_active`, identificadores, hash ni campos de otros usuarios.

## Perfil profesional

Se usan campos base existentes:

- Datos de usuario propios: `first_name`, `last_name`, `phone`.
- Datos de `ProfessionalProfile`: `title`, `bio`, `years_experience`, `consultation_mode`, `session_duration_minutes`, `address`, `city`, `country`.

Quedan fuera del contrato propio base:

- `category_id`.
- `specialty_ids`.
- `price`.
- `is_public`.
- `is_verified`.
- `professional_license`.
- disponibilidad y agenda.

Los endpoints propios `POST /professionals/profile`, `GET /professionals/me/profile` y `PATCH /professionals/me/profile` usan `ProfessionalSelfProfileRead` y `ProfessionalSelfProfileUpdate`. Los endpoints publicos de profesionales no se amplian en este modulo.

## Frontend

El token permanece en `localStorage` por compatibilidad con la base actual. Controles M2:

- Restaurar sesion consultando `/auth/me` cuando exista token local y no haya usuario cargado.
- Limpiar sesion ante `401`.
- Mostrar estado de carga inicial sin loop.
- Aplicar guardas de rol en rutas.
- Mantener logout limpiando token y usuario.

Riesgo aceptado temporalmente: `localStorage` es vulnerable a XSS; migracion futura a cookies HttpOnly/SameSite queda como deuda de hardening.

## Pruebas y validacion

Agregar pruebas pequenas de seguridad donde no requieran infraestructura nueva. Validar con Docker Compose v1:

- tests backend;
- build frontend;
- `/health`;
- `/ready`;
- login admin/professional/client;
- login invalido;
- token invalido;
- acceso permitido y denegado por rol;
- perfiles propios;
- intento de modificar campos protegidos.
