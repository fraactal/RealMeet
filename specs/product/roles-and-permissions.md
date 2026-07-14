# Roles y permisos

## Admin

Puede ver informacion global, gestionar usuarios, profesionales, categorias, especialidades, reservas, metricas globales y configuraciones permitidas.

Estado observado en Modulo 0: existen dependencias de rol admin en rutas `/admin`, creacion y edicion de categorias/especialidades, y metricas admin. Requiere validacion manual de todos los flujos y endurecimiento de payloads administrativos.

## Professional

Puede editar su perfil, gestionar especialidades propias, gestionar disponibilidad, bloquear horarios, ver sus reservas, confirmar, cancelar y completar reservas, ver metricas propias y agregar notas privadas.

Estado observado en Modulo 0: existen endpoints de perfil, disponibilidad, metricas y transiciones profesionales. La exposicion de notas privadas detectada en `AppointmentRead` fue remediada en `REM-P0-001` mediante contratos de salida por contexto.

## Client

Puede buscar profesionales, ver perfiles publicos, consultar disponibilidad, reservar, cancelar reservas futuras cuando aplique y ver su historial.

Estado observado en Modulo 0: existe registro cliente, login, busqueda publica, disponibilidad y creacion de reservas por rol client. No se observo restriccion temporal para cancelar solo reservas futuras.

## Regla base

El frontend no es control de seguridad suficiente. Los permisos deben aplicarse en backend y, cuando corresponda, reforzarse con restricciones de base de datos.
