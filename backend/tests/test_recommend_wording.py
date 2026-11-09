from app.services.recommend import RECOMMENDATION_TABLE, get_recommendation


def test_farmers_never_see_the_citation_placeholder():
    for (label, severity) in RECOMMENDATION_TABLE:
        assert "NEEDS KALRO" not in get_recommendation(label, severity)
    assert "NEEDS KALRO" not in get_recommendation("Something Else", "High")


def test_no_doubled_words_or_stray_spaces():
    for (label, severity) in RECOMMENDATION_TABLE:
        text = get_recommendation(label, severity)
        assert "standard standard" not in text
        assert "  " not in text and text == text.strip()


def test_high_severity_still_points_to_the_extension_officer():
    assert "extension officer" in get_recommendation("Common Rust", "High")
    assert "extension officer" in get_recommendation("Unknown", "High")
