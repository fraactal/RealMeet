from dataclasses import dataclass

from app.integrations.google_workspace.enums import GoogleWorkspaceServiceKey


IDENTITY_SCOPES = ["openid", "email", "profile"]
CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar.events"]
SHEETS_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]
DOCS_SCOPES = ["https://www.googleapis.com/auth/documents"]


@dataclass(frozen=True)
class GoogleWorkspaceServiceDefinition:
    key: GoogleWorkspaceServiceKey
    name: str
    description: str
    required_scopes: tuple[str, ...]
    optional_scopes: tuple[str, ...] = ()
    implemented: bool = True
    health_check_supported: bool = True


SERVICE_DEFINITIONS: dict[GoogleWorkspaceServiceKey, GoogleWorkspaceServiceDefinition] = {
    GoogleWorkspaceServiceKey.calendar: GoogleWorkspaceServiceDefinition(
        GoogleWorkspaceServiceKey.calendar,
        "Google Calendar",
        "Lectura y escritura de eventos usados por reservas.",
        tuple(CALENDAR_SCOPES),
    ),
    GoogleWorkspaceServiceKey.meet: GoogleWorkspaceServiceDefinition(
        GoogleWorkspaceServiceKey.meet,
        "Google Meet",
        "Creacion de enlaces Meet mediante eventos Calendar.",
        tuple(CALENDAR_SCOPES),
    ),
    GoogleWorkspaceServiceKey.sheets: GoogleWorkspaceServiceDefinition(
        GoogleWorkspaceServiceKey.sheets,
        "Google Sheets",
        "Exportaciones tabulares de RealMeet.",
        tuple(SHEETS_SCOPES),
    ),
    GoogleWorkspaceServiceKey.drive: GoogleWorkspaceServiceDefinition(
        GoogleWorkspaceServiceKey.drive,
        "Google Drive",
        "Almacenamiento de archivos creados o abiertos por RealMeet.",
        tuple(DRIVE_SCOPES),
    ),
    GoogleWorkspaceServiceKey.docs: GoogleWorkspaceServiceDefinition(
        GoogleWorkspaceServiceKey.docs,
        "Google Docs",
        "Generacion de documentos desde plantillas.",
        tuple(DOCS_SCOPES),
    ),
}


def services_to_scopes(services: list[GoogleWorkspaceServiceKey]) -> list[str]:
    scopes: list[str] = []
    for scope in IDENTITY_SCOPES:
        if scope not in scopes:
            scopes.append(scope)
    for service in services:
        for scope in SERVICE_DEFINITIONS[service].required_scopes:
            if scope not in scopes:
                scopes.append(scope)
    return scopes
