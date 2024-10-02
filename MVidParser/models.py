from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DECIMAL, DateTime
import os
from dotenv import load_dotenv

load_dotenv()

# Строка подключения к базе данных PostgreSQL
database_url = f"postgresql+asyncpg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_async_engine(database_url)

# Асинхронная сессия
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# Базовый класс для моделей
Base = declarative_base()


# Модель товара
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    rating = Column(Numeric(2, 1), nullable=True)
    url = Column(String(255), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=True)
    user_id = Column(String(255), nullable=False, index=True)


# Модель истории цен
class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    price = Column(DECIMAL(10, 2), nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)


# Создание всех таблиц (если они еще не созданы)
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
