import sqlalchemy
from .session import SqlAlchemyBase
from sqlalchemy import orm
class Event(SqlAlchemyBase):

    __tablename__ = 'events'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    date_begin = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    date_end = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    #image = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    place = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    #reports = orm.relationship("Report", back_populates='event')
    user = orm.relationship('User')
