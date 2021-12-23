import json
import re
import requests
from project_bot.loader import config, user_data_base, bot
from telebot import types, apihelper, TeleBot
from project_bot.history import saving_history


class SearchHotel:
    """
    Класс направленный на парсинг информации получаемой от request.
    """
    headers = {
        'x-rapidapi-key': config['RAPID_API_TOKEN'],
        'x-rapidapi-host': "hotels4.p.rapidapi.com"
    }

    @classmethod
    def search_city_data(cls, bot: TeleBot, message: types.Message) -> None:
        """
        Функция отправляет get запрос на сервер для получения информации,
        уточняет искомый город, записывает в объект User кеш ответа,
        отправляет список кликабельных городов.

        :param bot: объект телеграмм бота
        :param message: объект входящего сообщения от пользователя
        """
        url = "https://hotels4.p.rapidapi.com/locations/v2/search"
        querystring = {"query": message.text, "locale": user_data_base[message.chat.id].language}
        sys_message = bot.send_message(message.from_user.id, 'Идет поиск информации по городу')
        try:
            response = requests.get(url, headers=cls.headers, params=querystring, timeout=10)
            user_data_base[message.from_user.id].cache_data = json.loads(response.text)
            patterns_span = re.compile(r'<.*?>')
            cls.generating_buttons_list_for_city_clarification(bot=bot, message=message, patterns=patterns_span)
        except requests.exceptions.ConnectTimeout:
            bot.send_message(message.from_user.id, 'Возникла ошибка при поиске. Пожалуйста, попробуйте позднее')

    @classmethod
    def generating_buttons_list_for_city_clarification(cls, bot: TeleBot, message: types.Message,
                                                       patterns: re.Pattern) -> None:
        """
        Функция составляет и отправляет в чат список кликабельных городов в случае нахождения,
        или отправляет сообщение о том, что город не найден

        :param bot: объект телеграмм бота
        :param message: объект входящего сообщения от пользователя
        :param patterns: class 're.Pattern'
        :return:
        """
        if user_data_base[message.from_user.id].cache_data['suggestions'][0]['entities']:
            markup = types.InlineKeyboardMarkup()
            count = 0
            for entities_city in user_data_base[message.from_user.id].cache_data['suggestions'][0]['entities']:
                add = types.InlineKeyboardButton(text=patterns.sub('', entities_city['caption']),
                                                 callback_data='choice_city_{count}'.format(count=count), )
                markup.add(add)
                count += 1
            bot.send_message(message.from_user.id, "Уточните город", reply_markup=markup)
        else:
            bot.send_message(message.from_user.id, 'К сожалению, по данному городу нет данных')

    @classmethod
    def search_hotels(cls, bot: TeleBot, user_id: int) -> None:
        """
        Функция поиска отелей по выбранным параметрам метода поиска

        :param bot: объект телеграмм бота
        :param user_id: int уникальный id пользователя
        """
        url = "https://hotels4.p.rapidapi.com/properties/list"

        querystring = {
            "destinationId": user_data_base[user_id].id_city,
            "pageNumber": "1",
            "pageSize": f"{user_data_base[user_id].number_of_hotels_to_display}",
            "checkIn": user_data_base[user_id].checkin_date,
            "checkOut": user_data_base[user_id].checkout_date,
            "adults1": "1",
            "sortOrder": user_data_base[user_id].search_method,
            "locale": user_data_base[user_id].language,
            "currency": "RUB",
            "landmarkIds": "city center"
        }

        if user_data_base[user_id].search_method == 'best_deal':
            querystring.update({"priceMin": user_data_base[user_id].price_min_max['min'],
                                "priceMax": user_data_base[user_id].price_min_max['max'],
                                "sortOrder": "PRICE",
                                "landmarkIds": "city center"}
                               )
        sys_message = bot.send_message(user_id, 'Идет поиск отелей')
        response = requests.get(url, headers=cls.headers, params=querystring)
        user_data_base[user_id].cache_data = json.loads(response.text)
        apihelper.delete_message(config['TELEGRAM_API_TOKEN'], sys_message.chat.id,
                                 sys_message.id)
        cls.show_hotels(user_id)

    @classmethod
    def show_hotels(cls, user_id: int) -> None:
        """
        Функция собирает информацию из спарсенного кэша подготовленное сообщение,
        собирает список фотографий, если они были запрошены,
        и отправляет в чат подготовленные сообщения

        :param user_id: int уникальный id пользователя
        """
        url_get_photo = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        best_deal_view = 0
        for i in user_data_base[user_id].cache_data['data']['body']['searchResults']['results']:
            if user_data_base[user_id].distance_min_max \
                    and user_data_base[user_id].search_method == 'best_deal':
                min_dist = user_data_base[user_id].distance_min_max.get('min')
                max_dist = user_data_base[user_id].distance_min_max.get('max')
                dist_center = int(re.findall(r'\d+', i["landmarks"][0]["distance"])[0])
                if not min_dist <= dist_center <= max_dist:
                    continue
                else:
                    best_deal_view += 1
                    if best_deal_view > user_data_base[user_id].number_of_hotels_to_display:
                        break
            i_text = '*Название: {name}*\nАдрес: {address}, {address_locality}, {street_address}\n' \
                     'От центра города: {distance}\nЦена {price}\n\n'.format(
                                                                        name=i["name"],
                                                                        address=i["address"].get("countryName"),
                                                                        address_locality=i["address"].get("locality"),
                                                                        street_address=i["address"].get("streetAddress")
                                                                        if i["address"].get("streetAddress")
                                                                        else "",
                                                                        distance=i["landmarks"][0]["distance"],
                                                                        price=i["ratePlan"]["price"]["current"]
                                                                        )
            if user_data_base[user_id].photo:
                sys_message = bot.send_message(user_id, 'Идет поиск фото отеля *{name}*'.format(name=i["name"]))
                response = requests.get(url_get_photo, headers=cls.headers, params={"id": i["id"]})
                data = json.loads(response.text)
                if data:
                    photo_list = [
                        types.InputMediaPhoto(data['hotelImages'][0]['baseUrl'].format(size='l'), caption=i_text,
                                              parse_mode="Markdown")
                    ]
                    if len(data['hotelImages']) < user_data_base[user_id].count_show_photo:
                        count_photo = len(data['hotelImages'])
                    else:
                        count_photo = user_data_base[user_id].count_show_photo
                    if count_photo > 1:
                        for index in range(1, count_photo):
                            photo_list.append(
                                types.InputMediaPhoto(data['hotelImages'][index]['baseUrl'].format(size='l')))
                    bot.send_media_group(user_id, photo_list)
                    apihelper.delete_message(config['TELEGRAM_API_TOKEN'], sys_message.chat.id,
                                             sys_message.id)
                    photo_list.clear()
            else:
                bot.send_message(user_id, i_text)
            bot.send_message(user_id, 'https://ru.hotels.com/ho{hotel_id}'.format(hotel_id=i['id']))
        if best_deal_view == 0 and user_data_base[user_id].search_method == 'best_deal':
            bot.send_message(user_id, 'Подходящих отелей не найдено')
        saving_history(user_id)
        bot.send_message(user_id, 'Поиск завершен')
