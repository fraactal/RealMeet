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
- Metricas basicas.
- Backoffice administrativo minimo.
- Servicio de correo desacoplado.
- `MockMeetingProvider`.

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

Estas capacidades requieren specs futuras.
