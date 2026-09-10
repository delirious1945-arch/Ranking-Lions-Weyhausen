"""
Datenstrukturen für die Dart Analytics Engine.
"""
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class VisitData:
    order: int
    score: int
    rest_score: int
    player_id: int
    opponent_rest_at_visit: Optional[int] = None

@dataclass
class LegData:
    leg_num: int
    starter_player_id: int
    winner_player_id: int
    score_before_a: int = 0
    score_before_b: int = 0
    visits_a: List[VisitData] = field(default_factory=list)
    visits_b: List[VisitData] = field(default_factory=list)

@dataclass
class MatchData:
    player_a_id: int
    player_b_id: int
    player_a_name: str
    player_b_name: str
    match_date: str
    event_name: str = "Lions League"
    round_name: str = "Liga-Spiel"
    best_of_legs: int = 5
    location: str = "Heim"
    winner_id: Optional[int] = None
    season: str = "2026/2027"
    legs: List[LegData] = field(default_factory=list)
