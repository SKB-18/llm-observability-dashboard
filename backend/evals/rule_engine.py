"""
Rule-based text evaluator using named regex patterns.
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple


class RuleEvaluator:
    """Score text by checking it against a set of named regex rules."""

    def __init__(self):
        # Each rule: (name, pattern, weight)
        self._rules: List[Tuple[str, re.Pattern, float]] = []

    def add_rule(self, name: str, regex: str, weight: float = 1.0) -> None:
        """Register a named rule. Higher weight = more influence on final score."""
        self._rules.append((name, re.compile(regex, re.IGNORECASE | re.DOTALL), weight))

    def evaluate(self, text: str) -> Dict:
        """
        Check all rules against text.

        Returns:
            rule_matches: dict mapping rule name → bool
            weighted_score: fraction of weighted rules that matched (0–1)
        """
        if not self._rules:
            return {"rule_matches": {}, "weighted_score": 0.0}

        matches: Dict[str, bool] = {}
        total_weight = 0.0
        matched_weight = 0.0

        for name, pattern, weight in self._rules:
            hit = bool(pattern.search(text))
            matches[name] = hit
            total_weight += weight
            if hit:
                matched_weight += weight

        score = matched_weight / total_weight if total_weight > 0 else 0.0
        return {
            "rule_matches": matches,
            "weighted_score": round(score, 4),
        }
