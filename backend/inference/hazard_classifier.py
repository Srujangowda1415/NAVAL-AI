"""
Rule-based hazard classifier.

Reads its policy entirely from `backend/config/hazard_rules.yaml` — no
hazard logic is hardcoded here. This module exposes a small interface
(`HazardClassifier.classify`) so it can later be swapped for an ML-based
classifier (e.g. a lightweight model trained on behavior + class + context)
without changing any calling code.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "hazard_rules.yaml"

VALID_HAZARD_LEVELS = {"safe", "suspicious", "hazardous", "unknown"}


@dataclass(frozen=True)
class HazardResult:
    hazard_level: str
    reason: str


class HazardClassifier:
    """Loads hazard_rules.yaml once and classifies (ship_class, confidence) pairs."""

    def __init__(self, rules_path: Path | str = DEFAULT_RULES_PATH):
        self.rules_path = Path(rules_path)
        self._rules: dict[str, Any] = self._load_rules()

    def _load_rules(self) -> dict[str, Any]:
        if not self.rules_path.exists():
            raise FileNotFoundError(f"Hazard rules config not found at {self.rules_path}")
        with open(self.rules_path, "r", encoding="utf-8") as f:
            rules = yaml.safe_load(f)
        self._validate_rules(rules)
        return rules

    @staticmethod
    def _validate_rules(rules: dict[str, Any]) -> None:
        default_level = rules.get("default_hazard_level")
        if default_level not in VALID_HAZARD_LEVELS:
            raise ValueError(f"default_hazard_level must be one of {VALID_HAZARD_LEVELS}, got {default_level!r}")

        for ship_class, entry in rules.get("ship_classes", {}).items():
            level = entry.get("hazard_level")
            if level not in VALID_HAZARD_LEVELS:
                raise ValueError(
                    f"Invalid hazard_level {level!r} for ship class {ship_class!r}; "
                    f"must be one of {VALID_HAZARD_LEVELS}"
                )

    def reload(self) -> None:
        """Hot-reload rules from disk without restarting the service."""
        self._rules = self._load_rules()

    def classify(self, ship_class: str, confidence: float) -> HazardResult:
        """
        Determine hazard level for a single detected ship.

        Args:
            ship_class: normalized class name, e.g. "oil_tanker".
            confidence: detection/classification confidence in [0, 1].

        Returns:
            HazardResult with the resolved hazard level and a human-readable reason.
        """
        low_conf_threshold = self._rules.get("low_confidence_threshold", 0.0)
        low_conf_override = self._rules.get("low_confidence_override", "unknown")

        if confidence < low_conf_threshold:
            return HazardResult(
                hazard_level=low_conf_override,
                reason=f"Confidence {confidence:.2f} below threshold {low_conf_threshold:.2f}",
            )

        class_entry = self._rules.get("ship_classes", {}).get(ship_class)
        if class_entry is None:
            default_level = self._rules["default_hazard_level"]
            logger.info("Ship class %r not found in hazard_rules.yaml; using default %r", ship_class, default_level)
            return HazardResult(
                hazard_level=default_level,
                reason=f"No rule defined for class '{ship_class}'; used default",
            )

        return HazardResult(
            hazard_level=class_entry["hazard_level"],
            reason=class_entry.get("notes", f"Matched rule for class '{ship_class}'"),
        )


hazard_classifier = HazardClassifier()
