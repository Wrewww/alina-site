from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db_session import SqlAlchemyBase


class PersonalProduct(SqlAlchemyBase):
    __tablename__ = 'personal_products'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    calories = Column(Float, default=0)
    proteins = Column(Float, default=0)
    fats = Column(Float, default=0)
    carbs = Column(Float, default=0)
    user_id = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.now)

    user = relationship('User', back_populates='personal_products')