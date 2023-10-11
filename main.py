import telebot
from telebot import types
import settings
import sqlite3
import random
import time
import threading
import re
from datetime import datetime
bot = telebot.TeleBot(settings.TOKEN)
    


# Создание блокировки для работы с базой данных из разных потоков
db_lock = threading.Lock()

# Словарь для хранения активных игр
active_games = {}

# Словарь для хранения баланса пользователей
user_balances = {}

# Функция для обновления меню
def update_menu_markup(chat_id, user_status):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    
    if user_status == "Пользователь":
        item1 = types.KeyboardButton("Играть 🎰")
        item2 = types.KeyboardButton("Кошелек 💰")
        item3 = types.KeyboardButton("Профиль 🪪")
        item4 = types.KeyboardButton("Помощь ℹ️")
        
        markup.add(item1, item2, item3, item4)
        
        # Проверяем, является ли пользователь администратором и добавляем кнопку "Админ Панель" при необходимости
        user_id = chat_id
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        user_info = cursor.fetchone()

        if user_info and user_info[3] == "Администратор":
            admin_panel_button = types.KeyboardButton("Админ Панель 🛠")
            markup.add(admin_panel_button)
        
        conn.close()
    else:
        item1 = types.KeyboardButton("Назад ⬅️")  # Добавляем кнопку "Назад"
        markup.add(item1)
    
    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Глобальная переменная для хранения статусов пользователей
user_status = {}

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    user_id = message.from_user.id
    add_user_to_database(user_id, message)  # Передаем объект сообщения для получения информации о пользователе
    
    # Проверяем тип чата
    if message.chat.type == 'private':
        buttons = [
            types.KeyboardButton("Играть 🎰"),
            types.KeyboardButton("Кошелек 💰"),
            types.KeyboardButton("Профиль 🪪"),
            types.KeyboardButton("Помощь ℹ️")
        ]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(*buttons)
        bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
        
        # Устанавливаем статус пользователя "Пользователь"
        user_status[user_id] = "Пользователь"
    else:
        bot.send_message(message.chat.id, "Приветствую! Чтобы начать игру, напишите /game.")

# Обработчик кнопки "Назад"
@bot.message_handler(func=lambda message: message.text == "Назад ⬅️")
def go_back_to_menu(message):
    user_id = message.from_user.id
    user_status.setdefault(user_id, "Пользователь")  # Устанавливаем статус по умолчанию

    # Проверяем тип чата
    if message.chat.type == 'private':
        if user_status[user_id] == "Администратор":
            update_menu_markup(message.chat.id, "Администратор")  # Обновляем меню для администраторов
        else:
            update_menu_markup(message.chat.id, "Пользователь")  # Обновляем меню для пользователей
    else:
        bot.send_message(message.chat.id, "Кнопка 'Назад ⬅️' доступна только в личном чате с ботом.")








# Обработчик кнопки "Играть 🎰" в игровых чатах
@bot.message_handler(func=lambda message: message.text == "Играть 🎰" and message.chat.type != 'private')
def handle_play_in_game_chat(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Вы можете использовать команду /game для начала игры.")

# Обработчик кнопки "Играть 🎰" в личных чатах
@bot.message_handler(func=lambda message: message.text == "Играть 🎰" and message.chat.type == 'private')
def handle_play_in_private(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    bot.send_message(chat_id, "🎰Начать играть🎰\nhttps://t.me/+fYWDIZW__DFhYWVi")


conn = sqlite3.connect('database.db')
cursor = conn.cursor()

import sqlite3

# Функция для получения баланса пользователя из базы данных
def get_user_balance(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id=?", (user_id,))
    user_balance = cursor.fetchone()
    conn.close()
    return user_balance[0] if user_balance else 0.0

# Функция для обновления баланса пользователя в базе данных
def update_user_balance(user_id, new_balance):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET balance=? WHERE user_id=?", (new_balance, user_id))
    conn.commit()
    conn.close()

# Обработчик команды /game
@bot.message_handler(commands=['game'], func=lambda message: message.chat.type != 'private')
def start_game_with_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Проверяем синтаксис команды
    match = re.match(r"/game (\d+)$", message.text)
    if not match:
        bot.send_message(chat_id, "Для создания игры укажите ставку в виде команды `/game [ставка]`, например, `/game 100`.")
        return

    bet = int(match.group(1))
    user_balance = get_user_balance(user_id)

    if user_balance < bet:
        bot.send_message(chat_id, "У вас недостаточно средств для этой ставки.")
        return

    # Снимаем ставку с баланса пользователя
    new_balance = user_balance - bet
    update_user_balance(user_id, new_balance)

    game_id = f'game_{random.randint(1000, 9999)}'
    markup = types.InlineKeyboardMarkup()
    join_button = types.InlineKeyboardButton("Присоединиться", callback_data=game_id)
    markup.add(join_button)

    # Добавляем кнопку "Отмена" только для создателя игры
    if game_id in active_games and message.from_user.id == active_games[game_id]["creator_id"]:
        cancel_button = types.InlineKeyboardButton("Отмена", callback_data=f'cancel_{game_id}')
        markup.add(cancel_button)

    # Создаем сообщение о начале игры
    game_info_message = f"• Игрок @{message.from_user.username} создал запрос на игру 💸\n\n" \
                        f"• Игра: Кости🎲\n" \
                        f"• Ставка: {bet} 🪙\n" \
                        f"• Время создания игры: {time.strftime('%H:%M:%S', time.localtime())} 🕐"
    message = bot.send_message(chat_id, game_info_message, reply_markup=markup)

    active_games[game_id] = {"creator_id": user_id, "bet": bet, "canceled": False, "message_id": message.message_id}

@bot.callback_query_handler(func=lambda call: call.data.startswith('game_'))
def join_game(call):
    user_id = call.from_user.id
    game_id = call.data
    chat_id = call.message.chat.id

    if game_id in active_games:
        if active_games[game_id]["creator_id"] != user_id:
            # Удаление инлайн-кнопки после присоединения
            bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)

            # Начать игру
            player1_bet = active_games[game_id]["bet"]
            player2_bet = active_games[game_id]["bet"]

            # Сгенерировать числа для игроков (от 1 до 6)
            player1_roll = random.randint(1, 6)
            player2_roll = random.randint(1, 6)

            # Определить победителя
            if player1_roll > player2_roll:
                winner = f"Игрок @{active_games[game_id]['creator_id']} 🏆"
            elif player1_roll < player2_roll:
                winner = f"Игрок @{user_id} 🏆"
            else:
                winner = "Ничья"

            # Рассчитать выигрыш
            if winner == f"Игрок @{active_games[game_id]['creator_id']} 🏆":
                prize = int((player1_bet + player2_bet) * 0.95)
                new_balance_creator = get_user_balance(active_games[game_id]["creator_id"]) + prize
                update_user_balance(active_games[game_id]["creator_id"], new_balance_creator)
                new_balance = get_user_balance(user_id) - player1_bet
                update_user_balance(user_id, new_balance)
            elif winner == f"Игрок @{user_id} 🏆":
                prize = int((player1_bet + player2_bet) * 0.95)
                new_balance = get_user_balance(user_id) + prize
                update_user_balance(user_id, new_balance)
                new_balance_creator = get_user_balance(active_games[game_id]["creator_id"]) - player1_bet
                update_user_balance(active_games[game_id]["creator_id"], new_balance_creator)
            else:
                prize = 0

            # Отправить результат игры
            bot.send_message(chat_id, f"Игрок @{active_games[game_id]['creator_id']} выбросил {player1_roll}\n"
                                      f"Игрок @{user_id} выбросил {player2_roll}\n\n"
                                      f"Результат игры: {winner}\n"
                                      f"Выигрыш: {prize:.2f} 🪙")

            # Удалить игру из активных игр
            del active_games[game_id]
        else:
            bot.send_message(chat_id, "Вы не можете присоединиться к своей собственной игре.")
    else:
        bot.send_message(chat_id, "Игра не найдена. Возможно, она уже завершена.")

# Функция для получения информации о кошельке пользователя из базы данных
def get_wallet_info(user_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()
    conn.close()
    
    if user_info:
        id, user_id, username, first_name, last_name, chat_id, balance, status = user_info
        return {
            "username": username or "N/A",
            "id": user_id,
            "balance": balance,
            "status": status
        }
    else:
        return None

# Обработчик кнопки "Кошелек 💰"
# Обработчик кнопки "Кошелек 💰"
@bot.message_handler(func=lambda message: message.text == "Кошелек 💰")
def handle_wallet_menu(message):
    user_id = message.from_user.id
    
    # Получаем информацию о кошельке пользователя из базы данных
    wallet_info = get_wallet_info(user_id)
    
    if wallet_info:
        # Создаем клавиатуру с кнопками для меню "Кошелек"
        wallet_markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        deposit_button = types.KeyboardButton("Пополнить 💳")
        withdraw_button = types.KeyboardButton("Вывести 💸")
        transfer_button = types.KeyboardButton("Перевести 🔄")
        promo_code_button = types.KeyboardButton("Промокод 🎁")
        back_button = types.KeyboardButton("Назад ⬅️")
        
        wallet_markup.row(deposit_button, withdraw_button)
        wallet_markup.row(transfer_button, promo_code_button)
        wallet_markup.row(back_button)
        
        # Формируем сообщение с информацией о кошельке
        wallet_message = f"💰 Кошелек пользователя:\n\n"
        wallet_message += f"📛 Имя: @{wallet_info['username']} \n"
        wallet_message += f"🆔 ID: {wallet_info['id']}\n"
        wallet_message += f"💰 Баланс: {wallet_info['balance']} 🪙\n"
        
        # Отправляем сообщение с информацией о кошельке и клавиатурой
        bot.send_message(user_id, wallet_message, reply_markup=wallet_markup)
    else:
        bot.send_message(user_id, "Информация о кошельке не найдена. Пожалуйста, начните с команды /start.")

























# Функция для создания отдельного объекта cursor для каждого потока
def get_cursor():
    conn = sqlite3.connect('database.db')
    return conn.cursor()
def copy_admins_from_users():
    cursor = get_cursor()
    cursor.execute("SELECT user_id, username, first_name, last_name FROM users WHERE status='Администратор'")
    admins = cursor.fetchall()
    
    for admin in admins:
        # Вставляем данные пользователя в таблицу "admins"
        cursor.execute("INSERT OR IGNORE INTO admins (user_id, username, first_name, last_name) VALUES (?, ?, ?, ?)",
                       admin)
    
    cursor.connection.commit()
    cursor.connection.close()



# Запустите функцию для копирования администраторов
copy_admins_from_users()

# Обработчик команды "Пополнить 💳"
@bot.message_handler(func=lambda message: message.text == "Пополнить 💳")
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Sweat Wallet 🪙", callback_data="sweat_wallet"))
    bot.send_message(message.chat.id, "Выберите метод оплаты:", reply_markup=markup)
    bot.register_next_step_handler(message, enter_amount)  # Регистрируем следующий шаг здесь




def get_admins():
    cursor = get_cursor()
    cursor.execute("SELECT user_id FROM admins")
    admin_ids = cursor.fetchall()
    cursor.connection.close()
    return admin_ids

# Словарь для хранения текущих шагов пользователей
user_steps = {}

@bot.callback_query_handler(func=lambda call: call.data == "sweat_wallet")
def sweat_wallet_selected(call):
    bot.send_message(call.message.chat.id, "Выбран способ оплаты: Sweat Wallet🪙\nВведите сумму пополнения💸")

    # Сохраняем текущий шаг пользователя
    user_id = call.message.chat.id
    user_steps[user_id] = "enter_amount"

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: user_steps.get(message.chat.id) == "enter_amount")
def enter_amount(message):
    user_id = message.chat.id

    try:
        amount = float(message.text)

        # Здесь вы можете сохранить сумму и статус в базе данных
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO deposit (user_id, amount, status) VALUES (?, ?, ?)", (user_id, amount, 'Ожидание'))
        conn.commit()
        conn.close()

        user_steps[user_id] = "wait_for_receipt"  # Устанавливаем следующий шаг
        instructions = """• Заходите в ваш кошелек sweat walletℹ️\n• Слева по середине кнопка(transfer)ℹ️\n• Кнопка send в пункте transfer ℹ️\n• Выбор монет, выбираете первый пункт (sweat)ℹ️\n• Окно с поиском никнеймаℹ️\nНик для отправки👇\n\n(Позже)\n• После отправки прикрепите чек для подтверждения пополнения балансаℹ️\n ❗️На случай проблемы пополнения обращайтесь в поддержку❗️"""
        bot.send_message(user_id, instructions)
        bot.send_message(user_id, "Пожалуйста, отправьте фото чека оплаты.")
    except ValueError:
        bot.send_message(user_id, "Пожалуйста, введите сумму пополнения в числовом формате.")

# Обработчик фото
@bot.message_handler(content_types=['photo'], func=lambda message: user_steps.get(message.chat.id) == "wait_for_receipt")
def process_receipt(message):
    user_id = message.chat.id
    admin_ids = get_admins()
    user_info = f"Пользователь - {user_id} ({message.from_user.username})"

    # Получим ID заказа и сумму из вашей базы данных
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, amount FROM deposit WHERE user_id = ? ORDER BY id DESC LIMIT 1", (user_id,))
    last_order = cursor.fetchone()
    conn.close()

    if last_order:
        order_id, order_amount = last_order
        bot.send_message(user_id, f"Ваш заказ №{order_id} на сумму {order_amount} 🪙 был принят в обработку.\nОжидайте дальнейших уведомлений.")
    else:
        bot.send_message(user_id, "Ваш заказ был принят в обработку. Ожидайте дальнейших уведомлений.")

    message_text = f"Новый запрос на пополнение!\nID заказа - {order_id}\nСумма - {order_amount}\n{user_info}"

    # Создаем инлайн клавиатуру с кнопками "Принять" и "Отклонить"
    markup = types.InlineKeyboardMarkup()
    accept_button = types.InlineKeyboardButton("Принять", callback_data=f"accept_order:{order_id}")
    reject_button = types.InlineKeyboardButton("Отклонить", callback_data=f"reject_order:{order_id}")
    markup.add(accept_button, reject_button)

    for admin_id in admin_ids:
        bot.forward_message(admin_id[0], user_id, message.message_id)
        bot.send_message(admin_id[0], message_text, reply_markup=markup)

    # Сбрасываем текущий шаг
    user_steps[user_id] = None
# Функция для обновления баланса пользователя
def update_user_balance(user_id, amount):
    # Получите текущий баланс пользователя из базы данных
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    current_balance = cursor.fetchone()

    if current_balance is not None:
        current_balance = current_balance[0]
        new_balance = current_balance + amount

        # Обновите баланс пользователя в базе данных
        cursor.execute("UPDATE users SET balance = ? WHERE user_id = ?", (new_balance, user_id))
        conn.commit()

    conn.close()

# Обработчик инлайн кнопки "Принять" для админов
@bot.callback_query_handler(lambda call: call.data.startswith('accept_order:'))
def accept_order(call):
    # Извлечь ID заказа из данных колбэка
    order_id = int(call.data.split(':')[1])

    # Получить информацию о заказе из базы данных
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount, status FROM deposit WHERE id = ?", (order_id,))
    order_info = cursor.fetchone()

    if order_info:
        user_id, amount, status = order_info

        # Проверьте статус заказа
        if status == 'Ожидание':
            # Увеличьте баланс пользователя на сумму пополнения
            update_user_balance(user_id, amount)

            # Обновите статус заказа в базе данных
            cursor.execute("UPDATE deposit SET status = 'Принят' WHERE id = ?", (order_id,))
            conn.commit()

            # Отправить уведомление пользователю о пополнении баланса и статусе заказа
            bot.send_message(user_id, f"✅ Ваш баланс пополнен ✅\n💸 Сумма пополнения: {amount} 🪙\n\n🎰 [Приступить к игре](https://t.me/+fYWDIZW__DFhYWVi)", parse_mode="Markdown")

            # Отправьте админу подтверждение принятия заказа
            bot.answer_callback_query(call.id, text="Заказ принят!")
        elif status == 'Принят':
            # Отправьте админу уведомление, что заказ уже был обработан
            bot.answer_callback_query(call.id, text="Данный заказ не действителен. Заказ был ранее принят.")
        elif status == 'Отклонен':
            bot.answer_callback_query(call.id, text="Данный заказ не действителен. Заказ был ранее отклонен.")
        else:
            bot.answer_callback_query(call.id, text="Данный заказ не действителен, отсутствует в базе.")
    
    conn.close()



# Обработчик для кнопки "Отклонить" для админов
@bot.callback_query_handler(lambda call: call.data.startswith('reject_order:'))
def reject_order(call):
    # Извлечь ID заказа из данных колбэка
    order_id = int(call.data.split(':')[1])

    # Получить информацию о заказе из базы данных
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, amount FROM deposit WHERE id = ?", (order_id,))
    order_info = cursor.fetchone()

    if order_info:
        user_id, amount = order_info

        # Обновите статус заказа в базе данных
        cursor.execute("UPDATE deposit SET status = 'Отклонен' WHERE id = ?", (order_id,))
        conn.commit()

        # Сообщение для пользователя
        message_to_user = f"❌ Ваш платеж отклонен ❌\nНомер заказа: {order_id}\nСумма заказа: {amount} 🪙\n\n•Для детальной информации обратитесь @тех.поддержка❗️"

        # Отправить уведомление пользователю
        bot.send_message(user_id, message_to_user, parse_mode="Markdown")

    # Закрываем соединение с базой данных
    conn.close()



# Обработчик команды /create_promocode
@bot.message_handler(commands=['create_promocode'])
def create_promocode(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь администратором
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[7] == "Администратор":  # Проверяем статус пользователя
        # Попросим пользователя ввести промокод
        bot.send_message(chat_id, "Введите промокод:")
        bot.register_next_step_handler(message, process_promocode_step)
    else:
        bot.send_message(chat_id, "У вас нет доступа к этой команде.")

    conn.close()

# Функция для обработки введенного промокода
def process_promocode_step(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    promocode = message.text
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Здесь вы можете запросить у администратора другие параметры промокода, такие как reward, expiration_date, max_activations и т. д.

    # Добавьте код для создания промокода в базе данных с введенными параметрами
    # Например, вы можете спросить у админа о reward и дате окончания, а также о максимальном количестве активаций

    # Ваш код для запроса других параметров промокода здесь

    bot.send_message(chat_id, "Введите количество награды (например, 100):")
    bot.register_next_step_handler(message, process_reward_step, promocode)

# Функция для обработки введенной награды
def process_reward_step(message, promocode):
    user_id = message.from_user.id
    chat_id = message.chat.id
    reward = message.text
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        reward = int(reward)

        # Ваш код для запроса других параметров промокода здесь

        bot.send_message(chat_id, "Введите дату окончания действия промокода (в формате ГГГГ-ММ-ДД):")
        bot.register_next_step_handler(message, process_expiration_date_step, promocode, reward)
    except ValueError:
        bot.send_message(chat_id, "Награда должна быть целым числом. Попробуйте снова.")

# Функция для обработки введенной даты окончания действия
def process_expiration_date_step(message, promocode, reward):
    user_id = message.from_user.id
    chat_id = message.chat.id
    expiration_date = message.text
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Добавьте здесь код для запроса других параметров промокода, если это необходимо

    bot.send_message(chat_id, "Введите максимальное количество активаций (если неограничено, оставьте пустым):")
    bot.register_next_step_handler(message, process_max_activations_step, promocode, reward, expiration_date)

# Функция для обработки введенного максимального количества активаций
def process_max_activations_step(message, promocode, reward, expiration_date):
    user_id = message.from_user.id
    chat_id = message.chat.id
    max_activations_str = message.text
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Если max_activations_str пуст, установите значение в None (неограниченное количество активаций)
    max_activations = None if not max_activations_str else int(max_activations_str)

    # Теперь у вас есть все параметры промокода
    # Добавьте код для создания промокода в базе данных с введенными параметрами

    # Пример добавления записи в базу данных
    cursor.execute("INSERT INTO promocodes (code, reward, expiration_date, max_activations, current_activations) VALUES (?, ?, ?, ?, 0)", (promocode, reward, expiration_date, max_activations))
    conn.commit()

    bot.send_message(chat_id, f"Промокод '{promocode}' успешно создан. Награда: {reward}, Срок действия: {expiration_date}, Максимальное количество активаций: {max_activations if max_activations else 'неограничено'}.")










































# Обработчик инлайн-кнопки "Отмена"
@bot.callback_query_handler(func=lambda call: call.data.startswith('cancel_'))
def cancel_game(call):
    user_id = call.from_user.id
    game_id = call.data.replace('cancel_', '')
    chat_id = call.message.chat.id

    if game_id in active_games and active_games[game_id]["creator_id"] == user_id and not active_games[game_id]["canceled"]:
        # Возвращаем 95% ставки создателю игры
        bet = active_games[game_id]["bet"]
        prize = bet * 0.95
        new_balance = get_user_balance(user_id) + prize
        update_user_balance(user_id, new_balance)
        
        # Удаляем игру и помечаем как отмененную
        active_games[game_id]["canceled"] = True
        del active_games[game_id]

        # Удаляем кнопку "Отмена"
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=None)
        bot.send_message(chat_id, f"Игра была отменена, и вам возвращено {prize:.2f} 🪙.")
    else:
        bot.send_message(chat_id, "Вы не можете отменить эту игру.")

# Закрываем соединение с базой данных
conn.close()


# Функция для добавления пользователя в базу данных
def add_user_to_database(user_id, message):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Получаем информацию о пользователе с помощью API Telegram
    user = message.from_user
    user_id = user.id
    first_name = user.first_name
    last_name = user.last_name
    username = user.username if user.username else ""
    
    # Определяем тип чата
    chat_id = "personal" if message.chat.type == 'private' else "group"
    
    # Проверяем, есть ли пользователь уже в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()
    
    if existing_user is None:
        # Если пользователь отсутствует в базе данных, добавляем его со стандартными значениями
        cursor.execute("INSERT INTO users (user_id, first_name, last_name, username, chat_id, balance, status) VALUES (?, ?, ?, ?, ?, 0, 'Пользователь')", (user_id, first_name, last_name, username, chat_id))
        conn.commit()
    
    conn.close()


"""# Функция добавления пользователя в базу данных
def add_user_to_database(user_id, status):
    with db_lock:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO users (user_id, status) VALUES (?, ?)", (user_id, status))
        conn.commit()
        conn.close()



# Функция для добавления пользователя в базу данных
def add_user_to_database(user_id, username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Проверяем, есть ли пользователь в базе данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    existing_user = cursor.fetchone()
    
    if existing_user is None:
        # Если пользователь отсутствует в базе данных, добавляем его со стандартными значениями
        cursor.execute("INSERT INTO users (user_id, username, balance, status) VALUES (?, ?, 0, 'Пользователь')", (user_id, username))
        conn.commit()
    
    conn.close()

"""

# Обработчик команды /admin
@bot.message_handler(commands=['admin'])
def admin_panel(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь администратором
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[7] == "Администратор":  # Проверяем статус пользователя
        # Ваши действия в админской панели
        markup = types.ReplyKeyboardRemove()  # Убираем клавиатуру после команды /admin
        bot.send_message(message.chat.id, "Добро пожаловать в админскую панель! 🚀", reply_markup=markup)

        # Отправляем сообщение с доступными действиями в админской панели
        admin_menu = "Доступные действия в админской панели:\n"
        admin_menu += "/give_money <user_id> <amount> - Выдать бабки на баланс пользователя\n"
        admin_menu += "/send_broadcast <message> - Отправить рассылку всем пользователям\n"
        admin_menu += "/edit_profile <user_id> <new_status> - Изменить профиль пользователя"
        bot.send_message(message.chat.id, admin_menu)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админской панели.")

    conn.close()

# Обработчик команды /give_money
@bot.message_handler(commands=['give_money'])
def give_money(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь администратором
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[7] == "Администратор":  # Проверяем статус пользователя
        # Парсим команду и параметры
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.send_message(chat_id, "Используйте команду в формате: /give_money <username> <amount>")
            return

        username = command_parts[1]
        amount = int(command_parts[2])

        # Проверяем, существует ли пользователь с указанным ником
        cursor.execute("SELECT * FROM users WHERE username=?", (username,))
        recipient_info = cursor.fetchone()

        if recipient_info:
            recipient_user_id = recipient_info[0]
            # Обновляем баланс пользователя
            cursor.execute("UPDATE users SET balance = balance + ? WHERE username=?", (amount, username))
            conn.commit()
            bot.send_message(chat_id, f"Вы выдали {amount} 🪙 пользователю @{username}.")
        else:
            bot.send_message(chat_id, "Пользователь с указанным ником не найден.")
    else:
        bot.send_message(chat_id, "У вас нет доступа к этой команде.")

    conn.close()


# Обработчик команды /send_broadcast
@bot.message_handler(commands=['send_broadcast'])
def send_broadcast(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь администратором
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[7] == "Администратор":  # Проверяем статус пользователя
        # Парсим команду и параметры
        command_parts = message.text.split(' ', 1)
        if len(command_parts) != 2:
            bot.send_message(chat_id, "Используйте команду в формате: /send_broadcast <сообщение>")
            return

        broadcast_message = command_parts[1]

        # Получаем список всех пользователей
        cursor.execute("SELECT user_id FROM users")
        all_users = cursor.fetchall()

        # Отправляем рассылку каждому пользователю
        for user in all_users:
            bot.send_message(user[0], broadcast_message)

        bot.send_message(chat_id, f"Рассылка отправлена всем пользователям.")
    else:
        bot.send_message(chat_id, "У вас нет доступа к этой команде.")

    conn.close()

# Обработчик команды /edit_profile
@bot.message_handler(commands=['edit_profile'])
def edit_profile(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь администратором
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[3] == "Администратор":  # Проверяем статус пользователя
        # Парсим команду и параметры
        command_parts = message.text.split()
        if len(command_parts) != 3:
            bot.send_message(chat_id, "Используйте команду в формате: /edit_profile <user_id> <new_status>")
            return

        try:
            edited_user_id = int(command_parts[1])
            new_status = command_parts[2]
        except ValueError:
            bot.send_message(chat_id, "Неверный формат команды. Пожалуйста, введите правильные значения.")
            return

        # Проверяем, существует ли пользователь с указанным user_id
        cursor.execute("SELECT * FROM users WHERE user_id=?", (edited_user_id,))
        edited_user_info = cursor.fetchone()

        if edited_user_info:
            # Изменяем профиль пользователя
            cursor.execute("UPDATE users SET status = ? WHERE user_id=?", (new_status, edited_user_id))
            conn.commit()
            bot.send_message(chat_id, f"Профиль пользователя с ID {edited_user_id} изменен.")
        else:
            bot.send_message(chat_id, "Пользователь с указанным ID не найден.")
    else:
        bot.send_message(chat_id, "У вас нет доступа к этой команде.")

    conn.close()


# ...

# Глобальная переменная для хранения статуса пользователя (по умолчанию - "Пользователь")
user_status = {}

@bot.message_handler(func=lambda message: message.text == "Профиль 🪪")
def handle_profile_button(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Получаем информацию о пользователе из базы данных
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info:
        # Разбираем информацию о пользователе
        id, user_id, username, first_name, last_name, chat_id, balance, status = user_info[0], user_info[1], user_info[2], user_info[3], user_info[4], user_info[5], user_info[6], user_info[7]

        # Формируем сообщение с профилем пользователя и смайликами
        profile_message = f"👤 Профиль пользователя:\n\n"
        profile_message += f"📛 Имя: @{message.from_user.username or 'N/A'}\n"
        profile_message += f"🆔 ID: {message.from_user.id}\n"
        profile_message += f"💰 Баланс: {balance} 🪙\n"
        profile_message += f"📌 Статус: {status}\n"

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton("Назад ⬅️")  # Добавляем кнопку "Назад"
        markup.add(item1)

        bot.send_message(message.chat.id, profile_message, reply_markup=markup)
        
        # Обновляем статус пользователя в глобальной переменной
        user_status[user_id] = "Профиль"
    else:
        bot.send_message(message.chat.id, "Профиль не найден. Пожалуйста, начните с команды /start.")

    conn.close()




# ...

# ...
# Обработчик кнопки "Помощь ℹ️"
@bot.message_handler(func=lambda message: message.text == "Помощь ℹ️")
def handle_help_button(message):
    help_message = "ℹ️О проектеℹ️\n\nСлужба поддержки🗣️ @потом\nЧат игры🎲\nhttps://t.me/+fYWDIZW__DFhYWVi 📞\nГруппа общения💭\nhttps://t.me/+gJ3ZNwo9vt43MmI6 📞\nНовости проекта📰\nhttps://t.me/+3h271UiWGkRjMjEy 📞"
    bot.send_message(message.chat.id, help_message)

# ...

# Обработчик кнопки "Админ Панель"
@bot.message_handler(func=lambda message: message.text == "Админ Панель 🛠")
def open_admin_panel(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Проверяем, является ли пользователь администратором
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    user_info = cursor.fetchone()

    if user_info and user_info[7] == "Администратор":  # Проверяем статус пользователя
        # Ваши действия в админской панели
        markup = types.ReplyKeyboardRemove()  # Убираем клавиатуру после открытия админской панели
        bot.send_message(message.chat.id, "Добро пожаловать в админскую панель! 🚀", reply_markup=markup)

        # Отправляем сообщение с доступными действиями в админской панели
        admin_menu = "Доступные действия в админской панели:\n"
        admin_menu += "/give_money <user_id> <amount> - Выдать бабки на баланс пользователя\n"
        admin_menu += "/send_broadcast <message> - Отправить рассылку всем пользователям\n"
        admin_menu += "/edit_profile <user_id> <new_status> - Изменить профиль пользователя"
        bot.send_message(message.chat.id, admin_menu)
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к админской панели.")

    conn.close()

# ...



# Обработчик команды /help
@bot.message_handler(commands=['help'])
def handle_help(message):
    bot.send_message(message.chat.id, "Список доступных команд:\n/start - начать\n/help - получить справку")



# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.reply_to(message, "Не понимаю тебя.")


# Запуск бота
if __name__ == "__main__":
    bot.polling(none_stop=True)
