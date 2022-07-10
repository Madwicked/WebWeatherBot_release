import telebot
from telebot import types
from datetime import date, timedelta
import json
import os
import requests

token = os.environ['TELEGRAM_TOKEN']
WEATHER_TOKEN = os.environ['WEATHER_TOKEN']
WEATHER_URL = os.environ['WEATHER_URL']



bot = telebot.TeleBot(token)
MAIN_STATE = 'main'
CITY_STATE = 'city'
WEATHER_DATE_STATE = 'weather_date_handler'  # почему-то у него weather_date_handler




try: #ловит исключения, типа если нет файла, то создает
    data = json.load(open('data.json', 'r', encoding='utf-8'))
except FileNotFoundError:
    data = {
        'states': {},
        MAIN_STATE: {

        },
        CITY_STATE: {

        },
        WEATHER_DATE_STATE: {
            # id:city
        },
    }


def change_data(key, user_id, value):  # функция записи состояния в файл data.json
    data[key][user_id] = value
    json.dump(
        data,
        open('data.json', 'w', encoding='utf-8'),
        indent=4,       #отступы
        ensure_ascii=False,  # сохраняет русские символы
    )




@bot.message_handler(func=lambda message: True)
def dispecher(message):
    #    print(states)
    user_id = str(message.from_user.id)
    state = data['states'].get(user_id, MAIN_STATE)
    if state == MAIN_STATE:  # В зависимости от на каком состоянии пользователь вызывает соответствующую функцию
        main_handler(message)
    elif state == CITY_STATE:
        city_handler(message)
    elif state == WEATHER_DATE_STATE:
        weather_date(message)


def main_handler(message):  # функция главного состояния
    user_id = str(message.from_user.id)
    if message.text == '/start':  # по команде /start создает кнопку "Погода"
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('Погода'))
        bot.send_message(
            user_id,
            'Это бот погоды',
            reply_markup=markup,
        )  # Отправляет сообщение и меняет состояние пользователя на MAIN_STATE
        change_data('states', user_id, MAIN_STATE)
    # print(message)
    elif message.text.lower() == 'погода':  # если сразу отправляет погода, то добавляет 2 кнопки на которых будет написан результат переменных text1 и text2(число сегодня и завтра)
        text1 = str(date.today().strftime('%d/%m/%y')) #date.today возвращает сегодняшнюю дату,
                            # .strftime('%d%m//%y') приводит к виду дд/мм/гг
        #print(text1)
        text2 = str((date.today() + timedelta(1)).strftime('%d/%m/%y')) #timedelta прибавляет день (1) к сегодняшней дате
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            *[types.KeyboardButton(button) for button in [text1, text2]]

        )
        bot.send_message(user_id, 'Када? сегодня или завтра',
                         reply_markup=markup)  # Выдает сообщение и меняет состояние пользователя на CITY_STATE
        change_data('states', user_id, WEATHER_DATE_STATE)
    else:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(user_id, 'моя твоя не понимать', reply_markup=markup)


def city_handler(message):  # функция выбора города
    user_id = str(message.from_user.id)
    url = WEATHER_URL.format(city=message.text, token=WEATHER_TOKEN)  # WEATHER_URL берется с сайта (API call)
    response = requests.get(url)
#    print(response)
    if response.status_code != 200:
        bot.reply_to(message, 'моя твоя не понимать')
    else:
        change_data('city', user_id, message.text)
        change_data('states', user_id, MAIN_STATE)
        parse_weather_data(message)


  # функция выбора дня на который мы хотим получить погоду, выдает из словаря WEATHER
def weather_date(message):
    user_id = str(message.from_user.id)
    if message.text.lower() == str(date.today().strftime('%d/%m/%y')):  #создает 3 кнопки с городами или ждет
            #ввода другого города и в завиимости от того какую дату выбрал юзер, должен отправлять погоду на соответствующую дату, но пока только на сегодня
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            *[types.KeyboardButton(button) for button in ['москва', 'санкт-петербург', 'уфа']]
        )
        bot.send_message(user_id, 'Город? мск или спб или напиши свой ',
                         reply_markup=markup)  # Выдает сообщение и меняет состояние пользователя на CITY_STATE
        change_data('states', user_id, CITY_STATE)
        #city = data[WEATHER_DATE_STATE][user_id]

    elif message.text == str((date.today() + timedelta(1)).strftime('%d/%m/%y')):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(
            *[types.KeyboardButton(button) for button in ['москва', 'санкт-петербург', 'уфа']]
        )
        bot.send_message(user_id, 'Город? мск или спб или напиши свой ',
                         reply_markup=markup)  # Выдает сообщение и меняет состояние пользователя на CITY_STATE
        change_data('states', user_id, CITY_STATE)


def parse_weather_data(message):
    user_id = str(message.from_user.id)
    city = data['city'][user_id]
#    print(city)
    url = WEATHER_URL.format(city=city, token=WEATHER_TOKEN)
    response = requests.get(url)
    resp = json.loads(response.content)
#    print(url)
#    print(resp)
    for elem in resp['weather']:
        weather_state = elem['main']
    temp = round(resp['main']['temp'] - 273.15, 2),
    feels_like = round(resp['main']['feels_like'] - 273.15, 2),
    city = resp['name']
    country = resp['sys']['country']
    msg = f'the weather in {city}: Temp is {temp}, feels like {feels_like}, State is {weather_state}, country is {country}'
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(
        *[types.KeyboardButton(button) for button in ['погода']]
    )
    bot.send_message(user_id, msg, reply_markup=markup)

if __name__ == '__main__':
    bot.polling()
    print('бот остановлен')