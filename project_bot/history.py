from project_bot.models import *
from project_bot.loader import user_data_base, bot


def saving_history(user_id):
    """
    Функция сохраняет историю поиска в таблицу UserHistory по ключам
    column_user_id, column_command, column_hotels и column_date (сохраняет текущую дату при вызове)
    :param user_id: int уникальный id пользователя
    :return:
    """
    hotels = []
    for element in user_data_base[user_id].cache_data['data']['body']['searchResults']['results']:
        name = element["name"]
        country = element["address"].get("countryName")
        city = element["address"].get("locality")
        street = element["address"].get("streetAddress") if element["address"].get("streetAddress") else ""
        price = element["ratePlan"]["price"]["current"]
        addendum = (name, country, city, street, price)
        hotels.append(addendum)

    command = str()
    if user_data_base[user_id].search_method == 'PRICE':
        command = 'lowprice'
    elif user_data_base[user_id].search_method == 'PRICE_HIGHEST_FIRST':
        command = 'highprice'
    elif user_data_base[user_id].search_method == 'best_deal':
        command = 'bestdeal'
    with db:
        db.create_tables([UserHistory])
        UserHistory(column_user_id='{}'.format(user_id),
                    column_command='{}'.format(command),
                    column_hotels='{}'.format(hotels)).save()


def show_history(message):
    """
    Функция собирает информацию из базы данных по column_user_id,
    формирует сообщение и отправляет его в чат.
    В случае, если пользователя еще нет в базе, срабатывает блок else
    :param message: объект входящего сообщения от пользователя
    :return:
    """
    with db:
        history_message = ''
        user_history = UserHistory.select().where(UserHistory.column_user_id == message.from_user.id)
        if user_history:
            for i in user_history:
                history_message += '\n' + str(i.column_date)
                history_message += '\nМетод поиска /' + i.column_command
                hotels = ''
                for hotel_info in eval(i.column_hotels):
                    name = hotel_info[0]
                    country = hotel_info[1]
                    city = hotel_info[2]
                    street = hotel_info[3]
                    price = hotel_info[4]
                    hotels += f'\n{name}\n{country}, {city}, {street}\nЦена: {price}'
                history_message += hotels + '\n'
            bot.send_message(message.chat.id, history_message)
        else:
            bot.send_message(message.chat.id, 'История поиска отсутствует')
