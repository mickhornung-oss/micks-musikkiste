"""Genre- und Substil-Definitionen für Micks Musikkiste V2.

Zentrale Source of Truth für Genres und Substile.
Kein verschachteltes Preset-System, keine Copy-Paste-Logik pro Genre.

V2-Produktregel:
  Genre = Feld (techno | hiphop)
  Substil = Feld (freier Text aus vorgeschlagenen Werten)
  Prompt = freie Musikbeschreibung (primäres Steuerinstrument)
"""

from typing import Any

# ---------------------------------------------------------------------------
# Genre-Definitionen (hardcoded, klar, erweiterbar)
# ---------------------------------------------------------------------------

GENRES: dict[str, dict[str, Any]] = {
    "techno": {
        "label": "Techno",
        "substyles": [
            "dark",
            "melodic",
            "club",
            "hard",
            "minimal",
            "industrial",
            "acid",
        ],
        "bpm_range": [120, 150],
        "default_bpm": 128,
        "default_energy": 8,
        "default_darkness": 7,
        "description": "Elektronische Tanzmusik mit 4/4-Rhythmus, Kick-Dominanz und synthetischen Klängen.",
    },
    "hiphop": {
        "label": "Hip-Hop",
        "substyles": [
            "boombap",
            "trap",
            "lofi",
            "dark",
            "drill",
            "conscious",
            "phonk",
        ],
        "bpm_range": [70, 100],
        "default_bpm": 90,
        "default_energy": 6,
        "default_darkness": 5,
        "description": "Sample-basierte und beatgetriebene Musik mit Kick-Snare-Pattern und Bass.",
    },
}


def get_all_genres() -> list[dict[str, Any]]:
    """Gibt alle Genres als Liste zurück (für API-Response)."""
    return [
        {
            "id": genre_id,
            "label": data["label"],
            "substyles": data["substyles"],
            "bpm_range": data["bpm_range"],
            "default_bpm": data["default_bpm"],
            "description": data["description"],
        }
        for genre_id, data in GENRES.items()
    ]


def get_genre(genre_id: str) -> dict[str, Any] | None:
    """Gibt ein einzelnes Genre zurück oder None."""
    data = GENRES.get(genre_id.lower())
    if data is None:
        return None
    return {"id": genre_id.lower(), **data}


def get_substyles(genre_id: str) -> list[str]:
    """Gibt Substile für ein Genre zurück. Leere Liste wenn unbekannt."""
    data = GENRES.get(genre_id.lower())
    return data["substyles"] if data else []


def get_default_bpm(genre_id: str) -> int:
    """Standard-BPM für ein Genre. Fallback 120."""
    data = GENRES.get(genre_id.lower())
    return data["default_bpm"] if data else 120


def is_valid_genre(genre_id: str) -> bool:
    """Prüft ob ein Genre-ID bekannt ist."""
    return genre_id.lower() in GENRES
