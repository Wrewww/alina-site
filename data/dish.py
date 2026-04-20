import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import datetime


class Dish(SqlAlchemyBase):
    __tablename__ = 'dishes'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(200),
                             nullable=False)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('users.id'))
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    total_weight = sqlalchemy.Column(sqlalchemy.Float, nullable=True)

    user = orm.relationship('User')
    ingredients = orm.relationship('DishIngredient',
                                   back_populates='dish',
                                   cascade='all, delete-orphan',
                                   lazy='joined')  

    @property
    def total_calories(self):
        return sum(i.calories for i in self.ingredients if i.product)

    @property
    def total_proteins(self):
        return sum(i.proteins for i in self.ingredients if i.product)

    @property
    def total_fats(self):
        return sum(i.fats for i in self.ingredients if i.product)

    @property
    def total_carbs(self):
        return sum(i.carbs for i in self.ingredients if i.product)

    @property
    def calories_per_100g(self):
        if self.total_weight and self.total_weight > 0:
            return (self.total_calories / self.total_weight) * 100
        elif self.ingredients:
            total_weight = sum(i.weight for i in self.ingredients)
            if total_weight > 0:
                return (self.total_calories / total_weight) * 100
        return 0