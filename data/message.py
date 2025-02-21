from data.session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import orm
from datetime import datetime

class Message(SqlAlchemyBase):
    __tablename__ = "messages"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    author = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    file_url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
    message_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)
