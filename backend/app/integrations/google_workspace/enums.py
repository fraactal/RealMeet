import enum


class GoogleWorkspaceServiceKey(str, enum.Enum):
    calendar = "calendar"
    meet = "meet"
    sheets = "sheets"
    drive = "drive"
    docs = "docs"


class GoogleWorkspaceHealthStatus(str, enum.Enum):
    healthy = "healthy"
    authorized_not_resource_tested = "authorized_not_resource_tested"
    authorization_required = "authorization_required"
    disabled = "disabled"
    unavailable = "unavailable"
    error = "error"
