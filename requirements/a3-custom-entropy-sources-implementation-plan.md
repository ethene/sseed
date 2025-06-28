# A.3 Custom Entropy Sources Implementation Plan

## Executive Summary

This document provides a detailed step-by-step implementation plan for **A.3 Custom Entropy Sources** from the future-enhancements.md. This feature will add support for hex, dice, and other custom entropy input methods to the `sseed gen` command while maintaining security, backward compatibility, and following established patterns in the codebase.

## Current State Analysis

### Existing Entropy Infrastructure
- **Core Module**: `sseed/entropy.py` - Uses `secrets.SystemRandom()` for secure entropy
- **Generation Function**: `generate_entropy_bytes()` - Currently the sole entropy source
- **Integration Point**: `sseed/bip39.py:generate_mnemonic()` - Calls `generate_entropy_bytes()`
- **CLI Interface**: `sseed/cli/commands/gen.py` - Gen command with language/word count support
- **Validation**: `sseed/validation/crypto.py:validate_entropy_length()` - Validates entropy byte lengths

### Established Patterns
- **CLI Flag Patterns**: Consistent `-w/--words`, `-l/--language` patterns
- **Error Handling**: `CryptoError`, `ValidationError`, `MnemonicError` hierarchy
- **Security Logging**: `log_security_event()` for sensitive operations
- **Input Validation**: Comprehensive validation with clear error messages
- **Memory Safety**: `secure_delete_variable()` for cleanup

## Implementation Architecture

### Design Principles
1. **Security First**: All custom entropy must pass quality validation
2. **Backward Compatibility**: Default behavior unchanged
3. **Mutually Exclusive**: Only one entropy source at a time
4. **Explicit Warnings**: Clear security warnings for weak entropy
5. **Validation Heavy**: Comprehensive input validation and quality checks

### Integration Strategy
- **Extend `gen` command**: Add new `--entropy-*` flags
- **New entropy module**: `sseed/entropy/custom.py` for custom sources
- **Enhanced validation**: Extend existing validation infrastructure
- **Quality analysis**: Built-in entropy quality assessment

## Phase 1: Core Infrastructure (Days 1-2)

### Step 1.1: Create Custom Entropy Module
**File**: `sseed/entropy/custom.py`

```python
"""Custom entropy sources for BIP-39 generation.

Provides validated custom entropy input methods including hex strings,
dice rolls, and other deterministic sources with comprehensive quality analysis.
"""

import hashlib
import re
from typing import List, Optional, Tuple
from sseed.exceptions import EntropyError, ValidationError
from sseed.logging_config import get_logger, log_security_event

logger = get_logger(__name__)

class EntropyQuality:
    """Entropy quality assessment results."""
    def __init__(self, score: int, warnings: List[str], recommendations: List[str]):
        self.score = score  # 0-100
        self.warnings = warnings
        self.recommendations = recommendations
        self.is_acceptable = score >= 70  # Configurable threshold

def hex_to_entropy(hex_string: str, required_bytes: int) -> bytes:
    """Convert hex string to entropy bytes with validation."""
    
def dice_to_entropy(dice_rolls: str, required_bytes: int) -> bytes:
    """Convert dice rolls to entropy bytes with validation."""
    
def validate_entropy_quality(entropy: bytes) -> EntropyQuality:
    """Comprehensive entropy quality analysis."""
    
def analyze_entropy_patterns(entropy: bytes) -> List[str]:
    """Detect common weak patterns in entropy."""
```

### Step 1.2: Extend Entropy Module Structure
**File**: `sseed/entropy/__init__.py`

```python
"""Enhanced entropy generation with custom sources."""

from .core import generate_entropy_bits, generate_entropy_bytes, secure_delete_variable
from .custom import (
    hex_to_entropy,
    dice_to_entropy, 
    validate_entropy_quality,
    EntropyQuality,
)

__all__ = [
    "generate_entropy_bits",
    "generate_entropy_bytes", 
    "secure_delete_variable",
    "hex_to_entropy",
    "dice_to_entropy",
    "validate_entropy_quality",
    "EntropyQuality",
]
```

### Step 1.3: Rename and Refactor Core Entropy
**Action**: Move `sseed/entropy.py` → `sseed/entropy/core.py`
- Maintain all existing functionality
- Update imports across codebase
- Ensure zero breaking changes

## Phase 2: Custom Entropy Implementation (Days 3-4)

### Step 2.1: Hex Entropy Implementation

```python
def hex_to_entropy(hex_string: str, required_bytes: int) -> bytes:
    """Convert hex string to entropy bytes with comprehensive validation.
    
    Args:
        hex_string: Hexadecimal string (with or without 0x prefix)
        required_bytes: Number of entropy bytes needed
        
    Returns:
        Validated entropy bytes
        
    Raises:
        ValidationError: If hex string is invalid or insufficient
        EntropyError: If entropy quality is unacceptable
    """
    try:
        # Normalize hex string
        hex_clean = hex_string.strip().lower()
        if hex_clean.startswith('0x'):
            hex_clean = hex_clean[2:]
            
        # Validate hex format
        if not re.match(r'^[0-9a-f]+$', hex_clean):
            raise ValidationError("Invalid hex string: contains non-hex characters")
            
        # Ensure even length
        if len(hex_clean) % 2 != 0:
            hex_clean = '0' + hex_clean
            logger.warning("Padded hex string with leading zero")
            
        # Convert to bytes
        entropy_bytes = bytes.fromhex(hex_clean)
        
        # Check length requirements
        if len(entropy_bytes) < required_bytes:
            # Pad with secure random if insufficient
            from .core import generate_entropy_bytes
            padding_needed = required_bytes - len(entropy_bytes)
            padding = generate_entropy_bytes(padding_needed)
            entropy_bytes = entropy_bytes + padding
            
            log_security_event(
                f"Hex entropy padded with {padding_needed} secure random bytes",
                {"original_bytes": len(entropy_bytes) - padding_needed, 
                 "padding_bytes": padding_needed}
            )
        elif len(entropy_bytes) > required_bytes:
            # Truncate if too long
            entropy_bytes = entropy_bytes[:required_bytes]
            logger.warning("Truncated hex entropy to %d bytes", required_bytes)
            
        # Quality validation
        quality = validate_entropy_quality(entropy_bytes)
        if not quality.is_acceptable:
            raise EntropyError(
                f"Hex entropy quality insufficient (score: {quality.score}/100)",
                context={"warnings": quality.warnings, "recommendations": quality.recommendations}
            )
            
        logger.info("Successfully processed hex entropy: %d bytes", len(entropy_bytes))
        return entropy_bytes
        
    except Exception as e:
        logger.error("Hex entropy processing failed: %s", e)
        raise
```

### Step 2.2: Dice Entropy Implementation

```python
def dice_to_entropy(dice_rolls: str, required_bytes: int) -> bytes:
    """Convert dice rolls to entropy bytes using established cryptographic methods.
    
    Supports multiple formats:
    - Comma-separated: "1,2,3,4,5,6"
    - Space-separated: "1 2 3 4 5 6" 
    - Continuous: "123456"
    
    Args:
        dice_rolls: String of dice roll results
        required_bytes: Number of entropy bytes needed
        
    Returns:
        Validated entropy bytes derived from dice rolls
        
    Raises:
        ValidationError: If dice format is invalid
        EntropyError: If insufficient dice rolls or poor quality
    """
    try:
        # Parse dice rolls
        dice_values = _parse_dice_string(dice_rolls)
        
        # Validate dice values (1-6 for standard dice)
        for value in dice_values:
            if not (1 <= value <= 6):
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
        dice_string = ''.join(str(d) for d in dice_values)
        entropy_hash = hashlib.sha256(dice_string.encode('utf-8')).digest()
        
        # Extend entropy if needed using multiple hash rounds
        entropy_bytes = entropy_hash
        round_num = 1
        while len(entropy_bytes) < required_bytes:
            round_input = f"{dice_string}:{round_num}"
            additional_hash = hashlib.sha256(round_input.encode('utf-8')).digest()
            entropy_bytes += additional_hash
            round_num += 1
            
        # Truncate to required length
        entropy_bytes = entropy_bytes[:required_bytes]
        
        # Quality validation
        quality = validate_entropy_quality(entropy_bytes)
        if quality.score < 60:  # Lower threshold for dice due to deterministic nature
            logger.warning("Dice entropy quality below optimal: %d/100", quality.score)
            for warning in quality.warnings:
                logger.warning("Dice entropy warning: %s", warning)
                
        logger.info("Successfully processed dice entropy: %d rolls → %d bytes", 
                   len(dice_values), len(entropy_bytes))
        return entropy_bytes
        
    except Exception as e:
        logger.error("Dice entropy processing failed: %s", e)
        raise

def _parse_dice_string(dice_string: str) -> List[int]:
    """Parse dice string into list of integers."""
    dice_clean = dice_string.strip()
    
    # Try comma-separated first
    if ',' in dice_clean:
        return [int(x.strip()) for x in dice_clean.split(',')]
    
    # Try space-separated
    elif ' ' in dice_clean:
        return [int(x) for x in dice_clean.split()]
    
    # Try continuous digits
    elif dice_clean.isdigit():
        return [int(c) for c in dice_clean]
    
    else:
        raise ValidationError(f"Unable to parse dice string: {dice_string}")
```

### Step 2.3: Entropy Quality Analysis

```python
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
    warnings = []
    recommendations = []
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
        recommendations.append("Consider using system entropy instead of custom entropy")
    if score < 50:
        recommendations.append("This entropy is not suitable for cryptographic use")
        recommendations.append("Use 'sseed gen' without entropy flags for secure generation")
    if score < 30:
        recommendations.append("CRITICAL: This entropy appears to be non-random")
        
    return EntropyQuality(score, warnings, recommendations)

def _analyze_patterns(entropy: bytes, warnings: List[str]) -> int:
    """Analyze entropy for obvious patterns."""
    score = 100
    
    # All zeros
    if entropy == b'\x00' * len(entropy):
        warnings.append("Entropy is all zeros")
        return 0
        
    # All 0xFF
    if entropy == b'\xff' * len(entropy):
        warnings.append("Entropy is all 0xFF bytes") 
        return 0
        
    # Repeating patterns
    for pattern_len in [1, 2, 4]:
        if len(entropy) >= pattern_len * 4:
            pattern = entropy[:pattern_len]
            if entropy == pattern * (len(entropy) // pattern_len):
                warnings.append(f"Entropy contains repeating {pattern_len}-byte pattern")
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
    if len(entropy) < 16:
        return 100  # Skip for small samples
        
    # Count byte frequencies
    frequencies = [0] * 256
    for byte in entropy:
        frequencies[byte] += 1
        
    # Check for highly skewed distribution
    max_freq = max(frequencies)
    expected_freq = len(entropy) / 256
    
    if max_freq > expected_freq * 3:  # More than 3x expected
        warnings.append("Highly skewed byte distribution detected")
        return 60
        
    # Count unique bytes
    unique_bytes = sum(1 for f in frequencies if f > 0)
    if unique_bytes < len(entropy) / 4:
        warnings.append("Low byte diversity detected")
        return 70
        
    return 100

def _analyze_weakness_signatures(entropy: bytes, warnings: List[str]) -> int:
    """Check for known weak entropy signatures."""
    score = 100
    
    # Check for timestamp-like patterns (common weak entropy source)
    if len(entropy) >= 4:
        # Look for values that could be Unix timestamps
        for i in range(len(entropy) - 3):
            timestamp_candidate = int.from_bytes(entropy[i:i+4], 'big')
            # Unix timestamp range: 1970-2030 (rough check)
            if 0 < timestamp_candidate < 2000000000:
                warnings.append("Possible timestamp detected in entropy")
                score = min(score, 50)
                break
                
    # Check for ASCII text (another common mistake)
    try:
        text = entropy.decode('ascii')
        if text.isprintable():
            warnings.append("Entropy appears to contain ASCII text")
            score = min(score, 30)
    except UnicodeDecodeError:
        pass  # Good, not ASCII text
        
    return score
```

## Phase 3: CLI Integration (Day 5)

### Step 3.1: Extend Gen Command Arguments

**File**: `sseed/cli/commands/gen.py`

```python
def add_arguments(self, parser: argparse.ArgumentParser) -> None:
    """Add gen command arguments with custom entropy support."""
    # ... existing arguments ...
    
    # Custom entropy group (mutually exclusive)
    entropy_group = parser.add_mutually_exclusive_group()
    
    entropy_group.add_argument(
        "--entropy-hex",
        type=str,
        metavar="HEX",
        help=(
            "Use custom hex entropy (e.g., 'a1b2c3...' or '0xa1b2c3...'). "
            "Will be padded with secure random if insufficient, truncated if excessive. "
            "WARNING: Only use if you understand the security implications."
        )
    )
    
    entropy_group.add_argument(
        "--entropy-dice", 
        type=str,
        metavar="ROLLS",
        help=(
            "Use dice rolls as entropy source (e.g., '1,2,3,4,5,6' or '1 2 3 4 5 6'). "
            "Requires sufficient rolls for target word count. "
            "WARNING: Only use with fair dice and proper randomization."
        )
    )
    
    # Security flags
    parser.add_argument(
        "--allow-weak",
        action="store_true", 
        help="Allow weak entropy with warnings (not recommended)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force operation despite security warnings (dangerous)"
    )
    
    parser.add_argument(
        "--entropy-analysis",
        action="store_true",
        help="Show detailed entropy quality analysis"
    )
```

## Phase 4: Testing and Validation (Day 6)

### Step 4.1: Unit Tests

**File**: `tests/test_custom_entropy.py`

```python
"""Tests for custom entropy sources."""

import pytest
from sseed.entropy.custom import (
    hex_to_entropy,
    dice_to_entropy,
    validate_entropy_quality,
    EntropyQuality,
)
from sseed.exceptions import EntropyError, ValidationError

class TestHexEntropy:
    """Test hex entropy conversion."""
    
    def test_valid_hex_conversion(self):
        """Test valid hex string conversion."""
        hex_input = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
        entropy = hex_to_entropy(hex_input, 32)
        
        assert len(entropy) == 32
        assert entropy == bytes.fromhex(hex_input)
        
    def test_hex_with_0x_prefix(self):
        """Test hex string with 0x prefix."""
        hex_input = "0xa1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
        entropy = hex_to_entropy(hex_input, 32)
        
        assert len(entropy) == 32
        
    def test_hex_padding_insufficient(self):
        """Test hex padding when insufficient entropy."""
        short_hex = "a1b2c3d4"  # Only 4 bytes
        entropy = hex_to_entropy(short_hex, 16)  # Need 16 bytes
        
        assert len(entropy) == 16
        assert entropy[:4] == bytes.fromhex("a1b2c3d4")
        # Remaining bytes should be securely random
        
    def test_hex_truncation_excessive(self):
        """Test hex truncation when too much entropy."""
        long_hex = "a1b2c3d4" * 16  # 64 bytes
        entropy = hex_to_entropy(long_hex, 16)  # Only need 16
        
        assert len(entropy) == 16
        
    def test_invalid_hex_characters(self):
        """Test error handling for invalid hex."""
        with pytest.raises(ValidationError, match="Invalid hex string"):
            hex_to_entropy("xyz123", 16)
            
    def test_weak_hex_entropy(self):
        """Test detection of weak hex entropy."""
        weak_hex = "00000000000000000000000000000000"  # All zeros
        with pytest.raises(EntropyError, match="quality insufficient"):
            hex_to_entropy(weak_hex, 16)

class TestDiceEntropy:
    """Test dice entropy conversion."""
    
    def test_comma_separated_dice(self):
        """Test comma-separated dice format."""
        dice_input = "1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6"
        entropy = dice_to_entropy(dice_input, 16)
        
        assert len(entropy) == 16
        assert isinstance(entropy, bytes)
        
    def test_space_separated_dice(self):
        """Test space-separated dice format."""
        dice_input = "1 2 3 4 5 6 1 2 3 4 5 6 1 2 3 4 5 6 1 2 3 4 5 6 1 2 3 4 5 6"
        entropy = dice_to_entropy(dice_input, 16)
        
        assert len(entropy) == 16
        
    def test_continuous_dice(self):
        """Test continuous dice format."""
        dice_input = "123456123456123456123456123456"
        entropy = dice_to_entropy(dice_input, 16)
        
        assert len(entropy) == 16
        
    def test_insufficient_dice_rolls(self):
        """Test error for insufficient dice rolls."""
        short_dice = "1,2,3"  # Not enough for 16 bytes
        with pytest.raises(EntropyError, match="Insufficient dice rolls"):
            dice_to_entropy(short_dice, 16)
            
    def test_invalid_dice_values(self):
        """Test error for invalid dice values."""
        with pytest.raises(ValidationError, match="Invalid dice value"):
            dice_to_entropy("1,2,3,7,5,6", 16)  # 7 is invalid
            
    def test_dice_deterministic(self):
        """Test that same dice input produces same entropy."""
        dice_input = "1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6,1,2,3,4,5,6"
        entropy1 = dice_to_entropy(dice_input, 16)
        entropy2 = dice_to_entropy(dice_input, 16)
        
        assert entropy1 == entropy2

class TestEntropyQuality:
    """Test entropy quality analysis."""
    
    def test_good_entropy_quality(self):
        """Test analysis of good quality entropy."""
        # Use actual secure random entropy
        from sseed.entropy import generate_entropy_bytes
        good_entropy = generate_entropy_bytes(32)
        
        quality = validate_entropy_quality(good_entropy)
        assert quality.score >= 80
        assert quality.is_acceptable
        
    def test_weak_entropy_detection(self):
        """Test detection of weak entropy patterns."""
        # All zeros
        weak_entropy = b'\x00' * 32
        quality = validate_entropy_quality(weak_entropy)
        
        assert quality.score < 50
        assert not quality.is_acceptable
        assert any("zeros" in warning for warning in quality.warnings)
        
    def test_repeating_pattern_detection(self):
        """Test detection of repeating patterns."""
        pattern_entropy = b'\xa1\xb2' * 16  # Repeating 2-byte pattern
        quality = validate_entropy_quality(pattern_entropy)
        
        assert quality.score < 50
        assert any("repeating" in warning for warning in quality.warnings)
```

## Phase 5: Documentation and Security (Day 7)

### Step 5.1: Update CLI Help Documentation

**File**: `capabilities/cli-interface.md`

```markdown
### Custom Entropy Sources

The `gen` command supports custom entropy sources for specialized use cases:

#### Hex Entropy
```bash
# Use hex string as entropy source
sseed gen --entropy-hex "a1b2c3d4e5f6..." --allow-weak

# With quality analysis
sseed gen --entropy-hex "a1b2c3d4e5f6..." --entropy-analysis --allow-weak
```

#### Dice Entropy  
```bash
# Use dice rolls as entropy source
sseed gen --entropy-dice "1,2,3,4,5,6,1,2,3..." --force

# Different formats supported
sseed gen --entropy-dice "1 2 3 4 5 6 1 2 3..." --force
sseed gen --entropy-dice "123456123456..." --force
```

#### Security Flags
- `--allow-weak`: Allow entropy with quality score < 70
- `--force`: Force operation despite security warnings (dangerous)
- `--entropy-analysis`: Show detailed quality analysis

#### Security Warnings
⚠️ **Custom entropy sources may be less secure than system entropy**
- Only use if you understand the cryptographic implications
- Weak entropy can compromise wallet security
- Default system entropy is recommended for most users
```

### Step 5.2: Security Documentation

**File**: `docs/security/custom-entropy-security.md`

```markdown
# Custom Entropy Security Guidelines

## Overview
Custom entropy sources allow advanced users to provide their own randomness for mnemonic generation. This feature comes with significant security responsibilities.

## Security Principles

### Quality Requirements
- **Minimum Score**: 70/100 for `--allow-weak`, 50/100 for `--force`
- **Pattern Detection**: Automatic detection of weak patterns
- **Distribution Analysis**: Byte frequency analysis
- **Weakness Signatures**: Detection of common mistakes

### Common Pitfalls
1. **Insufficient Entropy**: Not enough random data
2. **Predictable Sources**: Timestamps, sequential data
3. **Biased Sources**: Non-uniform distributions
4. **Reused Entropy**: Using same entropy multiple times

### Best Practices
1. **Use System Entropy**: Default `sseed gen` is recommended
2. **Verify Quality**: Always use `--entropy-analysis`
3. **Understand Risks**: Only use if you understand implications
4. **Test First**: Validate entropy quality before production use

## Entropy Sources Comparison

| Source | Security | Ease of Use | Recommended |
|--------|----------|-------------|-------------|
| System Random | ★★★★★ | ★★★★★ | ✅ Yes |
| Fair Dice | ★★★★☆ | ★★☆☆☆ | ⚠️ Advanced |
| Hardware RNG | ★★★★★ | ★★☆☆☆ | ⚠️ Advanced |
| Hex Input | ★☆☆☆☆ | ★★★☆☆ | ❌ Dangerous |
```

## Success Criteria

### Functional Requirements ✅
- [x] Hex entropy input with validation
- [x] Dice entropy input with multiple formats
- [x] Entropy quality analysis and scoring
- [x] Security warnings and recommendations
- [x] Integration with existing word count and language features
- [x] Mutually exclusive entropy source flags

### Security Requirements ✅
- [x] Comprehensive entropy quality validation
- [x] Pattern detection for weak entropy
- [x] Explicit user consent for weak entropy (`--allow-weak`, `--force`)
- [x] Security event logging
- [x] Secure memory cleanup

### Usability Requirements ✅
- [x] Clear error messages and warnings
- [x] Helpful quality analysis output
- [x] Consistent CLI flag patterns
- [x] Comprehensive documentation

### Compatibility Requirements ✅
- [x] 100% backward compatibility
- [x] Works with all word counts (12, 15, 18, 21, 24)
- [x] Works with all 9 BIP-39 languages
- [x] Integrates with existing entropy display features

## Timeline Summary

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| 1 | 2 days | Core infrastructure, module structure |
| 2 | 2 days | Hex and dice entropy implementation |
| 3 | 1 day | CLI integration and argument parsing |
| 4 | 1 day | Unit and integration tests |
| 5 | 1 day | Documentation and security guidelines |
| 6 | 1 day | Integration testing and performance |

**Total**: 8 days

## Implementation Notes

### Code Quality
- Follow existing patterns in `sseed/bip85/` for validation and error handling
- Use existing logging and security event patterns
- Maintain consistent naming conventions

### Testing Strategy
- Unit tests for all entropy conversion functions
- CLI integration tests for all flag combinations
- Security tests for weak entropy detection
- Performance tests for acceptable response times

### Future Enhancements
- Support for additional entropy sources (coins, cards)
- Advanced statistical analysis
- Entropy source combination/mixing
- Custom entropy quality thresholds

This implementation plan provides a comprehensive roadmap for adding custom entropy sources to SSeed while maintaining security, usability, and backward compatibility. 