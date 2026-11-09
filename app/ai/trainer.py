import pandas as pd
import joblib 
import os
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from app.database import engine as default_engine

MODEL_DIR = Path(__file__).resolve().parent / "model_store"

def prepare_data_for_training(bind=None):
    # Usa el mismo motor que la app (SQLite o PostgreSQL según la configuración)
    engine = bind if bind is not None else default_engine

    query = "SELECT date, quantity, product_name FROM sales"
    df = pd.read_sql(query, engine)

    if df.empty:
        raise ValueError("❌ La base de datos está vacía. Ejecuta seed_suite.py primero.")
    
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values(['product_name', 'date'])

    df['month'] = df['date'].dt.month
    df['day_of_week'] = df['date'].dt.day_of_week
    df['is_weekend'] = df['day_of_week'].map(lambda x: 1 if x >= 5 else 0)

    df['sales_lag_1'] = df.groupby('product_name')['quantity'].shift(1)
    df['rolling_mean_7'] = df.groupby('product_name')['quantity'].transform(
        lambda x: x.rolling(window=7).mean()
    )

    df = df.dropna()
    return df

def train_model(bind=None, model_dir=None):
    print("🧠 Preparando datos para el entrenamiento...")
    df = prepare_data_for_training(bind)

    if df is None:
        return

    features = ['month', 'day_of_week', 'is_weekend', 'sales_lag_1', 'rolling_mean_7']
    X = df[features]
    y = df['quantity']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"📈 Entrenando Random Forest con {len(X_train)} registros...")
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"✅ Entrenamiento completado. Error Medio (MAE): {mae:.2f} unidades.")

    model_dir = Path(model_dir) if model_dir is not None else MODEL_DIR
    model_dir.mkdir(parents=True, exist_ok=True)

    model_path = model_dir / "stock_model.pkl"
    joblib.dump(model, model_path)
    print(f"💾 Modelo guardado en: {model_path}")
    return mae

if __name__ == "__main__":
    train_model()