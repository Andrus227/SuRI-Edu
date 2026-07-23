from __future__ import annotations

import json
import logging
from pathlib import Path

LIBRARY_VERSION = 1
DEFAULT_LIBRARY_PATH = Path.home() / ".suri_edu" / "metodos.json"

logger = logging.getLogger(__name__)


class MethodLibrary:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or DEFAULT_LIBRARY_PATH

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            logger.warning("Nao foi possivel carregar a biblioteca de metodos", exc_info=True)
            return {}

        methods = payload.get("methods", {}) if isinstance(payload, dict) else {}
        if not isinstance(methods, dict):
            return {}
        return {
            name: code
            for name, code in methods.items()
            if isinstance(name, str) and isinstance(code, str)
        }

    def save(self, methods: dict[str, str]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": LIBRARY_VERSION,
            "methods": dict(sorted(methods.items())),
        }
        temporary_path = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(self.path)
