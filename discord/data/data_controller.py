import logging
import sys
import traceback
from collections.abc import Iterator
from datetime import datetime
from statistics import mean
from typing import overload

from discord.data.data_objects import ScoreStats, PlayerStat, FastestPlayer
from discord.data.db_connection import DBConnection
from discord.data.models import MessageType
from wingspan_api.wapi import Match, Wapi, MatchState

logger = logging.getLogger(__name__)


class DataController:
    def __init__(self, db_connection: DBConnection, wapi: Wapi) -> None:
        self.db = db_connection
        self.wapi = wapi

    def add_message(self, match: Match | str, channel: int, player: str | None, message_type: MessageType) -> None:
        self.db.add_message(match, channel, player, message_type)

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
        if match.State == MatchState.WAITING:
            return MessageType.WAITING
        if match.State == MatchState.READY:
            return MessageType.READY
        if match.is_timed_out():
            return MessageType.GAME_TIMEOUT
        if match.State == MatchState.COMPLETED:
            return MessageType.GAME_COMPLETE
        if match.hours_remaining is None:
            raise ValueError("Unexpected None for hours_remaining")
        if match.hours_remaining <= 24:
            return MessageType.REMINDER
        return MessageType.NEW_TURN

    def get_data_start(self, channel_id: int, match: Match | str | None = None) -> datetime | None:
        return self.db.get_data_start(channel_id, match)

    @overload
    def get_monitored_matches(self, channel_id: int) -> list[str]:
        ...

    @overload
    def get_monitored_matches(self, channel_id: None = None) -> dict[int, list[str]]:
        ...

    def get_monitored_matches(self, channel_id: int | None = None) -> list[str] | dict[int, list[str]]:
        channel_to_matches: dict[int, list[str]] = {}
        for result in self.db.get_matches():
            if result.match_id is None or result.channel is None:
                raise ValueError(f"Unexpected None values when getting matches for channel {channel_id}")
            channel_to_matches.setdefault(result.channel, []).append(result.match_id)
        if channel_id is not None:
            return channel_to_matches.get(channel_id, [])
        return channel_to_matches

    def get_matches(self, channel: int | None = None) -> Iterator[tuple[int, Match | str]]:
        monitored_matches = self.get_monitored_matches()
        if channel is not None:
            monitored_matches = {channel: self.get_monitored_matches(channel)}
        for channel, match_ids in monitored_matches.items():
            for match_id in match_ids:
                try:
                    # TODO: cache get_game_info for match_id
                    match = self.wapi.get_game_info(match_id)
                    self.db.add_or_update_score(match)
                    yield channel, match
                except BaseException:
                    logger.error(f"Exception while getting data for match {match_id} in channel {channel}")
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    logger.error("".join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
                    yield channel, match_id

    def add(self, channel: int, game_id: str) -> bool:
        matches = self.get_monitored_matches().get(channel, [])
        if game_id in matches:
            return False
        else:
            self.wapi.get_game_info(game_id)  # raises if there's no game
            self.db.add_match(channel, game_id)
            return True

    def remove(self, channel: int, game_id: str) -> bool:
        matches = self.get_monitored_matches(channel)
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

    def get_highest_scores(self, match: str | Match | None = None) -> ScoreStats:
        return ScoreStats(
            highest_score=PlayerStat.from_scores(self.db.get_highest_score(match)),
            highest_bird_points=PlayerStat.from_scores(self.db.get_highest_bird_points(match)),
            highest_bonus_card_points=PlayerStat.from_scores(self.db.get_highest_bonus_card_points(match)),
            highest_goal_points=PlayerStat.from_scores(self.db.get_highest_goals_points(match)),
            highest_eggs_points=PlayerStat.from_scores(self.db.get_highest_eggs_points(match)),
            highest_cached_food_points=PlayerStat.from_scores(self.db.get_highest_cached_food_points(match)),
            highest_tucked_card_points=PlayerStat.from_scores(self.db.get_highest_tucked_cards_points(match))
        )

    def get_fastest_player(self, channel_id: int, match: str | Match | None = None) -> FastestPlayer | None:
        match_to_last_player: dict[str, tuple[str, datetime]] = {}
        times_for_turn: dict[str, list[float]] = {}
        for message in self.db.get_messages(channel_id, match):
            if message.datetime is None or message.match_id is None:
                raise ValueError("Unexpected None values when getting fastest player"
                                 f"for channel {channel_id}, match {match}")
            if message.match_id not in match_to_last_player:
                if message.player_turn is not None:
                    match_to_last_player[message.match_id] = (message.player_turn, message.datetime)
                continue
            if (message.message_type != MessageType.GAME_COMPLETE and
                    (message.player_turn is None or message.player_turn == match_to_last_player[message.match_id][0])):
                continue
            times_for_turn.setdefault(
                match_to_last_player[message.match_id][0], []).append(
                (message.datetime - match_to_last_player[message.match_id][1]).total_seconds() / 60 / 60)
            if message.player_turn is not None:
                match_to_last_player[message.match_id] = (message.player_turn, message.datetime)

        fastest_players: list[str] = []
        fastest_avg: float = 0
        for last_player, scores in times_for_turn.items():
            mean_scores = mean(scores)
            if fastest_avg == 0 or fastest_avg > mean_scores:
                fastest_players = [last_player]
                fastest_avg = mean_scores
            elif fastest_avg == mean_scores:
                fastest_players.append(last_player)

        return FastestPlayer(fastest_player=PlayerStat(wingspan_names=fastest_players, score=fastest_avg))
