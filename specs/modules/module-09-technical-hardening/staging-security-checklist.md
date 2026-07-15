# Checklist tecnico seguro para staging

## Antes de desplegar

- [ ] Definir `APP_ENV=staging`.
- [ ] Definir `DEBUG=false`.
- [ ] Rotar `SECRET_KEY` con valor fuerte de 32+ caracteres.
- [ ] Definir `ENABLE_DEMO_SEED=false` salvo staging privado de prueba.
- [ ] Desactivar o rotar credenciales demo si la instancia es publica.
- [ ] Definir `CORS_ORIGINS` con dominios explicitos, sin wildcard.
- [ ] Definir `ENABLE_DOCS=false` si staging sera accesible publicamente.
- [ ] Mantener `RATE_LIMIT_ENABLED=true`.
- [ ] Ajustar `RATE_LIMIT_WINDOW_SECONDS` y `RATE_LIMIT_MAX_REQUESTS`.
- [ ] Usar `EMAIL_MODE=log` si SMTP real no esta validado.
- [ ] No versionar `.env`, dumps, backups, certificados ni claves.

## Backup

- [ ] Ejecutar backup con `pg_dump` antes de migraciones.
- [ ] Guardar backup fuera del repositorio.
- [ ] Validar que el archivo no quede en Git.
- [ ] Probar `pg_restore --list` o restauracion en ambiente aislado.

## Runtime

- [ ] Validar `/health`.
- [ ] Validar `/ready`.
- [ ] Verificar headers de seguridad.
- [ ] Verificar CORS permitido.
- [ ] Verificar CORS no permitido.
- [ ] Verificar `429` de login con limite bajo en entorno controlado.
- [ ] Revisar logs sin tokens, secretos, passwords ni headers Authorization.
- [ ] Confirmar Docker Compose healthy.

## Diferido para produccion

- [ ] HTTPS y dominio.
- [ ] Cookies HttpOnly/SameSite y CSRF.
- [ ] Rate limiter distribuido.
- [ ] Backups programados y restore drill.
- [ ] SAST/SCA/Trivy/secret scanning.
- [ ] Observabilidad, alertas y monitoreo.
- [ ] Pentesting.
