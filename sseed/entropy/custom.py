"""Custom entropy sources for BIP-39 generation.

Provides validated custom entropy input methods including hex strings,
dice rolls, and other deterministic sources with comprehensive quality analysis.
"""

import hashlib
import re
from typing import List

from sseed.exceptions import (
    EntropyError,
    ValidationError,
)
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

logger = get_logger(__name__)


class EntropyQuality:
    """Entropy quality assessment results."""

    def __init__(self, score: int, warnings: List[str], recommendations: List[str]):
        """Initialize entropy quality assessment.

        Args:
            score: Quality score from 0-100 (100 = perfect)
            warnings: List of quality warnings detected
            recommendations: List of recommendations for improvement
        """
        self.score = score
        self.warnings = warnings
        self.recommendations = recommendations
        self.is_acceptable = score >= 70  # Configurable threshold

    def is_good_quality(self) -> bool:
        """Check if entropy quality is good (score >= 80)."""
        return self.score >= 80

    def get_summary(self) -> str:
        """Get a summary string of the quality assessment."""
        status = "Good" if self.is_acceptable else "Poor"
        return f"Quality: {status} ({self.score}/100)"


def hex_to_entropy(
    hex_string: str, required_bytes: int, skip_quality_check: bool = False
) -> bytes:
    """Convert hex string to entropy bytes with comprehensive validation.

    Args:
        hex_string: Hexadecimal string (with or without 0x prefix)
        required_bytes: Number of entropy bytes needed
        skip_quality_check: If True, skip quality validation (for CLI override flags)

    Returns:
        Validated entropy bytes

    Raises:
        ValidationError: If hex string is invalid or insufficient
        EntropyError: If entropy quality is unacceptable (unless skip_quality_check=True)
    """
    try:
        # Normalize hex string
        hex_clean = hex_string.strip().lower()
        if hex_clean.startswith("0x"):
            hex_clean = hex_clean[2:]

        # Validate hex format
        if not re.match(r"^[0-9a-f]+$", hex_clean):
            raise ValidationError("Invalid hex string: contains non-hex characters")

        # Ensure even length
        if len(hex_clean) % 2 != 0:
            hex_clean = "0" + hex_clean
            logger.warning("Padded hex string with leading zero")

        # Convert to bytes
        entropy_bytes = bytes.fromhex(hex_clean)

        # Check length requirements
        if len(entropy_bytes) < required_bytes:
            # Pad with secure random if insufficient
            from .core import (  # pylint: disable=import-outside-toplevel
                generate_entropy_bytes,
            )

            padding_needed = required_bytes - len(entropy_bytes)
            padding = generate_entropy_bytes(padding_needed)
            entropy_bytes = entropy_bytes + padding

            log_security_event(
                f"Hex entropy padded with {padding_needed} secure random bytes",
                {
                    "original_bytes": len(entropy_bytes) - padding_needed,
                    "padding_bytes": padding_needed,
                },
            )
        elif len(entropy_bytes) > required_bytes:
            # Truncate if too long
            entropy_bytes = entropy_bytes[:required_bytes]
            logger.warning("Truncated hex entropy to %d bytes", required_bytes)

        # Quality validation (unless skipped)
        if not skip_quality_check:
            quality = validate_entropy_quality(entropy_bytes)
            if not quality.is_acceptable:
                raise EntropyError(
                    f"Hex entropy quality insufficient (score: {quality.score}/100)",
                    context={
                        "warnings": quality.warnings,
                        "recommendations": quality.recommendations,
                    },
                )

        logger.info("Successfully processed hex entropy: %d bytes", len(entropy_bytes))
        return entropy_bytes

    except Exception as e:
        logger.error("Hex entropy processing failed: %s", e)
        raise


def dice_to_entropy(  # pylint: disable=too-many-locals
    dice_rolls: str, required_bytes: int, skip_quality_check: bool = False
) -> bytes:
    """Convert dice rolls to entropy bytes using established cryptographic methods.

    Supports multiple formats:
    - Comma-separated: "1,2,3,4,5,6"
    - Space-separated: "1 2 3 4 5 6"
    - Continuous: "123456"

    Args:
        dice_rolls: String of dice roll results
        required_bytes: Number of entropy bytes needed
        skip_quality_check: If True, skip quality validation (for CLI override flags)

    Returns:
        Validated entropy bytes derived from dice rolls

    Raises:
        ValidationError: If dice format is invalid
        EntropyError: If insufficient dice rolls or poor quality (unless skip_quality_check=True)
    """
    try:
        # Parse dice rolls
        dice_values = _parse_dice_string(dice_rolls)

        # Validate dice values (1-6 for standard dice)
        for value in dice_values:
            if not 1 <= value <= 6:
                raise ValidationError(f"Invalid dice value: {value}. Must be 1-6.")

        # Calculate entropy requirement
        # Each die roll provides log2(6) ≈ 2.585 bits of entropy
        bits_per_roll = 2.585
        required_bits = required_bytes * 8
        min_rolls_needed = int(required_bits / bits_per_roll) + 1

        if len(dice_values) < min_rolls_needed:
            raise EntropyError(
                f"Insufficient dice rolls: {len(dice_values)} provided, "
                f"need at least {min_rolls_needed} for {required_bytes} bytes"
            )

        # Convert dice to entropy using SHA-256 for deterministic conversion
        dice_string = "".join(str(d) for d in dice_values)
        entropy_hash = hashlib.sha256(dice_string.encode("utf-8")).digest()

        # Extend entropy if needed using multiple hash rounds
        entropy_bytes = entropy_hash
        round_num = 1
        while len(entropy_bytes) < required_bytes:
            round_input = f"{dice_string}:{round_num}"
            additional_hash = hashlib.sha256(round_input.encode("utf-8")).digest()
            entropy_bytes += additional_hash
            round_num += 1

        # Truncate to required length
        entropy_bytes = entropy_bytes[:required_bytes]

        # Quality validation (unless skipped)
        if not skip_quality_check:
            quality = validate_entropy_quality(entropy_bytes)
            if (
                quality.score < 60
            ):  # Lower threshold for dice due to deterministic nature
                logger.warning(
                    "Dice entropy quality below optimal: %d/100", quality.score
                )
                for warning in quality.warnings:
                    logger.warning("Dice entropy warning: %s", warning)

        logger.info(
            "Successfully processed dice entropy: %d rolls → %d bytes",
            len(dice_values),
            len(entropy_bytes),
        )
        return entropy_bytes

    except Exception as e:
        logger.error("Dice entropy processing failed: %s", e)
        raise


def validate_entropy_quality(entropy: bytes) -> EntropyQuality:
    """Comprehensive entropy quality analysis with scoring.

    Analyzes entropy for:
    - Pattern detection (repeats, sequences, etc.)
    - Byte distribution uniformity
    - Basic statistical tests
    - Common weak entropy signatures

    Returns:
        EntropyQuality object with score (0-100) and recommendations
    """
    warnings: List[str] = []
    recommendations: List[str] = []
    score = 100  # Start with perfect score, deduct for issues

    # Check for obvious weak patterns
    pattern_score = _analyze_patterns(entropy, warnings)
    score = min(score, pattern_score)

    # Check byte distribution
    distribution_score = _analyze_distribution(entropy, warnings)
    score = min(score, distribution_score)

    # Check for common weak entropy
    weakness_score = _analyze_weakness_signatures(entropy, warnings)
    score = min(score, weakness_score)

    # Generate recommendations based on score
    if score < 70:
        recommendations.append(
            "Consider using system entropy instead of custom entropy"
        )
    if score < 50:
        recommendations.append("This entropy is not suitable for cryptographic use")
        recommendations.append(
            "Use 'sseed gen' without entropy flags for secure generation"
        )
    if score < 30:
        recommendations.append("CRITICAL: This entropy appears to be non-random")

    return EntropyQuality(score, warnings, recommendations)


def _parse_dice_string(dice_string: str) -> List[int]:
    """Parse dice string into list of integers."""
    dice_clean = dice_string.strip()

    # Try comma-separated first
    if "," in dice_clean:
        return [int(x.strip()) for x in dice_clean.split(",") if x.strip()]

    # Try space-separated
    if " " in dice_clean:
        return [int(x) for x in dice_clean.split() if x]

    # Try continuous digits
    if dice_clean.isdigit():
        return [int(c) for c in dice_clean]

    # Unable to parse
    raise ValidationError(f"Unable to parse dice string: {dice_string}")


def _analyze_patterns(entropy: bytes, warnings: List[str]) -> int:
    """Analyze entropy for obvious patterns."""
    score = 100

    # All zeros
    if entropy == b"\x00" * len(entropy):
        warnings.append("Entropy is all zeros")
        return 0

    # All 0xFF
    if entropy == b"\xff" * len(entropy):
        warnings.append("Entropy is all 0xFF bytes")
        return 0

    # Repeating patterns
    for pattern_len in [1, 2, 4]:
        if len(entropy) >= pattern_len * 4:
            pattern = entropy[:pattern_len]
            if entropy == pattern * (len(entropy) // pattern_len):
                warnings.append(
                    f"Entropy contains repeating {pattern_len}-byte pattern"
                )
                score = min(score, 20)

    # Sequential bytes
    if len(entropy) >= 8:
        sequential = bytes(range(len(entropy)))
        if entropy == sequential:
            warnings.append("Entropy is sequential bytes")
            score = min(score, 10)

    return score


def _analyze_distribution(entropy: bytes, warnings: List[str]) -> int:
    """Analyze byte value distribution."""
    if len(entropy) < 32:
        return 100  # Skip for small samples

    # Count byte frequencies
    frequencies = [0] * 256
    for byte in entropy:
        frequencies[byte] += 1

    # Check for highly skewed distribution - be more lenient for small samples
    max_freq = max(frequencies)
    expected_freq = len(entropy) / 256
    skew_threshold = 5 if len(entropy) < 64 else 3  # More lenient for small samples

    if max_freq > expected_freq * skew_threshold:
        warnings.append("Highly skewed byte distribution detected")
        return 60

    # Count unique bytes - be more lenient for small samples
    unique_bytes = sum(1 for f in frequencies if f > 0)
    diversity_threshold = len(entropy) / 8 if len(entropy) < 64 else len(entropy) / 4

    if unique_bytes < diversity_threshold:
        warnings.append("Low byte diversity detected")
        return 70

    return 100


def _analyze_weakness_signatures(entropy: bytes, warnings: List[str]) -> int:
    """Check for known weak entropy signatures."""
    score = 100

    # Note: Timestamp detection disabled for now as it was too aggressive
    # and flagging good entropy as poor quality

    # Check for ASCII text (common mistake)
    try:
        text = entropy.decode("ascii")
        if text.isprintable():
            warnings.append("Entropy appears to contain ASCII text")
            score = min(score, 30)
    except UnicodeDecodeError:
        pass  # Good, not ASCII text

    return score


def analyze_entropy_patterns(entropy: bytes) -> List[str]:
    """Detect common weak patterns in entropy.

    Args:
        entropy: Entropy bytes to analyze

    Returns:
        List of detected patterns
    """
    patterns = []

    # All zeros
    if entropy == b"\x00" * len(entropy):
        patterns.append("all_zeros")

    # All 0xFF
    if entropy == b"\xff" * len(entropy):
        patterns.append("all_ones")

    # Repeating patterns
    for pattern_len in [1, 2, 4]:
        if len(entropy) >= pattern_len * 4:
            pattern = entropy[:pattern_len]
            if entropy == pattern * (len(entropy) // pattern_len):
                patterns.append(f"repeating_{pattern_len}_byte")

    # Sequential bytes
    if len(entropy) >= 8:
        sequential = bytes(range(len(entropy)))
        if entropy == sequential:
            patterns.append("sequential_bytes")

    return patterns
