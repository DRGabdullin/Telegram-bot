import telebot
import mysql.connector
import time
from pyowm import OWM
from pyowm.utils.config import get_default_config


bot = telebot.TeleBot("Token")

config_dict = get_default_config()
config_dict['language'] = 'ru'
owm = OWM('Token', config_dict)
mgr = owm.weather_manager()


mydatabase = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="RoleMr87",
    port="3306",
    database="telegram"
)

mycursor = mydatabase.cursor()
mycursor.execute("CREATE DATABASE telegram")
mycursor.execute("SHOW DATABASES")

for x in mycursor:
    print(x)

mycursor.execute("CREATE TABLE visitors(id INT AUTO_INCREMENT PRIMARY KEY, user_id INT UNIQUE,"
                "first_name VARCHAR(20), last_name VARCHAR(20))")


user_data = {}


class User:
    def __init__(self, first_name):
        self.first_name = first_name
        self.last_name = ''


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == "Привет":
        bot.send_message(message.from_user.id, "Привет! Это телеграм-бот регистрации"
                                               "\n/help - помощь"
                                               "\n/start - начало работы")
    elif message.text == '/help':
        bot.send_message(message.from_user.id, "Напиши /start")
    elif message.text == '/start':
        msg = bot.send_message(message.chat.id, "Введите имя")
        bot.register_next_step_handler(msg, process_firstname_step)
    elif message.text == '/weather':
        msg = bot.send_message(message.chat.id, "Название города")
        bot.register_next_step_handler(msg, process_weather)


def process_weather(message):
    try:
        observation = mgr.weather_at_place(message.text)
        weather = observation.weather
        temp = weather.temperature("celsius")["temp"]  # Присваиваем переменной значение температуры из таблицы
        barom = weather.barometric_pressure()
        wind = weather.wind()
        sun = weather.sunset_time(timeformat='date')
        answer = f"Температура: {temp} C, давление {barom['press']} кПа, " \
                 f"ветер {wind['speed']} м/с, время до заката солнышка {sun}"
    except Exception:
        answer = "Не найден город, попробуйте ввести название снова.\n"
        print(time.ctime(), "User id:", message.from_user.id)
        print(time.ctime(), "Message:", message.text.title(), 'Error')

    bot.send_message(message.chat.id, answer)


def process_firstname_step(message):
    try:
        user_id = message.from_user.id
        name = message.text
        user = User(name)
        user_data[user_id] = user
        msg = bot.send_message(message.chat.id, "Введите фамилию")
        bot.register_next_step_handler(msg, process_lastname_step)
    except Exception as e:
        bot.reply_to(message, 'oooops')


def process_lastname_step(message):
    try:
        user_id = message.chat.id
        user = user_data[user_id]
        user.last_name = message.text
        sql = "INSERT INTO visitors (user_id, first_name, last_name) VALUES (%s, %s, %s)"
        val = (user_id, user.first_name, user.last_name)
        mycursor.execute(sql, val)
        print(mycursor.rowcount, "record inserted.")
        bot.send_message(message.chat.id, "Регистрация прошла успешно")
        mydatabase.commit()
    except Exception as e:
        bot.reply_to(message, 'Вы уже зарегистрированы в системе!')


bot.enable_save_next_step_handlers(delay=2)
bot.load_next_step_handlers()

if __name__ == '__main__':
    bot.polling(none_stop=True)
