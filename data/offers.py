import sqlalchemy as sqla

from globals import *
from .db_session import SqlAlchemyBase


class Offer(SqlAlchemyBase):
    __tablename__ = 'Offers'
    id = sqla.Column(sqla.Integer,
                     primary_key=True, autoincrement=True)
    author = sqla.Column(sqla.Integer)
    picture = sqla.Column(sqla.String(300), nullable=True)
    taker = sqla.Column(sqla.Integer, nullable=True)
    text = sqla.Column(sqla.String(1000), nullable=True)
    price = sqla.Column(sqla.Integer, nullable=True)
    type = sqla.Column(sqla.String(15), default="default")
