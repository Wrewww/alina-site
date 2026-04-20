import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm


class DishIngredient(SqlAlchemyBase):
    __tablename__ = 'dish_ingredients'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    dish_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('dishes.id'))
    ingredient_id = sqlalchemy.Column(sqlalchemy.Integer,
                                      sqlalchemy.ForeignKey('products.id'))
    weight = sqlalchemy.Column(sqlalchemy.Float, nullable=False)

    dish = orm.relationship('Dish', back_populates='ingredients')
    product = orm.relationship('Product')

    @property
    def calories(self):
        try:
            cal = float(self.product.calories) if self.product else 0
            return (cal * self.weight) / 100
        except (TypeError, ValueError):
            return 0

    @property
    def proteins(self):
        try:
            prot = float(self.product.proteins) if self.product else 0
            return (prot * self.weight) / 100
        except (TypeError, ValueError):
            return 0

    @property
    def fats(self):
        try:
            fat = float(self.product.fats) if self.product else 0
            return (fat * self.weight) / 100
        except (TypeError, ValueError):
            return 0

    @property
    def carbs(self):
        try:
            carb = float(self.product.carbs) if self.product else 0
            return (carb * self.weight) / 100
        except (TypeError, ValueError):
            return 0

    def __repr__(self):
        product_name = self.product.name if self.product else "Unknown"
        return f'<DishIngredient> {product_name} - {self.weight}г'