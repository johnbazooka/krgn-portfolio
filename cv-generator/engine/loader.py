"""
Data loader: reads master profiles and derivative configs,
applies filters, and returns merged CV data.
"""

import json
from pathlib import Path

PROFILES_DIR = Path(__file__).parent.parent / "profiles"
DERIVATIVES_DIR = Path(__file__).parent.parent / "derivatives"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def load_profile(persona_id: str) -> dict:
    """Load a master profile JSON by persona_id."""
    path = PROFILES_DIR / f"{persona_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_derivative(persona_id: str, derivative_id: str) -> dict:
    """Load a derivative config JSON."""
    path = DERIVATIVES_DIR / persona_id / f"{derivative_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Derivative not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_profiles() -> list[str]:
    """Return all available profile IDs (excluding templates)."""
    return [
        p.stem
        for p in PROFILES_DIR.glob("*.json")
        if not p.stem.startswith("_")
    ]


def list_derivatives(persona_id: str) -> list[str]:
    """Return all derivative IDs for a given persona."""
    dir_path = DERIVATIVES_DIR / persona_id
    if not dir_path.exists():
        return []
    return [p.stem for p in dir_path.glob("*.json")]


def filter_experience(master: dict, config: dict) -> list[dict]:
    """Filter experience entries based on include/exclude lists."""
    include = set(config.get("experiencias_incluir", []))
    exclude = set(config.get("experiencias_ocultar", []))
    if include:
        return [e for e in master["experiencia"] if e["id"] in include]
    if exclude:
        return [e for e in master["experiencia"] if e["id"] not in exclude]
    return master["experiencia"]


def filter_skills(master: dict, config: dict) -> dict:
    """Filter skills to only highlight specified items."""
    highlight = set(config.get("habilidades_destacar", []))
    skills = master.get("habilidades", {})
    if not highlight:
        return skills
    filtered = {}
    for cat_key, cat_data in skills.items():
        items = [i for i in cat_data["items"] if i in highlight]
        if items:
            filtered[cat_key] = {**cat_data, "items": items}
    return filtered


def build_cv_data(persona_id: str, derivative_id: str) -> dict:
    """
    Merge a master profile with a derivative config,
    applying all filters and overrides.
    """
    master = load_profile(persona_id)
    derivative = load_derivative(persona_id, derivative_id)
    config = derivative["config"]

    return {
        "persona": master["persona"],
        "objetivo_laboral": config.get("objetivo_laboral", ""),
        "perfil_profesional": config.get("perfil_profesional", ""),
        "experiencia": filter_experience(master, config),
        "educacion": master.get("educacion", []),
        "habilidades": filter_skills(master, config),
        "idiomas": master.get("idiomas", []),
        "disponibilidad": config.get(
            "disponibilidad_custom",
            master["persona"].get("disponibilidad_base", "")
        ),
        "referencias": master.get("referencias", "Disponibles bajo solicitud"),
        "layout": config.get("layout", "single_col"),
        "paleta": config.get("paleta", "azul_acero"),
    }
