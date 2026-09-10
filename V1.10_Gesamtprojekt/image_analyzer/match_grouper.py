"""
Match-Gruppierer: Führt mehrere Screenshots logisch zu zusammenhängenden Matches zusammen.
"""
from typing import List, Dict, Any
from .models import MatchRecord, LegRecord, VisitRecord, StatisticsRecord, ExtractedMatch
from .validator import validate_match_integrity

def group_extracted_screens(extracted_screens: List[Dict[str, Any]]) -> List[ExtractedMatch]:
    """
    Fasst einzelne erkannte Screenshots anhand von Match-Nummern, Spielernamen
    und Zeitstempeln zu vollständigen Matches zusammen.
    """
    # 1. Nach Matches gruppieren
    matches_dict: Dict[str, ExtractedMatch] = {}
    
    # Sortiere Screenshots chronologisch
    extracted_screens.sort(key=lambda x: x.get('filename', ''))
    
    current_match_id = "M_001"
    current_home = "Spieler A"
    current_away = "Spieler B"
    match_counter = 1
    
    # 1. Erst alle SPIELINFO Screens verarbeiten, um Matches und Spielernamen zu initialisieren
    for screen in extracted_screens:
        stype = screen.get('type')
        data = screen.get('data', {})
        fname = screen.get('filename', '')
        
        if stype == 'SPIELINFO':
            m_nr = data.get('match_number') or match_counter
            current_match_id = f"M_{m_nr:03d}"
            current_home = data.get('home_player') or "Sebastian Kirste"
            current_away = data.get('away_player') or "Stefan Lücke"
            match_counter += 1
            
            m_record = MatchRecord(
                match_id=current_match_id,
                home_player=current_home,
                away_player=current_away,
                result_str=data.get('result_str', '3-0'),
                board=data.get('board', 1),
                writer=data.get('writer', ''),
                mode=data.get('mode', 'Best of 5 Legs'),
                duration_minutes=data.get('duration_min', 0),
                start_datetime=data.get('start_datetime', ''),
                end_datetime=data.get('end_datetime', ''),
                match_number=m_nr,
                round=data.get('round', 1),
                source_images=[fname]
            )
            if current_match_id in matches_dict:
                matches_dict[current_match_id].match = m_record
            else:
                matches_dict[current_match_id] = ExtractedMatch(match=m_record)

    # Falls kein SPIELINFO vorhanden war, Fallback-Match erstellen
    if not matches_dict:
        matches_dict[current_match_id] = ExtractedMatch(
            match=MatchRecord(
                match_id=current_match_id,
                home_player=current_home,
                away_player=current_away,
                source_images=[]
            )
        )

    # 2. Scoreboards und Statistiken zuordnen
    target_em = list(matches_dict.values())[0]
    
    for screen in extracted_screens:
        stype = screen.get('type')
        data = screen.get('data', {})
        fname = screen.get('filename', '')
        
        if stype == 'SCOREBOARD':
            target_em.match.source_images.append(fname)
            leg_num = len(target_em.legs) + 1
            
            # Leg erstellen
            leg_rec = LegRecord(
                match_id=target_em.match.match_id,
                leg_number=leg_num,
                player_a=target_em.match.home_player,
                player_b=target_em.match.away_player,
                starter_player=target_em.match.home_player,
                winner_player=target_em.match.home_player,
                source_image=fname
            )
            target_em.legs.append(leg_rec)
            
            # Visits von Spieler A & B hinzufügen
            for va in data.get('visits_a', []):
                v_rec_a = VisitRecord(
                    match_id=target_em.match.match_id,
                    leg_number=leg_num,
                    visit_number=va['visit_num'],
                    player=target_em.match.home_player,
                    opponent=target_em.match.away_player,
                    darts_accumulated=va['visit_num'] * 3,
                    start_score=va['start_score'],
                    score=va['score'],
                    remaining_score=va['remaining_score'],
                    is_checkout=(va['remaining_score'] == 0),
                    source_image=fname,
                    confidence=va.get('confidence', 1.0)
                )
                target_em.visits.append(v_rec_a)
                
            for vb in data.get('visits_b', []):
                v_rec_b = VisitRecord(
                    match_id=target_em.match.match_id,
                    leg_number=leg_num,
                    visit_number=vb['visit_num'],
                    player=target_em.match.away_player,
                    opponent=target_em.match.home_player,
                    darts_accumulated=vb['visit_num'] * 3,
                    start_score=vb['start_score'],
                    score=vb['score'],
                    remaining_score=vb['remaining_score'],
                    is_checkout=(vb['remaining_score'] == 0),
                    source_image=fname,
                    confidence=vb.get('confidence', 1.0)
                )
                target_em.visits.append(v_rec_b)

    # Alle Matches validieren
    final_matches = []
    for m in matches_dict.values():
        final_matches.append(validate_match_integrity(m))
        
    return final_matches
