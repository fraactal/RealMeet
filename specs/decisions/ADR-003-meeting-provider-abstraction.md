# ADR-003: Abstraccion de proveedores de reuniones

## Estado

Aceptada retrospectivamente.

## Contexto

El MVP debe generar reuniones mock y dejar preparada la integracion futura con Google Meet y Zoom sin implementarlas todavia.

## Decision

Usar una interfaz `MeetingProvider` con `MockMeetingProvider` operativo y clases preparadas para Google Meet y Zoom que lanzan `NotImplementedError`.

## Evidencia

- `backend/app/meetings/base.py`
- `backend/app/meetings/mock.py`
- `backend/app/meetings/google_meet.py`
- `backend/app/meetings/zoom.py`
- `backend/app/meetings/factory.py`
- Campos de reserva: `meeting_provider`, `meeting_url`, `external_meeting_id`, `calendar_event_id`.

## Consecuencias

La integracion real queda fuera del MVP actual. Se debe evitar configurar `DEFAULT_MEETING_PROVIDER` con valores reales hasta que existan specs e implementaciones verificadas.
