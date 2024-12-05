import sqlite3
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
import requests
import datetime
from secret import TOKEN
# Словарь с координатами городов
city_coordinates = {
    "москва": (55.75, 37.625),
    "санкт-петербург": (59.9343, 30.3351),
    "новосибирск": (55.0084, 82.9357),
    "екатеринбург": (56.8389, 60.6057),
    "казань": (55.7941, 49.1113),
    "нижний новгород": (56.2965, 43.9361),
    "самара": (53.1959, 50.1002),
    "омск": (54.9914, 73.3645),
    "ростов-на-дону": (47.2357, 39.7015),
    "уфа": (54.7388, 55.9721),
    "берлин": (52.52, 13.419998)
}
days_of_week = {
    'Mon': 'Пн',
    'Tue': 'Вт',
    'Wed': 'Ср',
    'Thu': 'Чт',
    'Fri': 'Пт',
    'Sat': 'Сб',
    'Sun': 'Вс'
}
# Функция для создания базы данных и таблицы
def create_db():
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            city TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# Функция для регистрации пользователя
def register_user(user_id, city):
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO users (user_id, city) VALUES (?, ?)', (user_id, city))
    conn.commit()
    conn.close()

# Функция для получения города пользователя
def get_user_city(user_id):
    conn = sqlite3.connect('user.db')
    cursor = conn.cursor()
    cursor.execute('SELECT city FROM users WHERE user_id = ?', (user_id,))
    city = cursor.fetchone()
    conn.close()
    return city[0] if city else None

# Обработка команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    city = get_user_city(user_id)

    if city:
        await update.message.reply_text(f'Добро пожаловать обратно! Ваш город: {city}')
    else:
        await update.message.reply_text('Привет! Пожалуйста, введите ваш город для регистрации.')

    await show_weather_buttons(update)

# Функция для отображения кнопок прогноза погоды
async def show_weather_buttons(update: Update):
    keyboard = [
        [KeyboardButton("Сегодня"), KeyboardButton("Завтра"), KeyboardButton("Неделя"), KeyboardButton("2 недели")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text('Выберите, какую погоду вы хотите узнать:', reply_markup=reply_markup)

# Обработка текстовых сообщений
async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    message_text = update.message.text.lower()

    if message_text in city_coordinates.keys():
        register_user(user_id, message_text)
        await update.message.reply_text(f'Город "{message_text}" успешно зарегистрирован!')
    elif message_text == "сегодня":
        await send_weather(update, "today")
    elif message_text == "завтра":
        await send_weather(update, "tomorrow")
    elif message_text == "неделя":
        await send_weather(update, "week")
    elif message_text == "2 недели":
        await send_weather(update, "two_weeks")
    else:
        await update.message.reply_text('Неизвестный город. Пожалуйста, введите один из следующих городов: ' + ', '.join(city_coordinates.keys()))

# Отправка прогноза погоды в зависимости от выбора
async def send_weather(update: Update, period: str):
    user_id = update.effective_user.id
    city = get_user_city(user_id)

    if city:
        lat, lon = city_coordinates[city]
        if period == "today":
            weather_data = get_weather(lat, lon)
            await update.message.reply_text(f"Погода на сегодня в городе - {city.upper()[0]+city.lower()[1:]}:\n{weather_data}")
        elif period == "tomorrow":
            weather_data = get_weather_tomorrow(lat, lon)
            await update.message.reply_text(f"Погода на завтра в городе - {city.upper()[0]+city.lower()[1:]}:\n{weather_data}")
        elif period == "week":
            weather_data = get_weather_week(lat, lon)
            await update.message.reply_text(f"Погода на неделю в городе - {city.upper()[0]+city.lower()[1:]}:\n{weather_data}\n")
        elif period == "two_weeks":
            weather_data = get_weather_two_weeks(lat, lon)
            await update.message.reply_text(f"Погода на 2 недели в городе - {city.upper()[0]+city.lower()[1:]}:\n{weather_data}\n")
    else:
        await update.message.reply_text('Сначала зарегистрируйтесь, используя команду /start.')

# Получение прогноза погоды на сегодня
def get_weather(lat, lon):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,rain&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe%2FMoscow&forecast_days=16"
    response = requests.get(api_url)
    try:
        if response.status_code == 200:
            data = response.json()
            t_max = data['daily']['temperature_2m_max'][0]
            t_min = data['daily']['temperature_2m_min'][0]
            rain = data['daily']['precipitation_sum'][0]
            return f'Максимальная температура: {t_max}°C\nМинимальная температура: {t_min}°C\nОсадки: {rain}мм\n'
        else:
            return 'Не удалось получить данные о погоде.'
    except ValueError:
        return 'Не удалось получить данные о погоде.'
# Получение прогноза погоды на завтра
def get_weather_tomorrow(lat, lon):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,rain&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe%2FMoscow&forecast_days=16"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        tomorrow_max = data['daily']['temperature_2m_max'][1]
        tomorrow_min = data['daily']['temperature_2m_min'][1]
        rain = data['daily']['precipitation_sum'][1]
        return f'Максимальная температура: {tomorrow_max}°C\nМинимальная температура: {tomorrow_min}°C\nОсадки: {rain}мм\n'
    else:
        return 'Не удалось получить данные о погоде.'

# Получение прогноза погоды на неделю
def get_weather_week(lat, lon):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,rain&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe%2FMoscow&forecast_days=16"
    response = requests.get(api_url)
    
    if response.status_code == 200:
        data = response.json()
        weekly_forecast = ""
        for i in range(7):
            max_temp = data['daily']['temperature_2m_max'][i]
            min_temp = data['daily']['temperature_2m_min'][i]
            day = data['daily']['time'][i]
            rain = data['daily']['precipitation_sum'][i]
            date = datetime.datetime.strptime(day, '%Y-%m-%d')
            day_of_week = days_of_week[date.strftime('%a')]
            weekly_forecast += f"{day_of_week} {day}: Макс: {max_temp}°C, Мин: {min_temp}°C, Осадки: {rain}мм\n"
        return weekly_forecast
    else:
        return 'Не удалось получить данные о погоде.'

def get_weather_two_weeks(lat, lon):
    api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,rain&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe%2FMoscow&forecast_days=16"
    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()
        weekly_forecast1 = []
        weekly_forecast2 = []
        for i in range(7):
            max_temp = data['daily']['temperature_2m_max'][i]
            min_temp = data['daily']['temperature_2m_min'][i]
            rain = data['daily']['precipitation_sum'][i]
            day = data['daily']['time'][i]
            date = datetime.datetime.strptime(day, '%Y-%m-%d')
            day_of_week = days_of_week[date.strftime('%a')]
            weekly_forecast1.append(f"{day_of_week} {day}: Макс: {max_temp}, Мин: {min_temp}°C, Осадки: {rain}мм")
        for i in range(7):
            max_temp = data['daily']['temperature_2m_max'][i+7]
            min_temp = data['daily']['temperature_2m_min'][i+7]
            rain = data['daily']['precipitation_sum'][i+7]
            day = data['daily']['time'][i+7]
            date = datetime.datetime.strptime(day, '%Y-%m-%d')
            day_of_week = days_of_week[date.strftime('%a')]
            weekly_forecast2.append(f"{day_of_week} {day}: Макс: {max_temp}, Мин: {min_temp}°C, Осадки: {rain}мм")
        two_weeks = 'Текущая неделя:\n\n'
        for i in range(7):
            two_weeks += f"{weekly_forecast1[i]}\n"
        two_weeks += "------------------------------------------------------------------------------\nСледующая неделя:\n\n"
        for i in range(7):
            two_weeks += f"{weekly_forecast2[i]}\n"
        return two_weeks
    else:
        return 'Не удалось получить данные о погоде.'
# Обработка команды /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "/start - начать взаимодействие с ботом\n"
        "/help - помощь\n"
        "/change - поменять город\n"
        "Выберите погоду, нажав на кнопку."
    )
    await update.message.reply_text(help_text)

# Обработка команды /change
async def change_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    city = get_user_city(user_id)

    if city:
        await update.message.reply_text('Введите новый город для замены старого.')
    else:
        await update.message.reply_text('Сначала зарегистрируйтесь, используя команду /start.')

# Основная функция
def main():
    create_db()
    application = ApplicationBuilder().token(TOKEN).build()  # Замените на ваш токен

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("change", change_city))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    application.run_polling()

if __name__ == '__main__':
    main()
