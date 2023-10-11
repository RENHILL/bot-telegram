import sqlite3

# Создаем базу данных и подключаемся к ней
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создаем таблицу 'users' с нужными полями
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT,
    chat_id INTEGER,
    balance REAL DEFAULT 0,
    status TEXT DEFAULT 'Пользователь'
)
''')

# Создаем таблицу 'admins' для администраторов
cursor.execute('''
CREATE TABLE IF NOT EXISTS admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    username TEXT,
    first_name TEXT,
    last_name TEXT
)
''')


# Создаем таблицу 'game_data' для хранения игровых данных
cursor.execute('''
CREATE TABLE IF NOT EXISTS game_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    score INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    inventory TEXT DEFAULT NULL
)
''')

# Создаем таблицу 'leaderboard' для рейтинга
cursor.execute('''
CREATE TABLE IF NOT EXISTS leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    score INTEGER DEFAULT 0,
    rank INTEGER DEFAULT NULL
)
''')

# Создаем таблицу 'tasks' для игровых заданий
cursor.execute('''
CREATE TABLE IF NOT EXISTS tasks (
    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_name TEXT,
    task_description TEXT,
    reward INTEGER DEFAULT 0
)
''')

# Создаем таблицу 'action_history' для записи действий пользователей
cursor.execute('''
CREATE TABLE IF NOT EXISTS action_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action_type TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    description TEXT
)
''')

import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Создаем таблицу 'promocodes' для хранения информации о промокодах с дополнительными полями
cursor.execute('''
CREATE TABLE IF NOT EXISTS promocodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT UNIQUE,
    reward INTEGER DEFAULT 0,
    expiration_date DATE,  -- Дата окончания действия промокода
    max_activations INTEGER,  -- Максимальное количество активаций
    current_activations INTEGER DEFAULT 0  -- Текущее количество активаций
)
''')

# Создаем таблицу 'deposit' для хранения информации о пополнениях
cursor.execute('''
CREATE TABLE IF NOT EXISTS deposit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    status TEXT,  -- Add a new 'status' column of data type TEXT
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')


# Создаем таблицу 'withdraw' для хранения информации о выводах
cursor.execute('''
CREATE TABLE IF NOT EXISTS withdraw (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount REAL,
    status TEXT, 
    reason TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

# Создаем таблицу 'transfer' для хранения информации о переводах
cursor.execute('''
CREATE TABLE IF NOT EXISTS transfer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    amount REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS user_promocodes (
    user_id INTEGER,
    promocode_id INTEGER,
    UNIQUE(user_id, promocode_id)
)
''')
# Сохраняем изменения и закрываем соединение
conn.commit()
conn.close()
