from datetime import datetime, timezone
from typing import Type

from sqlalchemy import create_engine, select, delete, update, desc, func, Column, Integer
from sqlalchemy.engine import Row
from sqlalchemy.orm import sessionmaker

from discord.data.models import Subscription, Monitor, StatusMessage, MessageType, Score
from wingspan_api.wapi import Match


def current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc)


class DBConnection:
    def __init__(self, db_connection: str):
        self.engine = create_engine(db_connection, future=True)
        self.Session = sessionmaker(self.engine)

    def add_or_update_score(self, match: Match) -> None:
        if match.StateData is None:
            raise ValueError(f"StateData in match {match} is unexpectedly None")
        with self.Session.begin() as session:
            for score in match.StateData.scores:
                player_name = match.get_player_username(score.ID)
                player_name = "AI/Computer" if player_name is None else player_name
                session.merge(Score(
                    match_id=match.MatchID,
                    updated=current_utc_datetime(),
                    player_name=player_name,
                    score=score.Score,
                    bird_points=score.BirdPoints,
                    bonus_card_points=score.BonusCardPoints,
                    goals_points=score.GoalsPoints,
                    eggs_points=score.EggsPoints,
                    cached_food_points=score.CachedFoodPoints,
                    tucked_cards_points=score.TuckedCardsPoints,
                    food_tokens=score.FoodTokens))

    def get_highest_score(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.score)

    def get_highest_bird_points(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.bird_points)

    def get_highest_bonus_card_points(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.bonus_card_points)

    def get_highest_goals_points(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.goals_points)

    def get_highest_eggs_points(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.eggs_points)

    def get_highest_cached_food_points(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.cached_food_points)

    def get_highest_tucked_cards_points(self, match: Match | str | None = None) -> list[Row]:
        return self._get_highest_score(match, Score.tucked_cards_points)

    def _get_highest_score(self, match: Match | str | None, score_type: Type[Column[Integer]]) -> list[Row]:
        with self.Session() as session:
            max_score = select(func.max(score_type))
            statement = select(Score.player_name, score_type)
            if match is not None:
                statement = statement.filter(Score.match_id == str(match))
                max_score = max_score.filter(Score.match_id == str(match))
            statement = statement.filter(score_type == max_score.scalar_subquery())
            return session.execute(statement).all()

    def get_scores(self, match: Match | str) -> list[Score]:
        with self.Session() as session:
            return session.execute(select(Score).filter_by(match_id=str(match))).scalars().all()

    def get_previous_message(self, channel: int, match: str | Match) -> StatusMessage | None:
        match_id = str(match)
        with self.Session() as session:
            result = session.execute(select(StatusMessage).filter_by(channel=channel, match_id=match_id).order_by(
                desc("datetime"))).scalars().first()
        return result

    def add_message(self, match: Match | str, channel: int, player: str | None, message_type: MessageType) -> None:
        match_id = str(match)
        with self.Session.begin() as session:
            session.add(StatusMessage(
                match_id=match_id,
                channel=channel,
                datetime=current_utc_datetime(),
                player_turn=player,
                message_type=message_type))

    def get_matches(self) -> list[Monitor]:
        with self.Session() as session:
            return session.execute(select(Monitor).filter(Monitor.removed.is_(None))).scalars().all()

    def get_data_start(self, channel_id: int, match: str | Match | None = None) -> datetime | None:
        with self.Session() as session:
            statement = select(func.min(Monitor.added)).filter(Monitor.channel == channel_id)
            if match is not None:
                statement = statement.filter(Monitor.match_id == str(match))
            return session.execute(statement).scalar()

    def remove_match(self, channel: int, match_id: str) -> None:
        with self.Session.begin() as session:
            session.execute(update(Monitor).filter_by(channel=channel, match_id=match_id).values(
                removed=current_utc_datetime()))

    def add_match(self, channel: int, match_id: str) -> None:
        with self.Session.begin() as session:
            session.add(Monitor(match_id=match_id, channel=channel, added=current_utc_datetime()))

    def get_subscriptions(self, channel: int) -> list[Subscription]:
        with self.Session() as session:
            return session.execute(select(Subscription).filter_by(channel=channel)).scalars().all()

    def remove_subscription(self, channel: int, discord_id: int, wingspan_name: str) -> None:
        with self.Session.begin() as session:
            session.execute(delete(Subscription).filter_by(
                channel=channel, discord_id=discord_id, wingspan_name=wingspan_name))

    def add_subscriptions(self, channel: int, discord_id: int, wingspan_name: str) -> None:
        with self.Session.begin() as session:
            session.add(Subscription(channel=channel, discord_id=discord_id, wingspan_name=wingspan_name))

    def get_messages(self, channel: int, match: Match | str | None = None) -> list[StatusMessage]:
        with self.Session() as session:
            statement = select(StatusMessage).filter(StatusMessage.channel == channel).order_by(StatusMessage.datetime)
            if match is not None:
                statement = statement.filter(StatusMessage.match_id == str(match))
            return session.execute(statement).scalars().all()
