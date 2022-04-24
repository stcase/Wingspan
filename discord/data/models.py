import enum

from sqlalchemy import Column, Integer, String, DateTime, Enum
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Monitor(Base):
    __tablename__ = "match"
    id = Column(Integer, primary_key=True)
    match_id = Column(String, nullable=False)
    channel = Column(Integer, nullable=False)
    added = Column(DateTime, nullable=False)
    removed = Column(DateTime, nullable=True)


class MessageType(enum.Enum):
    ERROR = "error"
    NEW_TURN = "new_turn"
    REMINDER = "reminder"
    GAME_COMPLETE = "complete"
    WAITING = "waiting"
    READY = "ready"


class StatusMessage(Base):
    __tablename__ = "status_message"
    id = Column(Integer, primary_key=True)
    match_id = Column(String, nullable=False)
    channel = Column(Integer, nullable=False)
    datetime = Column(DateTime, nullable=False)
    player_turn = Column(String, nullable=True)
    message_type = Column(Enum(MessageType), nullable=False)


class Subscription(Base):
    __tablename__ = "subscription"
    id = Column(Integer, primary_key=True)
    channel = Column(Integer, nullable=False)
    discord_id = Column(Integer, nullable=False)
    wingspan_name = Column(String, nullable=False)
