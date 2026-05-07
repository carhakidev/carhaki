"""
A-F vehicle grading algorithm based on normalized report data.
Score starts at 100 and penalties are deducted for negative findings.
"""


PENALTIES = {
    'salvage_title': 40,
    'junk_title': 40,
    'rebuilt_title': 20,
    'not_actual_mileage': 30,
    'exceeds_mechanical_limits': 25,
    'total_loss': 35,
    'flood_damage': 35,
    'major_accident': 20,   # per accident (airbags deployed)
    'minor_accident': 8,    # per accident
    'theft': 20,
    'open_recall': 10,      # per open recall (max 20 total)
    'many_owners': 5,       # 4+ owners
}

GRADE_BANDS = [
    (90, 'A'),
    (75, 'B'),
    (60, 'C'),
    (45, 'D'),
    (20, 'E'),
    (0,  'F'),
]

JAPAN_AUCTION_GRADE_MAP = {
    'S': 'A', '5': 'A',
    '4.5': 'B',
    '4': 'B',
    '3.5': 'C',
    '3': 'D',
    '2': 'E',
    '1': 'F',
    'R': 'F',
    'RA': 'F',
    'A': 'C',   # Japan "A" = minor interior issues
}


def calculate_grade(processed_data: dict) -> tuple[int, str]:
    score = 100
    brands = [b.upper() for b in processed_data.get('brands', [])]
    accidents = processed_data.get('accidents', [])
    theft_records = processed_data.get('theft', [])
    recalls = processed_data.get('recalls', [])
    title_history = processed_data.get('title_history', [])
    auction_grade = processed_data.get('auction_grade')

    # Title brands
    if 'SALVAGE' in brands or 'JUNK' in brands:
        score -= PENALTIES['salvage_title']
    if 'REBUILT' in brands:
        score -= PENALTIES['rebuilt_title']
    if 'NOT ACTUAL MILEAGE' in brands or 'EXCEEDS MECHANICAL LIMITS' in brands:
        score -= PENALTIES['not_actual_mileage']

    # Total loss / flood
    if processed_data.get('total_loss'):
        score -= PENALTIES['total_loss']
    if any('FLOOD' in b for b in brands):
        score -= PENALTIES['flood_damage']

    # Accidents
    major = sum(1 for a in accidents if a.get('airbags_deployed') or a.get('severity') == 'MAJOR')
    minor = len(accidents) - major
    score -= min(major * PENALTIES['major_accident'], 40)
    score -= min(minor * PENALTIES['minor_accident'], 24)

    # Theft
    if theft_records:
        score -= PENALTIES['theft']

    # Open recalls (max 20 penalty)
    open_recalls = [r for r in recalls if r.get('is_open')]
    score -= min(len(open_recalls) * PENALTIES['open_recall'], 20)

    # Many owners
    owner_count = len(set(t.get('state') for t in title_history))
    if owner_count >= 4:
        score -= PENALTIES['many_owners']

    # Japan auction grade override (if present and worse)
    if auction_grade and auction_grade in JAPAN_AUCTION_GRADE_MAP:
        auction_mapped = JAPAN_AUCTION_GRADE_MAP[auction_grade]
        auction_score = _grade_to_min_score(auction_mapped)
        score = min(score, auction_score)

    score = max(0, score)
    grade = _score_to_grade(score)
    return score, grade


def _score_to_grade(score: int) -> str:
    for min_score, grade in GRADE_BANDS:
        if score >= min_score:
            return grade
    return 'F'


def _grade_to_min_score(grade: str) -> int:
    mapping = {'A': 90, 'B': 75, 'C': 60, 'D': 45, 'E': 20, 'F': 0}
    return mapping.get(grade, 0)


GRADE_COLOURS = {
    'A': '#198754',
    'B': '#28a745',
    'C': '#ffc107',
    'D': '#fd7e14',
    'E': '#dc3545',
    'F': '#721c24',
}

GRADE_LABELS = {
    'A': 'Excellent',
    'B': 'Good',
    'C': 'Acceptable',
    'D': 'Concerning',
    'E': 'Poor — Avoid',
    'F': 'Critical Risk',
}

JAPAN_AUCTION_GRADE_EXPLANATIONS = {
    'S': 'Near perfect condition — like new',
    '5': 'Excellent condition — minimal wear',
    '4.5': 'Very good condition — light use',
    '4': 'Good condition — normal wear',
    '3.5': 'Acceptable — minor cosmetic issues',
    '3': 'Average — noticeable wear or small repairs',
    '2': 'Below average — significant issues',
    '1': 'Poor condition',
    'R': 'Repaired after accident — major bodywork done',
    'RA': 'Repaired after serious accident',
    'A': 'Interior issues only',
}
