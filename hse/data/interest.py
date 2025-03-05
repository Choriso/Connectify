import sqlalchemy
from .session import SqlAlchemyBase
from sqlalchemy import orm


class Interest(SqlAlchemyBase):

    __tablename__ = 'interests'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    # image of interest
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    reports = orm.relationship("Report", back_populates='interest')

    user = orm.relationship('User')

