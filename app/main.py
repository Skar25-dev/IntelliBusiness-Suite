import os
import json
from typing import List
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import SessionLocal, engine
from app.config import settings
from app.models import Product, Sale
from app.services.report_service import ReportService, REPORT_MODELS, get_columns_for_model
from app.services.email_service import EmailService

app = FastAPI(title=settings.app_name)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "app" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "app" / "templates"))

def get_db():
    db = SessionLocal(); yield db; db.close()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    total_products = db.query(Product).count()
    total_sales = db.query(Sale).count()
    return templates.TemplateResponse(
        request=request, name="index.html",
        context={"app_name": settings.app_name, "products_count": total_products, "sales_count": total_sales}
    )

@app.get("/reports", response_class=HTMLResponse)
async def reports_page(request: Request, db: Session = Depends(get_db)):
    REPORTS_DIR = BASE_DIR / "reports"
    files = sorted(os.listdir(REPORTS_DIR), reverse=True) if REPORTS_DIR.exists() else []
    
    return templates.TemplateResponse(
        request=request, 
        name="reports.html", 
        context={
            "reports": files, 
            "app_name": settings.app_name,
            "settings": settings
        }
    )

@app.get("/predictions", response_class=HTMLResponse)
async def predictions_page(request: Request, db: Session = Depends(get_db)):
    products = db.query(Product).all()
    
    return templates.TemplateResponse(
        request=request, 
        name="predictions.html", 
        context={
            "products": products, 
            "app_name": settings.app_name,
            "settings": settings
        }
    )

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request):
    """Carga el panel de configuración con lógica de columnas dinámica"""
    report_types = list(REPORT_MODELS.keys())
    # Preparamos las columnas de todas las tablas para los checkboxes
    all_columns = {t: get_columns_for_model(t) for t in report_types}
    
    return templates.TemplateResponse(
        request=request, 
        name="settings.html", 
        context={
            "request": request,
            "settings": settings,
            "app_name": settings.app_name,
            "report_types": report_types,
            "all_columns": all_columns
        }
    )

@app.post("/settings")
async def update_settings(
    app_name: str = Form(...),
    company_name: str = Form(...),
    contact_email: str = Form(...),
    report_schedule: str = Form(...),
    db_type: str = Form(...),
    default_report_type: str = Form(...),
    report_format: str = Form(...),
    default_days: int = Form(...),
    sheet_name: str = Form(...),
    included_columns: List[str] = Form(...)
):
    """Guarda los cambios en el JSON y reinicia la Suite"""
    new_config = {
        "app_name": app_name,
        "company_name": company_name,
        "contact_email": contact_email,
        "report_schedule": report_schedule,
        "db_type": db_type,
        "default_report_type": default_report_type,
        "report_format": report_format,
        "ai_settings": settings.ai_settings, # Mantenemos los de IA por ahora
        "report_settings": {
            "default_days": default_days,
            "sheet_name": sheet_name,
            "included_columns": included_columns
        }
    }

    with open("config/settings.json", "w") as f:
        json.dump(new_config, f, indent=4)

    # Alerta visual de éxito
    return HTMLResponse(content="""
        <script>
            alert('✅ Configuración guardada. Reiniciando Ecosistema...');
            window.location.href = '/settings';
        </script>
    """)