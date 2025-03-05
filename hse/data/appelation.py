import sqlalchemy
from .session import SqlAlchemyBase
from sqlalchemy import orm


class Appelation(SqlAlchemyBase):

    __tablename__ = 'appelations'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("users.id"))
    report_id = sqlalchemy.Column(sqlalchemy.Integer,
                                sqlalchemy.ForeignKey("reports.id"))
    # одобрено или отказано
    #success = sqlalchemy.Column(sqlalchemy.Integer,
    #                            nullable=None)
    report = orm.relationship("Report")
    user = orm.relationship('User')

