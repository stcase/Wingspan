from datetime import datetime, timezone

from sqlalchemy import create_engine, select, delete, update, desc
from sqlalchemy.orm import sessionmaker

from discord.data.models import Subscription, Monitor, StatusMessage, MessageType
from wingspan_api.wapi import Match


def current_utc_datetime() -> datetime:
    return datetime.now(timezone.utc)


class DBConnection:
    def __init__(self, db_connection: str):
        self.engine = create_engine(db_connection, future=True)
        self.Session = sessionmaker(self.engine)

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

    def get_matches(self) -> dict[int, list[str]]:
        with self.Session() as session:
            results = session.execute(select(Monitor).filter(Monitor.removed.is_(None))).scalars().all()

        channel_to_matches: dict[int, list[str]] = {}
        for result in results:
            channel_to_matches.setdefault(result.channel, []).append(result.match_id)
        return channel_to_matches

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
