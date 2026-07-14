from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_ready_returns_ready_when_database_check_passes(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_database_connection", lambda: True)
    monkeypatch.setattr("app.main.check_critical_configuration", lambda: True)
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok", "configuration": "ok"}


def test_ready_returns_503_when_database_check_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_critical_configuration", lambda: True)
    monkeypatch.setattr("app.main.check_database_connection", lambda: False)
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"]["status"] == "not_ready"


def test_ready_returns_503_when_critical_config_fails(monkeypatch) -> None:
    monkeypatch.setattr("app.main.check_critical_configuration", lambda: False)
    client = TestClient(app)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["detail"] == {"status": "not_ready", "configuration": "invalid"}
