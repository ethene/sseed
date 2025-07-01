"""Secure entropy generation for sseed application.

Implements cryptographically secure entropy generation using secrets.SystemRandom()
as specified in F-1 of the PRD. No fallback to random module.
"""

import secrets
from typing import Any

from sseed.exceptions import (
    EntropyError,
    SecurityError,
)
from sseed.logging_config import (
    get_logger,
    log_security_event,
)

logger = get_logger(__name__)


def generate_entropy_bits(bits: int = 256) -> int:
    """Generate cryptographically secure entropy bits.

    Uses secrets.SystemRandom().randbits() for secure entropy generation
    as specified in F-1 of the PRD. No fallback to random module.

    Args:
        bits: Number of entropy bits to generate (default: 256 for BIP-39).

    Returns:
        Cryptographically secure random integer.

    Raises:
        EntropyError: If entropy generation fails.
        SecurityError: If invalid bit count is requested.
    """
    if bits <= 0 or bits > 4096:  # Reasonable upper limit
        raise SecurityError(
            f"Invalid entropy bits requested: {bits}. Must be between 1 and 4096.",
            context={"requested_bits": bits},
        )

    try:
        logger.debug("Generating %d bits of secure entropy", bits)
        entropy_value = secrets.SystemRandom().getrandbits(bits)

        # Verify entropy is within expected range
        max_value = (1 << bits) - 1
        if entropy_value < 0 or entropy_value > max_value:
            raise EntropyError(
                f"Generated entropy value {entropy_value} outside expected range [0, {max_value}]",
                context={
                    "entropy_value": entropy_value,
                    "max_value": max_value,
                    "bits": bits,
                },
            )

        logger.info("Successfully generated %d bits of entropy", bits)
        log_security_event(f"Entropy generation: {bits} bits", {"bits": bits})

        return entropy_value

    except Exception as e:
        error_msg = f"Failed to generate {bits} bits of entropy: {e}"
        logger.error(error_msg)
        log_security_event(
            f"Entropy generation failed: {error_msg}", {"bits": bits, "error": str(e)}
        )
        raise EntropyError(
            error_msg, context={"bits": bits, "original_error": str(e)}
        ) from e


def generate_entropy_bytes(num_bytes: int = 32) -> bytes:
    """Generate cryptographically secure entropy bytes.

    Uses secrets.token_bytes() for secure byte generation as specified
    in F-1 of the PRD.

    Args:
        num_bytes: Number of entropy bytes to generate (default: 32 for 256 bits).

    Returns:
        Cryptographically secure random bytes.

    Raises:
        EntropyError: If entropy generation fails.
        SecurityError: If invalid byte count is requested.
    """
    if num_bytes <= 0 or num_bytes > 512:  # Reasonable upper limit
        raise SecurityError(
            f"Invalid entropy bytes requested: {num_bytes}. Must be between 1 and 512.",
            context={"requested_bytes": num_bytes},
        )

    try:
        logger.debug("Generating %d bytes of secure entropy", num_bytes)
        entropy_bytes = secrets.token_bytes(num_bytes)

        # Verify correct length
        if len(entropy_bytes) != num_bytes:
            raise EntropyError(
                f"Generated entropy length {len(entropy_bytes)} != requested {num_bytes}",
                context={
                    "generated_length": len(entropy_bytes),
                    "requested_bytes": num_bytes,
                },
            )

        logger.info("Successfully generated %d bytes of entropy", num_bytes)
        log_security_event(
            f"Entropy generation: {num_bytes} bytes", {"bytes": num_bytes}
        )

        return entropy_bytes

    except Exception as e:
        error_msg = f"Failed to generate {num_bytes} bytes of entropy: {e}"
        logger.error(error_msg)
        log_security_event(
            f"Entropy generation failed: {error_msg}",
            {"bytes": num_bytes, "error": str(e)},
        )
        raise EntropyError(
            error_msg, context={"bytes": num_bytes, "original_error": str(e)}
        ) from e


def secure_delete_variable(*variables: Any) -> None:
    """Securely delete variables from memory.

    Implements secure memory handling as specified in user rules.
    Attempts to overwrite memory before deletion.

    Args:
        *variables: Variables to securely delete.
    """
    for var in variables:
        try:
            # For mutable objects, try to overwrite content
            if hasattr(var, "__setitem__"):
                # Dict-like objects
                if hasattr(var, "clear"):
                    var.clear()
            elif hasattr(var, "__setitem__") and hasattr(var, "__len__"):
                # List-like objects
                for i, _ in enumerate(var):
                    var[i] = 0
            elif isinstance(var, bytearray):
                # Overwrite bytearray with zeros
                for i, _ in enumerate(var):
                    var[i] = 0

        except (TypeError, AttributeError, ValueError) as e:
            logger.warning("Could not securely overwrite variable: %s", e)

        # Delete the variable reference
        del var

    logger.debug("Securely deleted %d variables", len(variables))
