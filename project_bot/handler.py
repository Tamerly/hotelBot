import re
import datetime
from project_bot.loader import bot, user_data_base
from telebot import types
from typing import Callable
from project_bot.radapi import SearchHotel
from project_bot.loader import calendar, calendar_1_callback


def choosing_search_method(button_result: types.CallbackQuery) -> None:
    """
    Функция определяет наличие в кэше способа поиска.

    При его наличии запускается цепочка поиска города.
    При отсуствии вызывается инлайн клавиатура для выбора способа поиска
    :param button_result: результат нажатия кнопки
    :return:
    """
    if user_data_base[button_result.from_user.id].search_method:
        message_what_city = bot.send_message(button_result.from_user.id, 'В каком городе будем искать?')
        bot.register_next_step_handler(message_what_city, checking_input_message)
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton(text='Дешевые отели', callback_data='low_price'),
            types.InlineKeyboardButton(text='Дорогие отели', callback_data='high_price'),
            types.InlineKeyboardButton(text='Параметры цены и расположения', callback_data='best_deal'),
            row_width=True)
        bot.send_message(button_result.from_user.id, "Выберете способ поиска", reply_markup=markup)


def checking_input_message(message: types.Message) -> None:
    """
    Проверка названия города.

    :param message: полученное сообщение
    """
    if checking_method(message, 'Ошибка ввода. Давайте попробуем сначала'):
        pass
    elif len(re.findall(r'[А-Яа-яЁёa-zA-Z0-9 -]+', message.text)) > 1:
        text_error = bot.send_message(message.chat.id,
                                    'Название состоит из букв\nПожалуйста, повторите ввод')
        bot.register_next_step_handler(text_error, checking_input_message)
    else:
        user_data_base[message.chat.id].language = checking_language(message.text)
        user_data_base[message.chat.id].search_city = message.text
        SearchHotel.search_city_data(bot, message)


def checking_method(message: types.Message, text_error: str) -> (bool, Callable):
    """
    Функция вызывается, если пользователь не следует цепочке опроса.

    :param message: полученное в чате сообщение
    :param text_error: текст с ошибкой
    :return: булево значение, функция
    """
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


def request_photo(message: types.Message) -> None:
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


def checking_numbers_of_hotels(message: types.Message) -> None:
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
            err_num = bot.send_message(message.chat.id, 'Введенное число не должно быть больше 25'
                                       '\nПожалуйста, введите 25 или меньше')
            bot.register_next_step_handler(err_num, checking_numbers_of_hotels)

        else:
            user_data_base[message.chat.id].number_of_hotels_to_display = int(message.text)
            if user_data_base[message.chat.id].search_method == 'best_deal':
                msg_price = bot.send_message(message.chat.id,
                                             'Введите диапазон цен через дефис\nНапример, 100-1000')
                bot.register_next_step_handler(msg_price, checking_entered_price_range)
            else:
                request_photo(message)


def checking_entered_price_range(message: types.Message) -> None:
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


def checking_entered_distance(message: types.Message) -> None:
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


def checking_entered_photo_count(message: types.Message) -> None:
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
            bot.send_message(message.chat.id, 'Введенное количество больше 4'
                             '\nБудет показано 4 фотографии')
        else:
            user_data_base[message.chat.id].count_show_photo = int(message.text)
        SearchHotel.search_hotels(bot, message.chat.id)


def price_button_reaction(button_result: types.CallbackQuery) -> None:
    """
    Функция записывает способ поиска в кэш пользователя.

    Запускает цепочку обработки
    :param button_result: результат нажатия кнопки
    """
    user_data_base[button_result.message.chat.id].search_method = (
        'PRICE' if button_result.data == 'low_price' else 'PRICE_HIGHEST_FIRST')
    bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
    message_what_city = bot.send_message(button_result.message.chat.id, 'Введите название города для поиска')
    bot.register_next_step_handler(message_what_city, checking_input_message)


def bestdeal_button_reaction(button_result: types.CallbackQuery) -> None:
    """
    Функция записывает способ поиска в кэш пользователя.

    Запускает цепочку обработки
    :param button_result: результат нажатия кнопки
    """
    user_data_base[button_result.message.chat.id].search_method = 'best_deal'
    bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
    message_what_city = bot.send_message(button_result.message.chat.id, 'В каком городе будем искать?')
    bot.register_next_step_handler(message_what_city, checking_input_message)


def choice_city_button_reaction(button_result: types.CallbackQuery) -> None:
    """
    Функция записывает выбор города из инлайн клавиатуры.

    Запускает цепочку обработки
    :param button_result: результат нажатия кнопки
    :return:
    """
    choice_city = int(re.sub(r'choice_city_', '', button_result.data))
    user_data_base[button_result.message.chat.id].id_city = \
        user_data_base[button_result.message.chat.id].cache_data['suggestions'][0]['entities'][choice_city][
            'destinationId']
    bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
    input_number_of_hotels = bot.send_message(button_result.message.chat.id,
                                              'Введите кол-во отелей'
                                              )
    bot.register_next_step_handler(input_number_of_hotels, checking_numbers_of_hotels)


def data_function_router(button_result: types.CallbackQuery) -> None:
    """
    Функция принимает результат нажатия на кнопки календаря

    и распределяет их по соответствующим действиям.
    Пользователь может выбрать день, смену месяца или кнопку без функционала
    :param button_result: результат нажатия кнопки
    :return:
    """
    name, action, year, month, day = button_result.data.split(':')
    if action == 'DAY':
        bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
        setting_checkin_checkout_date(button_result)

    elif action in ['NEXT-MONTH', 'PREVIOUS-MONTH']:
        bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
        if action == 'NEXT-MONTH':
            if int(month) < 12:
                month = str(int(month) + 1)
            else:
                year = str(int(year) + 1)
                month = str(1)
        elif action == 'PREVIOUS-MONTH':
            if int(month) == 1:
                month = str(12)
                year = str(int(year) - 1)
            else:
                month = str(int(month) - 1)
        show_calendar(bot, button_result.message, int(month), int(year))
    elif action == 'CANCEL':
        bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
        bot.send_message(button_result.message.chat.id, 'Выбрана команда отмены.\nЕсли хотите продолжить'
                                                        ', нажмите \'🔍 Найти отель\'')
    else:
        bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
        bot.send_message(button_result.message.chat.id, 'Выбрана НЕ дата.\nЕсли хотите продолжить'
                                                        ', нажмите \'🔍 Найти отель\'')


def show_calendar(bot, message: types.Message, month: int = 0, year: int = 0) -> None:
    """
    Создание inline-клавиатуры календаря

    :param bot: чат-бот
    :param message: Полученное в чате сообщение
    :param month: номер месяца
    :param year: год
    :return:
    """
    now = datetime.datetime.now()
    if month == 0:
        month = now.month
    if year == 0:
        year = now.year
    if user_data_base[message.chat.id].calendar_stage == 'check_in':
        request_for_user = '✅ Выберите дату въезда в отель'
    else:
        request_for_user = 'Дата въезда: {userdate}\n🅾️ Выберите дату выезда из отеля'.format(
            userdate=user_data_base[message.chat.id].checkin_date)
    bot.send_message(
        message.chat.id,
        request_for_user,
        reply_markup=calendar.create_calendar(
            name=calendar_1_callback.prefix,
            year=year,
            month=month,
        ),
    )


def setting_checkin_checkout_date(message: types.CallbackQuery) -> None:
    """
    Получает даты въезда и выезда, записывает их в базу данных

    :param message: Полученное в чате сообщение
    """

    name, action, year, month, day = message.data.split(':')
    if user_data_base[message.from_user.id].calendar_stage == 'check_in':
        if datetime.datetime.strptime(':'.join([year, month, day]), "%Y:%m:%d").date() \
                >= datetime.datetime.today().date():
            user_data_base[message.from_user.id].checkin_date = datetime.datetime.strptime(':'.join([year, month, day]),
                                                                                           "%Y:%m:%d").date()
            user_data_base[message.from_user.id].calendar_stage = 'check_out'
            show_calendar(bot=bot, message=message.message)
        else:
            bot.send_message(message.from_user.id, 'Выбрана некорректная дата, попробуйте еще раз')
            show_calendar(bot=bot, message=message.message)
    elif user_data_base[message.from_user.id].calendar_stage == 'check_out':
        if datetime.datetime.strptime(
                ':'.join([year, month, day]), "%Y:%m:%d").date() > user_data_base[message.from_user.id].checkin_date:
            user_data_base[message.from_user.id].checkout_date = datetime.datetime.strptime(
                ':'.join([year, month, day]), "%Y:%m:%d").date()
            choosing_search_method(message)
        else:

            bot.send_message(message.from_user.id, 'Выбрана некорректная дата, попробуйте еще раз')
