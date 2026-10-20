import json
from types import SimpleNamespace

from app.config import load_settings
from app.database import get_database_url
from app.models import Product, Sale


def _write_settings_json(directory, data):
    (directory / "config").mkdir()
    (directory / "config" / "settings.json").write_text(json.dumps(data))


# ---------- Configuración ----------

def test_settings_json_overrides_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DB_TYPE", raising=False)
    _write_settings_json(tmp_path, {"app_name": "Mi Suite", "db_type": "sqlite"})

    settings = load_settings()

    assert settings.app_name == "Mi Suite"
    assert settings.db_type == "sqlite"


def test_environment_variable_wins_over_settings_json(tmp_path, monkeypatch):
    """Docker fuerza DB_TYPE=postgresql aunque settings.json diga sqlite."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_TYPE", "postgresql")
    _write_settings_json(tmp_path, {"db_type": "sqlite", "app_name": "Mi Suite"})

    settings = load_settings()

    assert settings.db_type == "postgresql"
    assert settings.app_name == "Mi Suite"  # el resto del JSON sigue aplicándose


# ---------- Selección de base de datos ----------

def test_database_url_defaults_to_sqlite():
    url = get_database_url(SimpleNamespace(db_type="sqlite"))
    assert url.startswith("sqlite:///") and url.endswith("suite.db")


def test_database_url_for_postgresql():
    cfg = SimpleNamespace(
        db_type="postgresql", POSTGRES_USER="admin", POSTGRES_PASSWORD="pw",
        POSTGRES_HOST="db", POSTGRES_PORT="5432", POSTGRES_DB="suite_db",
    )
    assert get_database_url(cfg) == "postgresql://admin:pw@db:5432/suite_db"


# ---------- Modelo de datos ----------

def test_sale_is_linked_to_its_product(db_session):
    sale = db_session.query(Sale).first()
    product = db_session.query(Product).filter_by(id=sale.product_id).one()

    assert sale.product.name == product.name
    assert len(product.sales) == 40
