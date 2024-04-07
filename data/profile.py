import sqlalchemy
from .session import SqlAlchemyBase
from sqlalchemy import orm


class Profile(SqlAlchemyBase):

    __tablename__ = 'profiles'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    information = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    interests = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    connection = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    image = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    is_allow_gps = sqlalchemy.Column(sqlalchemy.Boolean, nullable=True)
    user = orm.relationship('User')

    def __repr__(self):
        return f'<Job> {self.job}'
