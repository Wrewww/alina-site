import sqlalchemy
from .db_session import SqlAlchemyBase


class Product(SqlAlchemyBase):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String(200),
                             nullable=False, index=True)
    calories = sqlalchemy.Column(sqlalchemy.Float, nullable=False)  # на 100г
    proteins = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    fats = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    carbs = sqlalchemy.Column(sqlalchemy.Float, nullable=False)

    def __repr__(self):
        return f'<Product> {self.name}'