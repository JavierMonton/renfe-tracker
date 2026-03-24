"""Minimal backend i18n loader.

Translation strings live in frontend/src/i18n/*.json (single source of truth).
The Dockerfile copies those files to app/i18n/ so the backend can read them at runtime.
For local development the loader falls back to frontend/src/i18n/ relative to the project root.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SUPPORTED_LANGS = ("en", "es", "ca")
DEFAULT_LANG = "en"

_translations: dict[str, dict[str, Any]] = {}


def _find_translations_dir() -> Path:
    here = Path(__file__).parent
    # Docker: Dockerfile copies frontend/src/i18n/ → app/i18n/
    app_i18n = here / "i18n"
    if app_i18n.is_dir():
        return app_i18n
    # Local dev: resolve from project root
    frontend_i18n = here.parent / "frontend" / "src" / "i18n"
    if frontend_i18n.is_dir():
        return frontend_i18n
    raise FileNotFoundError("Could not find i18n translation directory")


def _load() -> dict[str, dict[str, Any]]:
    try:
        d = _find_translations_dir()
    except FileNotFoundError:
        logger.warning("i18n translation directory not found; email notifications will use English")
        return {}

    result: dict[str, dict[str, Any]] = {}
    for lang in SUPPORTED_LANGS:
        path = d / f"{lang}.json"
        if path.exists():
            with open(path, encoding="utf-8") as f:
                result[lang] = json.load(f)
    return result


def _get_translations() -> dict[str, dict[str, Any]]:
    global _translations
    if not _translations:
        _translations = _load()
    return _translations


def t(lang: str, key: str, **kwargs: Any) -> str:
    """Look up a dot-separated key (e.g. 'emailNotif.subjectDown') for the given language.

    Falls back to English when the key or language is missing.
    Substitutes {{variable}} placeholders with kwargs.
    """
    translations = _get_translations()
    resolved_lang = lang if lang in translations else DEFAULT_LANG

    def _lookup(data: dict[str, Any], parts: list[str]) -> str | None:
        value: Any = data
        for part in parts:
            if not isinstance(value, dict):
                return None
            value = value.get(part)
        return value if isinstance(value, str) else None

    parts = key.split(".")
    value = _lookup(translations.get(resolved_lang, {}), parts)

    if value is None and resolved_lang != DEFAULT_LANG:
        # Fallback to English
        value = _lookup(translations.get(DEFAULT_LANG, {}), parts)

    if value is None:
        logger.debug("Missing translation: lang=%s key=%s", lang, key)
        return key

    for k, v in kwargs.items():
        value = value.replace(f"{{{{{k}}}}}", str(v))

    return value
