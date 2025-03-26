from data.session import SqlAlchemyBase
import sqlalchemy
from sqlalchemy import orm
from datetime import datetime

class Message(SqlAlchemyBase):
    __tablename__ = "messages"

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    chat_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("chats.id"), nullable=False)
    author_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("users.id"), nullable=False)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    file_url = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    timestamp = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.utcnow)
    message_type = sqlalchemy.Column(sqlalchemy.String, nullable=False)

    chat = orm.relationship("Chat", back_populates="messages")
    author = orm.relationship("User", back_populates="messages")
