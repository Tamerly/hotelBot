from peewee import Model, SqliteDatabase, CharField, DateTimeField
from datetime import datetime

db = SqliteDatabase('file.db')


class UserHistory(Model):
    column_user_id = CharField()
    column_command = CharField()
    column_date = DateTimeField(default=datetime.now())
    column_hotels = CharField()

    class Meta:
        database = db
