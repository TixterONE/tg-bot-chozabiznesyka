import telebot
import sqlite3
import random
from datetime import datetime, timedelta
import time
import os

bot = telebot.TeleBot(os.environ["bot_token"])

businesses = {
    1: {"name": "Ларек", "price": 5000, "earn": 2},
    2: {"name": "Продуктовый магазин", "price": 10000, "earn": 4},
    3: {"name": "Магазин канцтоваров", "price": 15000, "earn": 5},
    4: {"name": "Обувной магазин", "price": 20000, "earn": 6},
    5: {"name": "Компьютерный клуб", "price": 25000, "earn": 8},
    6: {"name": "Сеть продуктовых магазинов", "price": 35000, "earn": 10},
    7: {"name": "Ночной клуб", "price": 50000, "earn": 13},
    8: {"name": "Автотранспортное предприятие", "price": 80000, "earn": 16},
    9: {"name": "Мясокомбинат", "price": 100000, "earn": 20},
    10: {"name": "Завод по производству резиновых членов", "price": 1000000, "earn": 9999}
}

def init_db():
    conn = sqlite3.connect('economy.db')
    cursor = conn.cursor()

    # Создаем базу БЕЗ лишних команд внутри
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (id INTEGER PRIMARY KEY, name TEXT, balance REAL, last_gain TEXT, 
                       biz_id INTEGER, biz_lvl INTEGER, last_profit TEXT)''')

    # Добавляем колонки по одной, если их нет
    cols = [
        ("bank", "REAL DEFAULT 0"),
        ("last_dep", "TEXT"),
        ("last_sh", "INTEGER DEFAULT 0"),
        ("credit_sum", "REAL DEFAULT 0"),
        ("credit_time", "INTEGER DEFAULT 0")
    ]

    for name, dtype in cols:
        try:
            cursor.execute(f"ALTER TABLE users ADD COLUMN {name} {dtype}")
        except:
            pass

    conn.commit()
    conn.close()


def update_db(user_id, **kwargs):
    conn = sqlite3.connect('economy.db')
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f"UPDATE users SET {key} = ? WHERE id = ?", (value, user_id))
    conn.commit()
    conn.close()


def get_user(m_user):
    user_id = m_user.id
    name = f"{m_user.first_name} {m_user.last_name}" if m_user.last_name else m_user.first_name

    conn = sqlite3.connect('economy.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if not user:
        # новые игроки
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
               (user_id, name, 100.0, None, 0, 0, now, 0.0, None, 0, 0, 0))

        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
    else:
        cursor.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        conn.commit()

    conn.close()
    return list(user)


#командики

@bot.message_handler(commands=['gain'])
def gain(message):
    user = get_user(message.from_user)
    now = datetime.now()

    if user[3]:
        last_time = datetime.strptime(user[3], '%Y-%m-%d %H:%M:%S')
        if now < last_time + timedelta(hours=6):
            wait = (last_time + timedelta(hours=6)) - now
            bot.reply_to(message, f"Следующее начисление будет через {wait.seconds // 3600}ч. {(wait.seconds // 60) % 60}м.\n(каждые 6 часов)")
            return

    amount = random.randint(44444444, 44444444)
    new_balance = int(user[2] + amount)
    update_db(user[0], balance=int(new_balance), last_gain=now.strftime('%Y-%m-%d %H:%M:%S'))
    bot.reply_to(message, f"Ты получил {amount}$ Твой баланс: {new_balance}$")


@bot.message_handler(commands=['bet'])
def bet(message):
    print(message.text)
    print(message.text.split())
    try:
        user = get_user(message.from_user)
        args = message.text.split()
        amount = int(args[1])
        risk = int(args[2])
        if risk < 20 or risk > 99: raise ValueError
    except:
        bot.reply_to(message, "эээ, введи: /bet <сумма> <риск от 20 до 99>", parse_mode="Markdown")
        return

    if amount > int(user[2]) or amount <= 0:
        bot.reply_to(message, "лох нищи")
        return

    # формула по идее: риск 50 = х1, риск 99 = х99
    # функц: y = 2x - 99
    if risk >= 50:
        multiplier = 2 * risk - 99
    else:
        multiplier = risk / 50  #ес риск меньше 50 то множитель будет дробным

    chance_to_win = 100 - risk
    tx = 0.98 #эта шо б дохуя денег нельзя было заработать

    if random.randint(1, 100) <= chance_to_win:
        win = int(amount * multiplier * tx)
        new_balance = int(user[2] + win)
        update_db(user[0], balance=int(new_balance))
        bot.reply_to(message,
                     f"Ты выиграл!\nВыигрыш: ${int(win)}\nБаланс: ${int(new_balance)}",
                     parse_mode="Markdown")
    else:
        new_balance = int(user[2] - amount)
        update_db(user[0], balance=new_balance)
        bot.reply_to(message, f"Аахахах лох\n🥰  Ты проебал: ${int(amount)}\nБаланс: ${int(new_balance)}",
                     parse_mode="Markdown")


@bot.message_handler(commands=['topbal'])
def top(message):
    conn = sqlite3.connect('economy.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, balance FROM users ORDER BY balance DESC LIMIT 10")
    users = cursor.fetchall()
    conn.close()

    res = "Топ 10 великих лохов:\n\n"
    for i, u in enumerate(users, 1):
        #у(0) это имя пользователя
        res += f"{i}. {u[0]} - **${int(u[1])}**\n"

    bot.send_message(message.chat.id, res, parse_mode="Markdown")


@bot.message_handler(commands=['biz'])
def business_handler(message):
    args = message.text.split()
    user = get_user(message.from_user)  # Юзер из базы

    # /biz list
    if len(args) > 1 and args[1].lower() == 'list':
        text = "Доступные бизнесы:\n\n"
        for i, b in businesses.items():
            text += f"{i}. {b['name']} - {b['price']}$ (Доход: {b['earn']}$/час)\n"
        text += "\nКупить: `/buy <номер>`"
        bot.reply_to(message, text, parse_mode="Markdown")
        return

    #данные юзера
    biz_id = int(user[4]) if user[4] else 0
    lvl = int(user[5]) if user[5] else 1
    raw_time = user[6]
    if raw_time:
        try:
            #ес там число
            last_time = int(float(raw_time))
        except ValueError:
            #ес там текст то делаем отэто
            last_time = int(datetime.strptime(raw_time, '%Y-%m-%d %H:%M:%S').timestamp())
    else:
        last_time = int(time.time())

    if biz_id == 0: #я ахуел что когда берешь данные то ес у тя есть бизнес то пишет 1, а если нету то 0
        bot.reply_to(message, "у тя нету бизнеса.\nпосмотри список: /biz list")
        return

    b_data = businesses.get(biz_id)

    # Расчет прибыли
    hours = (int(time.time()) - last_time) // 3600
    current_profit = (b_data['earn'] * lvl) * hours

    # цена апгрейда
    upgrade_cost = int((b_data['price'] / 5) * (lvl + 1))

    # /biz withdraw
    if len(args) > 1 and args[1].lower() == 'withdraw':
        if current_profit <= 0:
            return bot.reply_to(message, "нету денюжек")

        new_balance = user[2] + current_profit  #
        update_db(user[0], balance=new_balance, last_profit=str(int(time.time())))
        bot.reply_to(message, f"Ты снял {current_profit}$. Теперь на руках: {new_balance}$")
        return

    #инфа о бизнесе
    text = (f"Бизнес: {b_data['name']} ({lvl} lvl)\n"
            f"Накоплено: {current_profit}$\n"
            f"Цена улучшения: {upgrade_cost}$\n\n"
            f"Снять: /biz withdraw\n"
            f"Улучшить: /biz upgrade")
    bot.reply_to(message, text, parse_mode="Markdown")



@bot.message_handler(commands=['buy'])
def buy_handler(message):
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        bot.reply_to(message, "Напиши /buy <номер бизнеса> из списка /biz list")
        return

    biz_id = int(args[1])
    user = get_user(message.from_user)

    if biz_id not in businesses:
        bot.reply_to(message, "нету такого номера бизнеса")
        return

    biz = businesses[biz_id]

    # Проверка бабла (user[2] — это баланс)
    if user[2] < biz['price']:
        bot.reply_to(message, f"бомж момент")
        return

    if user[4] != 0: # user[4] — это поле biz_id в базе
        bot.reply_to(message, "у тебя уже есть бизнес")
        return

    #остоток
    new_balance = user[2] - biz['price']
    update_db(user[0], balance=new_balance, biz_id=biz_id, biz_lvl=1)

    bot.reply_to(message, f"Ты купил {biz['name']}. Теперь сосешь из него по {biz['earn']}$/час.")

#апгрейд
@bot.message_handler(commands=['upgrade'])
def upgrade_biz(message):
    user = get_user(message.from_user)
    try:
        biz_id = int(user[4]) if user[4] else 0
    except:
        biz_id = 0
    lvl = user[5]

    if biz_id == 0:
        bot.reply_to(message, "Сначала купи бизнес через /buy")
        return

    if lvl >= 10:
        bot.reply_to(message, "Твой бизнес на максимальном уровне")
        return

    bizd = businesses[biz_id]
    base_price = int(bizd['price'])
    base_income = int(bizd['earn'])


    #формула: цена / 5 * (lvl + 1)
    upgrade_cost = (int(base_price) / 5) * (int(lvl) + 1)

    if user[2] < upgrade_cost:
        bot.reply_to(message, f"Улучшение стоит ${int(upgrade_cost)}. Тебе не хватает ${int(upgrade_cost) - int(user[2])}")
        return

    new_lvl = lvl + 1
    new_balance = user[2] - upgrade_cost
    update_db(user[0], balance=new_balance, biz_id=biz_id, biz_lvl=new_lvl)

    #доход увеличивается ура
    new_income = base_income + (base_income * new_lvl)
    bot.reply_to(message,
                 f"Уровень поднят до {new_lvl}!\nНовый доход: ${new_income}/час\nСписано: ${int(upgrade_cost)}")


#продажа бизнеса
@bot.message_handler(commands=['sell'])
def sell_biz(message):
    user = get_user(message.from_user)
    if user[5] < 5:
        bot.reply_to(message, "У тя есть бизнес, прокачай до 5 уровня шоб продать и купить другой")
        return

    update_db(user[0], biz_id=0, biz_lvl=0)
    bot.reply_to(message, "Ты продал бизнес и теперь свободен от рабства к сожалению.")


def collect_profit(user_id):
    user = user_id(user_id)
    if not user or user[4] == 0: return  # Нет бизнеса - нет прибыли

    biz_id = user[5]
    lvl = user[5]
    last_time_str = user[6]

    if not last_time_str:
        update_db(user_id, last_profit=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return

    last_time = datetime.strptime(last_time_str, '%Y-%m-%d %H:%M:%S')
    hours_passed = (datetime.now() - last_time).total_seconds() // 3600

    if hours_passed >= 1:
        base_income = businesses[biz_id]
        current_hourly_income = base_income + (base_income * lvl)
        total_profit = hours_passed * current_hourly_income

        new_balance = user[2] + total_profit
        update_db(user_id, balance=new_balance, last_profit=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        return total_profit
    return 0


@bot.message_handler(commands=['credit'])
def get_credit(message):
    args = message.text.split()
    #сумма кредита и сумма которую нужно вернуть
    valid_sums = {500: 525, 1500: 1575, 5000: 5250}

    if len(args) < 2 or not args[1].isdigit() or int(args[1]) not in valid_sums:
        bot.reply_to(message, "ты короч можешь взять кредит только на 500$, 1500$ и 5000$")
        return

    amount = int(args[1])
    user = get_user(message.from_user)

    if user[10] > 0:
        return bot.reply_to(message, "эээ куда, рано")

    new_balance = user[2] + amount

    update_db(user[0], balance=new_balance, credit_sum=valid_sums[amount], credit_time=int(time.time()))
    bot.reply_to(message, f"Ты взял в кредит {amount}$,а должен вернуть {valid_sums[amount]}$ через 24 часа")


@bot.message_handler(commands=['helpa'])
def help_command(message):
    text = ("хелпа:\n/bet - Поставить ставку\n/balance - Посмотреть свой баланс\n/biz - посмотреть чо за бизнес сука (ес у тебя он есть)\n/biz list - Узнать список доступных бизнесов\n/upgrade - Улучшить свой бизнес (Если присутсвует)\n/buy | /sell - купить\продать бизнес\n/topbal - Узнать топ-10 игроков по балансу\n/gain - Получить деньги"
            "\n/credit - Оформить кредит ~~на цыганскую семью~~\n/deposit - Сдать под депозит деньги\n/withdraw - Снять деньги с депозита\n/sh - Подработать")
    bot.reply_to(message, text)

@bot.message_handler(commands=['start'])
def start_command(message):
    text = "Здарова нищи, крч введи команду /help шо б посмотреть команды"
    bot.reply_to(message, text)


@bot.message_handler(commands=['sh'])
def work_handler(message):
    jobs = {
        'rzl': {'name': 'промоутером(Раздача листовок)', 'pay': 40},
        'rzgr': {'name': 'разгрузчиком', 'pay': 60},
        'upk': {'name': 'упаковщиком', 'pay': 45}
    }

    args = message.text.split()
    if len(args) < 2 or args[1] not in jobs:
        bot.reply_to(message, "Варианты:\n/sh rzl (Раздача листовок, 40$)\n/sh rzgr (Разгрузчик, 60$)\n/sh upk (Упаковщик, 45$)")
        return

    user = get_user(message.from_user)

    last_sh_time = user[9] if user[9] else 0

    if time.time() - last_sh_time < 86400:
        wait_seconds = int(86400 - (time.time() - last_sh_time))
        hours = wait_seconds // 3600
        minutes = (wait_seconds // 60) % 60
        bot.reply_to(message, f"Ты не можешь подрабатывать больше раза на день.\nЖди {hours} часов {minutes} минуты")
        return

    job = jobs[args[1]]

    new_balance = user[2] + job['pay']

    update_db(user[0], balance=new_balance, last_sh=int(time.time()))

    bot.reply_to(message, f"Ты подработал {job['name']}. Ты заработал {job['pay']}$.\nТвой баланс: {new_balance}$")


@bot.message_handler(commands=['deposit'])
def handle_deposit(message):
    parts = message.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        return bot.reply_to(message, "пиши: /deposit <сумма>", parse_mode="Markdown")

    amount = int(parts[1])
    user = get_user(message.from_user)

    if amount < 99:
        return bot.reply_to(message, "надо минимум $100 для депозита.")

    if user[2] < amount:
        return bot.reply_to(message, "лох нищи")

    new_balance = user[2] - amount
    new_bank = user[7] + amount * 1.03
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    update_db(user[0], balance=new_balance, bank=new_bank, last_dep=now)

    bot.reply_to(message, f"Ты взял депозит суммой в {int(amount)}$ на 3% в банк на 24 часа.")

@bot.message_handler(commands=['balance'])
def balance_command(message):
        user = get_user(message.from_user)
        bot.reply_to(message, f"Твой баланс:\n\nНе в банке: {int(user[2])}$\nВ банке: {int(user[7])}$",
                     parse_mode="Markdown")


@bot.message_handler(commands=['withdraw'])
def withdraw_command(message):
    user = get_user(message.from_user)

    if not user[8]:  # Если даты депозита нет
        return bot.reply_to(message, "Ты ещё не оформлял кредит на семью депозит")

    last_dep_time = datetime.strptime(user[8], '%Y-%m-%d %H:%M:%S')
    unlock_time = last_dep_time + timedelta(seconds=1)
    now = datetime.now()

    if now < unlock_time:
        wait = unlock_time - now
        hours = wait.seconds // 3600
        minutes = (wait.seconds // 60) % 60
        return bot.reply_to(message, f"Депозит будет ещё действовать {hours}ч. {minutes}м.")

    # Если 24 часа прошло:
    amount_to_withdraw = user[7]
    new_balance = user[2] + amount_to_withdraw * 1.03

    update_db(user[0], balance=new_balance, bank=0, last_dep=None)

    bot.reply_to(message, f"Ты забрал из банка свои {int(amount_to_withdraw)}$. Теперь они на основном балансе!")


init_db()
bot.remove_webhook()
print("бот запустился")
bot.polling(none_stop=True)
