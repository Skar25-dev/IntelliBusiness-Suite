from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
import datetime

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    category = Column(String)
    current_stock = Column(Integer)
    min_stock_level = Column(Integer, default=10)
    price = Column(Float)
    unit_cost = Column(Float)

    sales = relationship("Sale", back_populates="product")

class Sale(Base):
    __tablename__ = "sales"
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    product_name = Column(String)
    customer_name = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    quantity = Column(Integer)
    amount = Column(Float)

    product = relationship("Product", back_populates="sales")