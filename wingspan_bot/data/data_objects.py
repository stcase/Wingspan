from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.engine import Row


@dataclass
class PlayerStat:
    wingspan_names: list[str]
    score: int | float

    def __str__(self) -> str:
        if len(self.wingspan_names) == 0:
            return "None"
        names = ", ".join(self.wingspan_names)
        if isinstance(self.score, float):
            return f"{self.score:5.2f} - {names}"
        return f"{self.score:5} - {names}"

    @staticmethod
    def from_scores(scores: list[Row] | list[tuple[str, int]]) -> PlayerStat:
        return PlayerStat(score=scores[0][1] if len(scores) > 0 else 0, wingspan_names=[score[0] for score in scores])


@dataclass
class ScoreStats:
    highest_score: PlayerStat
    highest_bird_points: PlayerStat
    highest_bonus_card_points: PlayerStat
    highest_goal_points: PlayerStat
    highest_eggs_points: PlayerStat
    highest_cached_food_points: PlayerStat
    highest_tucked_card_points: PlayerStat

    def __str__(self) -> str:
        return (
            f"Highest score:                     {self.highest_score}\n"
            f"Most points from birds:            {self.highest_bird_points}\n"
            f"Most points from bonus cards:      {self.highest_bonus_card_points}\n"
            f"Most points from goals:            {self.highest_goal_points}\n"
            f"Most points from eggs:             {self.highest_eggs_points}\n"
            f"Most points from cached food:      {self.highest_cached_food_points}\n"
            f"Most points from tucked cards:     {self.highest_tucked_card_points}\n"
        )


@dataclass
class FastestPlayer:
    fastest_player: PlayerStat

    def __str__(self) -> str:
        return f"Fastest average turn time (hours): {self.fastest_player}\n"


@dataclass
class TurnTiming:
    count_by_hour: dict[int, int] = field(default_factory=dict)
    num_bins = 4

    def increment(self, hour: int) -> None:
        if not (0 <= hour <= 23):
            raise ValueError("Invalid hour provided")
        self.count_by_hour[hour] = self.count_by_hour.get(hour, 0) + 1

    def __str__(self) -> str:
        bin_size = max(self.count_by_hour.values()) / self.num_bins
        out_str = ""
        for height in range(self.num_bins, 0, -1):
            for hour in range(0, 24):
                out_str += " "
                out_str += "x" if self.count_by_hour.get(hour, 0) > bin_size * (height - 1) else " "
                out_str += " "
            out_str += "\n"
        out_str += "-" * 24 * 3 + "\n"
        for hour in range(0, 24):
            out_str += f"{hour : ^3}"
        out_str += "\n"
        return out_str


@dataclass
class PlayerTurnTimings:
    player_turn_timings: dict[str, TurnTiming] = field(default_factory=dict)

    def increment_timing(self, player: str, hour: int) -> None:
        self.player_turn_timings.setdefault(player, TurnTiming()).increment(hour=hour)

    def __str__(self) -> str:
        out_str = "Hours each player commonly plays (in UTC):\n"
        out_str += ("\n".join([f"{player}:\n{player_turn_timing}"
                               for player, player_turn_timing in self.player_turn_timings.items()]))
        return out_str
