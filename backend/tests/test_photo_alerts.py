from app.services.photo_alerts import photo_alert_reason, photo_sms_text


def fusion(primary=None, secondary=()):
    return {"severity": "high", "primary_issue": primary, "secondary_issues": list(secondary), "retake": False, "notes": []}


def test_sensor_driven_alert_with_unsure_photo_says_so():
    f = fusion({"source": "sensor", "label": "waterlogging_risk", "level": "strong"})
    assert photo_alert_reason(f, "Gray Leaf Spot", 0.38) == "Your plot sensors show waterlogging risk. The leaf photo was not sure."


def test_strong_disease_alert_names_the_disease_and_confidence():
    f = fusion({"source": "disease", "label": "gray_leaf_spot", "level": "strong"})
    assert photo_alert_reason(f, "Gray Leaf Spot", 0.85) == "The leaf photo points to Gray Leaf Spot (85%)."


def test_weak_disease_alert_asks_for_a_check():
    f = fusion({"source": "disease", "label": "common_rust", "level": "weak"})
    text = photo_alert_reason(f, "Common Rust", 0.7)
    assert "may show Common Rust (70%)" in text and "Please check" in text


def test_disease_and_sensor_are_both_listed_in_order():
    f = fusion({"source": "disease", "label": "northern_leaf_blight", "level": "strong"},
               [{"source": "sensor", "label": "heat_stress", "level": "strong"}])
    text = photo_alert_reason(f, "Northern Leaf Blight", 0.9)
    assert text.index("leaf photo") < text.index("sensors") and "heat stress" in text


def test_nutrient_is_called_an_early_sign():
    f = fusion({"source": "nutrient", "label": "nitrogen_deficiency", "level": "weak"})
    assert "early sign only" in photo_alert_reason(f, "Healthy", 0.9)


def test_healthy_photo_is_not_called_unsure_and_nothing_flagged_has_a_fallback():
    assert photo_alert_reason(fusion(), "Healthy", 0.3) == "Please check your plot."
    assert photo_alert_reason(None, None, None) == "Please check your plot."


def test_sms_fits_one_segment():
    long_reason = "Your plot sensors show waterlogging risk. The leaf photo was not sure. " * 4
    text = photo_sms_text("A very long farm name that goes on", "High", long_reason)
    assert len(text) <= 160 and text.startswith("MaizeStress High: A very long farm")