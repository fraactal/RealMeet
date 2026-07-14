# Roles y permisos

## Admin

Puede ver informacion global, gestionar usuarios, profesionales, categorias, especialidades, reservas, metricas globales y configuraciones permitidas.

Estado observado en Modulo 0: existen dependencias de rol admin en rutas `/admin`, creacion y edicion de categorias/especialidades, y metricas admin. Requiere validacion manual de todos los flujos y endurecimiento de payloads administrativos.

Decision Modulo 2: no se implementa backoffice nuevo. Las rutas administrativas existentes deben conservar `require_roles(admin)` y no recibir permisos nuevos fuera de alcance.

Decision Modulo 3: el administrador puede crear, actualizar, activar y desactivar categorias y especialidades desde un backoffice minimo. No se implementa eliminacion destructiva ni backoffice completo.

## Professional

Puede editar su perfil, gestionar especialidades propias, gestionar disponibilidad, bloquear horarios, ver sus reservas, confirmar, cancelar y completar reservas, ver metricas propias y agregar notas privadas.

Estado observado en Modulo 0: existen endpoints de perfil, disponibilidad, metricas y transiciones profesionales. La exposicion de notas privadas detectada en `AppointmentRead` fue remediada en `REM-P0-001` mediante contratos de salida por contexto.

Decision Modulo 2: el perfil propio profesional se limita a campos base existentes. No debe permitir modificar categorias, especialidades, precio, publicacion, verificaciones, agenda ni disponibilidad desde el contrato base.

Decision Modulo 3: el profesional puede gestionar especialidades activas propias, campos publicos autorizados y visibilidad `is_public`. No puede gestionar disponibilidad, agenda, precios ni verificaciones clinicas.

## Client

Puede buscar profesionales, ver perfiles publicos, consultar disponibilidad, reservar, cancelar reservas futuras cuando aplique y ver su historial.

Estado observado en Modulo 0: existe registro cliente, login, busqueda publica, disponibilidad y creacion de reservas por rol client. No se observo restriccion temporal para cancelar solo reservas futuras.

Decision Modulo 2: el cliente debe contar con perfil propio seguro y no puede modificar rol, `is_active`, identificadores, hash ni campos administrativos.

Decision Modulo 3: el cliente consume el catalogo publico con los mismos contratos que un usuario anonimo; no obtiene datos privados adicionales de profesionales.

## Regla base

El frontend no es control de seguridad suficiente. Los permisos deben aplicarse en backend y, cuando corresponda, reforzarse con restricciones de base de datos.
