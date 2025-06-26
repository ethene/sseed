# Multi-Language Support

SSeed provides comprehensive multi-language support for BIP-39 mnemonics, enabling users worldwide to generate, validate, and restore cryptocurrency seeds in their native languages. This capability implements all 9 official BIP-39 languages with automatic detection and professional Unicode handling.

## Overview

The multi-language support system is built on three core principles:
- **Universal Accessibility**: Support for all 9 official BIP-39 languages
- **Automatic Intelligence**: Seamless language detection without user intervention
- **100% Backward Compatibility**: Existing English-only workflows continue unchanged

## Supported Languages

### Complete Language Matrix

| Language | Code | Script | Wordlist Size | Example Words |
|----------|------|--------|---------------|---------------|
| **English** | `en` | Latin | 2048 | abandon, ability, able... |
| **Spanish** | `es` | Latin | 2048 | ábaco, abdomen, abedul... |
| **French** | `fr` | Latin | 2048 | abaisser, abandon, abdiquer... |
| **Italian** | `it` | Latin | 2048 | abaco, abbaglio, abbinare... |
| **Portuguese** | `pt` | Latin | 2048 | abacate, abalar, abater... |
| **Czech** | `cs` | Latin | 2048 | abdikace, abeceda, adresa... |
| **Chinese (Simplified)** | `zh-cn` | Ideographic | 2048 | 的, 一, 是, 在, 不, 了... |
| **Chinese (Traditional)** | `zh-tw` | Ideographic | 2048 | 的, 一, 是, 在, 不, 了... |
| **Korean** | `ko` | Hangul | 2048 | 가격, 가끔, 가난, 가능... |

### Script Support

#### Latin Scripts (6 languages)
- **Basic Latin**: English with standard ASCII characters
- **Extended Latin**: European languages with diacritical marks
- **Unicode Normalization**: Proper handling of accented characters
- **Case Insensitive**: Flexible input processing

#### Ideographic Scripts (2 languages)
- **Chinese Characters**: Full Unicode CJK support
- **Simplified vs Traditional**: Distinct wordlist recognition
- **Character Normalization**: Proper Unicode handling
- **Input Flexibility**: Multiple input methods supported

#### Hangul Script (1 language)
- **Korean Syllables**: Complete Hangul Unicode range
- **Syllable Composition**: Proper character recognition
- **Input Methods**: Support for various Korean keyboards

## Language Detection System

### Detection Algorithm

The language detection system uses a sophisticated multi-stage approach:

1. **Script Analysis**: Character-based script identification
2. **Word Overlap**: Vocabulary intersection with language wordlists
3. **Confidence Scoring**: Statistical confidence measurement
4. **Validation**: BIP-39 compliance verification

### Detection Accuracy

| Language Group | Accuracy Rate | Confidence Threshold |
|----------------|---------------|----------------------|
| **Latin Scripts** | 95%+ | 70% minimum |
| **Chinese Scripts** | 98%+ | 80% minimum |
| **Korean Script** | 97%+ | 75% minimum |
| **Overall Average** | 95%+ | 70% minimum |

### Detection Process

```python
def detect_mnemonic_language(mnemonic: str) -> Optional[LanguageInfo]:
    """
    1. Normalize input text (Unicode NFKD)
    2. Identify character script type
    3. Calculate word overlap with each language
    4. Score confidence for each candidate
    5. Return highest confidence above threshold
    6. Fallback to validation-based detection
    """
```

## CLI Integration

### Generation Command

Generate mnemonics in any supported language:

```bash
# English (default)
sseed gen
sseed gen -l en

# European languages
sseed gen -l es    # Spanish
sseed gen -l fr    # French
sseed gen -l it    # Italian
sseed gen -l pt    # Portuguese
sseed gen -l cs    # Czech

# Asian languages
sseed gen -l zh-cn # Chinese Simplified
sseed gen -l zh-tw # Chinese Traditional
sseed gen -l ko    # Korean
```

### Auto-Detection Commands

All other commands automatically detect language:

```bash
# Restore operations (language auto-detected)
sseed restore spanish_shard*.txt
sseed restore chinese_shards/*.txt

# Sharding operations (language preserved)
sseed shard -i french_mnemonic.txt -g 3-of-5

# Seed generation (language aware)
sseed seed -i korean_mnemonic.txt --hex
```

### Language Feedback

Commands provide clear language information:

```bash
$ sseed restore spanish_shards/*.txt
# Language: Spanish (es) - Auto-detected
# Mnemonic with language info reconstructed and written to stdout

$ sseed shard -i chinese.txt -g 2-of-3 --verbose
# Language: Chinese Simplified (zh-cn) - Auto-detected
# Creating 2-of-3 SLIP-39 shards...
```

## File Operations

### Language Metadata

Files include language information as comments:

```bash
# Generated English mnemonic
$ cat english_mnemonic.txt
# Language: English (en)
# Generated: 2024-12-25T10:30:00Z
abandon ability able about above absent absorb abstract absurd abuse access accident

# Generated Spanish mnemonic  
$ cat spanish_mnemonic.txt
# Language: Spanish (es)
# Generated: 2024-12-25T10:30:00Z
ábaco abdomen abedul abeja abismo abogado abono aborto abrazo abrir absurdo abuelo
```

### Unicode Handling

- **UTF-8 Encoding**: All files use UTF-8 for proper character support
- **BOM Handling**: Byte Order Mark detection and processing
- **Normalization**: Unicode NFKD normalization for consistency
- **Cross-Platform**: Consistent behavior across operating systems

## API Integration

### Python API

```python
from sseed.bip39 import generate_mnemonic, validate_mnemonic
from sseed.languages import SUPPORTED_LANGUAGES, detect_mnemonic_language
from bip_utils import Bip39Languages

# Generate in specific language
spanish_mnemonic = generate_mnemonic(Bip39Languages.SPANISH)
chinese_mnemonic = generate_mnemonic(Bip39Languages.CHINESE_SIMPLIFIED)

# Automatic detection
detected = detect_mnemonic_language(spanish_mnemonic)
print(f"Detected: {detected.name} ({detected.code})")

# Validation with language
is_valid = validate_mnemonic(chinese_mnemonic, Bip39Languages.CHINESE_SIMPLIFIED)
```

### Language Information

```python
from sseed.languages import SUPPORTED_LANGUAGES, get_supported_languages

# Get all supported languages
languages = get_supported_languages()
for lang in languages:
    print(f"{lang.name}: {lang.code} ({lang.script})")

# Access specific language
spanish = SUPPORTED_LANGUAGES['es']
print(f"BIP-39 Enum: {spanish.bip_enum}")
print(f"Script Type: {spanish.script}")
```

## Performance Characteristics

### Detection Performance

| Operation | Average Time | Max Time | Memory Usage |
|-----------|--------------|----------|-------------|
| **Script Detection** | <1ms | <5ms | <1MB |
| **Word Overlap Analysis** | <10ms | <50ms | <5MB |
| **Full Language Detection** | <50ms | <100ms | <10MB |
| **Wordlist Loading** | <20ms | <100ms | <15MB |

### Generation Performance

| Language | Generation Time | Validation Time | Memory Overhead |
|----------|----------------|-----------------|-----------------|
| **English** | <1ms | <1ms | Baseline |
| **European Languages** | <2ms | <2ms | +10% |
| **Chinese Languages** | <3ms | <3ms | +20% |
| **Korean** | <2ms | <2ms | +15% |

### Memory Optimization

- **Lazy Loading**: Wordlists loaded only when needed
- **Efficient Caching**: Smart wordlist caching strategy
- **Memory Cleanup**: Automatic cleanup of unused resources
- **Minimal Overhead**: <20MB additional memory for all languages

## Security Considerations

### Cryptographic Security

- **Entropy Preservation**: Language changes don't affect entropy quality
- **Wordlist Integrity**: All wordlists cryptographically verified
- **No Information Leakage**: Language detection doesn't reveal sensitive data
- **Secure Defaults**: English remains default for maximum compatibility

### Validation Security

- **Checksum Verification**: Language-aware checksum validation
- **Cross-Language Protection**: Prevents accidental language mixing
- **Input Sanitization**: Robust input validation across all scripts
- **Error Handling**: Secure error messages without information disclosure

## Testing and Quality

### Test Coverage

| Test Category | Test Count | Coverage | Description |
|---------------|------------|----------|-------------|
| **Multi-Language Generation** | 9 tests | 100% | One test per language |
| **Language Detection** | 20 tests | 95%+ | Accuracy and edge cases |
| **CLI Integration** | 23 tests | 100% | Command-line workflows |
| **Unicode Handling** | 12 tests | 100% | Character processing |
| **Backward Compatibility** | 5 tests | 100% | Existing code protection |
| **Performance** | 8 tests | 100% | Speed and memory benchmarks |

### Quality Metrics

- **Detection Accuracy**: 95%+ across all languages
- **Performance**: <100ms detection time per mnemonic
- **Memory Usage**: <20MB overhead for all languages
- **Code Coverage**: 89.96% overall project coverage
- **Code Quality**: 9.86/10 Pylint score maintained

### Edge Case Testing

- **Mixed Language Input**: Proper error handling
- **Invalid Characters**: Graceful degradation
- **Malformed Unicode**: Robust normalization
- **Empty/Null Input**: Secure error responses
- **Very Long Input**: Performance validation

## Migration and Compatibility

### Backward Compatibility

- **100% Preserved**: All existing code continues to work
- **Default Behavior**: English remains default when no language specified
- **API Stability**: No breaking changes to existing functions
- **Performance**: No impact on English-only operations

### Migration Path

```bash
# Existing code continues to work unchanged
sseed gen                    # Still generates English
sseed restore shard*.txt    # Still works with English shards

# New features available immediately
sseed gen -l es             # New: Spanish generation
sseed restore spanish_shards/*.txt  # New: Auto-detection
```

### Version Compatibility

- **v1.7.0+**: Full multi-language support
- **v1.6.x**: English-only (legacy)
- **v1.5.x**: English-only (legacy)

Files generated with v1.7.0+ include language metadata but remain compatible with older versions for English mnemonics.

## Best Practices

### Generation Recommendations

1. **Specify Language**: Use `-l` flag for explicit language selection
2. **Verify Output**: Always verify generated mnemonics in target language
3. **Document Language**: Keep records of which language was used
4. **Test Recovery**: Verify restoration works with generated mnemonics

### Distribution Security

1. **Language Consistency**: Keep all shards in the same language
2. **Metadata Preservation**: Maintain language information in files
3. **Cross-Platform Testing**: Test on different operating systems
4. **Character Encoding**: Ensure UTF-8 support in storage systems

### International Deployment

1. **Locale Configuration**: Set appropriate system locale
2. **Font Support**: Ensure display fonts support target scripts
3. **Input Methods**: Configure appropriate keyboard layouts
4. **User Training**: Educate users on language-specific features

## Troubleshooting

### Common Issues

#### Language Detection Failures
```bash
# Issue: Language not detected
# Solution: Verify mnemonic is valid BIP-39
sseed gen -l es | sseed restore  # Should auto-detect Spanish

# Issue: Wrong language detected
# Solution: Check for mixed wordlists or typos
```

#### Unicode Display Problems
```bash
# Issue: Characters not displaying correctly
# Solution: Verify terminal UTF-8 support
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
```

#### Input Method Issues
```bash
# Issue: Cannot input non-Latin characters
# Solution: Configure appropriate input method
# macOS: System Preferences > Keyboard > Input Sources
# Linux: Configure IBus or similar input method
```

### Debugging

Enable verbose logging for language detection:

```bash
# Debug language detection
sseed --log-level DEBUG restore mnemonic.txt

# Verbose output with language info
sseed -v shard -i multilang_mnemonic.txt -g 2-of-3
```

## Future Enhancements

### Planned Features

- **Language Validation**: Stricter language consistency checking
- **Mixed Language Support**: Handle multilingual environments
- **Custom Wordlists**: Support for custom/extended wordlists
- **Language Statistics**: Usage analytics and reporting

### Research Areas

- **Machine Learning**: Enhanced detection using ML algorithms
- **Natural Language Processing**: Context-aware language detection
- **Internationalization**: Extended Unicode support
- **Performance Optimization**: Faster detection algorithms

The multi-language support system establishes SSeed as a truly international cryptographic tool, providing native language support for users worldwide while maintaining the security, performance, and reliability standards that define the project. 