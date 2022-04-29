from __future__ import annotations

from dataclasses import dataclass

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
            f"Most points from goal cards:       {self.highest_goal_points}\n"
            f"Most points from eggs:             {self.highest_eggs_points}\n"
            f"Most points from cached food:      {self.highest_cached_food_points}\n"
            f"Most points from tucked cards:     {self.highest_tucked_card_points}\n"
        )


@dataclass
class FastestPlayer:
    fastest_player: PlayerStat

    def __str__(self) -> str:
        return f"Fastest average turn time (hours): {self.fastest_player}\n"
