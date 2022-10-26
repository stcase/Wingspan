from wingspan_bot.data.data_objects import PlayerStat, TurnTiming, PlayerTurnTimings


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


class TestTurnTiming:
    def test_increment(self) -> None:
        turn_timing = TurnTiming()
        turn_timing.increment(hour=7)
        turn_timing.increment(hour=7)
        turn_timing.increment(hour=10)
        assert turn_timing.count_by_hour == {7: 2, 10: 1}

    def test_str(self) -> None:
        turn_timing = TurnTiming(count_by_hour={1: 100, 4: 75, 7: 26, 16: 1})
        expected = (
            "    x                                                                   \n"
            "    x        x                                                          \n"
            "    x        x        x                                                 \n"
            "    x        x        x                          x                      \n"
            "------------------------------------------------------------------------\n"
            " 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 \n"
        )
        assert str(turn_timing) == expected


class TestPlayerTurnTimings:
    def test_increment_timing(self) -> None:
        turn_timings = PlayerTurnTimings()
        turn_timings.increment_timing(player="player 1", hour=3)
        turn_timings.increment_timing(player="player 1", hour=3)
        turn_timings.increment_timing(player="player 2", hour=3)
        turn_timings.increment_timing(player="player 1", hour=7)
        assert (turn_timings.player_turn_timings ==
                {"player 1": TurnTiming({3: 2, 7: 1}), "player 2": TurnTiming({3: 1})})

    def test_str(self) -> None:
        turn_timings = PlayerTurnTimings(
            player_turn_timings={"Victor": TurnTiming({1: 100, 4: 75, 7: 26, 16: 1}), "Jeff": TurnTiming({12: 10})}
        )
        expected = (
            "Hours each player commonly plays (in UTC):\n"
            "Victor:\n"
            "    x                                                                   \n"
            "    x        x                                                          \n"
            "    x        x        x                                                 \n"
            "    x        x        x                          x                      \n"
            "------------------------------------------------------------------------\n"
            " 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 \n"
            "\n"
            "Jeff:\n"
            "                                     x                                  \n"
            "                                     x                                  \n"
            "                                     x                                  \n"
            "                                     x                                  \n"
            "------------------------------------------------------------------------\n"
            " 0  1  2  3  4  5  6  7  8  9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 \n"
        )
        assert str(turn_timings) == expected
