from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import SessionLocal
from app.services.report_service import ReportService
from app.services.email_service import EmailService
from app.services.ai_service import AIService
from app.models import Product
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def scheduled_report_job():
    logger.info("🤖 Robot: Iniciando tarea programada...")
    db = SessionLocal()
    try:
        report_service = ReportService(db)
        path = report_service.get_report(report_type=settings.default_report_type)

        ai_service = AIService()
        products = db.query(Product).all()

        alert_msg = ""
        for p in products:
            analysis = ai_service.predict_next_month_demand(db, p.id)
            if analysis and analysis["recommendation"] > 0:
                alert_msg += f"- ⚠️ {analysis['product_name']}: Stock actual ({analysis['current_stock']}). " \
                             f"Demanda prevista: {analysis['forecast_30d']} uds. " \
                             f"Se recomienda comprar {analysis['recommendation']} uds.\n"
        
        body = "Hola, \n\nAdjunto encontrarás el reporte empresarial generado automáticamente por la suite.\n\n"

        if alert_msg:
            body += "🚨 ALERTAS DE STOCK PREDICTIVAS (IA):\n"
            body += "Basado en las tendencias de ventas, la IA recomienda revisar el stock de los siguientes productos:\n\n"
            body += alert_msg + "\n"
        else:
            body += "✅ La IA indica que tienes stock suficiente para cubrir la demanda de los próximos 30 días.\n\n"
            body += "Saludos,\nIntelliBusiness Suite."
        
        if path:
            email_service = EmailService()
            await email_service.send_report_email(file_path=path, body=body)
            logger.info("📧 Robot: Reporte y alertas de IA enviados.")
    
    except Exception as e:
        logger.error(f"❌ Robot: Error en la tarea: {e}")
    finally:
        db.close()

def start_scheduler():
    scheduler = AsyncIOScheduler()
    hour, minute = settings.report_schedule.split(":")

    scheduler.add_job(
        scheduled_report_job,
        'cron',
        hour=hour,
        minute=minute,
        id="daily_report_job"
    )

    scheduler.start()
    logger.info(f"Scheduler iniciado: Reporte programado todos los días a las {settings.report_schedule}")
    return scheduler

def reload_scheduler(new_hour: str):
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    hour, minute = new_hour.split(":")
