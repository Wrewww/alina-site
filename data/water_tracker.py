import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
import datetime


class WaterEntry(SqlAlchemyBase):
    __tablename__ = 'water_entries'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey('users.id'))
    amount = sqlalchemy.Column(sqlalchemy.Float, nullable=False)
    date = sqlalchemy.Column(sqlalchemy.Date, default=datetime.date.today)
    created_at = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)

    user = orm.relationship('User')

    def __repr__(self):
        return f'<WaterEntry> {self.amount}ml on {self.date}'