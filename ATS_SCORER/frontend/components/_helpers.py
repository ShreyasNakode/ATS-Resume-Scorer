from typing import Tuple


def get_score_color(score: float) -> Tuple[str, str]:
    """Return (text_color, background_color) for a 0–100 score."""
    if score >= 80:
        return "#10B981", "#ECFDF5"  # Emerald green
    if score >= 60:
        return "#F59E0B", "#FFFBEB"  # Amber orange
    return "#EF4444", "#FEF2F2"      # Crimson red


def get_score_emoji(score: float) -> str:
    """Emoji matching the score band."""
    if score >= 90:
        return "🌟"
    if score >= 80:
        return "✅"
    if score >= 70:
        return "👍"
    if score >= 60:
        return "⚠️"
    return "🔴"


def get_severity_style(severity: str) -> Tuple[str, str, str]:
    """Return (icon, text_color, background_color) for severity levels."""
    level = (severity or "").lower()
    if level in ("critical", "high"):
        return "🔴", "#DC2626", "#FEF2F2"
    if level in ("moderate", "medium"):
        return "🟡", "#D97706", "#FFFBEB"
    return "🟢", "#059669", "#ECFDF5"
