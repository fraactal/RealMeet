from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status


def _resolve_examples_dir() -> Path:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / "docs" / "n8n" / "examples"
        if candidate.is_dir():
            return candidate
    package_candidate = current.parent / "example_workflows"
    if package_candidate.is_dir():
        return package_candidate
    return current.parents[2] / "docs" / "n8n" / "examples"


EXAMPLES_DIR = _resolve_examples_dir()


@dataclass(frozen=True)
class AutomationExample:
    key: str
    name: str
    description: str
    recommended_event_types: list[str]
    required_n8n_credentials: list[str]
    workflow_filename: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


EXAMPLES: tuple[AutomationExample, ...] = (
    AutomationExample(
        key="google_sheets_appointment_log",
        name="Registrar reservas en Google Sheets",
        description="Agrega una fila cuando se crea o cancela una reserva.",
        recommended_event_types=["appointment.created", "appointment.cancelled"],
        required_n8n_credentials=["Google Sheets OAuth2"],
        workflow_filename="realmeet-google-sheets-appointments.json",
    ),
    AutomationExample(
        key="generic_crm_upsert",
        name="Actualizar contacto en CRM generico",
        description="Transforma una reserva creada en un upsert de contacto hacia un CRM HTTP.",
        recommended_event_types=["appointment.created"],
        required_n8n_credentials=["CRM API credential"],
        workflow_filename="realmeet-generic-crm-upsert.json",
    ),
    AutomationExample(
        key="internal_failure_notification",
        name="Notificar errores operativos internos",
        description="Resume errores de notificacion para avisar a un canal interno configurable.",
        recommended_event_types=["notification.failed"],
        required_n8n_credentials=["Internal notification endpoint or Slack OAuth2"],
        workflow_filename="realmeet-internal-failure-notification.json",
    ),
)


def list_automation_examples() -> list[dict[str, Any]]:
    return [example.as_dict() for example in EXAMPLES]


def get_automation_example(example_key: str) -> AutomationExample:
    for example in EXAMPLES:
        if example.key == example_key:
            return example
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation example not found")


def get_automation_example_detail(example_key: str) -> dict[str, Any]:
    example = get_automation_example(example_key)
    workflow_path = EXAMPLES_DIR / example.workflow_filename
    if not workflow_path.is_file() or workflow_path.parent != EXAMPLES_DIR:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Automation workflow example not found")
    with workflow_path.open("r", encoding="utf-8") as file:
        workflow = json.load(file)
    return {"example": example.as_dict(), "workflow": workflow}
