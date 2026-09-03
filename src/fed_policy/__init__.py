"""Fed funds futures based FOMC decision-probability model."""

from .contracts import contract_symbol, next_contract_symbol
from .model import calculate_meeting_probabilities

__all__ = ["contract_symbol", "next_contract_symbol", "calculate_meeting_probabilities"]
