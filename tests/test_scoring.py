from app.utils.scoring import calculate_opportunity_score


def test_score_bounds_and_rounding():
    s = calculate_opportunity_score(volume=5000, difficulty=10, domain_visible=False)
    assert 0.0 <= s <= 1.0
    assert round(s, 2) == s


def test_score_visibility_penalty():
    a = calculate_opportunity_score(volume=1000, difficulty=50, domain_visible=False)
    b = calculate_opportunity_score(volume=1000, difficulty=50, domain_visible=True)
    assert a > b

