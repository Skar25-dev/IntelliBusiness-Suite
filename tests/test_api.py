import pytest
from fastapi.testclient import TestClient

from app import main
from app.models import Product


@pytest.fixture
def client(db_session, tmp_path, monkeypatch):
    # Sin "with TestClient": no se ejecuta el lifespan (ni scheduler ni create_all)
    monkeypatch.setattr(main, "BASE_DIR", tmp_path)  # reports/ temporal
    main.app.dependency_overrides[main.get_db] = lambda: db_session
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_home_shows_counts(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "IntelliBusiness" in response.text


def test_predictions_page_lists_products(client):
    response = client.get("/predictions")

    assert response.status_code == 200
    assert "Monitor" in response.text and "Silla" in response.text


def test_reports_page_works_when_reports_folder_does_not_exist(client):
    """Regresión: antes lanzaba UnboundLocalError (500) en un entorno nuevo."""
    assert client.get("/reports").status_code == 200


def test_reports_page_lists_only_report_files(client, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "Reporte_ventas.xlsx").write_bytes(b"x")
    (reports / "notas.txt").write_text("no")

    body = client.get("/reports").text

    assert "Reporte_ventas.xlsx" in body
    assert "notas.txt" not in body


def test_download_existing_and_missing_report(client, tmp_path):
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "r.pdf").write_bytes(b"contenido")

    ok = client.get("/download/r.pdf")
    assert ok.status_code == 200 and ok.content == b"contenido"
    assert client.get("/download/no_existe.pdf").status_code == 404


# ---------- /api/chart-data ----------

def test_chart_data_returns_history_forecast_and_inventory_status(client, db_session, trained_model):
    silla = db_session.query(Product).filter_by(name="Silla").one()

    data = client.get(f"/api/chart-data/{silla.id}").json()

    assert data["product_name"] == "Silla"
    assert len(data["history"]) == 15
    assert len(data["forecast"]) == 30
    assert data["inventory"]["current"] == 5
    # Stock 5 frente a una demanda de ~10 uds/día: crítico
    assert data["inventory"]["day"]["status"] == "CRÍTICO"
    assert data["inventory"]["month"]["recommendation"] > 0


def test_chart_data_unknown_product_returns_404(client, trained_model):
    assert client.get("/api/chart-data/9999").status_code == 404


def test_chart_data_without_trained_model_returns_503(client, db_session):
    producto = db_session.query(Product).first()

    response = client.get(f"/api/chart-data/{producto.id}")

    assert response.status_code == 503
    assert "trainer" in response.json()["detail"]
