import datetime
from collections.abc import Iterable
from typing import TypeVar

from freezegun import freeze_time

from wingspan_bot.data.db_connection import DBConnection
from tests.conftest import MessageTestData
from wingspan_api.wapi import Match


T = TypeVar('T')


def iterable_to_scalar(iterable: Iterable[T]) -> T:
    vals = list(iterable)
    assert len(vals) == 1
    return vals[0]


class TestDBConnection:
    def test_get_matches(self, db: DBConnection) -> None:
        db.add_match(channel=1, match_id="match1")
        db.add_match(channel=1, match_id="match2")
        db.remove_match(channel=1, match_id="match1")
        matches = db.get_matches()
        assert len(matches) == 1
        assert matches[0].match_id == "match2"

    def test_get_matches_all(self, db: DBConnection) -> None:
        db.add_match(channel=1, match_id="match1")
        db.add_match(channel=1, match_id="match2")
        db.remove_match(channel=1, match_id="match1")
        matches = db.get_matches(currently_monitored=False)
        assert len(matches) == 2

    def test_get_previous_message_empty(self, db: DBConnection) -> None:
        assert db.get_previous_message(1, "match-id") is None

    def test_get_previous_message(self, db: DBConnection, message_expecteds: MessageTestData) -> None:
        message_expecteds.call_add(db)
        actual = db.get_previous_message(channel=message_expecteds.channel, match=message_expecteds.match_id)
        message_expecteds.assert_equal_status_message(actual)

    def test_get_previous_message_others(self, db: DBConnection, message_expecteds: MessageTestData) -> None:
        message_expecteds.call_add(db)
        db.add_message(
            match=message_expecteds.match_id,
            channel=42,
            player=message_expecteds.player_id,
            message_type=message_expecteds.msg_type)
        actual = db.get_previous_message(channel=message_expecteds.channel, match=message_expecteds.match_id)
        message_expecteds.assert_equal_status_message(actual)

    def test_add_or_update_score_add(self, db: DBConnection, game_in_progress_obj: Match) -> None:
        db.add_or_update_score(game_in_progress_obj)
        assert len(db.get_scores(game_in_progress_obj)) == 5

    def test_add_or_update_score_update(self, db: DBConnection, game_in_progress_obj: Match) -> None:
        db.add_or_update_score(game_in_progress_obj)
        db.add_or_update_score(game_in_progress_obj)
        assert len(db.get_scores(game_in_progress_obj)) == 5

    def test_get_highest_score_empty(self, db: DBConnection) -> None:
        assert len(list(db.get_highest_score(1))) == 0

    def test_get_highest_bird_points_empty_with_match(self, db: DBConnection) -> None:
        assert len(list(db.get_highest_bird_points(1, "non-existent-match"))) == 0

    def test_get_highest_bonus_card_points_multiple_entries(
            self, db: DBConnection, game_in_progress_obj: Match, game_completed_obj: Match) -> None:
        db.add_match(channel=1, match_id=str(game_completed_obj))
        db.add_match(channel=1, match_id=str(game_in_progress_obj))
        db.add_or_update_score(game_completed_obj)
        db.add_or_update_score(game_in_progress_obj)
        assert iterable_to_scalar(db.get_highest_bonus_card_points(1))[1] == 14

    def test_get_highest_goals_points_multiple_entries_with_match(
            self, db: DBConnection, game_in_progress_obj: Match, game_completed_obj: Match) -> None:
        db.add_match(channel=1, match_id=str(game_completed_obj))
        db.add_match(channel=1, match_id=str(game_in_progress_obj))
        db.add_or_update_score(game_completed_obj)
        db.add_or_update_score(game_in_progress_obj)
        assert iterable_to_scalar(db.get_highest_eggs_points(1, game_completed_obj))[1] == 29

    def test_get_highest_eggs_points_missing_match(self, db: DBConnection, game_completed_obj: Match) -> None:
        db.add_or_update_score(game_completed_obj)
        assert len(db.get_highest_eggs_points(1, "non-existent-match")) == 0

    def test_get_highest_cached_food_points_multiple_games(
            self, db: DBConnection, game_completed_obj: Match, game_in_progress_obj: Match) -> None:
        db.add_match(channel=1, match_id=str(game_completed_obj))
        db.add_match(channel=1, match_id=str(game_in_progress_obj))
        db.add_or_update_score(game_completed_obj)
        db.add_or_update_score(game_in_progress_obj)
        assert iterable_to_scalar(db.get_highest_cached_food_points(1, "in-progress-match-id"))[1] == 4
        assert iterable_to_scalar(db.get_highest_cached_food_points(1, "completed-match-id"))[1] == 9

    def test_get_highest_tucked_card_points_tie(self, db: DBConnection, game_completed_obj: Match) -> None:
        db.add_match(channel=1, match_id=str(game_completed_obj))
        db.add_or_update_score(game_completed_obj)
        scores = list(db.get_highest_tucked_cards_points(1))
        assert len(scores) == 2
        assert scores[0][1] == scores[1][1] == 11

    def test_get_highest_cached_food_points_multiple_channels(
            self, db: DBConnection, game_completed_obj: Match, game_in_progress_obj: Match) -> None:
        db.add_match(channel=1, match_id=str(game_completed_obj))
        db.add_match(channel=2, match_id=str(game_in_progress_obj))
        db.add_or_update_score(game_completed_obj)
        db.add_or_update_score(game_in_progress_obj)
        assert iterable_to_scalar(db.get_highest_cached_food_points(2))[1] == 4

    def test_get_highest_cached_food_points_wrong_channel(
            self, db: DBConnection, game_completed_obj: Match, game_in_progress_obj: Match) -> None:
        db.add_match(channel=1, match_id=str(game_completed_obj))
        db.add_match(channel=2, match_id=str(game_in_progress_obj))
        db.add_or_update_score(game_completed_obj)
        db.add_or_update_score(game_in_progress_obj)
        assert len(db.get_highest_cached_food_points(2, str(game_completed_obj))) == 0

    @freeze_time("2022-1-1")
    def test_get_data_start(self, db: DBConnection) -> None:
        db.add_match(1, "match-id")
        assert db.get_data_start(1) == datetime.datetime.now()

    def test_get_data_start_empty(self, db: DBConnection) -> None:
        assert db.get_data_start(1) is None

    def test_get_data_start_multiple(self, db: DBConnection) -> None:
        with freeze_time("2022-1-1"):
            db.add_match(1, "match1")
        with freeze_time("2022-1-2"):
            db.add_match(1, "match2")
        assert db.get_data_start(1) == datetime.datetime(2022, 1, 1)

    def test_get_data_start_multiple_channel(self, db: DBConnection) -> None:
        with freeze_time("2022-1-1"):
            db.add_match(1, "match1")
        with freeze_time("2022-1-2"):
            db.add_match(1, "match2")
            db.add_match(2, "match2")
        with freeze_time("2022-1-3"):
            assert datetime.datetime.now() == datetime.datetime(2022, 1, 3)
            db.add_match(1, "match4")
            db.add_match(1, "match3")
        assert db.get_data_start(1, "match2") == datetime.datetime(2022, 1, 2)
