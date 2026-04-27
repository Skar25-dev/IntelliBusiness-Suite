import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models import Product, Sale
from app.config import settings
from pathlib import Path

class AIService:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent.parent
        MODEL_PATH = BASE_DIR / "app" / "ai" / "model_store" / "stock_model.pkl"

        if MODEL_PATH.exists():
            self.model = joblib.load(MODEL_PATH)
        else:
            self.model = None
            print("⚠️ Advertencia: No se encontró el modelo de IA. El entrenamiento es necesario.")
        
    def predict_next_month_demand(self, db: Session, product_id: int) -> dict:
        if not self.model:
            return None
        
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return None

        last_sales = db.query(Sale)\
                        .filter(Sale.product_id == product_id)\
                        .order_by(Sale.date.desc())\
                        .limit(7).all()
        
        if len(last_sales) < 7:
            return None
        
        current_window = [s.quantity for s in reversed(last_sales)]
        total_forecast = 0
        future_date = datetime.now() + timedelta(days=1)

        # Predecimos 30 días en bucle (Inferencia Recursiva)
        for _ in range(30):
            month = future_date.month
            day_of_week = future_date.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            sales_lag_1 = current_window[-1]
            rolling_mean_7 = np.mean(current_window)

            input_df = pd.DataFrame([[month, day_of_week, is_weekend, sales_lag_1, rolling_mean_7]],
                                    columns=['month', 'day_of_week', 'is_weekend', 'sales_lag_1', 'rolling_mean_7'])
            
            pred = max(0, self.model.predict(input_df)[0])
            total_forecast += pred

            current_window.pop(0)
            current_window.append(pred)
            future_date += timedelta(days=1)
        
        # Lógica para la recomendación de compra
        safety_margin = settings.ai_settings.get("safety_stock_margin", 0.2)
        needed_total = total_forecast * (1 + safety_margin)
        recommendation = max(0, int(needed_total - product.current_stock))

        return {
            "product_name": product.name,
            "current_stock": product.current_stock,
            "forecast_30d": round(total_forecast),
            "recommendation": recommendation
        }