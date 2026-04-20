import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class Favorite(SqlAlchemyBase):
    __tablename__ = 'favorites'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('users.id'))
    dish_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('dishes.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=sqlalchemy.func.now())

    # Связи
    user = orm.relationship('User')
    dish = orm.relationship('Dish')