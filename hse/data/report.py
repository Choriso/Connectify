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
                sqlalchemy.ForeignKey("interests.id"))

    # одобрено или отказано
    #success = sqlalchemy.Column(sqlalchemy.Integer,default=0, nullable=True)

    interest = orm.relationship("Interest")
    user = orm.relationship('User')

