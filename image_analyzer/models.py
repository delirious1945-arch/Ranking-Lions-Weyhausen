"""
Datenmodelle für den Dart Match Image Analyzer (Match, Leg, Visit, Statistics).
"""
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any

@dataclass
class VisitRecord:
    match_id: str
    leg_number: int
    visit_number: int
    player: str
    opponent: str
    darts_accumulated: int
    start_score: int
    score: int
    remaining_score: int
    opponent_remaining_score: int = 501
    is_break: bool = False
    is_checkout: bool = False
    source_image: str = ""
    confidence: float = 1.0
    validation_status: str = "VALID"   # VALID, WARNING_MATH_MISMATCH, NEEDS_REVIEW
    validation_message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class LegRecord:
    match_id: str
    leg_number: int
    player_a: str
    player_b: str
    starter_player: str
    winner_player: str
    darts_winner: int = 0
    darts_loser: int = 0
    checkout_winner: Optional[int] = None
    is_break: bool = False
    avg_player_a: Optional[float] = None
    avg_player_b: Optional[float] = None
    source_image: str = ""
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class StatisticsRecord:
    match_id: str
    player: str
    overall_average: Optional[float] = None
    first_9_avg: Optional[float] = None
    first_12_avg: Optional[float] = None
    first_15_avg: Optional[float] = None
    first_18_avg: Optional[float] = None
    scoring_60_plus: int = 0
    scoring_80_plus: int = 0
    scoring_100_plus: int = 0
    scoring_140_plus: int = 0
    scoring_180: int = 0
    source_image: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MatchRecord:
    match_id: str
    home_player: str
    away_player: str
    result_home: int = 0
    result_away: int = 0
    result_str: str = ""
    board: int = 1
    writer: str = ""
    mode: str = "Best of 5 Legs"
    duration_minutes: int = 0
    start_datetime: str = ""
    end_datetime: str = ""
    match_number: int = 0
    round: int = 1
    starting_player: str = ""
    source_images: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class ExtractedMatch:
    match: MatchRecord
    legs: List[LegRecord] = field(default_factory=list)
    visits: List[VisitRecord] = field(default_factory=list)
    statistics: List[StatisticsRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'match': self.match.to_dict(),
            'legs': [l.to_dict() for l in self.legs],
            'visits': [v.to_dict() for v in self.visits],
            'statistics': [s.to_dict() for s in self.statistics],
            'warnings': self.warnings
        }
