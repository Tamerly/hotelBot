from telebot import TeleBot
from dotenv import dotenv_values
from telebot_calendar import Calendar, CallbackData, RUSSIAN_LANGUAGE


user_data_base = dict()
config = dotenv_values(".env")
bot = TeleBot(config['TELEGRAM_API_TOKEN'])

calendar = Calendar(language=RUSSIAN_LANGUAGE)
calendar_1_callback = CallbackData("calendar_1", "action", "year", "month", "day")


class Users:

    def __init__(self, user) -> None:
        self.username: str = user.from_user.username
        self.id_user: int = user.from_user.id
        self._search_method = None
        self._search_city = None
        self._id_city = None
        self._language = 'ru_RU'
        self._cache_data = None
        self._number_of_hotels_to_display = None
        self._price_min_max: dict = dict()
        self._distance_min_max: dict = dict()
        self._photo = None
        self._count_show_photo = None
        self._checkin_date = None
        self._checkout_date = None
        self._calendar_stage = 'check_in'

    def clear_cache(self) -> None:
        """
        Очистка кэша атрибутов поиска отеля.
        """
        self._search_method = None
        self._search_city = None
        self._cache_data = None
        self._checkin_date = None
        self._checkout_date = None
        self._calendar_stage = 'check_in'
        self._language = 'ru_RU'

    @property
    def search_method(self) -> str:
        """
        Геттер метода поиска отелей
        :return: _search_method
        :rtype: str
        """
        return self._search_method

    @search_method.setter
    def search_method(self, method: str) -> None:
        """
        Сеттер метода поиска отелей
        :param method: город
        """
        self._search_method = method

    @property
    def language(self) -> str:
        """
        Геттер метода языка
        :return: _language
        :rtype: str
        """
        return self._language

    @language.setter
    def language(self, language: str) -> None:
        """
        Сеттер метода языка
        :param language: язык
        """
        self._language: str = language

    @property
    def search_city(self):
        """
        Геттер искомого города
        :return: __search_city
        :rtype: str
        """
        return self._search_city

    @search_city.setter
    def search_city(self, city: str) -> None:
        """
        Сеттер искомого города
        :param city: город
        """
        self._search_city = city

    @property
    def checkin_date(self):
        """
        Геттер даты бронирования
        :return: __checkin_date
        :rtype: str
        """
        return self._checkin_date

    @checkin_date.setter
    def checkin_date(self, date) -> None:
        """
        Сеттер даты бронирования
        :param date: дата
        """
        self._checkin_date = date

    @property
    def checkout_date(self):
        """
        Геттер даты бронирования
        :return: __checkout_date
        :rtype: str
        """
        return self._checkout_date

    @checkout_date.setter
    def checkout_date(self, date) -> None:
        """
        Сеттер даты бронирования
        :param date: дата
        """
        self._checkout_date = date

    @property
    def calendar_stage(self):
        """
        Геттер состояния для вызова календаря
        :return: __calendar_stage
        :rtype: str
        """
        return self._calendar_stage

    @calendar_stage.setter
    def calendar_stage(self, stage) -> None:
        """
        Сеттер состояния для вызова календаря
        :param stage: stage
        """
        self._calendar_stage = stage

    @property
    def cache_data(self):
        """
        Геттер кэша с информацией
        :return: _cache_data
        :rtype: [dict, list]
        """
        return self._cache_data

    @cache_data.setter
    def cache_data(self, data: [dict, list]) -> None:
        """
        Сеттер кэша с информацией
        :param data:
        """
        self._cache_data: [dict, list] = data

    @property
    def number_of_hotels_to_display(self):
        """
        Геттер количества отелей
        :return: _count_show_hotels
        :rtype: int
        """
        return self._number_of_hotels_to_display

    @number_of_hotels_to_display.setter
    def number_of_hotels_to_display(self, number: str) -> None:
        """
        Сеттер количества отелей
        :param number: кол-во отелей для поиска
        """
        self._number_of_hotels_to_display = int(number)

    @property
    def id_city(self):
        """
        Геттер id города
        :return: _id_city
        :rtype: int
        """
        return self._id_city

    @id_city.setter
    def id_city(self, id_city: int) -> None:
        """
        Сеттер id города
        :param id_city: номер города
        """
        self._id_city = id_city

    @property
    def price_min_max(self):
        """
        Геттер минимальной и максимальной цены искомого отеля
        :return: _price_min_max
        :rtype: dict
        """
        return self._price_min_max

    @price_min_max.setter
    def price_min_max(self, price_min_max: dict) -> None:
        """
        Сеттер минимальной и максимальной цены искомого отеля
        """
        self._price_min_max = price_min_max

    @property
    def distance_min_max(self):
        """
        Геттер диапазона поиска отелей между минимальным и максимальным расстоянием
        :return: _distance_min_max
        :rtype: dict
        """
        return self._distance_min_max

    @distance_min_max.setter
    def distance_min_max(self, distance_min_max: dict) -> None:
        """
        Сеттер диапазона поиска отелей между минимальным и максимальным расстоянием
        """
        self._distance_min_max = distance_min_max

    @property
    def photo(self):
        """
        Геттер bool значения поиска фотографий отелей.
        :return: _photo
        :rtype: bool
        """
        return self._photo

    @photo.setter
    def photo(self, flag: bool) -> None:
        """
        Сеттер bool значения поиска фотографий отелей
        """
        self._photo: bool = flag

    @property
    def count_show_photo(self):
        """
        Геттер кол-ва отображаемых фотографий
        :return: _count_show_photo
        :rtype: int
        """
        return self._count_show_photo

    @count_show_photo.setter
    def count_show_photo(self, number: str) -> None:
        """
        Сеттер кол-ва отображаемых фотографий
        """
        self._count_show_photo: int = int(number)
