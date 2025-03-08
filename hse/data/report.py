import sqlalchemy
from .session import SqlAlchemyBase
from sqlalchemy import orm


class Report(SqlAlchemyBase):

    __tablename__ = 'reports'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    interest_id = sqlalchemy.Column(sqlalchemy.Integer,
                sqlalchemy.ForeignKey("interests.id"), nullable=True)
    #event_id = sqlalchemy.Column(sqlalchemy.Integer,
    #            sqlalchemy.ForeignKey("events.id"), nullable=True)
    # одобрено или отказано
    #success = sqlalchemy.Column(sqlalchemy.Integer,default=0, nullable=True)
    #event = orm.relationship("Event")
    interest = orm.relationship("Interest")
    user = orm.relationship('User')

