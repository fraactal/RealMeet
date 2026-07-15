# Criterios de aceptacion del Modulo 9

| ID | Criterio | Estado | Evidencia |
| --- | --- | --- | --- |
| AC-M9-001 | La aplicacion diferencia desarrollo, staging y produccion mediante configuracion. | aprobado | `APP_ENV`, `DEBUG`, `ENABLE_DOCS`, `ENABLE_DEMO_SEED`. |
| AC-M9-002 | Staging rechaza secretos placeholder o inseguros. | aprobado | Tests de settings. |
| AC-M9-003 | CORS admite origenes explicitos y restringidos. | aprobado | Settings y validacion runtime. |
| AC-M9-004 | No se utiliza wildcard inseguro con credenciales. | aprobado | Test de settings. |
| AC-M9-005 | Backend incluye headers de seguridad basicos. | aprobado | Middleware y runtime headers. |
| AC-M9-006 | Login tiene rate limiting configurable. | aprobado | Middleware y test. |
| AC-M9-007 | Exceso de solicitudes devuelve `429`. | aprobado | Test/runtime acotado. |
| AC-M9-008 | Swagger puede habilitarse o deshabilitarse por entorno. | aprobado | `ENABLE_DOCS`; runtime dev docs 200. |
| AC-M9-009 | Logs no exponen tokens ni secretos. | aprobado | Revision estatica/logs. |
| AC-M9-010 | Usuarios demo pueden deshabilitarse fuera de desarrollo. | aprobado | `ENABLE_DEMO_SEED`. |
| AC-M9-011 | Docker Compose continua funcionando. | aprobado | Servicios healthy. |
| AC-M9-012 | Dockerfiles no requieren privilegios innecesarios cuando es viable. | aprobado | Usuarios no root; volumenes nombrados para `node_modules` y `dist`. |
| AC-M9-013 | Existe documentacion de backup. | implementado | README/checklist. |
| AC-M9-014 | Existe documentacion de restauracion. | implementado | README/checklist. |
| AC-M9-015 | Archivos de secretos permanecen ignorados. | implementado | `.gitignore`, `.dockerignore`. |
| AC-M9-016 | Dependencias vulnerables estan documentadas. | aprobado | `npm audit`: 5 vulnerabilidades. |
| AC-M9-017 | No se ejecuta actualizacion forzada de npm. | aprobado | No se ejecuto `npm audit fix --force`. |
| AC-M9-018 | `/health` y `/ready` continuan funcionando. | aprobado | HTTP 200. |
| AC-M9-019 | Pruebas backend pasan. | aprobado | `52 passed, 2 warnings`. |
| AC-M9-020 | Frontend compila. | aprobado con observacion | Primer intento fallo por carrera/permisos previos; build final OK. |
| AC-M9-021 | Trazabilidad actualizada. | implementado | Matriz. |
| AC-M9-022 | Existe registro de riesgos residuales. | implementado | `security-risk-register.md`. |
| AC-M9-023 | Existe un unico commit final. | aprobado al cierre | Git final. |
| AC-M9-024 | No se realizo despliegue. | aprobado | Confirmacion final. |
| AC-M9-025 | No se implementaron funciones clinicas o comerciales nuevas. | implementado | Solo hardening tecnico. |
