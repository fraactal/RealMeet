# Criterios de aceptacion 11.1

| ID | Criterio | Estado |
| --- | --- | --- |
| AC-11.1-001 | Se definen tipos de integracion estables. | aprobado |
| AC-11.1-002 | Se definen proveedores conocidos sin declararlos implementados. | aprobado |
| AC-11.1-003 | `Integration` persiste configuracion no secreta y comienza deshabilitada. | aprobado |
| AC-11.1-004 | `IntegrationExecution` persiste ejecuciones con intento e idempotencia. | aprobado |
| AC-11.1-005 | `UNIQUE (integration_id, idempotency_key)` impide duplicados. | aprobado |
| AC-11.1-006 | Configuracion y metadata rechazan claves sensibles recursivamente. | aprobado |
| AC-11.1-007 | `secret_reference` acepta solo formato de referencia segura. | aprobado |
| AC-11.1-008 | Schemas rechazan campos protegidos y mass assignment. | aprobado |
| AC-11.1-009 | Repositorios permiten crear, obtener, listar, actualizar y consultar por idempotencia. | aprobado |
| AC-11.1-010 | Migracion Alembic es reversible y no modifica migraciones historicas. | aprobado |
| AC-11.1-011 | Pruebas acotadas del submodulo pasan. | aprobado |
| AC-11.1-012 | No se modifica frontend, seed, reservas, API ni proveedores reales. | aprobado |
