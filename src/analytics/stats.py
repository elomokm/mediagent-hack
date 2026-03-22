"""Statistiques agrégées pour le dashboard clinique — logique pure."""

from collections import Counter
from datetime import datetime

from src.models.schemas import DailyStats
from src.tools.data_store import get_calls_by_date, get_all_calls


def get_daily_kpis(date: str | None = None) -> DailyStats:
    """Récupère les KPIs d'une journée depuis la BDD."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    calls = get_calls_by_date(date)
    return compute_daily_stats(calls, date)


def _get_care_type(c: dict) -> str:
    """Extrait le care_type d'un appel — compatible BDD et pipeline."""
    care = c.get("care")
    if isinstance(care, dict):
        return care.get("care_type", "inconnu")
    return c.get("care_type", c.get("orientation", "inconnu"))


def _get_urgency_score(c: dict) -> float:
    """Extrait le score d'urgence — compatible BDD (colonne) et pipeline (dict)."""
    # BDD : colonne directe urgency_score
    if isinstance(c.get("urgency_score"), (int, float)):
        return c["urgency_score"]
    # Pipeline : dict urgency.score
    urgency = c.get("urgency", {})
    if isinstance(urgency, dict):
        return urgency.get("score", 0)
    return 0


def compute_daily_stats(calls: list[dict], date: str) -> DailyStats:
    """Calcule les KPIs d'une journée à partir d'une liste d'appels.

    Chaque call est un dict avec les clés :
    - status, care_type, duration_seconds, urgency (dict avec score/confidence),
      analysis (dict avec sentiment_global, themes_principaux), appointment (dict ou None)
    """
    if not calls:
        return DailyStats(
            date=date,
            total_appels=0,
            appels_par_orientation={},
            duree_moyenne_secondes=0.0,
            taux_rdv_pris=0.0,
            urgences_detectees=0,
            transferts_samu=0,
            sentiment_distribution={},
            top_motifs=[],
        )

    total = len(calls)

    # Répartition par orientation
    orientations = Counter(_get_care_type(c) for c in calls)

    # Durée moyenne (compatible BDD: duration_sec ET pipeline: duration_seconds)
    durees = [c.get("duration_sec", 0) or c.get("duration_seconds", 0) for c in calls]
    duree_moyenne = sum(durees) / total if total > 0 else 0.0

    # Taux de RDV pris — vérifier via care_type (generaliste/teleconsultation = RDV probable)
    rdv_types = {"generaliste", "teleconsultation"}
    rdv_count = sum(1 for c in calls if _get_care_type(c) in rdv_types)
    taux_rdv = rdv_count / total if total > 0 else 0.0

    # Urgences et transferts SAMU
    urgences = sum(1 for c in calls if _get_urgency_score(c) >= 0.6)
    transferts = sum(1 for c in calls if c.get("status") == "TRANSFERE_SAMU")

    # Sentiment
    sentiments = Counter(
        c.get("analysis", {}).get("sentiment_global", "inconnu")
        for c in calls if c.get("analysis")
    )

    # Top motifs
    all_motifs = []
    for c in calls:
        themes = c.get("analysis", {}).get("themes_principaux", [])
        if isinstance(themes, list):
            all_motifs.extend(themes)
    top_motifs = [motif for motif, _ in Counter(all_motifs).most_common(10)]

    return DailyStats(
        date=date,
        total_appels=total,
        appels_par_orientation=dict(orientations),
        duree_moyenne_secondes=round(duree_moyenne, 1),
        taux_rdv_pris=round(taux_rdv, 2),
        urgences_detectees=urgences,
        transferts_samu=transferts,
        sentiment_distribution=dict(sentiments),
        top_motifs=top_motifs,
    )


def compute_doctor_load(calls: list[dict], doctors: list[dict]) -> dict[str, float]:
    """Taux d'occupation par médecin (nombre de RDV / total appels avec booking)."""
    rdv_per_doctor: dict[str, int] = Counter()
    total_bookable = 0

    for c in calls:
        appt = c.get("appointment")
        if appt and appt.get("booked"):
            doctor_name = appt.get("doctor_name", "inconnu")
            rdv_per_doctor[doctor_name] += 1
            total_bookable += 1

    if total_bookable == 0:
        return {f"Dr. {d['prenom']} {d['nom']}": 0.0 for d in doctors}

    return {name: round(count / total_bookable, 2) for name, count in rdv_per_doctor.items()}


def compute_peak_hours(calls: list[dict]) -> dict[int, int]:
    """Distribution des appels par heure de la journée (0-23)."""
    hours: dict[int, int] = {}
    for c in calls:
        ts = c.get("timestamp_start")
        if ts and hasattr(ts, "hour"):
            h = ts.hour
            hours[h] = hours.get(h, 0) + 1
    return dict(sorted(hours.items()))


def format_stats_terminal(stats: DailyStats) -> str:
    """Formate les stats pour affichage terminal."""
    lines = [
        "",
        "=" * 55,
        f"  STATS JOURNALIÈRES — {stats.date}",
        "=" * 55,
        f"  Appels total     : {stats.total_appels}",
        f"  Durée moyenne    : {stats.duree_moyenne_secondes:.0f}s",
        f"  Taux RDV pris    : {stats.taux_rdv_pris:.0%}",
        f"  Urgences (>0.6)  : {stats.urgences_detectees}",
        f"  Transferts SAMU  : {stats.transferts_samu}",
    ]

    if stats.appels_par_orientation:
        lines.append("  Orientations     :")
        for orient, count in stats.appels_par_orientation.items():
            pct = count / stats.total_appels * 100 if stats.total_appels else 0
            lines.append(f"    {orient:20s} : {count} ({pct:.0f}%)")

    if stats.sentiment_distribution:
        lines.append("  Sentiments       :")
        for sent, count in stats.sentiment_distribution.items():
            lines.append(f"    {sent:20s} : {count}")

    if stats.top_motifs:
        lines.append(f"  Top motifs       : {', '.join(stats.top_motifs[:5])}")

    lines.append("=" * 55)
    return "\n".join(lines)
