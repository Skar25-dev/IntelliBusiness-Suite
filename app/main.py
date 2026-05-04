import os
import json
from typing import List
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app.database import SessionLocal, engine
from app.config import settings
from app.models import Product, Sale
from app.services.report_service import ReportService, REPORT_MODELS, get_columns_for_model
from app.services.email_service import EmailService
from app.services.ai_service import AIService
from app.ai.predictor import predict_sales_range

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
    
    if REPORTS_DIR.exists():
        files = [f for f in os.listdir(REPORTS_DIR) if f.endswith(('.xlsx', '.pdf'))]

        report_files = sorted(
            files,
            key=lambda x: os.path.getmtime(REPORTS_DIR / x),
            reverse=True
        )
    
    return templates.TemplateResponse(
        request=request, 
        name="reports.html", 
        context={
            "reports": report_files, 
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

@app.post("/run-report")
async def run_report_manual():
    from app.services.scheduler_service import scheduled_report_job
    try:
        await scheduled_report_job()
        return {"status": "success", "message": "Reporte e IA procesados con éxito"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_report(filename: str):
    REPORTS_DIR = BASE_DIR / "reports"
    file_path = REPORTS_DIR / filename

    if file_path.exists():
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    raise HTTPException(status_code=404, detail="Archivo no encontrado")

@app.get("/api/chart-data/{product_id}")
async def get_chart_data(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product: 
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    sales = db.query(Sale).filter(Sale.product_id == product_id)\
                .order_by(Sale.date.desc()).limit(15).all()
    
    if len(sales) < 7:
        raise HTTPException(status_code=400, detail="Se necesitan al menos 7 días de datos")
    
    history = [{"date": s.date.strftime("%d %b"), "value": s.quantity} for s in reversed(sales)]

    forecast_series = predict_sales_range(db, product.name, days_to_forecast=30)

    tomorrow_demand = forecast_series[0]['value']
    month_demand = sum([f['value'] for f in forecast_series])

    def get_status(current, demand):
        if current < demand * 0.5: return "CRÍTICO", "critical"
        if current < demand: return "BAJO", "low"
        return "ÓPTIMO", "optimal"
    
    day_status, day_color = get_status(product.current_stock, tomorrow_demand)
    month_status, month_color = get_status(product.current_stock, month_demand)

    return {
        "history": history,
        "forecast": forecast_series,
        "product_name": product.name,
        "inventory": {
            "current": product.current_stock,
            "day": {
                "status": day_status,
                "color": day_color,
                "recommendation": max(0, int(tomorrow_demand * 1.2 - product.current_stock)),
                "demand": round(tomorrow_demand, 1)
            },
            "month": {
                "status": month_status,
                "color": month_color,
                "recommendation": max(0, int(month_demand * 1.2 - product.current_stock)),
                "demand": round(month_demand)
            }
        }
    }