import sqlite3
import asyncio
import uuid
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from pyrogram.errors.exceptions.bad_request_400 import UserIsBlocked  # Импортируем исключение

api_id = 27237447
api_hash = '8caac0861f06f211c6c27ec00b98d33c'
bot_token = '7036230952:AAEYL9EsIy8oIJ4yTUdluI1ymjY3u9_wwIk'

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

admin_chat_id = 7048194752  # Замените на ID администратора

products = {
    "АНГАРСК": [],
    "ИРКУТСК": [],
    "УСОЛЬЕ-СИБИРСКОЕ": [],
    "ЗИМА": [],
    "САЯНСК": []
}
current_order = {}
pending_orders = {}

reviews = [
    {"author": "Saimon(peзерв)", "text": "РОВНЯГА МЭДЖИК 0,3 под камнем, без СОМНЕНИЙ и в КАСАНИЕ", "date": "11 июл", "city": "АНГАРСК"},
    {"author": "Саня", "text": "В касание 05 дом", "date": "10 июл", "city": "АНГАРСК"},
    {"author": "руский", "text": "Дома камень?", "date": "10 июл", "city": "АНГАРСК"},
    {"author": "nekiy", "text": "Забрал", "date": "10 июл", "city": "АНГАРСК"},
    {"author": "Ротобек", "text": "Привет всем) хорошо ложите, всё перекопано. Но я своё нашёл. Всё отлично👍👏😆", "date": "09 июл", "city": "АНГАРСК"},
    {"author": "Честный", "text": "Дома гусек👍", "date": "08 июл", "city": "АНГАРСК"},
    {"author": "Isconber", "text": "👍", "date": "06 июл", "city": "АНГАРСК"},
    {"author": "Надежда", "text": "Кач огонь", "date": "04 июл", "city": "АНГАРСК"},
    {"author": "Братан", "text": "На завтра нашел это лучший маркет!!!", "date": "01 июл", "city": "АНГАРСК"},
    {"author": "Вася", "text": "1г домашний", "date": "30 июн", "city": "АНГАРСК"},
    {"author": "vanesh", "text": "Кура гений ахахахах👌", "date": "26 июн", "city": "АНГАРСК"},
    {"author": "Кто Убил Билли", "text": "Клад в касуху еду пробывать", "date": "18 июн", "city": "АНГАРСК"},
    {"author": "vanesh", "text": "мефчик птичка в клетке гусь в духовки", "date": "25 июн", "city": "АНГАРСК"},
    {"author": "Вася", "text": "Саврик дома", "date": "03 июн", "city": "АНГАРСК"},
    {"author": "антигерой", "text": "грам кристалов поднятные", "date": "02 июн", "city": "АНГАРСК"},
    {"author": "Valentin", "text": "мэджик спс в кэс", "date": "19 мая", "city": "АНГАРСК"},
    {"author": "Марина", "text": "Бралa в первый раз, по адресу были сложности, но тех.поддержка быстро решила этот вопрос, после уточнения заветный свёрток был найден 🥲", "date": "05 мая", "city": "ИРКУТСК"},
    {"author": "Kasper84", "text": "Выпил и в касание снят. В городе.", "date": "30 апр", "city": "АНГАРСК"},
    {"author": "Alla", "text": "Далеко, но всё супер!", "date": "17 апр", "city": "АНГАРСК"},
    {"author": "Лёха", "text": "Далеко, но поднял в кэс, качество з6с!!!! от души.", "date": "03 апр", "city": "АНГАРСК"},
    {"author": "Lust", "text": "Родной камень дома 👍", "date": "01 апр", "city": "АНГАРСК"},
    {"author": "Dark", "text": "Первый раз берём в данном маркете. От покупки до подъёма 15 мин. Адрес поднят в кэс магнит городская локация. За качество отпишем завтра", "date": "21 мар", "city": "АНГАРСК"},
    {"author": "Kasper84", "text": "вип ск был обнаружен и обезврежен.", "date": "15 мар", "city": "АНГАРСК"},
    {"author": "Kasper84", "text": "Саврик домашний", "date": "12 мар", "city": "АНГАРСК"},
    {"author": "Думаю", "text": "Всё красиво 👍", "date": "07 мар", "city": "АНГАРСК"},
]

BTC_EXCHANGE_RATE = 2500000

# Инициализация базы данных
conn = sqlite3.connect('users.db', check_same_thread=False)
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS users
             (chat_id INTEGER PRIMARY KEY, user_id INTEGER)''')
c.execute('''CREATE TABLE IF NOT EXISTS purchases
             (user_id INTEGER, product_name TEXT, city TEXT, date TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS reviews
             (user_id INTEGER, review TEXT, author TEXT, date TEXT, city TEXT)''')

def get_user_id(chat_id):
    with conn:
        c.execute("SELECT user_id FROM users WHERE chat_id = ?", (chat_id,))
        row = c.fetchone()
        if row:
            return row[0]
        else:
            user_id = c.execute("SELECT COUNT(*) FROM users").fetchone()[0] + 1
            c.execute("INSERT INTO users (chat_id, user_id) VALUES (?, ?)", (chat_id, user_id))
            return user_id

def calculate_btc_amount(rub_amount):
    return rub_amount / BTC_EXCHANGE_RATE

async def notify_users(product):
    with conn:
        c.execute("SELECT chat_id FROM users")
        users = c.fetchall()
    for user in users:
        chat_id = user[0]
        message = (
            f"Город {product['city']} пополнен свежими {product['weight']} {product['name']} в районе {product['location']}.\n"
            f"Тип: {product['type']}\n"
            "Приятных покупок."
        )
        buttons = [
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        try:
            await app.send_message(chat_id, message, reply_markup=InlineKeyboardMarkup(buttons))
        except UserIsBlocked:
            print(f"Пользователь {chat_id} заблокировал бота. Сообщение не отправлено.")
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {chat_id}: {str(e)}")

@app.on_message(filters.command("start"))
async def start(client, message):
    chat_id = message.chat.id
    user_id = get_user_id(chat_id)
    buttons = [
        [InlineKeyboardButton("Начать покупки [В наличии]", callback_data="start_shopping")],
        [InlineKeyboardButton("Личный кабинет", callback_data="personal_account")],
        [InlineKeyboardButton("Проблемы с оплатой?", callback_data="payment_issues")],
        [InlineKeyboardButton(f"Отзывы клиентов [{len(reviews)}]", callback_data="customer_reviews")],
        [InlineKeyboardButton("Обновить страницу", callback_data="refresh_page")],
        [InlineKeyboardButton("Контакты магазина", callback_data="shop_contacts")],
        [InlineKeyboardButton("Швырокуры", url="https://t.me/+Zx3PQ4wedFA1OGUy")],
        [InlineKeyboardButton("Получил 50 рублей на счёт!", callback_data="get_bonus")],
        [InlineKeyboardButton("Людской ход", url="https://t.me/+Igh2MH5neNc2ЗDNk")],
        [InlineKeyboardButton("EPIC GROUP - Ровный чат РФ", url="https://t.me/+vWTGHDyhvP5mMTEx")],
        [InlineKeyboardButton("Анонимный фотохостинг", url="https://t.me/necroimg_bot")]
    ]
    await message.reply_text(
        f"Добро пожаловать в streetmagic38.\n"
        f"==============================\n"
        f"АНГАРСК - {('Есть наличие' if products['АНГАРСК'] else 'Пусто')}\n"
        f"Усолье-Сибирское - {('Есть наличие' if products['УСОЛЬЕ-СИБИРСКОЕ'] else 'Пусто')}\n"
        f"Зима - {('Есть наличие' if products['ЗИМА'] else 'Пусто')}\n"
        f"Саянск - {('Есть наличие' if products['САЯНСК'] else 'Пусто')}\n"
        f"Иркутск - {('Есть наличие' if products['ИРКУТСК'] else 'Пусто')}\n"
        f"==============================\n"
        f"О магазине:\n"
        f"Приветствую, маркет представляет витрину товара высочайшего качества\n"
        f"==============================\n"
        f"Ваш баланс: 0 рублей\n"
        f"Ваш ID внутри системы: {user_id}\n"
        f"Ваш CHAT-ID: {chat_id}\n"
        f"==============================\n"
        f"Скидки и акции: Отсутствуют",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_message(filters.command("admin") & filters.user(admin_chat_id))
async def admin_panel(client, message):
    await message.reply_text(
        "Админ панель\n"
        "Используйте команду /add_product <название>, <вес>, <район>, <тип>, <цена>, <город> для добавления товара.\n"
        "Используйте команду /delete_product <order_id> для удаления товара.\n"
        "Пример: /add_product Alphapvp, 1г, Центр, Тайник, 5000₽, АНГАРСК\n"
        "Пример: /delete_product 123e4567-e89b-12d3-a456-426614174000"
    )

@app.on_message(filters.command("add_product") & filters.user(admin_chat_id))
async def add_product(client, message: Message):
    try:
        _, product_info = message.text.split(" ", 1)
        name, weight, location, product_type, price, *city = map(str.strip, product_info.split(","))
        city = city[0].upper() if city else "АНГАРСК"
        if city not in products:
            await message.reply_text("Неверный формат. Город указан неправильно.")
            return
        order_id = str(uuid.uuid4())
        product = {"name": name, "weight": weight, "location": location, "type": product_type, "price": price, "order_id": order_id, "city": city}
        products[city].append(product)
        await message.reply_text(f"Товар {name} добавлен успешно в город {city}!")
        await notify_users(product)
        print(f"Добавлен товар: {name}, {weight}, {location}, {product_type}, {price}, {order_id}, {city}")  # Отладочное сообщение
    except ValueError:
        await message.reply_text("Неверный формат. Используйте /add_product <название>, <вес>, <район>, <тип>, <цена>, <город>")

@app.on_message(filters.command("delete_product") & filters.user(admin_chat_id))
async def delete_product(client, message: Message):
    try:
        _, order_id = message.text.split(" ", 1)
        order_id = order_id.strip()
        product_to_delete = None
        for city in products:
            product_to_delete = next((product for product in products[city] if product["order_id"] == order_id), None)
            if product_to_delete:
                products[city].remove(product_to_delete)
                break
        if product_to_delete:
            await message.reply_text(f"Товар с ID {order_id} удален успешно!")
            print(f"Удален товар: {product_to_delete['name']}, {product_to_delete['weight']}, {product_to_delete['location']}, {product_to_delete['price']}, {order_id}")  # Отладочное сообщение
        else:
            await message.reply_text(f"Товар с ID {order_id} не найден.")
    except ValueError:
        await message.reply_text("Неверный формат. Используйте /delete_product <order_id>")

@app.on_message(filters.command("confirm_payment") & filters.user(admin_chat_id))
async def confirm_payment(client, message: Message):
    try:
        _, order_id = message.text.split(" ", 1)
        order_id = order_id.strip()
        if order_id in pending_orders:
            chat_id = pending_orders[order_id]['chat_id']
            product = pending_orders[order_id]['product']
            location_url = "https://t.me/necroimg_bot?start=photo8e2ea538f92"  # замените на реальную ссылку на координаты товара
            await app.send_message(chat_id, f"Оплата подтверждена {location_url}")
            user_id = get_user_id(chat_id)
            with conn:
                c.execute("INSERT INTO purchases (user_id, product_name, city, date) VALUES (?, ?, ?, ?)", 
                          (user_id, product['name'], product['city'], datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            del pending_orders[order_id]
        else:
            await message.reply_text("Заказ с таким ID не найден.")
    except ValueError:
        await message.reply_text("Неверный формат. Используйте /confirm_payment <order_id>")

@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    global current_order
    data = callback_query.data
    chat_id = callback_query.message.chat.id
    user_id = get_user_id(chat_id)

    if data == "start_shopping":
        buttons = [
            [InlineKeyboardButton(f"г.АНГАРСК [{('Есть наличие' if products['АНГАРСК'] else 'Пусто')}] [Выбрать]", callback_data="choose_АНГАРСК")],
            [InlineKeyboardButton(f"г.ИРКУТСК [{('Есть наличие' if products['ИРКУТСК'] else 'Пусто')}] [Выбрать]", callback_data="choose_ИРКУТСК")],
            [InlineKeyboardButton(f"г.УСОЛЬЕ-СИБИРСКОЕ [{('Есть наличие' if products['УСОЛЬЕ-СИБИРСКОЕ'] else 'Пусто')}] [Выбрать]", callback_data="choose_УСОЛЬЕ-СИБИРСКОЕ")],
            [InlineKeyboardButton(f"г.ЗИМА [{('Есть наличие' if products['ЗИМА'] else 'Пусто')}] [Выбрать]", callback_data="choose_ЗИМА")],
            [InlineKeyboardButton(f"г.САЯНСК [{('Есть наличие' if products['САЯНСК'] else 'Пусто')}] [Выбрать]", callback_data="choose_САЯНСК")],
            [InlineKeyboardButton("Назад", callback_data="main_menu"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Оформление покупки\n"
            "==============================\n"
            "Выбери нужный город из наличия:\n",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data.startswith("choose_"):
        city = data.split("_")[1]
        product_buttons = [
            [InlineKeyboardButton(f"{p['name']} ({p['weight']}) за {p['price']}₽ [Выбрать]", callback_data=f"buy_{city}_{i}")]
            for i, p in enumerate(products[city])
        ]
        if not product_buttons:
            product_buttons.append([InlineKeyboardButton("Товаров нет", callback_data="no_products")])
        product_buttons.append([InlineKeyboardButton("Назад", callback_data="start_shopping"), InlineKeyboardButton("Главное меню", callback_data="main_menu")])
        await callback_query.message.edit_text(
            f"Оформление покупки\n"
            f"==============================\n"
            f"Город: {city}\n"
            f"==============================\n"
            f"Выберите нужный товар:",
            reply_markup=InlineKeyboardMarkup(product_buttons)
        )
    elif data.startswith("buy_"):
        _, city, product_index = data.split("_")
        product_index = int(product_index)
        product = products[city][product_index]
        current_order = {
            "product": product,
            "type": product["type"],
            "location": product["location"],
            "city": city
        }
        buttons = [
            [InlineKeyboardButton(f"Тип: {product['type']} [Выбрать]", callback_data=f"type_{city}_{product_index}_{product['type']}")],
            [InlineKeyboardButton("Назад", callback_data=f"choose_{city}"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            f"Оформление покупки\n"
            f"==============================\n"
            f"Город: {city}\n"
            f"Товар: {product['name']} ({product['weight']})\n"
            f"Описание товара: не указано\n"
            f"Выберите нужный тип клада:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data.startswith("type_"):
        _, city, product_index, product_type = data.split("_")
        product_index = int(product_index)  # Определение product_index
        current_order["type"] = product_type
        product = products[city][product_index]
        buttons = [
            [InlineKeyboardButton(f"р-н: {product['location']} [Выбрать]", callback_data=f"location_{city}_{product_index}_{product['location']}")],
            [InlineKeyboardButton("Назад", callback_data=f"buy_{city}_{product_index}"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            f"Оформление покупки\n"
            f"==============================\n"
            f"Город: {city}\n"
            f"Товар: {product['name']} ({product['weight']})\n"
            f"Тип клада: {product_type}\n"
            f"==============================\n"
            f"Выберите нужный район:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data.startswith("location_"):
        _, city, product_index, product_location = data.split("_")
        product_index = int(product_index)  # Определение product_index
        current_order["location"] = product_location
        buttons = [
            [InlineKeyboardButton("Всё понятно", callback_data="all_understood"), InlineKeyboardButton("Отменить заказ", callback_data="cancel_order")],
            [InlineKeyboardButton("Назад", callback_data=f"type_{city}_{product_index}_{current_order['type']}"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Правила магазина\n"
            "==============================\n"
            "перезакладов нет. Для решения, снимайте видео перед началом поисков, до того как дошли до места",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    elif data == "all_understood":
        product = current_order["product"]
        btc_amount = calculate_btc_amount(float(product["price"]))
        order_id = str(uuid.uuid4())
        pending_orders[order_id] = {"chat_id": chat_id, "product": product}

        # Уведомление администратора
        await app.send_message(admin_chat_id, f"Новый заказ:\n\nТовар: {product['name']} ({product['weight']})\nЦена: {product['price']}₽\nID заказа: {order_id}\n\nПодтвердите оплату командой /confirm_payment {order_id}")

        buttons = [
            [InlineKeyboardButton(f"Город: {current_order['city']} [изменить]", callback_data=f"choose_{current_order['city']}")],
            [InlineKeyboardButton(f"Товар: {product['name']} ({product['weight']}) [изменить]", callback_data=f"buy_{current_order['city']}_{products[current_order['city']].index(product)}")],
            [InlineKeyboardButton(f"Район: {current_order['location']} [изменить]", callback_data=f"location_{current_order['city']}_{products[current_order['city']].index(product)}_{current_order['location']}")],
            [InlineKeyboardButton(f"Тип клада: {current_order['type']} [изменить]", callback_data=f"type_{current_order['city']}_{products[current_order['city']].index(product)}_{current_order['type']}")],
            [InlineKeyboardButton(f"Оплатить {product['price']} [На карту]", callback_data="pay_card")],
            [InlineKeyboardButton(f"Оплатить {product['price']} [По СБП]", callback_data="pay_sbp")],
            [InlineKeyboardButton("Отменить заказ", callback_data="cancel_order")],
        ]
        await callback_query.message.edit_text(
            f"Финансовая инфа по заказу:\n"
            f"==============================\n"
            f"Баланс RUB: 0\n"
            f"Баланс BTC: 0.00000000\n"
            f"Баланс LTC: 0.00000000\n"
            f"==============================\n"
            f"Личная скидка: 0%\n"
            f"Общая скидка: 0%\n"
            f"Цена товара RUB: {product['price']}\n"
            f"Комиссия: 0%\n"
            f"==============================\n"
            f"Итого к оплате: {product['price']}\n"
            f"В Bitcoin: {btc_amount:.8f}\n"
            f"До отмены осталось: 49 мин.\n"
            f"ID заказа: {order_id}\n",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

        # Запуск таймера на 49 минут
        asyncio.create_task(order_timeout(order_id, callback_query.message))

    elif data == "cancel_order":
        current_order.clear()
        await callback_query.message.edit_text("Заказ был отменен.")

    elif data == "pay_card":
        product = current_order["product"]
        await display_payment_info(callback_query.message, product, "2200700457065448", "На карту")

    elif data == "pay_sbp":
        product = current_order["product"]
        await display_payment_info(callback_query.message, product, "2200700457065448", "По СБП")

    elif data == "card_and_amount":
        product = current_order["product"]
        await callback_query.message.reply_text(
            f"Реквизиты для оплаты:\n"
            f"Карта: 2200700457065448\n"
            f"Сумма к оплате: {product['price']} рублей"
        )

    elif data == "personal_account":
        chat_id = callback_query.message.chat.id
        user_id = get_user_id(chat_id)
        with conn:
            c.execute("SELECT COUNT(*) FROM purchases WHERE user_id = ?", (user_id,))
            purchases_count = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM reviews WHERE user_id = ?", (user_id,))
            reviews_count = c.fetchone()[0]
        buttons = [
            [InlineKeyboardButton("Список Ваших счетов", callback_data="account_list")],
            [InlineKeyboardButton(f"Список Ваших покупок [{purchases_count}]", callback_data="purchase_list")],
            [InlineKeyboardButton(f"Ваши отзывы [{reviews_count}]", callback_data="customer_reviews")],
            [InlineKeyboardButton("PIN-код блокировки бота: [Включить]", callback_data="pin_code")],
            [InlineKeyboardButton("Пополнить баланс", callback_data="top_up_balance")],
            [InlineKeyboardButton("Управление вашим ботом", callback_data="bot_management")],
            [InlineKeyboardButton("Обращения в поддержку [0]", callback_data="support_requests")],
            [InlineKeyboardButton("<< Вернуться на главную", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            f"Добро пожаловать в твой личный кабинет, выбери нужный пункт меню.\n"
            f"==============================\n"
            f"Ваш ID внутри системы: {user_id}\n"
            f"Ваш CHAT-ID: {chat_id}\n"
            f"==============================\n"
            f"Баланс RUB: 0\n"
            f"Баланс BTC: 0.00000000\n"
            f"Баланс LTC: 0.00000000\n"
            f"==============================\n"
            f"Покупок: {purchases_count}\n"
            f"Отзывы: {reviews_count}\n"
            f"Одобренных тикетов: 0\n"
            f"Отказанных тикетов: 0",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "account_list":
        buttons = [
            [InlineKeyboardButton("Назад", callback_data="personal_account"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Просмотр списка счетов\n"
            "==============================\n"
            "Здесь находится Ваша история платежей, так же здесь вы можете проверить истекшую, по времени, заявку.\n"
            "==============================\n"
            "Для проверки заявки, нажмите на нужную, далее нажмите проверить оплату",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "purchase_list":
        with conn:
            c.execute("SELECT product_name, city, date FROM purchases WHERE user_id = ?", (user_id,))
            purchases = c.fetchall()
        purchases_text = "\n".join([f"{purchase[0]} ({purchase[1]}) - {purchase[2]}" for purchase in purchases]) or "У вас ещё нет покупок."
        buttons = [
            [InlineKeyboardButton("Назад", callback_data="personal_account"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            f"Ваши последние покупки\n"
            "==============================\n"
            f"{purchases_text}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "top_up_balance":
        buttons = [
            [InlineKeyboardButton("Пополнить через VISA/MASTERCARD", callback_data="top_up_visa")],
            [InlineKeyboardButton("Пополнить через Litecoin", callback_data="top_up_litecoin")],
            [InlineKeyboardButton("Активировать купон", callback_data="activate_coupon")],
            [InlineKeyboardButton("Назад", callback_data="personal_account"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Пополнение личного баланса\n"
            "==============================\n"
            "Выберите удобный из доступных, способ пополнения баланса:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "bot_management":
        buttons = [
            [InlineKeyboardButton("Отменить", callback_data="personal_account"), InlineKeyboardButton("Продолжить", callback_data="continue_bot_management")]
        ]
        await callback_query.message.edit_text(
            "Твой неубиваемый бот от магазина streetmagic38.\n"
            "==============================\n"
            "1. Ты получаешь бонус за создание бота 50 руб. на баланс.\n"
            "2. Ты получаешь 5% на баланс, с каждого кто купит через твой бот.\n"
            "3. Ты всегда на связи со своим любимым магазином, т.к он только твой бот.\n"
            "==============================\n"
            "Больше не нужно бродить по чатам в поисках нового контакта нашего магазина, попадая на фейков и шаверщиков.\n"
            "==============================\n"
            "Шаг - 1: Создание бота.\n"
            "==============================\n"
            "Перейдите на этот аккаунт: @BotFather и нажмите или отправьте /start",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "support_requests":
        buttons = [
            [InlineKeyboardButton("Начать переписку", url="https://t.me/helpmagic1")],
            [InlineKeyboardButton("Назад", callback_data="personal_account"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Запросы в поддержку\n"
            "==============================\n"
            "Здесь находятся ваши активные и нет запросы в службу поддержки магазина.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "payment_issues":
        buttons = [
            [InlineKeyboardButton("Назад", callback_data="main_menu"), InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Проблемы с оплатой\n"
            "==============================\n"
            "1. Не ошибись в сумме, нажми на неё и она скопируется тебе в буфер, как и карта.\n"
            "2. Для твоего удобства, есть кнопка для выдачи тебе карты и суммы отдельными сообщениями.\n"
            "3. Если оплата не проходит более 40 минут, пишите оператору.\n"
            "4. По вопросам оплаты писать на Контакт: @helpmagic1",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "refresh_page":
        await callback_query.message.edit_text("Обновление страницы магазина...", reply_markup=callback_query.message.reply_markup)
        await callback_query.message.edit_text(
            f"Добро пожаловать в streetmagic38.\n"
            f"==============================\n"
            f"АНГАРСК - {('Есть наличие' if products['АНГАРСК'] else 'Пусто')}\n"
            f"Усолье-Сибирское - {('Есть наличие' if products['УСОЛЬЕ-СИБИРСКОЕ'] else 'Пусто')}\n"
            f"Зима - {('Есть наличие' if products['ЗИМА'] else 'Пусто')}\n"
            f"Саянск - {('Есть наличие' if products['САЯНСК'] else 'Пусто')}\n"
            f"Иркутск - {('Есть наличие' if products['ИРКУТСК'] else 'Пусто')}\n"
            f"==============================\n"
            f"О магазине:\n"
            f"Приветствую, маркет представляет витрину товара высочайшего качества\n"
            f"==============================\n"
            f"Ваш баланс: 0 рублей\n"
            f"Ваш ID внутри системы: {user_id}\n"
            f"Ваш CHAT-ID: {chat_id}\n"
            f"==============================\n"
            f"Скидки и акции: Отсутствуют",
            reply_markup=callback_query.message.reply_markup
        )

    elif data == "shop_contacts":
        buttons = [
            [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
        ]
        await callback_query.message.edit_text(
            "Контакты магазина:\n"
            "==============================\n"
            "Оператор: @helpmagic1\n"
            "==============================\n"
            "Бот: @magic138_bot\n"
            "==============================\n"
            "Второй бот: Не указано\n"
            "==============================\n"
            "Адрес сайта: не указано\n"
            "==============================\n"
            "Группа: Не указана ссылка на группу\n"
            "==============================\n"
            "Канал: https://t.me/+PjE_YOlRQz0zMGQ0",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "get_bonus":
        buttons = [
            [InlineKeyboardButton("Отменить", callback_data="personal_account"), InlineKeyboardButton("Продолжить", callback_data="continue_get_bonus")]
        ]
        await callback_query.message.edit_text(
            "Твой неубиваемый бот от магазина streetmagic38.\n"
            "==============================\n"
            "1. Ты получаешь бонус за создание бота 50 руб. на баланс.\n"
            "2. Ты получаешь 5% на баланс, с каждого кто купит через твой бот.\n"
            "3. Ты всегда на связи со своим любимым магазином, т.к он только твой бот.\n"
            "==============================\n"
            "Больше не нужно бродить по чатам в поисках нового контакта нашего магазина, попадая на фейков и шаверщиков.\n"
            "==============================\n"
            "Шаг - 1: Создание бота.\n"
            "==============================\n"
            "Перейдите на этот аккаунт: @BotFather и нажмите или отправьте /start",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "main_menu":
        buttons = [
            [InlineKeyboardButton("Начать покупки [В наличии]", callback_data="start_shopping")],
            [InlineKeyboardButton("Личный кабинет", callback_data="personal_account")],
            [InlineKeyboardButton("Проблемы с оплатой?", callback_data="payment_issues")],
            [InlineKeyboardButton(f"Отзывы клиентов [{len(reviews)}]", callback_data="customer_reviews")],
            [InlineKeyboardButton("Обновить страницу", callback_data="refresh_page")],
            [InlineKeyboardButton("Контакты магазина", callback_data="shop_contacts")],
            [InlineKeyboardButton("Швырокуры", url="https://t.me/+Zx3PQ4wedFA1OGUy")],
            [InlineKeyboardButton("Получил 50 рублей на счёт!", callback_data="get_bonus")],
            [InlineKeyboardButton("Людской ход", url="https://t.me/+Igh2MH5neNc2ЗDNk")],
            [InlineKeyboardButton("EPIC GROUP - Ровный чат РФ", url="https://t.me/+vWTGHDyhvP5mMTEx")],
            [InlineKeyboardButton("Анонимный фотохостинг", url="https://t.me/necroimg_bot")]
        ]
        await callback_query.message.edit_text(
            f"Добро пожаловать в streetmagic38.\n"
            f"==============================\n"
            f"АНГАРСК - {('Есть наличие' if products['АНГАРСК'] else 'Пусто')}\n"
            f"Усолье-Сибирское - {('Есть наличие' if products['УСОЛЬЕ-СИБИРСКОЕ'] else 'Пусто')}\n"
            f"Зима - {('Есть наличие' if products['ЗИМА'] else 'Пусто')}\n"
            f"Саянск - {('Есть наличие' if products['САЯНСК'] else 'Пусто')}\n"
            f"Иркутск - {('Есть наличие' if products['ИРКУТСК'] else 'Пусто')}\n"
            f"==============================\n"
            f"О магазине:\n"
            f"Приветствую, маркет представляет витрину товара высочайшего качества\n"
            f"==============================\n"
            f"Ваш баланс: 0 рублей\n"
            f"Ваш ID внутри системы: {user_id}\n"
            f"Ваш CHAT-ID: {chat_id}\n"
            f"==============================\n"
            f"Скидки и акции: Отсутствуют",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data == "customer_reviews":
        await show_review(client, callback_query.message, 0, user_id)

    elif data.startswith("prev_review_"):
        index = int(data.split("_")[2])
        await show_review(client, callback_query.message, index - 1, user_id)

    elif data.startswith("next_review_"):
        index = int(data.split("_")[2])
        await show_review(client, callback_query.message, index + 1, user_id)

    elif data == "add_review":
        with conn:
            c.execute("SELECT COUNT(*) FROM reviews WHERE user_id = ?", (user_id,))
            review_count = c.fetchone()[0]
        if review_count < 1:
            await callback_query.message.edit_text(
                "Введите ваш отзыв:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Отмена", callback_data="customer_reviews")]])
            )
        else:
            await callback_query.message.edit_text("Вы уже оставили отзыв для этой покупки.")

    elif data == "check_payment":
        await check_payment_status(callback_query.message)

    elif data == "payment_help":
        await callback_query.message.edit_text(
            "1. Не ошибись в сумме, нажми на неё и она скопируется тебе в буфер, как и карта.\n"
            "2. Для твоего удобства, есть кнопка для выдачи тебе карты и суммы отдельными сообщениями.\n"
            "3. Если оплата не проходит более 40 минут, пишите оператору.\n"
            "4. По вопросам оплаты писать на Контакт: @helpmagic1",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Вернуться к заявке", callback_data="return_to_order")]
            ])
        )

    elif data == "return_to_order":
        await check_payment_status(callback_query.message)

async def order_timeout(order_id, message):
    await asyncio.sleep(49 * 60)
    if order_id in pending_orders:
        await app.send_message(pending_orders[order_id]['chat_id'], "Заказ был отменен.")
        del pending_orders[order_id]

async def check_payment_status(message):
    product = current_order.get("product", {})
    card_number = "2200700457065448"
    buttons = [
        [InlineKeyboardButton("Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton("Карта и сумма отдельно", callback_data="card_and_amount")],
        [InlineKeyboardButton("Помощь и информация по оплате", callback_data="payment_help")]
    ]

    for remaining_minutes in range(49, -1, -1):
        btc_amount = calculate_btc_amount(float(product.get('price', 0)))
        await message.edit_text(
            f"Активный заказ.\n"
            f"==============================\n"
            f"Товар: {product.get('name', 'Неизвестно')} ({product.get('weight', 'Неизвестно')})\n"
            f"Город: {current_order.get('city', 'Неизвестно')}\n"
            f"Район: {current_order.get('location', 'Неизвестно')}\n"
            f"Тип клада: {current_order.get('type', 'Неизвестно')}\n"
            f"==============================\n"
            f"Номер заказа: {product.get('order_id', 'Неизвестно')}\n"
            f"Карта для оплаты: {card_number}\n"
            f"Сумма к оплате: {product.get('price', 'Неизвестно')} рублей\n"
            f"==============================\n"
            f"ВНИМАТЕЛЬНО проверьте сумму заказа, оплатили не точную сумму - оплатили чужой заказ.\n"
            f"Ожидаем твою оплату {product.get('price', 'Неизвестно')} рублей.\n"
            f"В Bitcoin: {btc_amount:.8f}\n"
            f"До отмены осталось: {remaining_minutes} мин.\n",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        await asyncio.sleep(60)

async def display_payment_info(message, product, card_number, payment_method):
    buttons = [
        [InlineKeyboardButton("Проверить оплату", callback_data="check_payment")],
        [InlineKeyboardButton("Карта и сумма отдельно", callback_data="card_and_amount")],
        [InlineKeyboardButton("Помощь и информация по оплате", callback_data="payment_help")]
    ]
    btc_amount = calculate_btc_amount(float(product['price']))
    await message.edit_text(
        f"Активный заказ.\n"
        f"==============================\n"
        f"Товар: {product['name']} ({product['weight']})\n"
        f"Город: {product['city']}\n"
        f"Район: {product['location']}\n"
        f"Тип клада: {product['type']}\n"
        f"==============================\n"
        f"Номер заказа: {product['order_id']}\n"
        f"Карта для оплаты: {card_number}\n"
        f"Сумма к оплате: {product['price']} рублей\n"
        f"==============================\n"
        f"ВНИМАТЕЛЬНО проверьте сумму заказа, оплатили не точную сумму - оплатили чужой заказ.\n"
        f"Ожидаем твою оплату {product['price']} рублей.\n"
        f"В Bitcoin: {btc_amount:.8f}\n"
        f"До отмены осталось: 49 мин.\n",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def show_review(client, message, index, user_id):
    if index < 0:
        index = 0
    if index >= len(reviews):
        index = len(reviews) - 1
    review = reviews[index]
    with conn:
        c.execute("SELECT review, author, date, city FROM reviews WHERE user_id = ?", (user_id,))
        user_reviews = c.fetchall()
    user_reviews_text = "\n\n".join([f"{ur[1]}: {ur[0]} ({ur[3]}, {ur[2]})" for ur in user_reviews])
    text = (
        f"Отзывы и трипы магазина\n"
        f"==============================\n"
        f"Пишет {review['author']}:\n"
        f"{review['text']}\n"
        f"==============================\n"
        f"Отзыв написан {review['date']}, {review['city']}\n\n"
        f"{user_reviews_text}"
    )
    buttons = [
        [InlineKeyboardButton("<<", callback_data=f"prev_review_{index}"), InlineKeyboardButton(f"{index + 1} из {len(reviews)}", callback_data="ignore"), InlineKeyboardButton(">>", callback_data=f"next_review_{index}")],
        [InlineKeyboardButton("Добавить новый отзыв", callback_data="add_review")],
        [InlineKeyboardButton("Главное меню", callback_data="main_menu")]
    ]
    await message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_message(filters.text & filters.user(admin_chat_id))
async def add_user_review(client, message):
    chat_id = message.chat.id
    user_id = get_user_id(chat_id)
    review_text = message.text
    purchase_exists = c.execute("SELECT EXISTS(SELECT 1 FROM purchases WHERE user_id=?)", (user_id,)).fetchone()[0]
    if purchase_exists:
        product = c.execute("SELECT product_name, city FROM purchases WHERE user_id=?", (user_id,)).fetchone()
        review = {"author": "User", "text": review_text, "date": datetime.now().strftime('%d %b'), "city": product[1]}
        reviews.append(review)
        with conn:
            c.execute("INSERT INTO reviews (user_id, review, author, date, city) VALUES (?, ?, ?, ?, ?)", 
                      (user_id, review_text, "User", datetime.now().strftime('%d %b'), product[1]))
        await message.reply_text("Ваш отзыв успешно добавлен!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Вернуться к отзывам", callback_data="customer_reviews")]]))
    else:
        await message.reply_text("Вы не можете оставить отзыв без покупки.")

if __name__ == "__main__":
    app.run()