import asyncio
import logging
from app.services.scheduler_service import scheduled_report_job

logging.basicConfig(level=logging.INFO)

async def run_test():
    print("🚀 Iniciando prueba del Robot Híbrido (Reportes + IA)...")
    await scheduled_report_job()
    print("🏁 Prueba finalizada.")

if __name__ == "__main__":
    asyncio.run(run_test())