from telebot import types
from project_bot.loader import bot, user_data_base, Users
from project_bot.handler import checking_entered_photo_count, show_calendar, data_function_router, \
    price_button_reaction, bestdeal_button_reaction, choice_city_button_reaction
from project_bot.radapi import SearchHotel
from project_bot.history import show_history

info = '● /help — помощь по командам бота\n' \
       '● /lowprice — вывод самых дешёвых отелей в городе\n' \
       '● /highprice — вывод самых дорогих отелей в городе\n' \
       '● /bestdeal — вывод отелей, наиболее подходящих по цене и расположению от центра\n' \
       '● /history - вывод истории поиска отелей'


@bot.message_handler(commands=['start', 'help', 'lowprice', 'highprice', 'bestdeal', 'history'])
def handle_start_help(message: types.Message):
    """
    Функция-обработки входящих сообщений: /start, /help, /lowprice, /highprice, /bestdeal, /history

    :param message: объект входящего сообщения от пользователя
    :type: message: types.Message
    """
    if not user_data_base.get(message.from_user.id):
        user_data_base[message.from_user.id] = Users(message)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=False)
    btn_a = types.KeyboardButton('🔍 Найти отель')
    btn_b = types.KeyboardButton('📖 Руководство')
    btn_c = types.KeyboardButton('ℹ️Информация')
    markup.row(btn_a, btn_b)
    markup.row(btn_c)

    if message.text == '/start':
        start_help_text = "Приветствую {user},\n" \
                          "Чтобы начать, нажмите кнопку \"🔍 Найти отель\"".format(
            user=user_data_base[message.from_user.id].username
        )
        bot.send_message(message.from_user.id, start_help_text, reply_markup=markup)

    elif message.text == '/help':
        bot.send_message(message.from_user.id, info, reply_markup=markup)

    elif message.text in ['/lowprice', '/highprice']:
        user_data_base[message.from_user.id].clear_cache()
        if message.text == '/lowprice':
            user_data_base[message.from_user.id].search_method = 'PRICE'
        else:
            user_data_base[message.from_user.id].search_method = 'PRICE_HIGHEST_FIRST'
        show_calendar(bot=bot, message=message)
    elif message.text == '/bestdeal':
        user_data_base[message.from_user.id].clear_cache()
        user_data_base[message.from_user.id].search_method = 'best_deal'
        show_calendar(bot=bot, message=message)
    elif message.text == '/history':
        show_history(message)


@bot.message_handler(content_types=['text'])
def handler_for_commands_and_buttons(message: types.Message):
    """
    Функция-обработчик входящих сообщений:

    1. '🔍 Найти отель' - выдаст пользователю в окне мессенджера варианты поиска отелей.
    2. '📖 Руководство' - краткое руководство пользователя.
    3. 'ℹ️Информация' - вводное сообщение.
    :param message: объект входящего сообщения от пользователя
    :type: message: types.Message
    """
    if not user_data_base.get(message.from_user.id):
        user_data_base[message.from_user.id] = Users(message)

    if message.text == '🔍 Найти отель':
        user_data_base[message.from_user.id].clear_cache()
        show_calendar(bot=bot, message=message)

    elif message.text == '📖 Руководство':
        bot.send_message(message.from_user.id, info)
    elif message.text == 'ℹ️Информация':
        bot.send_message(message.from_user.id,
                         'Telegram-бот для поиска отелей. Дипломный проект Skillbox')


@bot.callback_query_handler(func=lambda button_result: True)
def inline(button_result: types.CallbackQuery):
    """
    Функция-обработчик возвращаемого значения при клике "кнопки" пользователем в окне мессенджера.

    :param button_result: response объекта от пользователя при клике на кнопки.
    :return:
    """
    if button_result.data.startswith('calendar'):
        try:
            data_function_router(button_result)

        except ValueError:
            bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
            bot.send_message(button_result.message.chat.id, 'Дата выбрана некорректно.\nПерезапустите бота')
    else:
        if button_result.data in ['low_price', 'high_price']:
            price_button_reaction(button_result)

        elif button_result.data == 'best_deal':
            bestdeal_button_reaction(button_result)

        elif button_result.data.startswith('choice_city_'):
            choice_city_button_reaction(button_result)

        elif button_result.data in ['yes_photo', 'no_photo']:
            user_data_base[button_result.message.chat.id].photo = (True if button_result.data == 'yes_photo' else False)
            bot.delete_message(button_result.message.chat.id, button_result.message.message_id)
            if user_data_base[button_result.message.chat.id].photo:
                msg2 = bot.send_message(button_result.message.chat.id,
                                        'Введите количество фотографий - максимум 4')
                bot.register_next_step_handler(msg2, checking_entered_photo_count)
            else:
                user_id = button_result.message.chat.id
                SearchHotel.search_hotels(bot, user_id)


if __name__ == '__main__':
    while True:
        bot.polling(none_stop=True, interval=0)
