# Modulo 2: Autenticacion, autorizacion y perfiles base

## Contexto

RealMeet ya cuenta con una fundacion operativa validada en Modulo 1: backend FastAPI, frontend React/Vite, PostgreSQL, migraciones, seed demo, `/health`, `/ready` y login demo. La remediacion `REM-P0-001` separo contratos de reservas para evitar exponer notas privadas del profesional.

Este modulo se limita a robustecer autenticacion, autorizacion y perfiles propios base para los roles `admin`, `professional` y `client`.

## Problema

La inspeccion inicial confirma riesgos acotados:

- `AuthService.login` no rechaza usuarios inactivos.
- `get_current_user` rechaza usuario inexistente o inactivo, pero no controla de forma robusta un `sub` no numerico.
- `/users/me` reutiliza `UserUpdate`, permitiendo que un usuario modifique `is_active`.
- El perfil profesional propio reutiliza contratos con campos de modulos posteriores: `category_id`, `specialty_ids`, `price` e `is_public`.
- No existe un perfil propio dedicado para cliente.
- El frontend protege rutas principalmente por presencia de token local, sin restaurar sesion contra `/auth/me` ni aplicar guardas de rol en rutas.

## Objetivo

Dejar login, validacion JWT, permisos por rol y perfiles propios base funcionando de manera segura, con contratos explicitos y controles minimos reproducibles.

## Alcance

- Login con usuario activo.
- Rechazo de usuario inactivo en login y en acceso con token previo.
- Validacion de firma, expiracion y estructura minima del JWT.
- `/auth/me` con schema seguro.
- Dependencias de autenticacion y rol consistentes.
- Perfil propio de cliente con lectura y actualizacion segura.
- Perfil propio de profesional con lectura y actualizacion segura de campos base.
- Frontend con restauracion de sesion, limpieza ante `401`, guardas por rol y logout.
- Pruebas pequenas y validacion runtime cuando el entorno lo permita.
- Documentacion SDD, trazabilidad y commits por fase.

## Exclusiones

- Registro publico nuevo o ampliado.
- Recuperacion o cambio de password.
- MFA, OAuth, login social o Google Auth.
- Categorias, especialidades, disponibilidad, agenda, slots y reservas nuevas.
- Metricas nuevas o backoffice completo.
- Pagos, suscripciones, facturacion, Google Meet, Zoom, WhatsApp e IA.
- Datos clinicos, ficha clinica o cumplimiento regulatorio clinico.
- Hardening transversal completo, rate limiting, headers de seguridad globales o auditoria de infraestructura.
- Migraciones de base de datos salvo cambio real de esquema. No se espera cambio de esquema.

## Actores

- `admin`: usuario autenticado con acceso administrativo existente.
- `professional`: usuario autenticado que administra solo su perfil profesional propio.
- `client`: usuario autenticado que administra solo su perfil cliente propio.
- Usuario anonimo: solo puede acceder a endpoints publicos.

## Decision de alcance sobre registro

No se implementa registro publico en este modulo. Los endpoints existentes se documentan como comportamiento heredado y no se expanden. La creacion de usuarios queda para seed local, administracion futura o modulos posteriores.

## Comportamiento esperado

- Credenciales validas de un usuario activo emiten JWT.
- Credenciales invalidas o usuario inactivo responden `401` sin revelar si fallo email, password o estado.
- Token ausente, invalido, vencido, sin `sub` valido o asociado a usuario inactivo responde `401`.
- Usuario autenticado sin rol permitido responde `403`.
- `/auth/me` no expone hash, password, token, secretos ni datos internos innecesarios.
- Los perfiles propios no permiten modificar `role`, `is_active`, identificadores, hashes ni campos administrativos.
- El perfil profesional base no permite actualizar `category_id`, `specialty_ids`, `price` ni `is_public`.
- El frontend complementa la seguridad del backend con guardas de sesion y rol.

## Contratos

Contratos esperados:

- `LoginRequest`.
- `TokenResponse`.
- Usuario actual seguro.
- Perfil cliente lectura.
- Perfil cliente actualizacion.
- Perfil profesional propio lectura.
- Perfil profesional propio actualizacion.
- Contratos administrativos existentes, sin ampliar permisos en este modulo.

## Seguridad y riesgos

- Datos y activos protegidos: credenciales, JWT, hash de password, roles, estado `is_active`, perfiles propios, campos administrativos y datos privados de usuario.
- Roles involucrados: `admin`, `professional`, `client` y anonimo.
- Amenazas identificadas: acceso con usuario inactivo, token malformado, escalamiento por update de `is_active`, acceso visual por rol incorrecto y modificacion de campos fuera de modulo.
- Controles previstos: schemas separados, validacion JWT robusta, dependencias de rol, servicios para perfiles propios, interceptores frontend y pruebas minimas.
- Riesgos aceptados temporalmente: token en `localStorage` por compatibilidad con la base actual; migracion futura a cookies seguras queda como deuda.
- Deuda tecnica prevista: hardening transversal posterior, revision completa de registro publico y vulnerabilidades npm no relacionadas.

## Fases

1. Baseline y contratos de autenticacion.
2. JWT, usuario activo y errores.
3. Autorizacion por rol.
4. Perfil base de cliente.
5. Perfil base de profesional.
6. Sesion y proteccion frontend.
7. Validacion integrada y cierre.

## Definition of Done

El modulo termina cuando los criterios `AC-M2-001` a `AC-M2-029` esten cumplidos o documentados con una razon no bloqueante, los controles minimos pasen, la matriz de trazabilidad este actualizada, cada fase tenga commit independiente, no se haya hecho push y no se haya avanzado al Modulo 3.
