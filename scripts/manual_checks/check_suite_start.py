from app.config import settings

print(f"--- 📊 TEST DE INICIO DE SUITE ---")
print(f"App: {settings.app_name}")
print(f"Email configurado: {settings.MAIL_USERNAME}")
print(f"Formato de reporte: {settings.report_format}")
print(f"Margen de seguridad IA: {settings.ai_settings['safety_stock_margin']}")
print(f"--- ✅ TODO CARGADO CORRECTAMENTE ---")