import pytest

from discord.data.data_controller import DataController
from discord.data.models import MessageType
from wingspan_api.wapi import Match


class TestDataControllerMessages:
    def test_get_message_type_new_turn(self, data_controller: DataController, game_in_progress_obj: Match) -> None:
        assert data_controller.get_message_type(game_in_progress_obj) == MessageType.NEW_TURN

    def test_get_message_type_reminder(
            self, data_controller: DataController, game_in_progress_low_time_obj: Match) -> None:
        assert data_controller.get_message_type(game_in_progress_low_time_obj) == MessageType.REMINDER

    def test_get_message_type_completed(self, data_controller: DataController, game_completed_obj: Match) -> None:
        assert data_controller.get_message_type(game_completed_obj) == MessageType.GAME_COMPLETE

    def test_get_message_type_waiting(self, data_controller: DataController, game_waiting_obj: Match) -> None:
        assert data_controller.get_message_type(game_waiting_obj) == MessageType.WAITING

    def test_get_message_type_ready(self, data_controller: DataController, game_ready_obj: Match) -> None:
        assert data_controller.get_message_type(game_ready_obj) == MessageType.READY

    def test_get_message_type_error(self, data_controller: DataController) -> None:
        assert data_controller.get_message_type("error") == MessageType.ERROR

    def test_get_message_timed_out(self, data_controller: DataController, game_timed_out_obj: Match) -> None:
        assert data_controller.get_message_type(game_timed_out_obj) == MessageType.GAME_TIMEOUT

    def helper_should_send_message(
            self,
            data_controller: DataController,
            match: Match | str,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        channel = 1
        if sent_message is not None:
            player = sent_message[0]
            message_type = sent_message[1]
            data_controller.db.add_message(
                match=match, channel=channel, player=player, message_type=message_type)
        assert data_controller.should_send_message(channel_id=channel, match=match) == expected

    @pytest.mark.parametrize(
        "sent_message, expected", [
            ((None, MessageType.WAITING), True),
            (None, True),
            (("victor", MessageType.NEW_TURN), False),
            (("prev_player", MessageType.NEW_TURN), True)])
    def test_should_send_message_in_progress(
            self,
            data_controller: DataController,
            game_in_progress_obj: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, game_in_progress_obj, sent_message, expected)

    @pytest.mark.parametrize(
        "sent_message, expected", [
            (("player", MessageType.NEW_TURN), True),
            (None, True),
            (("victor", MessageType.REMINDER), False),
            (("prev_player", MessageType.REMINDER), True),
            ((None, MessageType.ERROR), True)])
    def test_should_send_message_in_progress_low_time(
            self,
            data_controller: DataController,
            game_in_progress_low_time_obj: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, game_in_progress_low_time_obj, sent_message, expected)

    @pytest.mark.parametrize(
        "sent_message, expected", [
            (("player", MessageType.REMINDER), True),
            ((None, MessageType.GAME_COMPLETE), False),
        ])
    def test_should_send_message_completed(
            self,
            data_controller: DataController,
            game_completed_obj: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, game_completed_obj, sent_message, expected)

    @pytest.mark.parametrize(
        "sent_message, expected", [
            (("miguel", MessageType.REMINDER), True),
            (("miguel", MessageType.GAME_TIMEOUT), False),
        ])
    def test_should_send_message_timed_out(
            self,
            data_controller: DataController,
            game_timed_out_obj: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, game_timed_out_obj, sent_message, expected)

    @pytest.mark.parametrize(
        "sent_message, expected", [
            (None, True),
            (("victor", MessageType.WAITING), False),
        ])
    def test_should_send_message_waiting(
            self,
            data_controller: DataController,
            game_waiting_obj: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, game_waiting_obj, sent_message, expected)

    @pytest.mark.parametrize(
        "sent_message, expected", [
            (None, True),
            (("victor", MessageType.READY), False),
        ])
    def test_should_send_message_ready(
            self,
            data_controller: DataController,
            game_ready_obj: Match,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, game_ready_obj, sent_message, expected)

    @pytest.mark.parametrize(
        "sent_message, expected", [
            (("player", MessageType.ERROR), True),
            ((None, MessageType.ERROR), False),
            (("player", MessageType.NEW_TURN), True),
        ])
    def test_should_send_message_error(
            self,
            data_controller: DataController,
            sent_message: tuple[str | None, MessageType] | None,
            expected: bool) -> None:
        self.helper_should_send_message(data_controller, "error", sent_message, expected)
