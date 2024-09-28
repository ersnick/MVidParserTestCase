from telethon import TelegramClient, events
from models import Product, SessionLocal, PriceHistory
import os
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# Инициализация клиента
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
db = SessionLocal()


@client.on(events.NewMessage(pattern='/add'))
async def add_product(event):
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) < 2:
        await event.reply("Использование: /add <ссылка на товар>")
        return

    product_url = parts[1]

    db_product = Product(url=product_url)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    await event.reply(f"Товар добавлен на мониторинг: {product_url}")


@client.on(events.NewMessage(pattern='/remove'))
async def remove_product(event):
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) < 2:
        await event.reply("Использование: /remove <ID товара>")
        return

    product_id = parts[1]

    db_product = db.query(Product).filter(Product.id == product_id).first()
    if db_product is None:
        await event.reply(f"Товар с ID {product_id} не найден.")

    # Удаляем связанные записи из таблицы price_history
    db.query(PriceHistory).filter(PriceHistory.product_id == product_id).delete()

    db.delete(db_product)
    db.commit()

    await event.reply(f"Товар с ID {product_id} удалён.")


@client.on(events.NewMessage(pattern='/list'))
async def list_products(event):
    response = "Товары на мониторинге:\n"
    products = db.query(Product).all()

    # Устанавливаем лимит на длину одного сообщения (например, 4096 символов)
    max_message_length = 4000
    message_chunk = ""

    for product in products:
        product_info = f"ID: {product.id}\nНазвание: {product.name}\nОписание: {product.description}\nСсылка: " \
                    f"{product.url}\nЦена: {product.price}\nРейтинг: {product.rating}\n\n "

        # Если добавление информации о продукте превышает лимит, отправляем сообщение
        if len(message_chunk) + len(product_info) > max_message_length:
            await event.reply(message_chunk)
            message_chunk = ""  # Очищаем сообщение для следующего блока

        message_chunk += product_info

        # Отправляем оставшуюся часть сообщения
    if message_chunk:
        await event.reply(message_chunk)


@client.on(events.NewMessage(pattern='/history'))
async def get_price_history(event):
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) < 2:
        await event.reply("Использование: /history <ID товара>")
        return

    product_id = parts[1]
    history = db.query(PriceHistory).filter(PriceHistory.product_id == product_id).all()
    if not history:
        await event.reply(f"Товар с ID {product_id} не найден.")

    # Устанавливаем лимит на длину одного сообщения (например, 4096 символов)
    max_message_length = 4000
    message_chunk = ""

    for hstr in history:
        history_info = f"product_id: {hstr.product_id}\nЦена: {hstr.price}\nДата: {hstr.recorded_at}\n\n"

        # Если добавление информации о продукте превышает лимит, отправляем сообщение
        if len(message_chunk) + len(history_info) > max_message_length:
            await event.reply(message_chunk)
            message_chunk = ""  # Очищаем сообщение для следующего блока

        message_chunk += history_info

    # Отправляем оставшуюся часть сообщения
    if message_chunk:
        await event.reply(message_chunk)


if __name__ == '__main__':
    print("Бот запущен!")
    client.run_until_disconnected()
