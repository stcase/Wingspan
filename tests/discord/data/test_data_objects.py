from discord.data.data_objects import PlayerStat


class TestPlayerStat:
    def test_str_int(self) -> None:
        assert str(PlayerStat(score=0, wingspan_names=["player1", "player2"])) == "    0 - player1, player2"

    def test_str_float(self) -> None:
        assert str(PlayerStat(score=12.3456, wingspan_names=["player1"])) == "12.35 - player1"

    def test_str_empty(self) -> None:
        assert str(PlayerStat(score=0, wingspan_names=[])) == "None"

    def test_from_scores(self) -> None:
        assert PlayerStat.from_scores([("player", 5)]) == PlayerStat(score=5, wingspan_names=["player"])

    def test_from_scores_multiple(self) -> None:
        assert (PlayerStat.from_scores([("player1", 5), ("player2", 5)]) ==
                PlayerStat(score=5, wingspan_names=["player1", "player2"]))

    def test_from_scores_empty(self) -> None:
        test_list: list[tuple[str, int]] = []
        assert PlayerStat.from_scores(test_list) == PlayerStat(score=0, wingspan_names=[])
