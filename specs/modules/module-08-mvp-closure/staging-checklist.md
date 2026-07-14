# Checklist de staging

## Configuracion

- [ ] Crear entorno staging separado.
- [ ] Definir secretos fuera del repositorio.
- [ ] Rotar `SECRET_KEY`.
- [ ] Restringir `CORS_ORIGINS` al dominio frontend real.
- [ ] Definir `VITE_API_URL` con URL backend staging.
- [ ] Definir URL backend publica.
- [ ] Configurar PostgreSQL staging.
- [ ] Definir `EMAIL_MODE` (`log` o `smtp`) segun objetivo.
- [ ] Configurar SMTP si se prueba correo real.
- [ ] Mantener `DEFAULT_MEETING_PROVIDER=mock` hasta spec de integracion real.
- [ ] Revisar nivel y destino de logs.

## Infraestructura

- [ ] Construir imagen backend.
- [ ] Construir imagen frontend.
- [ ] Configurar red entre servicios.
- [ ] Configurar volumen o servicio PostgreSQL persistente.
- [ ] Ejecutar migraciones `alembic upgrade head`.
- [ ] Tomar backup previo si se actualiza una base existente.
- [ ] Validar healthcheck backend.
- [ ] Validar readiness backend.
- [ ] Validar reinicio de servicios.
- [ ] Definir rollback de imagen y migracion.

## Seguridad

- [ ] Confirmar que `.env` y secretos no estan versionados.
- [ ] Deshabilitar, eliminar o rotar credenciales demo si staging es publico.
- [ ] Evaluar si Swagger queda expuesto.
- [ ] Restringir CORS.
- [ ] Usar JWT secret fuerte.
- [ ] Exigir contrasenas seguras.
- [ ] Configurar SMTP con credenciales seguras si aplica.
- [ ] Usar HTTPS antes de exponer usuarios externos.
- [ ] Validar usuarios inactivos.
- [ ] Revisar accesos admin.

## Validacion posterior al despliegue

- [ ] `GET /health`.
- [ ] `GET /ready`.
- [ ] Login cliente.
- [ ] Login profesional.
- [ ] Login admin.
- [ ] Catalogo publico.
- [ ] Disponibilidad publica.
- [ ] Creacion de reserva.
- [ ] Dashboard cliente.
- [ ] Dashboard profesional.
- [ ] Dashboard admin.
- [ ] Logs sin tracebacks.
- [ ] Logs sin secretos.

## No incluido

- No crea infraestructura cloud.
- No crea Terraform.
- No ejecuta despliegue.
