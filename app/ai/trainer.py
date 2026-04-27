import pandas as pd
import joblib 
import os
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
from sqlalchemy import create_engine
from app.database import DB_PATH

def prepare_data_for_training():
    engine = create_engine(f"sqlite:///{DB_PATH}")

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

def train_model():
    print("🧠 Preparando datos para el entrenamiento...")
    df = prepare_data_for_training()

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

    model_dir = Path(__file__).resolve().parent / "model_store"
    model_dir.mkdir(exist_ok=True)

    model_path = model_dir / "stock_model.pkl"
    joblib.dump(model, model_path)
    print(f"💾 Modelo guardado en: {model_path}")

if __name__ == "__main__":
    train_model()