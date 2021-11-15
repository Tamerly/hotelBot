import re
import datetime
from project_bot.loader import bot, user_data_base
from telebot import types, apihelper
from project_bot.radapi import SearchHotel
from project_bot.loader import calendar, calendar_1_callback, config


def choosing_search_method(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(text='Дешевые отели', callback_data='low_price'),
        types.InlineKeyboardButton(text='Дорогие отели', callback_data='high_price'),
        types.InlineKeyboardButton(text='Параметры цены и расположения', callback_data='best_deal'),
        row_width=True)
    bot.send_message(message.from_user.id, "Выберете способ поиска", reply_markup=markup)


def checking_input_message(message):
    """
    Проверка названия города.
    """
    if checking_method(message, 'Ошибка ввода. Давайте попробуем сначала'):
        pass
    elif len(re.findall(r'[А-Яа-яЁёa-zA-Z0-9 -]+', message.text)) > 1:
        err_city = bot.send_message(message.chat.id,
                                    'Название состоит из букв\nПожалуйста, повторите ввод')
        bot.register_next_step_handler(err_city, checking_input_message)
    else:
        user_data_base[message.chat.id].language = checking_language(message.text)
        user_data_base[message.chat.id].search_city = message.text
        SearchHotel.search_city_data(bot, message)


def checking_method(message: types.Message, text_error):
    if message.text in ['/help', '/lowprice', '/highprice', '/bestdeal', '/history', '/start', 'Найти отель',
                        'Руководство', 'Информация']:
        return True, bot.send_message(message.chat.id, text_error)


def checking_language(text: str) -> str:
    """
    Проверка языка
    :param text: принимаемый текст входящего текста города
    :return: 'en_US' или 'ru_RU'
    """
    if re.findall(r'[А-Яа-яЁё -]', re.sub(r'[- ]', '', text)):
        return "ru_RU"
    else:
        return "en_US"


def request_photo(message):
    """
    Функция отправляет в чат кнопки Да Нет, для поиска фотографий
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    markup = types.InlineKeyboardMarkup()
    yes_photo_hotels = types.InlineKeyboardButton(text='Да', callback_data='yes_photo')
    no_photo_hotels = types.InlineKeyboardButton(text='Нет', callback_data='no_photo')
    markup.add(yes_photo_hotels, no_photo_hotels)
    bot.send_message(message.chat.id, "Показать фотографии отелей?", reply_markup=markup)


def checking_numbers_of_hotels(message):
    """
    Проверка ввода кол-ва отелей в городе.
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    if checking_method(message, 'Введенный формат не поддерживается на этом этапе.\nПерезапуск'):
        pass

    elif not isinstance(message.text, str) or not message.text.isdigit():
        err_num = bot.send_message(message.chat.id,
                                   'Пожалуйста, введите количество отелей с помощью цифр.'
                                   '\nВведенное число не должно быть больше 25')
        bot.register_next_step_handler(err_num, checking_numbers_of_hotels)

    else:
        if int(message.text) > 25:
            user_data_base[message.chat.id].number_of_hotels_to_display = 25
            bot.send_message(message.chat.id, 'Введенное количество больше 25')

        else:
            user_data_base[message.chat.id].number_of_hotels_to_display = int(message.text)
            if user_data_base[message.chat.id].search_method == 'best_deal':
                msg_price = bot.send_message(message.chat.id,
                                             'Введите диапазон цен через дефис\nНапример, 200-2000')
                bot.register_next_step_handler(msg_price, checking_entered_price_range)
            else:
                request_photo(message)


def checking_entered_price_range(message):
    """
    Проверка ввода диапазона чисел цены отелей
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    price_min_max_list = list(map(int, re.findall(r'\d+', message.text)))

    if checking_method(message, 'Введенный формат не поддерживается на этом этапе.\nПерезапуск'):
        pass

    elif not isinstance(message.text, str) or len(price_min_max_list) != 2:
        err_num = bot.send_message(message.chat.id,
                                   'Введите два числа через дефис')
        bot.register_next_step_handler(err_num, checking_entered_price_range)

    else:
        user_data_base[message.chat.id].price_min_max['min'] = min(price_min_max_list)
        user_data_base[message.chat.id].price_min_max['max'] = max(price_min_max_list)
        msg_dist = bot.send_message(
            message.chat.id, 'Укажите диапазон расстояния от центра в {distance_format} Пример (1-5)'.format(
                distance_format="км." if user_data_base[message.chat.id].language == "ru_RU" else "милях"
            )
        )
        bot.register_next_step_handler(msg_dist, checking_entered_distance)


def checking_entered_distance(message):
    """
    Проверка ввода диапазона чисел расстояния от центра
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    distance_list = list(map(int, re.findall(r'\d+', message.text)))

    if checking_method(message, 'Введенный формат не поддерживается на этом этапе.\nПерезапуск'):
        pass

    elif not isinstance(message.text, str) or len(distance_list) != 2:
        err_num = bot.send_message(message.chat.id,
                                   'Введите два числа через дефис')
        bot.register_next_step_handler(err_num, checking_entered_distance)

    else:
        user_data_base[message.chat.id].distance_min_max['min'] = min(distance_list)
        user_data_base[message.chat.id].distance_min_max['max'] = max(distance_list)
        request_photo(message)


def checking_entered_photo_count(message):
    """
    Проверка введенного диапазона количества фотографий
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    if checking_method(message, 'Введенный формат не поддерживается на этом этапе.\nПерезапуск'):
        pass

    elif not isinstance(message.text, str) or not message.text.isdigit():
        err_num = bot.send_message(message.chat.id,
                                   'Введите количество фотографий с помощью цифр')
        bot.register_next_step_handler(err_num, checking_entered_photo_count)

    else:
        if int(message.text) > 4:
            user_data_base[message.chat.id].count_show_photo = 4
            bot.send_message(message.chat.id, 'Введенное количество больше 4')
        else:
            user_data_base[message.chat.id].count_show_photo = int(message.text)
        SearchHotel.search_hotels(bot, message.chat.id)


def show_calendar(bot, id, request_for_user='Выберите дату въезда в отель',
                  name=calendar_1_callback.prefix):
    now = datetime.datetime.now()
    bot.send_message(
        id,
        request_for_user,
        reply_markup=calendar.create_calendar(
            name=calendar_1_callback.prefix,
            year=now.year,
            month=now.month,
        ),
    )


def setting_checkin_checkout_date(message):
    name, action, year, month, day = message.data.split(':')
    if user_data_base[message.from_user.id].calendar_stage == 'check_in':
        print(datetime.datetime.strptime(':'.join([year, month, day]), "%Y:%m:%d").date())
        print(datetime.datetime.today().date())
        if datetime.datetime.strptime(':'.join([year, month, day]), "%Y:%m:%d").date() \
                >= datetime.datetime.today().date():
            user_data_base[message.from_user.id].checkin_date = datetime.datetime.strptime(':'.join([year, month, day]),
                                                                                           "%Y:%m:%d").date()
            user_data_base[message.from_user.id].calendar_stage = 'check_out'
            show_calendar(bot=bot, id=message.from_user.id, request_for_user='Выберите дату выезда')
        else:
            bot.send_message(message.from_user.id, 'Выбрана некорректная дата, попробуйте еще раз')
            show_calendar(bot=bot, id=message.from_user.id)
    elif user_data_base[message.from_user.id].calendar_stage == 'check_out':
        if datetime.datetime.strptime(
                ':'.join([year, month, day]), "%Y:%m:%d").date() > user_data_base[message.from_user.id].checkin_date:
            user_data_base[message.from_user.id].checkout_date = datetime.datetime.strptime(
                ':'.join([year, month, day]), "%Y:%m:%d").date()
            choosing_search_method(message)
