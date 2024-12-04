import logging
from datetime import datetime, timedelta, timezone
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, ConversationHandler, filters
import requests
from token import TOKEN
# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# Определяем состояния разговора
CHOOSING, TYPING_CITY = range(2)

# Храним данные пользователей {user_id: {'city': city_name}}
user_data = {}


# Функция для получения данных о погоде
def get_weather(latitude, longitude, day_offset):
    current_date = datetime.now() + timedelta(days=day_offset)
    current_date_str = current_date.strftime('%Y-%m-%d')

    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=Europe%2FMoscow&past_days=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()

        if 'daily' in data and 'time' in data['daily']:
            try:
                # Находим индекс нужной даты
                date_index = data['daily']['time'].index(current_date_str)

                # Извлекаем данные о погоде для нужной даты
                temperature_max = data['daily']['temperature_2m_max'][date_index]
                temperature_min = data['daily']['temperature_2m_min'][date_index]
                precipitation = data['daily']['precipitation_sum'][date_index]

                return f"Погода на {current_date_str}:\nМакс. температура: {temperature_max}°C\nМин. температура: {temperature_min}°C\nОсадки: {precipitation} мм"
            except ValueError:
                return "Не удалось получить данные о погоде."
    return "Не удалось получить данные о погоде."


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data[user_id] = {}
    await update.message.reply_text(
        "Привет! Введите название вашего города для регистрации в системе:"
    )
    return TYPING_CITY


# Обработчик ввода города
async def received_city(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    user_data[user_id]['city'] = update.message.text
    await update.message.reply_text(
        "Спасибо! Ваш город сохранён. Выберите, какую погоду вы хотите посмотреть:",
        reply_markup=ReplyKeyboardMarkup(
            [['Сегодня', 'Завтра'], ['Послезавтра', 'Вчера']],
            one_time_keyboard=True
        )
    )
    return CHOOSING


# Обработчик выбора дня
async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    city = user_data[user_id].get('city')

    # Пример координат для Москвы и Берлина
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

    if city.lower() not in city_coordinates:
        await update.message.reply_text("Извините, я не знаю ваш город.")
        return CHOOSING

    latitude, longitude = city_coordinates[city.lower()]

    day_offset = {
        'Сегодня': 0,
        'Завтра': 1,
        'Послезавтра': 2,
        'Вчера': -1
    }.get(update.message.text, 0)

    weather_info = get_weather(latitude, longitude, day_offset)
    await update.message.reply_text(weather_info)
    return CHOOSING


# Завершение разговора
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("До свидания!")
    return ConversationHandler.END


def main() -> None:
    # Введите свой токен, который вы получили от BotFather
    application = ApplicationBuilder().token(TOKEN).build()

    # Создаём обработчики
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            TYPING_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, received_city)],
            CHOOSING: [MessageHandler(filters.Regex('^(Сегодня|Завтра|Послезавтра|Вчера)$'), show_weather)],
        },
        fallbacks=[CommandHandler('done', done)],
    )

    # Добавляем обработчики в приложение
    application.add_handler(conv_handler)

    # Запускаем бота
    application.run_polling()


if __name__ == '__main__':
    main()