from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.ai import predictor, trainer
from app.config import settings
from app.database import Base
from app.models import Product, Sale
from app.utils import excel_generator, pdf_generator

DAYS_OF_HISTORY = 40


@pytest.fixture
def db_session():
    """SQLite en memoria con 2 productos y 40 días de ventas deterministas."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    now = datetime.now()
    products = [
        Product(name="Monitor", category="Electrónica", current_stock=50,
                min_stock_level=10, price=300.0, unit_cost=200.0),
        Product(name="Silla", category="Hogar", current_stock=5,
                min_stock_level=10, price=80.0, unit_cost=50.0),
    ]
    session.add_all(products)
    session.flush()

    for product in products:
        for age in range(DAYS_OF_HISTORY, 0, -1):
            quantity = 10 + (age % 7)
            session.add(
                Sale(
                    product_id=product.id,
                    product_name=product.name,
                    customer_name="Cliente",
                    # +1 h para evitar ambigüedad en el límite exacto de N días
                    date=now - timedelta(days=age, hours=1),
                    quantity=quantity,
                    amount=quantity * product.price,
                )
            )
    session.commit()

    yield session

    session.close()
    engine.dispose()


@pytest.fixture(autouse=True)
def reports_dir(tmp_path, monkeypatch):
    """Los reportes generados en los tests van a una carpeta temporal."""
    monkeypatch.setattr(excel_generator, "REPORTS_DIR", tmp_path)
    monkeypatch.setattr(pdf_generator, "REPORTS_DIR", tmp_path)
    return tmp_path


@pytest.fixture(autouse=True)
def fixed_settings(monkeypatch):
    """Configuración fija, independiente de config/settings.json."""
    monkeypatch.setattr(settings, "report_format", "xlsx")
    monkeypatch.setattr(settings, "ai_settings", {"forecast_days": 30, "safety_stock_margin": 0.2})
    monkeypatch.setattr(
        settings,
        "report_settings",
        {
            "default_days": 30,
            "included_columns": ["product_name", "category", "amount", "date"],
            "sheet_name": "Reporte de Ventas",
        },
    )


@pytest.fixture(autouse=True)
def isolated_model(tmp_path_factory, monkeypatch):
    """Aísla el modelo de IA: por defecto no hay ninguno y no se toca el real."""
    model_dir = tmp_path_factory.mktemp("model_store")
    monkeypatch.setattr(predictor, "MODEL_PATH", model_dir / "stock_model.pkl")
    monkeypatch.setattr(predictor, "_model", None)
    monkeypatch.setattr(trainer, "MODEL_DIR", model_dir)
    return model_dir


@pytest.fixture
def trained_model(db_session):
    """Entrena un modelo real (pequeño) con los datos del fixture y lo deja cargable."""
    trainer.train_model(bind=db_session.get_bind())
    return predictor.get_model()
