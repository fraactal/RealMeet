# Alcance MVP

## Incluido

- Autenticacion JWT.
- Roles `admin`, `professional` y `client`.
- Registro base de usuarios y registro de clientes.
- Perfil profesional.
- Categorias y especialidades.
- Relacion profesional-especialidad.
- Catalogo publico con filtros, paginacion y perfil profesional seguro.
- Disponibilidad semanal.
- Bloqueos manuales.
- Calculo publico de slots disponibles por fecha o rango corto.
- Busqueda publica de profesionales.
- Consulta de disponibilidad.
- Creacion y consulta de reservas.
- Historial de cambios de reservas.
- Estados `pending`, `confirmed`, `cancelled`, `completed`, `no_show`.
- Dashboards basicos por rol.
- Backoffice administrativo minimo de usuarios, profesionales y reservas.
- Metricas basicas.
- Backoffice administrativo minimo de catalogo.
- Servicio de correo desacoplado.
- `MockMeetingProvider` con URL local de desarrollo.
- Notificaciones basicas de reserva creada, confirmada y cancelada.
- Auditoria administrativa basica para cambios administrativos relevantes.
- Cierre integrado con checklist de staging y reporte de readiness.
- Hardening tecnico inicial para staging: settings por entorno, headers basicos, rate limiting local, Swagger configurable y seed demo configurable.

## Excluido por ahora

- Google Meet real.
- Zoom real.
- WhatsApp real.
- Pagos.
- Suscripciones.
- Facturacion.
- Firma digital.
- Inteligencia artificial.
- Ficha clinica electronica.
- Receta medica.
- Telemedicina certificada.
- Integraciones con FONASA, aseguradoras o interoperabilidad clinica.
- Auditorias regulatorias avanzadas.
- Produccion clinica.
- Pentesting, pruebas de carga, SAST/SCA completo, backups y observabilidad productiva.
- Rate limiting distribuido, WAF, SIEM, Redis obligatorio, cookies HttpOnly y CSRF completo.

Estas capacidades requieren specs futuras.
