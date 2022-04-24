import pytest

from discord.data.data_controller import DataController


class TestDataController:
    @pytest.fixture
    def dc_monitor_many(self, data_controller: DataController) -> DataController:
        data_controller.add(1, "game1")
        data_controller.add(1, "game2")
        data_controller.add(1, "game3")
        data_controller.add(2, "game1")
        data_controller.add(2, "game4")
        return data_controller

    def test_get_all_matches(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = [  # type: ignore[attr-defined]
            "game1", "game2", "game3", "game1", "game4"]
        matches = set(dc_monitor_many.get_matches())
        assert matches == {(1, "game1"), (1, "game2"), (1, "game3"), (2, "game1"), (2, "game4")}

    def test_get_all_matches_empty(self, data_controller: DataController) -> None:
        matches = list(data_controller.get_matches())
        assert len(matches) == 0

    def test_get_matches(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = ["game 1", "game 2", "game 3"]  # type: ignore[attr-defined]
        matches = set(dc_monitor_many.get_matches(1))
        assert matches == {(1, "game 1"), (1, "game 2"), (1, "game 3")}

    def test_get_matches_empty(self, dc_monitor_many: DataController) -> None:
        matches = list(dc_monitor_many.get_matches(5))
        assert len(matches) == 0

    def test_get_matches_error(self, dc_monitor_many: DataController) -> None:
        dc_monitor_many.wapi.get_game_info.side_effect = Exception("test error")  # type: ignore[attr-defined]
        matches = set(dc_monitor_many.get_matches(1))
        assert matches == {(1, "game1"), (1, "game2"), (1, "game3")}

    def test_add_to_empty(self, data_controller: DataController) -> None:
        assert data_controller.add(1, "game1")
        assert len(data_controller.db.get_matches()) == 1

    def test_add_to_many(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.db.get_matches()
        assert dc_monitor_many.add(2, "game2")
        after = dc_monitor_many.db.get_matches()
        assert before[1] == after[1]
        assert before[2] != after[2]

    def test_add_already_present(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.db.get_matches()
        assert not dc_monitor_many.add(1, "game3")
        after = dc_monitor_many.db.get_matches()
        assert before == after

    def test_remove_empty(self, data_controller: DataController) -> None:
        assert not data_controller.remove(1, "game1")

    def test_remove_from_many(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.db.get_matches()
        assert dc_monitor_many.remove(1, "game2")
        after = dc_monitor_many.db.get_matches()
        assert before != after

    def test_remove_nonexistent_from_many(self, dc_monitor_many: DataController) -> None:
        before = dc_monitor_many.db.get_matches()
        assert not dc_monitor_many.remove(5, "game2")
        after = dc_monitor_many.db.get_matches()
        assert before == after

    def test_add_remove_add(self, data_controller: DataController) -> None:
        assert data_controller.add(1, "game1")
        assert data_controller.remove(1, "game1")
        assert not data_controller.remove(1, "game1")
        assert data_controller.add(1, "game1")
        assert not data_controller.add(1, "game1")
        assert data_controller.remove(1, "game1")
        assert not data_controller.remove(1, "game1")

    @pytest.fixture
    def dc_many_subscriptions(self, data_controller: DataController) -> DataController:
        data_controller.subscribe(1, 1, "user1")
        data_controller.subscribe(1, 2, "user2")
        data_controller.subscribe(1, 21, "user2")
        data_controller.subscribe(2, 2, "user2")
        return data_controller

    def test_subscribe_already_present(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert not dc_many_subscriptions.subscribe(1, 2, "user2")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before == after

    def test_subscribe_to_many(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert dc_many_subscriptions.subscribe(1, 3, "user3")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before != after

    def test_subscribe_to_empty(self, data_controller: DataController) -> None:
        assert data_controller.subscribe(1, 1, "user1")
        assert len(data_controller.get_subscriptions(1)) == 1

    def test_unsubscribe_from_many(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert dc_many_subscriptions.unsubscribe(1, 2, "user2")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before != after

    def test_unsubscribe_from_one(self, data_controller: DataController) -> None:
        data_controller.subscribe(1, 1, "user1")
        assert data_controller.unsubscribe(1, 1, "user1")
        assert len(data_controller.db.get_subscriptions(1)) == 0

    def test_unsubscribe_different_channel(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert not dc_many_subscriptions.unsubscribe(2, 1, "user1")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before == after

    def test_unsubscribe_not_present(self, dc_many_subscriptions: DataController) -> None:
        before = dc_many_subscriptions.get_subscriptions(1)
        assert not dc_many_subscriptions.unsubscribe(1, 1, "user3")
        after = dc_many_subscriptions.get_subscriptions(1)
        assert before == after

    def test_unsubscribe_empty(self, data_controller: DataController) -> None:
        assert not data_controller.unsubscribe(1, 1, "user1")
