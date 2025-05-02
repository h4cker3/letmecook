import sqlalchemy as sqla
from flask_login import UserMixin

from globals import *
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'Users'
    id = sqla.Column(sqla.Integer,
                     primary_key=True, autoincrement=True)
    fio = sqla.Column(sqla.String(100), nullable=True)
    login = sqla.Column(sqla.String(30), unique=True)
    password = sqla.Column(sqla.String(100))
    role = sqla.Column(sqla.String(20), default=UserType.default)
    age = sqla.Column(sqla.Integer, nullable=True)
    telephone = sqla.Column(sqla.String(20), nullable=True)
    verified = sqla.Column(sqla.Integer, default=0)
