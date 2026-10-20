import joblib
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.ai import predictor, trainer
from app.database import Base
from app.models import Product, Sale
from app.services.ai_service import AIService

from .conftest import DAYS_OF_HISTORY

FEATURES = ["month", "day_of_week", "is_weekend", "sales_lag_1", "rolling_mean_7"]


# ---------- Entrenamiento ----------

def test_prepare_data_builds_features_and_drops_incomplete_rows(db_session):
    df = trainer.prepare_data_for_training(db_session.get_bind())

    assert set(FEATURES) <= set(df.columns)
    assert not df[FEATURES].isna().any().any()
    # rolling_mean_7 necesita 7 días: se pierden 6 filas por producto
    assert len(df) == 2 * (DAYS_OF_HISTORY - 6)
    # is_weekend coherente con day_of_week
    assert (df["is_weekend"] == (df["day_of_week"] >= 5).astype(int)).all()


def test_prepare_data_with_empty_database_raises():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with pytest.raises(ValueError):
        trainer.prepare_data_for_training(engine)


def test_train_model_saves_a_loadable_model_and_returns_mae(db_session, isolated_model):
    mae = trainer.train_model(bind=db_session.get_bind())

    model_path = isolated_model / "stock_model.pkl"
    assert model_path.exists()
    assert mae >= 0
    assert hasattr(joblib.load(model_path), "predict")


# ---------- Predictor ----------

def test_predict_without_model_raises_clear_error(db_session):
    with pytest.raises(predictor.ModelNotTrainedError):
        predictor.predict_sales_range(db_session, "Monitor")


def test_predict_returns_requested_horizon_with_non_negative_values(db_session, trained_model):
    forecast = predictor.predict_sales_range(db_session, "Monitor", days_to_forecast=30)

    assert len(forecast) == 30
    assert all(point["value"] >= 0 for point in forecast)
    assert set(forecast[0]) == {"date", "value"}


def test_predict_unknown_product_returns_none(db_session, trained_model):
    assert predictor.predict_sales_range(db_session, "No existe") is None


def test_predict_with_less_than_7_sales_returns_none(db_session, trained_model):
    nuevo = Product(name="Nuevo", category="Hogar", current_stock=1, price=1.0, unit_cost=1.0)
    db_session.add(nuevo)
    db_session.flush()
    db_session.add(Sale(product_id=nuevo.id, product_name="Nuevo", quantity=3, amount=3.0))
    db_session.commit()

    assert predictor.predict_sales_range(db_session, "Nuevo") is None


# ---------- AIService (recomendación de compra) ----------

def test_ai_service_without_model_returns_none(db_session):
    assert AIService().predict_next_month_demand(db_session, 1) is None


def test_ai_service_recommends_purchase_when_stock_is_low(db_session, trained_model):
    silla = db_session.query(Product).filter_by(name="Silla").one()  # stock 5

    result = AIService().predict_next_month_demand(db_session, silla.id)

    assert result["product_name"] == "Silla"
    assert result["forecast_30d"] > silla.current_stock
    # recomendación = demanda * (1 + margen 0.2) - stock actual
    assert result["recommendation"] > 0


def test_ai_service_recommends_nothing_when_stock_is_enough(db_session, trained_model):
    silla = db_session.query(Product).filter_by(name="Silla").one()
    silla.current_stock = 100_000
    db_session.commit()

    result = AIService().predict_next_month_demand(db_session, silla.id)

    assert result["recommendation"] == 0
