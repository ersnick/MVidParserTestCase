import asyncio
import aiohttp
from sqlalchemy.future import select
from models import AsyncSessionLocal, Product, PriceHistory, init_db
import logging
from logging import INFO


# Настройка логирования
def __config_logger():
    file_log = logging.FileHandler('parser-service.log')
    console_log = logging.StreamHandler()
    FORMAT = '[%(levelname)s] %(asctime)s : %(message)s | %(filename)s'
    logging.basicConfig(level=INFO,
                        format=FORMAT,
                        handlers=(file_log, console_log),
                        datefmt='%d-%m-%y - %H:%M:%S')


logger = logging.getLogger()

cookies = {
    '__lhash_': 'aa2659c8a18fa628c9773fa7e18a28ff',
    'MVID_REGION_ID': '1',
    'MVID_CITY_ID': 'CityCZ_975',
    'MVID_TIMEZONE_OFFSET': '3',
    'MVID_KLADR_ID': '7700000000000',
    'MVID_REGION_SHOP': 'S002',
    'MVID_NEW_LK_OTP_TIMER': 'true',
    'MVID_CHAT_VERSION': '6.6.0',
    'SENTRY_TRANSACTIONS_RATE': '0.1',
    'SENTRY_REPLAYS_SESSIONS_RATE': '0.01',
    'SENTRY_REPLAYS_ERRORS_RATE': '0.01',
    'SENTRY_ERRORS_RATE': '0.1',
    'MVID_FILTER_CODES': 'true',
    'MVID_SERVICES': '111',
    'MVID_FLOCKTORY_ON': 'true',
    'MVID_IS_NEW_BR_WIDGET': 'true',
    'MVID_NEW_LK_CHECK_CAPTCHA': 'true',
    'MVID_MULTIOFFER': 'true',
    'MVID_GTM_ENABLED': '011',
    'MVID_CRITICAL_GTM_INIT_DELAY': '3000',
    'MVID_WEB_SBP': 'true',
    'MVID_CREDIT_SERVICES': 'true',
    'MVID_TYP_CHAT': 'true',
    'MVID_SP': 'true',
    'MVID_CREDIT_DIGITAL': 'true',
    'MVID_CASCADE_CMN': 'true',
    'MVID_EMPLOYEE_DISCOUNT': 'true',
    'MVID_AB_UPSALE': 'true',
    'MVID_AB_PERSONAL_RECOMMENDS': 'true',
    'MVID_SERVICE_AVLB': 'true',
    'MVID_ACCESSORIES_PDP_BY_RANK': 'true',
    'MVID_NEW_CHAT_PDP': 'true',
    'MVID_GROUP_BY_QUALITY': 'true',
    'MVID_DISPLAY_ACCRUED_BR': 'true',
    'MVID_DISPLAY_PERS_DISCOUNT': 'true',
    'MVID_AB_PERSONAL_RECOMMENDS_SRP': 'true',
    'MVID_DIGINETICA_ENABLED': 'true',
    'MVID_ACCESSORIES_ORDER_SET_VERSION': '2',
    'MVID_BR_CONVERSION': 'true',
    'MVID_IMG_RESIZE': 'true',
    'MVID_MCOMBO_SUBSCRIPTION': 'true',
    'MVID_DISABLEDITEM_PRICE': '1',
    'MVID_RECOMENDATION_SET_ALGORITHM': '1',
    'MVID_ENVCLOUD': 'prod1',
    '__hash_': '0b83774af33195a2a7789767bd8e9514',
    '__rhash_': 'affde5eb0db195a2a776d3f13e29a6aa',
    '_userGUID': '0:m1i5orf4:dDQKu2DQ9DgD~ilFXLXZF9CyZmtcNDBM',
    'dSesn': '1cce13a0-263b-3872-0788-7a614138ae3d',
    '_dvs': '0:m1i5orf4:zBtfDnzkuWs1Yj2b82Tyyuh8ljgxdGl4',
    '_userGUID': '0:m1i5orf4:dDQKu2DQ9DgD~ilFXLXZF9CyZmtcNDBM',
    'mindboxDeviceUUID': '5ee64e9b-3bba-4f91-8918-9db16b76214e',
    'directCrm-session': '%7B%22deviceGuid%22%3A%225ee64e9b-3bba-4f91-8918-9db16b76214e%22%7D',
    '_ym_uid': '1727286340598426632',
    '_ym_d': '1727286340',
    '_ga': 'GA1.1.1467942275.1727286340',
    '_sp_ses.d61c': '*',
    '_ym_isad': '1',
    '_ym_visorc': 'w',
    '__SourceTracker': 'google__organic',
    'admitad_deduplication_cookie': 'google__organic',
    'SMSError': '',
    'authError': '',
    'flocktory-uuid': 'e65a4fa7-de07-417a-85f5-0b48a3aabaf1-9',
    'customer_email': 'null',
    'advcake_track_id': '7f48a273-aa8d-c6d2-7161-ac824aeb7235',
    'advcake_session_id': '83467ade-820d-612e-1ae4-34417a9d62fd',
    'uxs_uid': 'fd5d05a0-7b65-11ef-b667-f399f4a2aa57',
    'flacktory': 'no',
    'BIGipServeratg-ps-prod_tcp80': '2969885706.20480.0000',
    'bIPs': '-971835924',
    'afUserId': 'af3f4c2f-2309-447c-8004-50e941f41438-p',
    'AF_SYNC': '1727286345188',
    'adid': '172728634556877',
    'MVID_GEOLOCATION_NEEDED': 'false',
    'advcake_track_url': '%3D20240923mR7oiWxC7oOx4ihPI4GeZeSVP8U%2FpPu7PIf40ZsW8Rq00mrPihZVGJW17HOdlB7tWoR%2F4TbMFGVquLwvTHiNiLI98Pd0g49wF9u1%2F1QevXa4X7Rpcqslci7UhCCkLijqYoJDOFpVtsxw%2Bk8xntrvkOudfO%2BP7Cy3jGwgb0S%2FH345hg4JOVtl%2B%2B0mq41BtspfbUmlAcaAVO0agDRVqIbo16%2Fg93ypx8R5Lt2QENYlF1FqjOgcA8L%2BK%2BEaX4E8VMFHT3gYp9TfTyW0r6xGURLK1n2tBZkvYDrI0eTWxth%2FFVGX5Qb9fE7VabPAUcrCWbe6H7OuRgSub8Acfnt0k4yqG2t%2FMx2zBPRhHFPM6ApmEAMZX96wzKQSwgDEZahtHv9LPRonuuMzM8JPw7L4BlAsg7s25vZje4lYt%2BN8w9xJfjLhPsq0INZyvGCDbxqdhOlPTozK5B9%2FiFJejer4ioMRGwTXFvaGTRi5zgL3XblLqfpSRHTTyvUZH4ENvzJ5sgVVELn%2B6l9BDy%2Bnz92lpRmXrZqhnOnasYiO4QGpaHGOe%2FT0vOji51bfgq8ZenYxjyuQnVMniD6b75NhJe6fUrqGFmBDYcsZbx1u9sBsRVEGW9htuXq4WXw9YJ4E2InDO%2BCoyhfXkYvYlI7JuZa7YleEj9f1qA7us3fhKwmgMPGvTuozS5uheqp9tu8%3D',
    'digi_uc': '|v:172728:20084970:20035898:30074325:30064273|c:172728:400347986',
    '_sp_id.d61c': 'af66f5ae-36d2-4fe9-a052-caf0d55e54f4.1727286340.1.1727286769..b78b67ad-62ac-4dd0-9732-a1f7b672f3ff..0a56bcf4-4f65-438e-b6fd-81506817396f.1727286340359.95',
    'gsscgib-w-mvideo': '1wGfa5zDkLtzXpJxf82qKZWeDZ+gEix0g7ohfM09JdEy0/Hsy5rbMeeYN9PNK88cSg2pA3V0WrulTdXPUHEyBsdqjU6xnrutvbHgjuZVgDiXD604LvH59U+nLbzQH9mt9GT0hN3zx///T1D5PhCV60WEbQjwXosBbLm+fG4Iivs411DEe5IMbRfLU4TnAcZdkCFVeL/PO4yMjEGfx7p8uyrl8tF9ePLMK9tNJG/oFnqGj96Pad4V84s4g/xfXcTNROJ5wrMD',
    'gsscgib-w-mvideo': '1wGfa5zDkLtzXpJxf82qKZWeDZ+gEix0g7ohfM09JdEy0/Hsy5rbMeeYN9PNK88cSg2pA3V0WrulTdXPUHEyBsdqjU6xnrutvbHgjuZVgDiXD604LvH59U+nLbzQH9mt9GT0hN3zx///T1D5PhCV60WEbQjwXosBbLm+fG4Iivs411DEe5IMbRfLU4TnAcZdkCFVeL/PO4yMjEGfx7p8uyrl8tF9ePLMK9tNJG/oFnqGj96Pad4V84s4g/xfXcTNROJ5wrMD',
    'fgsscgib-w-mvideo': 'sTpOc858a7860bbb9afc41b0fb1eef7a0a5c365e',
    'fgsscgib-w-mvideo': 'sTpOc858a7860bbb9afc41b0fb1eef7a0a5c365e',
    'gsscgib-w-mvideo': 'pdK1IaHl8CfLHO3kzYS72lSFTLAQkLWKZYusoQZLnI0SQ64qWTDmtQz0cY2iA+fVXilrAFt+uwFawAoUBOmLWAc1uSzNIyigfQ/A69zO72b9HDEs0JUDGVPGgJy/7jxl1gjc0ZHONulrKBatqUH+BSx/Gmd8S4wNH8QhhUUP2x+R7CLMwoLnIdpjlVq4GsXm7fQT1f5t1Du1ACevfeF/VT0Qhj2n+wMcgCUOKkYbBUjmMnwTYGh2clDWiHHBqe0nfdR2cyGJ',
    'cfidsgib-w-mvideo': 'cyATepWz9BwdJinTo+fwtXuo+8sqZKHmR5NXUxaI6Nh/sN0JeJqN1YRgkARiMb1/tILoJZiq9T7vAnLNlcKf75AuMZrwuyLcL6/7STEnVWr7o7M8HnvXi9VBjk3rjk+ZkzM2T/airxS1iymMBid7XmPI1iinuCkkaLNTCQ==',
    '_ga_BNX5WPP3YK': 'GS1.1.1727286339.1.1.1727286783.60.0.0',
    '_ga_CFMZTSS5FM': 'GS1.1.1727286339.1.1.1727286783.0.0.0',
}


async def get_product_data(product_url):
    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'referer': product_url,
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }

    product_id = headers['referer'].rsplit('-', 1)[-1]
    params_product = {
        'multioffer': 'true',
        'productId': product_id,
    }

    try:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get('https://www.mvideo.ru/bff/product-details', params=params_product,
                                   headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при получении данных продукта: {response.status}")
                    return None
                data = await response.json()

        product_name = data['body']['name']
        product_rating = data['body']['rating']['star']
        product_description = data['body']['description']
        logger.info(f"Получены данные продукта: {product_name}, рейтинг: {product_rating}")
        return product_name, product_rating, product_description
    except Exception as e:
        logger.error(f"Ошибка при запросе данных продукта: {e}")
        return None


async def get_product_price(product_url):
    headers = {
        'accept': '*/*',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'priority': 'u=1, i',
        'referer': product_url,
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
    }

    product_id = headers['referer'].rsplit('-', 1)[-1]

    params_price = {
        'addBonusRubles': 'true',
        'isPromoApplied': 'true',
        'productIds': product_id,
    }

    try:
        async with aiohttp.ClientSession(cookies=cookies) as session:
            async with session.get('https://www.mvideo.ru/bff/products/prices', params=params_price,
                                   headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Ошибка при получении цены: {response.status}")
                    return None
                data_price = await response.json()

        product_price = data_price['body']['materialPrices'][0]['price']['salePrice']
        logger.info(f"Получена цена продукта: {product_price}")
        return product_price
    except Exception as e:
        logger.error(f"Ошибка при запросе цены: {e}")
        return None


# Функция для обновления информации о товаре
async def update_product_data():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(select(Product))
            products = result.scalars().all()

            for product in products:
                logger.info(f"Обработка товара: {product.url}")
                if product.name is None:
                    product_data = await get_product_data(product.url)
                    if product_data:
                        name, rating, description = product_data
                        price = await get_product_price(product.url)

                        # Обновление данных в базе
                        product.name = name
                        product.rating = rating
                        product.description = description
                        product.price = price

                        # Сохранение изменений
                        await db.commit()

                        # Сохранение истории цен
                        price_history = PriceHistory(product_id=product.id, price=price)
                        db.add(price_history)
                    else:
                        logger.warning(f"Не удалось получить данные для товара: {product.url}")
                else:
                    price = await get_product_price(product.url)
                    if price:
                        # Обновление данных в базе
                        product.price = price

                        # Сохранение изменений
                        await db.commit()

                        # Сохранение истории цен
                        price_history = PriceHistory(product_id=product.id, price=price)
                        db.add(price_history)
                    else:
                        logger.warning(f"Не удалось обновить цену для товара: {product.url}")

            await db.commit()
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных товара: {e}")


# Запуск планировщика
async def run_scheduler():
    await init_db()
    while True:
        try:
            await update_product_data()
            await asyncio.sleep(3600)  # Ждём 1 час перед следующим запуском
        except Exception as e:
            logger.error(f"Ошибка в планировщике: {e}")


if __name__ == "__main__":
    __config_logger()
    asyncio.run(run_scheduler())
