import asyncio
from app.database import SessionLocal
from app.services.report_service import ReportService
from app.services.email_service import EmailService

async def test_fusion_logic():
    db = SessionLocal()
    report_service = ReportService(db)
    
    print("🚀 Probando generación multireporte...")

    print("📊 Generando reporte de Ventas...")
    path_ventas = report_service.get_report(report_type="ventas", days=30)
    if path_ventas:
        print(f"✅ Reporte de Ventas creado en: {path_ventas}")
    
    print("📦 Generando reporte de Inventario...")
    path_inv = report_service.get_report(report_type="inventario")
    if path_inv:
        print(f"✅ Reporte de Inventario creado en: {path_inv}")

    # email_service = EmailService()
    # await email_service.send_report_email(path_ventas)

    db.close()

if __name__ == "__main__":
    asyncio.run(test_fusion_logic())