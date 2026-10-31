"""Plain-language reason for a photo check-in alert.

The overall severity of a check-in combines the leaf photo and the plot sensors. A photo alert can be High only because the
sensors flag waterlogging while the leaf photo was not sure. Saying only "High severity for <disease>" would then be wrong,
so the alert and its SMS say what actually caused it. Pure functions, no database or model needed."""

WEAK_MIN = 0.60  # same as weak_min in models/fusion/fusion_rules.yaml
NOT_FLAGGING = {"healthy", "no_deficiency", "unassessed", "unknown", ""}


def _key(label):
    return str(label or "").strip().lower().replace(" ", "_")


def _words(label):
    return _key(label).replace("_", " ")


def _title(label):
    return _words(label).title()


def _pct(label, disease_label, disease_conf):
    if disease_conf is not None and _key(label) == _key(disease_label):
        return f" ({round(disease_conf * 100)}%)"
    return ""


def _issue_text(issue, disease_label, disease_conf):
    source, label, level = issue.get("source"), issue.get("label"), issue.get("level")
    if not label:
        return None
    if source == "sensor":
        return f"Your plot sensors show {_words(label)}."
    if source == "disease":
        pct = _pct(label, disease_label, disease_conf)
        if level == "strong":
            return f"The leaf photo points to {_title(label)}{pct}."
        return f"The leaf photo may show {_title(label)}{pct}. Please check."
    if source == "nutrient":
        return f"The leaf photo may show {_words(label)}. This is an early sign only."
    return None


def photo_alert_reason(fusion, disease_label, disease_conf):
    """What caused this photo alert, in plain words. `fusion` is the fusion block stored with the prediction."""
    fusion = fusion or {}
    issues = [i for i in [fusion.get("primary_issue")] + list(fusion.get("secondary_issues") or []) if i]
    parts = []
    for issue in issues:
        text = _issue_text(issue, disease_label, disease_conf)
        if text and text not in parts:
            parts.append(text)
    disease_named = any(i.get("source") == "disease" for i in issues)
    disease_unsure = (
        _key(disease_label) not in NOT_FLAGGING and disease_conf is not None and disease_conf < WEAK_MIN
    )
    if disease_unsure and not disease_named:
        parts.append("The leaf photo was not sure.")
    return " ".join(parts) if parts else "Please check your plot."


def photo_sms_text(farm_name, severity, reason):
    """One SMS segment (160 characters)."""
    text = f"MaizeStress {severity}: {(farm_name or '')[:20].rstrip()}. {reason}"
    return text[:160].rstrip()