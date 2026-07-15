# Reporte de validacion 11.2

Estado: aprobado.

## Validaciones ejecutadas

| Validacion | Resultado |
| --- | --- |
| `docker-compose exec -T backend alembic upgrade head` | aprobado |
| `docker-compose exec -T backend pytest -q tests/test_integration_domain.py tests/test_integration_service_api.py` | `28 passed, 1 warning in 7.80s` |
| `docker-compose exec -T backend alembic current` | `20260715_0004 (head)` |
| `docker-compose ps` | db, backend y frontend `Up` y `healthy` |
| `/health` | HTTP 200, `{"status":"ok","environment":"docker"}` |
| `/ready` | HTTP 200, `{"status":"ready","database":"ok","configuration":"ok"}` |

## Validacion manual API

Con admin demo:

- Listado admin respondio OK.
- Creacion de `Test 11.2 Manual Mock` respondio OK con `enabled=false`.
- Validacion devolvio `mock_configuration_valid`.
- Habilitacion dejo `enabled=true`.
- Health check devolvio `mock_health_ok`.
- Test devolvio `mock_test_ok`.
- Repeticion con misma idempotency key devolvio `skipped=true`.
- Listado de ejecuciones mostro 2 ejecuciones.
- Deshabilitacion dejo `enabled=false`.
- Intento de habilitar `google_meet` devolvio 409.

Autorizacion runtime:

- Sin token: 401.
- Cliente demo: 403.
- Profesional demo: 403.

Datos manuales:

- Se crearon integraciones manuales IDs 20 y 21.
- Se limpiaron integraciones 20 y 21, sus ejecuciones y auditorias asociadas con SQL especifico.

## Observaciones

- Se reinicio solo el servicio backend para que el proceso cargara las rutas nuevas. No se reconstruyeron imagenes ni se tocaron volumenes.
- No se ejecuto build frontend porque 11.2 no modifica frontend.
- No se agrego migracion nueva en 11.2.

## Resultado final

Submodulo 11.2 listo para revision. La API backend queda preparada para el backoffice de 11.3.
