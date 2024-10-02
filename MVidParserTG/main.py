import asyncio
from sqlalchemy import delete
from telethon import TelegramClient, events
from models import Product, get_db, PriceHistory, init_db
from sqlalchemy.future import select
import os
from dotenv import load_dotenv
import logging
from logging import INFO


logger = logging.getLogger()


# Настройка логирования
def __config_logger():
    file_log = logging.FileHandler('telegram-bot.log')
    console_log = logging.StreamHandler()
    FORMAT = '[%(levelname)s] %(asctime)s : %(message)s | %(filename)s'
    logging.basicConfig(level=INFO,
                        format=FORMAT,
                        handlers=(file_log, console_log),
                        datefmt='%d-%m-%y - %H:%M:%S')


load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# Инициализация клиента
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)


@client.on(events.NewMessage(pattern='/add'))
async def add_product(event):
    user_id = str(event.sender_id)
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) < 2:
        await event.reply("Использование: /add <ссылка на товар>")
        return

    product_url = parts[1]

    try:
        async for db in get_db():
            db_product = Product(url=product_url, user_id=user_id)
            db.add(db_product)
            await db.commit()
            await db.refresh(db_product)
            await event.reply(f"Товар добавлен на мониторинг: {product_url}")
            logger.info(f"Товар добавлен: {product_url} пользователем {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при добавлении товара: {e}")
        await event.reply("Произошла ошибка при добавлении товара.")


@client.on(events.NewMessage(pattern='/remove'))
async def remove_product(event):
    user_id = str(event.sender_id)
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) < 2:
        await event.reply("Использование: /remove <ID товара>")
        return

    product_id = int(parts[1])

    try:
        async for db in get_db():
            db_product = await db.get(Product, product_id)
            if not db_product or db_product.user_id != user_id:
                await event.reply(f"Товар с ID {product_id} не найден.")
                return

            # Удаляем связанные записи из таблицы price_history
            await db.execute(
                delete(PriceHistory).where(PriceHistory.product_id == product_id)
            )

            await db.delete(db_product)
            await db.commit()
            await event.reply(f"Товар с ID {product_id} удалён.")
            logger.info(f"Товар с ID {product_id} удалён пользователем {user_id}")
    except Exception as e:
        logger.error(f"Ошибка при удалении товара: {e}")
        await event.reply("Произошла ошибка при удалении товара.")


@client.on(events.NewMessage(pattern='/list'))
async def list_products(event):
    user_id = str(event.sender_id)

    try:
        async for db in get_db():
            result = await db.execute(select(Product).where(Product.user_id == user_id))
            products = result.scalars().all()

            if not products:
                await event.reply("У вас нет товаров на мониторинге.")
                return

            # Устанавливаем лимит на длину одного сообщения (например, 4096 символов)
            max_message_length = 4000
            message_chunk = "Товары на мониторинге:\n"

            for product in products:
                product_info = (f"ID: {product.id}\nНазвание: {product.name}\nОписание: {product.description}\n"
                                f"Ссылка: {product.url}\nЦена: {product.price}\nРейтинг: {product.rating}\n\n")

                # Если добавление информации о продукте превышает лимит, отправляем сообщение
                if len(message_chunk) + len(product_info) > max_message_length:
                    await event.reply(message_chunk)
                    message_chunk = "" # Очищаем сообщение для следующего блока

                message_chunk += product_info

            # Отправляем оставшуюся часть сообщения
            if message_chunk:
                await event.reply(message_chunk)
            logger.info(f"Пользователь {user_id} запросил список товаров.")
    except Exception as e:
        logger.error(f"Ошибка при получении списка товаров: {e}")
        await event.reply("Произошла ошибка при получении списка товаров.")


@client.on(events.NewMessage(pattern='/history'))
async def get_price_history(event):
    user_id = str(event.sender_id)
    message_text = event.message.message
    parts = message_text.split()

    if len(parts) < 2:
        await event.reply("Использование: /history <ID товара>")
        return

    product_id = int(parts[1])

    try:
        async for db in get_db():
            result = await db.execute(
                select(Product).where(Product.id == product_id, Product.user_id == user_id)
            )
            product = result.scalars().first()

            if not product:
                await event.reply(f"Товар с ID {product_id} не найден.")
                return

            result = await db.execute(select(PriceHistory).where(PriceHistory.product_id == product_id))
            history = result.scalars().all()

            if not history:
                await event.reply(f"История цен для товара с ID {product_id} не найдена.")
                return

            # Устанавливаем лимит на длину одного сообщения (например, 4096 символов)
            max_message_length = 4000
            message_chunk = ""

            for hstr in history:
                history_info = f"product_id: {hstr.product_id}\nЦена: {hstr.price}\nДата: {hstr.recorded_at}\n\n"

                # Если добавление информации о продукте превышает лимит, отправляем сообщение
                if len(message_chunk) + len(history_info) > max_message_length:
                    await event.reply(message_chunk)
                    message_chunk = ""

                message_chunk += history_info

            # Отправляем оставшуюся часть сообщения
            if message_chunk:
                await event.reply(message_chunk)
            logger.info(f"Пользователь {user_id} запросил историю цен для товара с ID {product_id}.")
    except Exception as e:
        logger.error(f"Ошибка при получении истории цен: {e}")
        await event.reply("Произошла ошибка при получении истории цен.")


async def main():
    # Инициализируем базу данных
    await init_db()
    logger.info("База данных инициализирована")

    # Запускаем бота
    await client.start(bot_token=bot_token)
    logger.info("Бот запущен!")

    # Запускаем бота в event loop до отключения
    await client.run_until_disconnected()


if __name__ == '__main__':
    __config_logger()
    # Запуск всего приложения в существующем event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
