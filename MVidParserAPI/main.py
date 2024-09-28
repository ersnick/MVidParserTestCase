from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from models import ProductView, ProductCreate, Product, get_db, PriceHistoryView, PriceHistory

app = FastAPI()


# Добавление нового товара на мониторинг
@app.post("/products/", response_model=ProductView)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(url=product.url)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


# Удаление товара
@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Удаляем связанные записи из таблицы price_history
    db.query(PriceHistory).filter(PriceHistory.product_id == product_id).delete()

    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted"}


# Получение списка товаров на мониторинге
@app.get("/products/", response_model=List[ProductView])
def get_products(db: Session = Depends(get_db)):
    return db.query(Product).all()


# Получение истории цен на товар
@app.get("/products/{product_id}/price-history", response_model=List[PriceHistoryView])
def get_price_history(product_id: int, db: Session = Depends(get_db)):
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).all()
    if not history:
        raise HTTPException(status_code=404, detail="No price history found for this product")
    return history
