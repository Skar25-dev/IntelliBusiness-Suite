from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import json

class Settings(BaseSettings):
    # --- 🔐 SECRETOS (Vienen del .env) ---
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "database"

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = ""
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False

    # --- ⚙️ AJUSTES DE USUARIO (Vienen del JSON) ---
    app_name: str = "IntelliBusiness Suite"
    company_name: str = "Daniel Sánchez"
    db_type: str = "sqlite" 
    contact_email: str = ""
    report_schedule: str = "08:00"
    default_report_type: str = "ventas"
    report_format: str = "xlsx"

    # --- 🧠 AJUSTES DE IA (Faltaban estos) ---
    ai_settings: dict = {
        "forecast_days": 30,
        "safety_stock_margin": 0.2
    }

    # --- 📊 AJUSTES DE REPORTES ---
    report_settings: dict = {
        "default_days": 30,
        "included_columns": ["product_name", "category", "amount", "date"],
        "sheet_name": "Reporte de Ventas"
    }

    # Configuración de Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )
    
def load_settings():
    settings = Settings()

    json_path = Path("config/settings.json")
    if json_path.exists():
        with open(json_path, "r") as f:
            config_data = json.load(f)
            for key, value in config_data.items():
                if hasattr(settings, key):
                    setattr(settings, key, value)
    
    return settings

# Cargamos la configuración global
settings = load_settings()