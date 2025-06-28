"""Unified entropy module for sseed.

Provides both secure system entropy generation and custom entropy input methods
with comprehensive quality validation.
"""

# Import all functions from core entropy module
from .core import (
    generate_entropy_bits,
    generate_entropy_bytes,
    secure_delete_variable,
)

# Import all functions from custom entropy module
from .custom import (
    EntropyQuality,
    analyze_entropy_patterns,
    dice_to_entropy,
    hex_to_entropy,
    validate_entropy_quality,
)

# Export all public functions
__all__ = [
    # Core entropy functions
    "generate_entropy_bits",
    "generate_entropy_bytes",
    "secure_delete_variable",
    # Custom entropy functions
    "EntropyQuality",
    "hex_to_entropy",
    "dice_to_entropy",
    "validate_entropy_quality",
    "analyze_entropy_patterns",
]
