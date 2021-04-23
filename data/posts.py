import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    creator = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=True)
    user = orm.relation('User')

    text = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    # modified_date = sqlalchemy.Column(sqlalchemy.String,
    #                                 default=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    # для heroku: дата не будет отображаться
    modified_date = ''
    likes = sqlalchemy.Column(sqlalchemy.Integer)
