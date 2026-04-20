import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import datetime


class Meal(SqlAlchemyBase):
    __tablename__ = 'meals'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    meal_type = sqlalchemy.Column(sqlalchemy.String(20), nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Date, default=datetime.date.today)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User')
    dishes = orm.relationship('MealDish', back_populates='meal', cascade='all, delete-orphan')

    @property
    def total_calories(self):
        return sum(md.calories for md in self.dishes)

    @property
    def total_proteins(self):
        return sum(md.proteins for md in self.dishes)

    @property
    def total_fats(self):
        return sum(md.fats for md in self.dishes)

    @property
    def total_carbs(self):
        return sum(md.carbs for md in self.dishes)


class MealDish(SqlAlchemyBase):
    __tablename__ = 'meal_dishes'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    meal_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('meals.id'))
    dish_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('dishes.id'))
    grams = sqlalchemy.Column(sqlalchemy.Integer, default=100)

    meal = orm.relationship('Meal', back_populates='dishes')
    dish = orm.relationship('Dish')

    @property
    def calories(self):
        if self.dish and self.dish.total_weight and self.dish.total_weight > 0:
            return (self.dish.total_calories * self.grams) / self.dish.total_weight
        return 0

    @property
    def proteins(self):
        if self.dish and self.dish.total_weight and self.dish.total_weight > 0:
            return (self.dish.total_proteins * self.grams) / self.dish.total_weight
        return 0

    @property
    def fats(self):
        if self.dish and self.dish.total_weight and self.dish.total_weight > 0:
            return (self.dish.total_fats * self.grams) / self.dish.total_weight
        return 0

    @property
    def carbs(self):
        if self.dish and self.dish.total_weight and self.dish.total_weight > 0:
            return (self.dish.total_carbs * self.grams) / self.dish.total_weight
        return 0