# Spec-Driven Development en RealMeet

Este directorio define la base de Spec-Driven Development (SDD) para RealMeet. Su objetivo es que cada cambio funcional tenga contexto, alcance, criterios de aceptacion, impacto tecnico, validacion y trazabilidad antes de implementarse.

## Proposito

Las specs conectan requisitos de producto con implementacion, validacion y deuda tecnica. No reemplazan al codigo ni al README; documentan que se espera, que existe, que falta y que riesgo queda.

## Ciclo de vida de una spec

1. Identificar problema funcional.
2. Definir alcance y exclusiones.
3. Identificar actores y reglas de negocio.
4. Definir criterios de aceptacion.
5. Evaluar impacto en backend, frontend, base de datos, API, Docker y documentacion.
6. Registrar supuestos, riesgos y dependencias.
7. Dividir implementacion en pasos pequenos.
8. Implementar solo cuando la spec este lista.
9. Ejecutar controles minimos.
10. Actualizar matriz de trazabilidad, estado y deuda tecnica.

## Estados permitidos

- `verified`: implementado y comprobado mediante control documentado.
- `implemented-unverified`: implementado, pero sin validacion suficiente en este modulo.
- `partial`: flujo o modulo implementado parcialmente.
- `designed`: estructura o abstraccion preparada, pero flujo incompleto.
- `not-implemented`: no existe implementacion suficiente.
- `blocked`: no se pudo validar o completar por dependencia, entorno o decision pendiente.
- `out-of-scope`: fuera del alcance del MVP actual o de la fase.

## Convencion de identificadores

Usar prefijos estables por dominio:

- `CFG`: configuracion y arranque.
- `HEALTH`: healthcheck.
- `READY`: readiness.
- `AUTH`: autenticacion.
- `ROLE`: autorizacion y permisos.
- `PROFILE`: perfiles propios de usuario.
- `CATALOG`: catalogo profesional publico y administrable.
- `PROF`: profesionales y busqueda publica.
- `CAT`: categorias.
- `SPEC`: especialidades.
- `AVAIL`: disponibilidad.
- `BOOK`: reservas.
- `METRIC`: metricas.
- `ADMIN`: backoffice.
- `EMAIL`: correo.
- `MEET`: reuniones.
- `FRONT`: frontend.
- `INFRA`: Docker e infraestructura local.
- `MIG`: migraciones.
- `SEED`: datos iniciales.

Formato recomendado: `PREFIX-001`.

## Definition of Ready

Una funcionalidad esta lista para implementacion cuando tiene:

- problema definido;
- alcance definido;
- exclusiones claras;
- actores identificados;
- reglas de negocio documentadas;
- criterios de aceptacion;
- impacto tecnico evaluado;
- riesgos principales identificados;
- dependencias conocidas;
- implementacion dividida en pasos pequenos.

## Definition of Done actual

Durante las primeras etapas del MVP, una funcionalidad puede considerarse terminada cuando:

- la spec esta aprobada;
- los criterios de aceptacion estan definidos;
- el diseno tecnico esta documentado;
- backend implementado, si corresponde;
- frontend implementado, si corresponde;
- migracion incluida, si corresponde;
- contratos de API documentados;
- permisos revisados;
- manejo de errores incluido;
- controles funcionales minimos ejecutados;
- integracion afectada validada;
- flujo principal validado;
- Docker Compose continua operativo;
- documentacion actualizada;
- matriz de trazabilidad actualizada;
- riesgos y deuda tecnica registrados.

No es obligatorio todavia: Gherkin, pruebas de carga, pruebas de estres, pruebas de rendimiento, cobertura minima, suites completas de API ni pruebas end-to-end complejas.

## Relacion entre requisitos, implementacion y validacion

Cada requisito debe aparecer en `traceability/requirements-matrix.md`. La matriz debe apuntar a archivos, endpoints, base de datos y controles realizados. Si un requisito existe en codigo pero no fue validado, su estado no debe ser `verified`.

## Specs retrospectivas y prospectivas

Las specs retrospectivas documentan comportamiento ya existente sin reescribirlo. Deben registrar criterios cumplidos, pendientes, riesgos y deuda. Las specs prospectivas se escriben antes de implementar funcionalidad nueva y deben cumplir la Definition of Ready.

## Regla de no implementar sin spec

No se debe implementar funcionalidad nueva sin una spec suficientemente clara. Las correcciones criticas tambien deben registrar el problema, impacto, criterio de aceptacion y validacion esperada antes de tocar codigo.

## Estrategia progresiva de pruebas

En el Modulo 0 no se crean pruebas automatizadas nuevas. La validacion se basa en inspeccion estatica, revision de configuracion, Docker Compose config, migraciones, seed, rutas, schemas, servicios, permisos y controles manuales permitidos.

En modulos futuros se podran agregar pruebas pequenas y rapidas para health, readiness, autenticacion, permisos, persistencia o integraciones criticas cuando reduzcan riesgo real de regresion.

Gherkin no se utiliza en la etapa actual.

## Modulos activos

- `modules/module-00-baseline`: baseline retrospectivo y remediaciones iniciales.
- `modules/module-01-foundation`: fundacion tecnica verificada en runtime.
- `modules/module-02-auth-profiles`: autenticacion, autorizacion y perfiles base. Estado inicial: en progreso.
- `modules/module-03-professional-catalog`: catalogo profesional y busqueda publica. Estado inicial: en progreso.
- `modules/module-04-availability`: disponibilidad semanal, bloqueos y calculo de slots. Estado inicial: en progreso.
