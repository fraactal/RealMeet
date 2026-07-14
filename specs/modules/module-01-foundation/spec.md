# Modulo 1: Fundacion tecnica y entorno reproducible

## Contexto

RealMeet ya cuenta con backend FastAPI, frontend React/Vite, PostgreSQL en Docker Compose, migracion inicial, seed demo, endpoints `/health` y `/ready`, y documentacion SDD del Modulo 0. La remediacion `REM-P0-001` fue aplicada y validada estaticamente, pero no pudo validarse en runtime por limitaciones del entorno local.

## Problema

El proyecto tiene una base tecnica implementada, pero varias capacidades permanecen `implemented-unverified` porque el entorno no se ha validado de forma reproducible. El Modulo 0 registro limitaciones de Docker Compose v2, Python, npm y pruebas locales en PATH. Tambien se detectaron brechas de documentacion y necesidad de estabilizar variables, arranque, migraciones, seed, health, readiness y logs.

## Objetivo

Dejar una fundacion reproducible y documentada para levantar RealMeet principalmente con contenedores, minimizando dependencias directas del host para el flujo normal de ejecucion.

## Alcance

- Documentacion SDD del Modulo 1.
- Inventario y documentacion de variables de entorno.
- `.env.example` raiz, backend y frontend.
- `.gitignore`.
- Docker Compose y Dockerfiles, si requieren ajustes acotados.
- Espera controlada de PostgreSQL.
- Migraciones integradas al flujo de arranque.
- Seed idempotente y logs seguros.
- `/health` y `/ready`.
- Logs de arranque sin secretos.
- README con flujo reproducible local.
- Controles minimos posibles y registro de limitaciones.
- Validacion runtime de `REM-P0-001` si el stack queda operativo.

## Exclusiones

- No implementar funcionalidades de negocio.
- No modificar disponibilidad, reservas, metricas, backoffice, pagos, IA ni integraciones externas.
- No crear migraciones si no hay cambios reales de esquema.
- No eliminar volumenes, contenedores, datos ni archivos del usuario.
- No crear suites completas de API, E2E, carga, estres o rendimiento.
- No hacer commit ni push.

## Actores

- Desarrollador local.
- Equipo tecnico que continuara modulos funcionales.
- Operador local que necesita diagnosticar arranque.

## Comportamiento esperado

Un desarrollador debe poder preparar variables, levantar el stack con Docker Compose, validar salud/readiness, acceder al frontend, iniciar sesion con usuarios demo y repetir el flujo sin instrucciones ocultas.

## Supuestos

- Docker Compose v2 es la ruta recomendada; Compose v1 se documenta como alternativa si esta disponible.
- El entorno host de Codex puede seguir sin Python/npm, por lo que el flujo principal debe depender de contenedores.
- No se deben usar comandos destructivos como `down -v` o prune.

## Riesgos

- El repositorio completo aparece sin seguimiento en Git, lo que dificulta distinguir cambios previos de cambios del modulo.
- La validacion runtime puede quedar bloqueada si Docker no puede ejecutar contenedores o si Compose v2 no esta instalado.
- El seed inicial era idempotente solo por existencia del admin demo; esto puede dejar datos demo incompletos si hay un estado parcial.

## Definicion de finalizacion

El modulo termina cuando la fundacion queda documentada, los ejemplos de entorno y README estan alineados, el arranque y seed son mas diagnosticables, se ejecutan los controles posibles y se actualiza la trazabilidad. Si runtime no puede ejecutarse, el estado final sera `implemented-unverified` con comandos pendientes claros.
