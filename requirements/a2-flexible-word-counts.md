# A.2 Flexible Word Counts Implementation Requirements

## Executive Summary

This document details the implementation requirements for **A.2 Flexible Word Counts** from the future enhancements roadmap. Currently, SSeed is hardcoded to generate only 24-word BIP-39 mnemonics (256 bits entropy). This enhancement will add support for all standard BIP-39 mnemonic lengths: 12, 15, 18, 21, and 24 words, corresponding to 128, 160, 192, 224, and 256 bits of entropy respectively.

## Current State Analysis

### Hardcoded 24-Word Implementation

**Key Finding**: The codebase is systematically hardcoded for 24-word mnemonics:

1. **Generation Function** (`sseed/bip39.py:92`):
   ```python
   mnemonic = str(generator.FromWordsNumber(24))  # HARDCODED
   ```

2. **Documentation and Comments**: Extensive references to "24-word" throughout:
   - CLI help text: "Generate a 24-word BIP-39 mnemonic"
   - Function docstrings: "Generated BIP-39 mnemonic string (24 words)"
   - Test assertions: `assert len(words) == 24`

3. **Entropy Assumptions**: Fixed 256-bit entropy generation:
   ```python
   generate_entropy_bits(bits: int = 256)  # Default for 24 words
   ```

### Existing Infrastructure Support

**Positive Finding**: Core validation infrastructure already supports flexible word counts:

1. **Validation Constants** (`sseed/validation/input.py:17`):
   ```python
   BIP39_MNEMONIC_LENGTHS = [12, 15, 18, 21, 24]  # Already defined!
   ```

2. **Entropy Validation** (`sseed/validation/crypto.py:114-115`):
   ```python
   # BIP-39 supports entropy lengths: 128, 160, 192, 224, 256 bits
   valid_lengths = {16, 20, 24, 28, 32}  # bytes - Already correct!
   ```

3. **Multi-Language Support**: All word count validation works across languages.

## BIP-39 Word Count to Entropy Mapping

| Word Count | Entropy Bits | Entropy Bytes | Checksum Bits | Use Case |
|------------|--------------|---------------|---------------|----------|
| 12 words   | 128 bits     | 16 bytes      | 4 bits        | Standard wallets |
| 15 words   | 160 bits     | 20 bytes      | 5 bits        | Enhanced security |
| 18 words   | 192 bits     | 24 bytes      | 6 bits        | High security |
| 21 words   | 224 bits     | 28 bytes      | 7 bits        | Maximum security |
| 24 words   | 256 bits     | 32 bytes      | 8 bits        | Current default |

**Formula**: `entropy_bits = (word_count * 11) - checksum_bits`
**Checksum**: `checksum_bits = entropy_bits / 32` (rounded down)

## Implementation Requirements

### Phase 1: Core Function Updates

#### 1.1 Update `generate_mnemonic()` Function

**File**: `sseed/bip39.py`
**Current**: Hardcoded 24-word generation
**Required**: Add optional `word_count` parameter

```python
def generate_mnemonic(
    language: Optional[Bip39Languages] = None,
    word_count: int = 24  # NEW PARAMETER
) -> str:
    """Generate a BIP-39 mnemonic with optional language and word count support.

    Args:
        language: Optional BIP-39 language. Defaults to English for backward compatibility.
        word_count: Number of words in mnemonic (12, 15, 18, 21, or 24). Defaults to 24.

    Returns:
        Generated BIP-39 mnemonic string with specified word count.

    Raises:
        CryptoError: If mnemonic generation fails.
        ValidationError: If word_count is not valid BIP-39 length.
    """
```

**Implementation Changes**:
- Replace `generator.FromWordsNumber(24)` with `generator.FromWordsNumber(word_count)`
- Add word count validation using existing `BIP39_MNEMONIC_LENGTHS`
- Update logging to include word count information
- Maintain backward compatibility (default 24 words)

#### 1.2 Update Entropy Generation

**File**: `sseed/entropy.py`
**Current**: Fixed 256-bit default
**Required**: Calculate entropy bits from word count

**Word Count to Entropy Mapping Function**:
```python
def word_count_to_entropy_bits(word_count: int) -> int:
    """Convert BIP-39 word count to required entropy bits.
    
    Args:
        word_count: Number of words (12, 15, 18, 21, or 24)
        
    Returns:
        Required entropy bits for the word count
        
    Raises:
        ValidationError: If word count is invalid
    """
    entropy_map = {
        12: 128,  # 128 bits entropy + 4 bits checksum = 132 bits = 12 words * 11 bits
        15: 160,  # 160 bits entropy + 5 bits checksum = 165 bits = 15 words * 11 bits  
        18: 192,  # 192 bits entropy + 6 bits checksum = 198 bits = 18 words * 11 bits
        21: 224,  # 224 bits entropy + 7 bits checksum = 231 bits = 21 words * 11 bits
        24: 256   # 256 bits entropy + 8 bits checksum = 264 bits = 24 words * 11 bits
    }
    
    if word_count not in entropy_map:
        raise ValidationError(
            f"Invalid word count: {word_count}. Must be one of: {list(entropy_map.keys())}"
        )
    
    return entropy_map[word_count]
```

### Phase 2: CLI Integration

#### 2.1 Add `--words` Flag to Gen Command

**File**: `sseed/cli/commands/gen.py`
**Current**: No word count option
**Required**: Add `--words` argument

```python
def add_arguments(self, parser: argparse.ArgumentParser) -> None:
    """Add gen command arguments."""
    # Existing arguments...
    
    # NEW: Word count argument
    parser.add_argument(
        "-w",
        "--words",
        type=int,
        choices=[12, 15, 18, 21, 24],
        default=24,
        metavar="COUNT",
        help=(
            "Number of words in generated mnemonic (default: 24). "
            "Choices: 12 (128-bit), 15 (160-bit), 18 (192-bit), "
            "21 (224-bit), 24 (256-bit)"
        ),
    )
```

#### 2.2 Update CLI Help and Descriptions

**Files to Update**:
- `sseed/cli/commands/gen.py`: Command description and help text
- Documentation files: Remove "24-word" hardcoding

**Example Updates**:
- Change: "Generate a 24-word BIP-39 mnemonic"
- To: "Generate a BIP-39 mnemonic (12-24 words)"

## CLI Design Examples

### Generation with Different Word Counts

```bash
# Generate 12-word mnemonic (128-bit entropy)
sseed gen --words 12
# Output: abandon ability able about above absent absorb abstract absurd abuse access accident

# Generate 24-word mnemonic (256-bit entropy, default)
sseed gen --words 24
sseed gen  # Same as above (backward compatible)

# Generate with language and word count
sseed gen --language spanish --words 15
sseed gen -l es -w 15  # Short form

# Save to file with entropy display
sseed gen --words 18 --show-entropy -o wallet-18.txt
```

### Auto-Detection in Other Commands

```bash
# All commands auto-detect word count (no changes needed)
sseed shard -i wallet-12.txt -g 3-of-5    # Auto-detects 12 words
sseed shard -i wallet-24.txt -g 3-of-5    # Auto-detects 24 words

sseed restore shard*.txt                  # Works with any word count
sseed seed -i wallet-15.txt               # Auto-detects 15 words
```

## Implementation Priority

### High Priority (Must Have)
1. **Core Function Update**: `generate_mnemonic()` with `word_count` parameter
2. **CLI Integration**: `--words` flag in gen command
3. **Test Updates**: Fix hardcoded assertions, add parameterized tests
4. **Documentation**: Update help text and documentation

### Medium Priority (Should Have)
1. **Enhanced Validation**: Better error messages for invalid word counts
2. **Performance Testing**: Verify performance across all word counts
3. **Cross-Tool Compatibility**: Test with official BIP-39 tools

### Low Priority (Nice to Have)
1. **Advanced CLI Features**: Word count recommendations based on use case
2. **Entropy Quality Analysis**: Per-word-count entropy quality metrics

## Backward Compatibility Guarantee

### Unchanged Behavior
- **Default Generation**: `sseed gen` still produces 24-word mnemonics
- **All Other Commands**: Continue to work with any valid mnemonic length
- **File Formats**: No changes to input/output file formats
- **API Compatibility**: All existing function signatures preserved

### New Behavior
- **Optional Enhancement**: `--words` flag provides new functionality
- **Validation Messages**: More specific error messages for invalid lengths
- **Documentation**: Updated to reflect flexible word count support

## Implementation Estimate

### Development Effort
- **Core Implementation**: 4-6 hours
- **CLI Integration**: 2-3 hours
- **Test Updates**: 6-8 hours
- **Documentation Updates**: 3-4 hours
- **Total**: 15-21 hours

### Testing Effort
- **Unit Tests**: 3-4 hours
- **Integration Tests**: 2-3 hours
- **Compatibility Testing**: 2-3 hours
- **Total**: 7-10 hours

### Overall Timeline
- **Development**: 1-2 days
- **Testing**: 1 day
- **Documentation**: 0.5 days
- **Total**: 2.5-3.5 days

This enhancement represents a significant capability expansion while maintaining the security-first, automation-friendly design philosophy of SSeed. The implementation leverages existing validation infrastructure and maintains complete backward compatibility.

## Additional Refactoring Analysis

After analyzing the codebase architecture, several opportunities for cleaner implementation have been identified:

### Architecture Analysis

#### Current Generation Pattern: `FromWordsNumber` vs `FromEntropy`

**Current Implementation**:
```python
# sseed/bip39.py:92
generator = Bip39MnemonicGenerator(language)
mnemonic = str(generator.FromWordsNumber(24))  # Word count approach
```

**Alternative Pattern Found in Codebase**:
```python
# sseed/slip39_operations.py:244 and tests/test_shamir_cli_compatibility.py:65
bip39_mnemonic = Bip39MnemonicGenerator().FromEntropy(master_secret)  # Entropy approach
```

#### Recommended Refactoring: Entropy-First Architecture

**Benefits of Entropy-First Approach**:
1. **More Explicit Control**: Direct control over entropy quality and quantity
2. **Better Testing**: Easier to test with known entropy values
3. **Cleaner Separation**: Separates entropy generation from mnemonic encoding
4. **Future Extensibility**: Supports custom entropy sources (A.3 requirement)

**Proposed Refactored Architecture**:
```python
def generate_mnemonic(
    language: Optional[Bip39Languages] = None,
    word_count: int = 24
) -> str:
    """Generate BIP-39 mnemonic using entropy-first approach."""
    
    # 1. Calculate required entropy from word count
    entropy_bits = word_count_to_entropy_bits(word_count)
    entropy_bytes = entropy_bits // 8
    
    # 2. Generate secure entropy
    entropy = generate_entropy_bytes(entropy_bytes)
    
    # 3. Convert entropy to mnemonic
    generator = Bip39MnemonicGenerator(language)
    mnemonic = str(generator.FromEntropy(entropy))
    
    return mnemonic
```

### Additional Refactoring Opportunities

#### 1. Entropy Module Enhancement

**Current State**: Fixed defaults (256 bits, 32 bytes)
**Recommended**: Word-count aware entropy generation

```python
# New function in sseed/entropy.py
def generate_entropy_for_word_count(word_count: int) -> bytes:
    """Generate entropy appropriate for BIP-39 word count."""
    entropy_bits = word_count_to_entropy_bits(word_count)
    entropy_bytes = entropy_bits // 8
    return generate_entropy_bytes(entropy_bytes)
```

#### 2. CLI Architecture Improvement

**Current Pattern**: Command-specific validation and generation
**Recommended**: Centralized parameter validation

```python
# New validation in sseed/cli/commands/gen.py
def validate_generation_params(args: argparse.Namespace) -> GenerationConfig:
    """Validate and normalize generation parameters."""
    config = GenerationConfig(
        language=validate_language_code(args.language).bip_enum,
        word_count=args.words,
        output_file=args.output,
        show_entropy=args.show_entropy
    )
    
    # Cross-validate parameters
    if config.word_count not in BIP39_MNEMONIC_LENGTHS:
        raise ValidationError(f"Invalid word count: {config.word_count}")
    
    return config
```

#### 3. Test Architecture Modernization

**Current Issues Identified**:
- Hardcoded assertions: `assert len(words) == 24`
- Fixed entropy expectations: `assert len(entropy) == 32`
- Non-parameterized tests for word count variations

**Recommended Test Refactoring**:
```python
# Parameterized test approach
@pytest.mark.parametrize("word_count,expected_entropy_bytes", [
    (12, 16), (15, 20), (18, 24), (21, 28), (24, 32)
])
class TestFlexibleWordCounts:
    def test_generation_entropy_consistency(self, word_count, expected_entropy_bytes):
        """Test entropy consistency across word counts."""
        mnemonic = generate_mnemonic(word_count=word_count)
        entropy = get_mnemonic_entropy(mnemonic)
        
        assert len(mnemonic.split()) == word_count
        assert len(entropy) == expected_entropy_bytes
```

### Updated Implementation Requirements

#### Phase 1: Core Refactoring (RECOMMENDED)

**1.1 Entropy-First Architecture Migration**
- Refactor `generate_mnemonic()` to use `FromEntropy` instead of `FromWordsNumber`
- Add `word_count_to_entropy_bits()` mapping function
- Add `generate_entropy_for_word_count()` helper function

**Benefits**:
- Cleaner architecture aligned with existing patterns
- Better testability with deterministic entropy
- Foundation for A.3 (Custom Entropy Sources)
- More explicit entropy handling

**1.2 Parameter Validation Centralization**
- Create `GenerationConfig` dataclass for parameter validation
- Centralize word count validation logic
- Improve error messages with context

#### Phase 2: CLI Integration (UNCHANGED)
- Add `--words` flag to gen command
- Update help text and descriptions

#### Phase 3: Test Modernization (ENHANCED)

**3.1 Parameterized Test Migration**
- Convert hardcoded word count tests to parameterized tests
- Add entropy consistency validation across word counts
- Implement cross-validation test matrix

**3.2 Architecture Test Coverage**
- Test entropy-first generation path
- Validate word count to entropy mapping
- Test parameter validation logic

### Risk Assessment Update

#### Low Risk (Architecture Benefits)
- **Entropy-First Pattern**: Already used successfully in SLIP-39 operations
- **Parameter Validation**: Improves error handling and user experience
- **Test Modernization**: Reduces maintenance burden

#### Medium Risk (Implementation Scope)
- **Refactoring Scope**: Larger than minimal implementation but provides better foundation
- **Test Migration**: More test updates required but results in better coverage

### Recommendation: Enhanced Implementation

**Recommended Approach**: Implement the entropy-first refactoring for these reasons:

1. **Architectural Consistency**: Aligns with existing SLIP-39 patterns
2. **Future-Proofing**: Provides foundation for A.3 (Custom Entropy Sources)
3. **Better Testability**: Enables deterministic testing with known entropy
4. **Code Quality**: More explicit and maintainable architecture

**Trade-off**: Slightly more implementation work for significantly better architecture.

## Updated Implementation Estimate

### Development Time (Enhanced Approach)
- **Phase 1**: 3-4 days (core refactoring with entropy-first architecture)
- **Phase 2**: 1 day (CLI integration)
- **Phase 3**: 3-4 days (comprehensive test modernization)
- **Phase 4**: 1 day (documentation updates)
- **Total**: 8-10 days

### Testing Requirements
- **Unit Tests**: 75+ new/updated test cases (parameterized)
- **Integration Tests**: CLI command testing with all word counts
- **Architecture Tests**: Entropy-first generation validation
- **Compatibility Tests**: Cross-tool validation with official BIP-39 tools
- **Performance Tests**: Verify consistent performance across word counts

### Risk Level: **MEDIUM** (Enhanced Implementation)
- Entropy-first architecture provides better foundation
- Parameterized testing reduces future maintenance
- Larger scope but significantly better long-term maintainability
- Foundation for future enhancements (A.3, B.1)

## Implementation Decision

### Option 1: Minimal Implementation (Original Plan)
- **Time**: 2.5-3.5 days
- **Risk**: Low
- **Benefits**: Quick delivery, minimal changes
- **Drawbacks**: Technical debt, limited extensibility

### Option 2: Enhanced Implementation (Recommended)
- **Time**: 8-10 days
- **Risk**: Medium
- **Benefits**: Better architecture, future-proofing, improved testability
- **Drawbacks**: Longer development time

**Recommendation**: Choose Option 2 (Enhanced Implementation) for better long-term maintainability and alignment with existing codebase patterns.
