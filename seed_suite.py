import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from app.database import SessionLocal, engine, Base
from app.models import Product, Sale
from faker import Faker
from faker_commerce import Provider as CommerceProvider 
import random

fake = Faker()
fake.add_provider(CommerceProvider)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

def seed_suite_data(num_products=15):
    print(f"⏳ Poblando IntelliBusiness Suite con {num_products} productos...")

    db.query(Sale).delete()
    db.query(Product).delete()

    categories = ['Electrónica', 'Hogar', 'Oficina', 'Deportes']

    for _ in range(num_products):
        p_name = fake.unique.ecommerce_name()
        cost = round(random.uniform(50.0, 200.0), 2)
        price = round(cost * 1.5, 2) # Margen del 50%

        product = Product(
            name=p_name,
            category=random.choice(categories),
            current_stock=random.randint(20, 100),
            min_stock_level=15,
            price=price,
            unit_cost=cost
        )
        db.add(product)
        db.flush()

        trend = random.uniform(-0.002, 0.005) # Algunos suben, otros bajan
        base_sales = random.randint(5, 15)

        for d in range(365):
            date = datetime.now() - timedelta(days=365-d)

            weekday_factor = 1.5 if date.weekday() >= 5 else 1.0
            trend_factor = 1 + (trend * d)
            noise = np.random.normal(0, 15)

            qty = int(max(0, (base_sales * weekday_factor * trend_factor) + noise))

            if qty > 0:
                sale = Sale(
                    product_id=product.id,
                    product_name=product.name,
                    customer_name=fake.name(),
                    date=date,
                    quantity=qty,
                    amount=round(qty * price, 2)
                )
                db.add(sale)
        
        db.commit()
        print("✅ Ecosistema de datos listo para Reportes e IA.")
    
if __name__ == "__main__":
    seed_suite_data()
