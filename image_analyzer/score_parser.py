"""
Score Parser & 501 Calculation Engine für Copy-Paste / Direkteingabe
Exakte 3-Dart-Average-Berechnung gemäß Darts-Standard:
Average = (Gesamtpunktzahl / Anzahl geworfener Darts) * 3
"""
import re
from typing import List, Dict, Any, Tuple, Optional
from .models import LegRecord, VisitRecord, MatchRecord, StatisticsRecord, ExtractedMatch

# Unmögliche 3-Dart-Scores
IMPOSSIBLE_SCORES = {163, 166, 169, 172, 173, 175, 176, 178, 179}

def parse_score_text(raw_text: str) -> List[int]:
    """
    Parst rohen Text (zeilenweise, kommasortiert oder Tab-separiert) in eine Liste von Integer-Scores.
    """
    if not raw_text:
        return []
    
    tokens = re.findall(r'\b\d+\b', raw_text)
    scores = []
    for t in tokens:
        try:
            val = int(t)
            if 0 <= val <= 180 and val not in IMPOSSIBLE_SCORES:
                scores.append(val)
        except ValueError:
            continue
    return scores

def calculate_leg_from_scores(
    match_id: str,
    leg_number: int,
    player_a_name: str,
    player_b_name: str,
    scores_a: List[int],
    scores_b: List[int],
    starter_player: str = "",
    final_darts_a: Optional[int] = None,
    final_darts_b: Optional[int] = None
) -> Tuple[LegRecord, List[VisitRecord], List[str]]:
    """
    Berechnet ein Leg (501 -> 0) anhand der eingegebenen Scores für Spieler A und B.
    Nutzt die offizielle Darts-Formel: Leg-Avg = ((501 - Rest) / Darts) * 3
    """
    warnings = []
    starter = starter_player if starter_player else player_a_name
    winner = None
    
    visits: List[VisitRecord] = []
    
    # 1. Spieler A berechnen
    rest_a = 501
    darts_a_total = 0
    winner_a = False
    
    for idx, sc in enumerate(scores_a, 1):
        start = rest_a
        rest = start - sc
        
        # Check für Bust
        if rest < 0 or rest == 1:
            warnings.append(f"Leg {leg_number} - {player_a_name}: Visit {idx} (Score {sc}) ist ungültig (Rest {rest} nicht checkbar).")
            rest = start  # Bust: Rest bleibt unverändert
            
        darts_this_visit = 3
        if rest == 0:
            winner_a = True
            winner = player_a_name
            if final_darts_a is not None and final_darts_a > 0:
                # Berechne Rest-Darts für die Checkout-Aufnahme
                d_checkout = final_darts_a - ((idx - 1) * 3)
                if 1 <= d_checkout <= 3:
                    darts_this_visit = d_checkout
                    
        darts_a_total += darts_this_visit
        
        # Ermittle gegnerischen Rest zum Zeitpunkt dieser Aufnahme
        opp_rest = 501
        if idx <= len(scores_b):
            curr_b = 501
            for sb in scores_b[:idx]:
                if curr_b - sb >= 0 and curr_b - sb != 1:
                    curr_b -= sb
            opp_rest = curr_b
            
        v_rec = VisitRecord(
            match_id=match_id,
            leg_number=leg_number,
            visit_number=idx,
            player=player_a_name,
            opponent=player_b_name,
            darts_accumulated=darts_a_total,
            start_score=start,
            score=sc,
            remaining_score=rest,
            opponent_remaining_score=opp_rest,
            is_checkout=(rest == 0),
            source_image="Manuelle Eingabe",
            validation_status="VALID" if rest >= 0 else "INVALID",
            validation_message="Bust" if rest < 0 else ""
        )
        visits.append(v_rec)
        rest_a = rest
        if winner_a:
            break

    # Falls final_darts_a explizit angegeben wurde (z. B. 28)
    if final_darts_a is not None and final_darts_a > 0:
        darts_a_total = final_darts_a

    # 2. Spieler B berechnen
    rest_b = 501
    darts_b_total = 0
    winner_b = False
    
    for idx, sc in enumerate(scores_b, 1):
        start = rest_b
        rest = start - sc
        
        # Check für Bust
        if rest < 0 or rest == 1:
            warnings.append(f"Leg {leg_number} - {player_b_name}: Visit {idx} (Score {sc}) ist ungültig (Rest {rest} nicht checkbar).")
            rest = start
            
        darts_this_visit = 3
        if rest == 0 and not winner_a:
            winner_b = True
            winner = player_b_name
            if final_darts_b is not None and final_darts_b > 0:
                d_checkout = final_darts_b - ((idx - 1) * 3)
                if 1 <= d_checkout <= 3:
                    darts_this_visit = d_checkout
                    
        darts_b_total += darts_this_visit
        
        # Ermittle gegnerischen Rest zum Zeitpunkt dieser Aufnahme
        opp_rest = 501
        if idx <= len(scores_a):
            curr_a = 501
            for sa in scores_a[:idx]:
                if curr_a - sa >= 0 and curr_a - sa != 1:
                    curr_a -= sa
            opp_rest = curr_a
            
        v_rec = VisitRecord(
            match_id=match_id,
            leg_number=leg_number,
            visit_number=idx,
            player=player_b_name,
            opponent=player_a_name,
            darts_accumulated=darts_b_total,
            start_score=start,
            score=sc,
            remaining_score=rest,
            opponent_remaining_score=opp_rest,
            is_checkout=(rest == 0),
            source_image="Manuelle Eingabe",
            validation_status="VALID" if rest >= 0 else "INVALID",
            validation_message="Bust" if rest < 0 else ""
        )
        visits.append(v_rec)
        rest_b = rest
        if winner_b:
            break

    if final_darts_b is not None and final_darts_b > 0:
        darts_b_total = final_darts_b

    if not winner:
        winner = player_a_name if rest_a < rest_b else player_b_name

    co_win = None
    if winner == player_a_name and scores_a and rest_a == 0:
        co_win = scores_a[-1]
    elif winner == player_b_name and scores_b and rest_b == 0:
        co_win = scores_b[-1]

    # Exakte 3-Dart-Average-Berechnung für dieses Leg: ((501 - Rest) / Darts) * 3
    pts_a = 501 - rest_a
    leg_avg_a = round((pts_a / darts_a_total * 3), 2) if darts_a_total > 0 else 0.0

    pts_b = 501 - rest_b
    leg_avg_b = round((pts_b / darts_b_total * 3), 2) if darts_b_total > 0 else 0.0

    leg_rec = LegRecord(
        match_id=match_id,
        leg_number=leg_number,
        player_a=player_a_name,
        player_b=player_b_name,
        starter_player=starter,
        winner_player=winner,
        darts_winner=(darts_a_total if winner == player_a_name else darts_b_total),
        darts_loser=(darts_b_total if winner == player_a_name else darts_a_total),
        checkout_winner=co_win,
        avg_player_a=leg_avg_a,
        avg_player_b=leg_avg_b,
        source_image="Manuelle Eingabe"
    )

    return leg_rec, visits, warnings

def build_full_match_from_legs_input(
    match_id: str,
    home_player: str,
    away_player: str,
    legs_data: List[Dict[str, Any]],
    board: int = 1,
    round_nr: int = 1,
    match_nr: int = 1,
    writer: str = "",
    mode: str = "Best of 5 Legs",
    start_time: str = "",
    end_time: str = "",
    duration_min: int = 15
) -> ExtractedMatch:
    """
    Erstellt ein vollständiges ExtractedMatch aus den eingegebenen Daten für bis zu 5 Legs.
    Berechnet den Gesamt-Average exakt nach:
    Gesamt-Average = (Gesamtpunkte aller Legs / Gesamtdarts aller Legs) * 3
    """
    all_legs: List[LegRecord] = []
    all_visits: List[VisitRecord] = []
    all_warnings: List[str] = []
    
    wins_a = 0
    wins_b = 0
    
    for l_idx, leg_info in enumerate(legs_data, 1):
        scores_a = parse_score_text(leg_info.get('scores_a_raw', ''))
        scores_b = parse_score_text(leg_info.get('scores_b_raw', ''))
        
        if not scores_a and not scores_b:
            continue
            
        starter = home_player if (l_idx % 2 == 1) else away_player
        if leg_info.get('starter'):
            starter = leg_info.get('starter')
            
        # Parse optionale Darts-Eingabe (z. B. "28" oder int)
        d_a = leg_info.get('darts_a')
        d_b = leg_info.get('darts_b')
        final_d_a = int(d_a) if (d_a is not None and str(d_a).strip().isdigit()) else None
        final_d_b = int(d_b) if (d_b is not None and str(d_b).strip().isdigit()) else None
        
        leg_rec, visits, warns = calculate_leg_from_scores(
            match_id=match_id,
            leg_number=l_idx,
            player_a_name=home_player,
            player_b_name=away_player,
            scores_a=scores_a,
            scores_b=scores_b,
            starter_player=starter,
            final_darts_a=final_d_a,
            final_darts_b=final_d_b
        )
        
        if leg_rec.winner_player == home_player:
            wins_a += 1
        elif leg_rec.winner_player == away_player:
            wins_b += 1
            
        all_legs.append(leg_rec)
        all_visits.extend(visits)
        all_warnings.extend(warns)

    result_str = f"{wins_a}-{wins_b}"
    
    m_record = MatchRecord(
        match_id=match_id,
        home_player=home_player,
        away_player=away_player,
        result_home=wins_a,
        result_away=wins_b,
        result_str=result_str,
        board=board,
        writer=writer,
        mode=mode,
        duration_minutes=duration_min,
        start_datetime=start_time,
        end_datetime=end_time,
        match_number=match_nr,
        round=round_nr,
        source_images=["Copy-Paste Direkteingabe"]
    )
    
    # 🎯 Exakte Gesamt-Statistiken über die Gesamtzahl aller geworfenen Darts:
    # Average = (Gesamtpunkte / Gesamtdarts) * 3
    stats_list: List[StatisticsRecord] = []
    for p_name in [home_player, away_player]:
        p_visits = [v for v in all_visits if v.player == p_name]
        p_scores = [v.score for v in p_visits]
        
        total_pts = sum(p_scores)
        total_darts = 0
        
        f9_pts = 0
        f9_darts = 0
        
        for leg in all_legs:
            leg_v = [v for v in p_visits if v.leg_number == leg.leg_number]
            if not leg_v:
                continue
                
            # Darts in diesem Leg
            if p_name == leg.winner_player:
                l_darts = leg.darts_winner if leg.darts_winner > 0 else (len(leg_v) * 3)
            else:
                l_darts = leg.darts_loser if leg.darts_loser > 0 else (len(leg_v) * 3)
                
            total_darts += l_darts
            
            # First 9 Darts (erste 3 Aufnahmen)
            f9_v = [v for v in leg_v if v.visit_number <= 3]
            f9_pts += sum(v.score for v in f9_v)
            f9_darts += min(l_darts, len(f9_v) * 3)
            
        overall_avg = round((total_pts / total_darts * 3), 2) if total_darts > 0 else 0.0
        first_9_avg = round((f9_pts / f9_darts * 3), 2) if f9_darts > 0 else 0.0
        
        s60 = sum(1 for s in p_scores if 60 <= s < 80)
        s80 = sum(1 for s in p_scores if 80 <= s < 100)
        s100 = sum(1 for s in p_scores if 100 <= s < 140)
        s140 = sum(1 for s in p_scores if 140 <= s < 180)
        s180 = sum(1 for s in p_scores if s == 180)
        
        checkouts = [v.score for v in p_visits if v.remaining_score == 0]
        high_co = max(checkouts) if checkouts else 0
        
        stats_list.append(StatisticsRecord(
            match_id=match_id,
            player=p_name,
            overall_average=overall_avg,
            first_9_avg=first_9_avg,
            scoring_60_plus=s60,
            scoring_80_plus=s80,
            scoring_100_plus=s100,
            scoring_140_plus=s140,
            scoring_180=s180,
            source_image="Automatische Berechnung"
        ))

    return ExtractedMatch(
        match=m_record,
        legs=all_legs,
        visits=all_visits,
        statistics=stats_list,
        warnings=all_warnings
    )
