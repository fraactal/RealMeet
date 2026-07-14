# Modulo 0: Baseline SDD

## Contexto

RealMeet ya cuenta con una base de backend FastAPI, frontend React/Vite, Docker Compose, migracion inicial y seed demo. La adopcion SDD comienza sin reescribir codigo existente y sin implementar funcionalidad nueva.

## Problema

El estado real del MVP no estaba clasificado con una linea base trazable. El README describe funcionalidades, pero cada modulo requiere evidencia, estado, riesgos, deuda y controles minimos.

## Objetivo

Crear la base metodologica de Spec-Driven Development, documentar el estado real encontrado y proponer el orden correcto para continuar el MVP.

## Alcance

- Inspeccion estatica de backend, frontend, migraciones, seed, Docker, configuracion y documentacion.
- Creacion de estructura `specs/`.
- Specs retrospectivas iniciales dentro de `implementation-status.md`.
- Matriz de trazabilidad inicial.
- Backlog priorizado y roadmap sugerido.
- Controles minimos no destructivos.

## Exclusiones

- No implementar funcionalidades nuevas.
- No corregir bugs.
- No refactorizar.
- No instalar dependencias.
- No crear suites nuevas de pruebas.
- No ejecutar despliegues, commits, push ni comandos destructivos.

## Actores

- Equipo de producto.
- Administrador RealMeet.
- Profesional.
- Cliente o paciente.
- Desarrolladores que continuaran el MVP.

## Comportamiento esperado

Al finalizar este modulo, cualquier persona del equipo debe poder revisar que existe, que falta, que esta en riesgo y que modulo conviene abordar despues.

## Entregables

- `specs/README.md`
- `specs/product/*.md`
- `specs/modules/module-00-baseline/*.md`
- `specs/decisions/*.md`
- `specs/traceability/requirements-matrix.md`

## Restricciones

- Mantener monolito modular.
- No cambiar stack.
- No modificar contratos API.
- No crear pruebas nuevas.
- Documentar problemas sin corregirlos en este modulo.

## Supuestos

- El repositorio inspeccionado en `C:\Users\Jona\Documents\RealMeet` es la fuente real para este modulo.
- La ausencia de runtime local (`python`, `npm`, `pytest`) limita validaciones ejecutables.
- Docker Compose clasico (`docker-compose`) esta disponible, pero Docker emite advertencia de acceso a config de usuario.

## Riesgos principales

- `AppointmentRead` exponia `professional_private_notes`, incumpliendo privacidad para clientes. Este riesgo fue remediado posteriormente en `REM-P0-001`.
- La prevencion de doble reserva esta en servicio, pero no se observo restriccion transaccional en base de datos.
- La creacion de reservas no valida explicitamente que el bloque solicitado pertenezca a la disponibilidad calculada.
- Rutas frontend autenticadas no filtran por rol; backend debe seguir siendo la fuente de seguridad.
- `backend/.env.example` y `frontend/.env.example` son mencionados en README, pero no existen en el repositorio inspeccionado.

## Criterios de aceptacion

Ver `acceptance-criteria.md`.

## Controles minimos

Ver `validation-report.md`.

## Definicion de finalizacion

El Modulo 0 se considera finalizado cuando la documentacion SDD existe, no contiene archivos vacios, refleja hallazgos reales, registra validaciones ejecutadas/no ejecutadas y propone backlog y roadmap sin implementar el siguiente modulo.
