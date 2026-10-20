from app.database import SessionLocal, engine, Base
from app.models import Product, Sale
import datetime

# 1. Inicializar la base de datos (Crear tablas fusionadas)
print("⏳ Creando tablas fusionadas en suite.db...")
Base.metadata.create_all(bind=engine)

def test_merging_logic():
    db = SessionLocal()
    try:
        print("🚀 Iniciando prueba de integridad de la Suite...")

        # 2. Crear un producto de prueba (Atributos de StockWise)
        test_product = Product(
            name="Monitor UltraWide 34",
            category="Electrónica",
            current_stock=50,
            min_stock_level=10,
            price=450.0,
            unit_cost=300.0
        )
        db.add(test_product)
        db.commit()
        db.refresh(test_product)
        print(f"✅ Producto creado: {test_product.name} (ID: {test_product.id})")

        # 3. Crear una venta asociada (Atributos de BPAR + FK)
        test_sale = Sale(
            product_id=test_product.id,
            product_name=test_product.name,
            customer_name="Daniel Sánchez",
            quantity=2,
            amount=900.0,
            date=datetime.datetime.now()
        )
        db.add(test_sale)
        db.commit()
        db.refresh(test_sale)
        print(f"✅ Venta registrada: {test_sale.quantity} unidades para {test_sale.customer_name}")

        # 4. Verificar la relación (JOIN)
        # Consultamos la venta y accedemos al objeto producto gracias a relationship()
        queried_sale = db.query(Sale).filter(Sale.id == test_sale.id).first()
        
        print("\n--- 🔍 VERIFICACIÓN DE RELACIÓN ---")
        print(f"Venta ID: {queried_sale.id}")
        print(f"Producto vinculado desde DB: {queried_sale.product.name}")
        print(f"Stock actual del producto: {queried_sale.product.current_stock}")
        
        if queried_sale.product.id == test_product.id:
            print("\n🏆 ¡ÉXITO! Las tablas de BPAR y StockWise están correctamente vinculadas.")
        else:
            print("\n❌ ERROR: La relación de base de datos no es correcta.")

    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_merging_logic()