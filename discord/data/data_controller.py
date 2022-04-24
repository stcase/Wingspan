import logging
import sys
import traceback
from collections.abc import Iterator

from discord.data.db_connection import DBConnection
from discord.data.models import MessageType
from wingspan_api.wapi import Match, Wapi, State

logger = logging.getLogger(__name__)


class DataController:
    def __init__(self, db_connection: DBConnection, wapi: Wapi) -> None:
        self.db = db_connection
        self.wapi = wapi

    def get_subscriptions(self, channel_id: int) -> dict[str, list[int]]:
        results = self.db.get_subscriptions(channel_id)

        wingspan_name_to_subscribers: dict[str, list[int]] = {}
        for result in results:
            if result.wingspan_name is None:
                raise ValueError(f"wingspan_name in {result} unexpectedly None")
            if result.wingspan_name is None:
                raise ValueError(f"discord_id in {result} unexpectedly None")
            if result.discord_id is None:
                raise ValueError(f"discord_id unexpected None in {result}")
            wingspan_name_to_subscribers.setdefault(result.wingspan_name, []).append(result.discord_id)
        return wingspan_name_to_subscribers

    def should_send_message(self, channel_id: int, match: Match | str) -> bool:
        previous_message = self.db.get_previous_message(channel_id, match)
        if previous_message is None:
            return True
        if previous_message.message_type != self.get_message_type(match):
            return True
        current_player = None if isinstance(match, str) else match.current_player_name
        if previous_message.player_turn != current_player:
            return True
        return False

    @staticmethod
    def get_message_type(match: Match | str) -> MessageType:
        if isinstance(match, str):
            return MessageType.ERROR
        if match.State == State.WAITING:
            return MessageType.WAITING
        if match.State == State.READY:
            return MessageType.READY
        if match.State == State.COMPLETED:
            return MessageType.GAME_COMPLETE
        if match.hours_remaining is None:
            raise ValueError("Unexpected None for hours_remaining")
        if match.hours_remaining <= 24:
            return MessageType.REMINDER
        return MessageType.NEW_TURN

    def get_matches(self, channel: int | None = None) -> Iterator[tuple[int, Match | str]]:
        monitored_matches = self.db.get_matches()
        if channel is not None:
            monitored_matches = {channel: monitored_matches.get(channel, [])}
        for channel, match_ids in monitored_matches.items():
            for match_id in match_ids:
                try:
                    # TODO: cache get_game_info for match_id
                    yield channel, self.wapi.get_game_info(match_id)
                except BaseException:
                    logger.error(f"Exception while getting data for match {match_id} in channel {channel}")
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                    yield channel, match_id

    def add(self, channel: int, game_id: str) -> bool:
        matches = self.db.get_matches().get(channel, [])
        if game_id in matches:
            return False
        else:
            self.wapi.get_game_info(game_id)  # raises if there's no game
            self.db.add_match(channel, game_id)
            return True

    def remove(self, channel: int, game_id: str) -> bool:
        matches = self.db.get_matches().get(channel, [])
        if game_id not in matches:
            return False
        else:
            self.db.remove_match(channel, game_id)
            return True

    def subscribe(self, channel: int, subscriber_id: int, wingspan_name: str) -> bool:
        subscriptions = self.get_subscriptions(channel)
        if subscriber_id in subscriptions.get(wingspan_name, []):
            return False
        else:
            self.db.add_subscriptions(channel, subscriber_id, wingspan_name)
            return True

    def unsubscribe(self, channel: int, subscriber_id: int, wingspan_name: str) -> bool:
        subscriptions = self.get_subscriptions(channel)
        if subscriber_id not in subscriptions.get(wingspan_name, []):
            return False
        else:
            self.db.remove_subscription(channel, subscriber_id, wingspan_name)
            return True
