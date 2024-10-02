from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from models import ProductView, ProductCreate, Product, get_db, PriceHistoryView, PriceHistory, init_db
import logging
from logging import INFO

app = FastAPI()


# Настройка логирования
def __config_logger():
    file_log = logging.FileHandler('parser-api.log')
    console_log = logging.StreamHandler()
    FORMAT = '[%(levelname)s] %(asctime)s : %(message)s | %(filename)s'
    logging.basicConfig(level=INFO,
                        format=FORMAT,
                        handlers=(file_log, console_log),
                        datefmt='%d-%m-%y - %H:%M:%S')


logger = logging.getLogger()
__config_logger()


# Обработчик события запуска приложения
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()  # Инициализация базы данных
        logger.info("База данных инициализирована")
        yield  # Успешная инициализация, продолжаем выполнение приложения
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при инициализации базы данных")

app = FastAPI(lifespan=lifespan)


# Добавление нового товара на мониторинг
@app.post("/products/", response_model=ProductView)
async def create_product(product: ProductCreate, request: Request, db: AsyncSession = Depends(get_db)):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    try:
        db_product = Product(url=product.url, user_id=session_id)
        db.add(db_product)
        await db.commit()
        await db.refresh(db_product)
        logger.info(f"Товар добавлен на мониторинг пользователем {session_id}: {product.url}")
        return db_product
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при добавлении товара")


# Удаление товара
@app.delete("/products/{product_id}")
async def delete_product(product_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    try:
        db_product = await db.get(Product, product_id)
        if not db_product or db_product.user_id != session_id:
            raise HTTPException(status_code=404, detail="Product not found or does not belong to you")

        # Удаляем связанные записи из таблицы price_history
        await db.execute(
            delete(PriceHistory).where(PriceHistory.product_id == product_id)
        )
        await db.delete(db_product)
        await db.commit()
        logger.info(f"Товар с ID {product_id} удалён пользователем {session_id}")
        return {"message": "Product deleted"}
    except Exception as e:
        logger.error(f"Ошибка при удалении товара с ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при удалении товара")


# Получение списка товаров на мониторинге
@app.get("/products/", response_model=List[ProductView])
async def get_products(request: Request, db: AsyncSession = Depends(get_db)):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    try:
        result = await db.execute(
            select(Product).where(Product.user_id == session_id)
        )
        products = result.scalars().all()
        logger.info(f"Пользователь {session_id} запросил список товаров")
        return products
    except Exception as e:
        logger.error(f"Ошибка при получении списка товаров: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении списка товаров")


# Получение истории цен на товар
@app.get("/products/{product_id}/price-history", response_model=List[PriceHistoryView])
async def get_price_history(request: Request, product_id: int, db: AsyncSession = Depends(get_db)):
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID is required")

    try:
        result = await db.execute(
            select(Product).where(Product.id == product_id, Product.user_id == session_id)
        )
        product = result.scalars().first()

        if not product:
            raise HTTPException(status_code=404, detail="Product not found or does not belong to you")

        result = await db.execute(
            select(PriceHistory).where(PriceHistory.product_id == product_id)
        )
        history = result.scalars().all()

        if not history:
            raise HTTPException(status_code=404, detail="No price history found for this product")

        logger.info(f"Пользователь {session_id} запросил историю цен для товара с ID {product_id}")
        return history
    except Exception as e:
        logger.error(f"Ошибка при получении истории цен для товара с ID {product_id}: {e}")
        raise HTTPException(status_code=500, detail="Ошибка при получении истории цен")
