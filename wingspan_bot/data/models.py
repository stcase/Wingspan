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
    GAME_TIMEOUT = "timeout"
    GAME_FORFEIT = "forfeit"
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


class Score(Base):
    __tablename__ = "score"
    match_id = Column(String, primary_key=True)
    player_name = Column(String, primary_key=True)
    updated = Column(DateTime, nullable=False)
    score = Column(Integer, nullable=False)
    bird_points = Column(Integer, nullable=False)
    bonus_card_points = Column(Integer, nullable=False)
    goals_points = Column(Integer, nullable=False)
    eggs_points = Column(Integer, nullable=False)
    cached_food_points = Column(Integer, nullable=False)
    tucked_cards_points = Column(Integer, nullable=False)
    food_tokens = Column(Integer, nullable=False)
