# BIP85 Implementation Guide

SSeed provides a complete, specification-compliant implementation of [BIP85: Deterministic Entropy From BIP32 Keychains](https://github.com/bitcoin/bips/blob/master/bip-0085.mediawiki).

## Overview

BIP85 allows you to derive multiple child entropy sources from a single master seed in a deterministic and secure manner. This is useful for:

- Generating multiple BIP39 mnemonics from one master seed
- Creating deterministic passwords and hex entropy
- Maintaining a single backup while having multiple wallets
- Reducing key management complexity

## Key Features

✅ **Full BIP85 Specification Compliance**
- Correct BIP39 derivation path: `m/83696968'/39'/{language}'/{words}'/{index}'`
- Proper HMAC-SHA512 implementation with "bip-entropy-from-k" key
- Support for all official BIP85 applications

✅ **Verified Against Official Test Vectors**
- Matches canonical test vectors from the BIP85 specification
- Compatible with reference implementations

✅ **Multi-Language Support**
- Support for all BIP39 languages supported by BIP85
- Proper language code mapping per specification

✅ **Security-Focused Design**
- Memory-secure cleanup of sensitive data
- No sensitive data exposure in error messages
- Comprehensive input validation

## Quick Start

### Basic Usage

```python
import hashlib
from sseed.bip85.applications import Bip85Applications

# Generate master seed from your main mnemonic
master_mnemonic = "your master mnemonic here"
master_seed = hashlib.pbkdf2_hmac(
    'sha512', 
    master_mnemonic.encode('utf-8'), 
    b'mnemonic', 
    2048, 
    64
)

# Create BIP85 applications instance
apps = Bip85Applications()

# Generate child BIP39 mnemonics
child_mnemonic_1 = apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")  # 12 words, index 0
child_mnemonic_2 = apps.derive_bip39_mnemonic(master_seed, 12, 1, "en")  # 12 words, index 1
child_mnemonic_3 = apps.derive_bip39_mnemonic(master_seed, 24, 0, "en")  # 24 words, index 0

# Generate hex entropy
hex_entropy = apps.derive_hex_entropy(master_seed, 32, 0)  # 32 bytes, index 0

# Generate passwords
password = apps.derive_password(master_seed, 20, 0, "base64")  # 20 chars, index 0
```

### Using SSeed CLI

```bash
# Generate child BIP39 mnemonic
python -m sseed.cli bip85 bip39 --master-mnemonic "your master mnemonic" --words 12 --index 0

# Generate hex entropy
python -m sseed.cli bip85 hex --master-mnemonic "your master mnemonic" --bytes 32 --index 0

# Generate password
python -m sseed.cli bip85 password --master-mnemonic "your master mnemonic" --length 20 --index 0
```

## Supported Applications

### BIP39 Mnemonics (Application 39)

Generate deterministic BIP39 mnemonics in multiple languages:

```python
# English (default)
mnemonic_en = apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")

# Spanish
mnemonic_es = apps.derive_bip39_mnemonic(master_seed, 12, 0, "es")

# French
mnemonic_fr = apps.derive_bip39_mnemonic(master_seed, 12, 0, "fr")

# Supported word counts: 12, 15, 18, 21, 24
mnemonic_24 = apps.derive_bip39_mnemonic(master_seed, 24, 0, "en")
```

**Supported Languages:**
- English (`en`) - Language code 0
- Spanish (`es`) - Language code 3  
- French (`fr`) - Language code 6
- Italian (`it`) - Language code 7
- Portuguese (`pt`) - Language code 9
- Czech (`cs`) - Language code 8
- Chinese Simplified (`zh-cn`) - Language code 4
- Chinese Traditional (`zh-tw`) - Language code 5
- Korean (`ko`) - Language code 2

### Hex Entropy (Application 128)

Generate deterministic hexadecimal entropy:

```python
# Generate 32 bytes of hex entropy
hex_32 = apps.derive_hex_entropy(master_seed, 32, 0)  # Returns 64-char hex string

# Generate different lengths
hex_16 = apps.derive_hex_entropy(master_seed, 16, 0)  # 32-char hex string
hex_64 = apps.derive_hex_entropy(master_seed, 64, 0)  # 128-char hex string

# Uppercase format
hex_upper = apps.derive_hex_entropy(master_seed, 32, 0, uppercase=True)
```

### Passwords (Application 9999)

Generate deterministic passwords with various character sets:

```python
# Base64 character set (default)
password_b64 = apps.derive_password(master_seed, 20, 0, "base64")

# Alphanumeric only
password_alnum = apps.derive_password(master_seed, 20, 0, "alphanumeric")

# ASCII printable characters
password_ascii = apps.derive_password(master_seed, 20, 0, "ascii")

# Numbers only
password_num = apps.derive_password(master_seed, 10, 0, "numeric")
```

## BIP85 Derivation Path

The BIP85 specification defines different derivation paths for different applications:

### BIP39 Mnemonics
```
m/83696968'/39'/{language}'/{words}'/{index}'
```

Example for 12-word English mnemonic at index 0:
```
m/83696968'/39'/0'/12'/0'
```

### Other Applications  
```
m/83696968'/{application}'/{length}'/{index}'
```

Example for 32-byte hex entropy at index 0:
```
m/83696968'/128'/32'/0'
```

## Official Test Vectors

Our implementation passes all official BIP85 test vectors:

### Master Test Mnemonic
```
install scatter logic circle pencil average fall shoe quantum disease suspect usage
```

### Expected Results
- **12 words, index 0:** `girl mad pet galaxy egg matter matrix prison refuse sense ordinary nose`
- **18 words, index 0:** `near account window bike charge season chef number sketch tomorrow excuse sniff circle vital hockey outdoor supply token`
- **24 words, index 0:** `puppy ocean match cereal symbol another shed magic wrap hammer bulb intact gadget divorce twin tonight reason outdoor destroy simple truth cigar social volcano`

## Security Considerations

### Best Practices

1. **Master Seed Security**
   - Use a secure, high-entropy master mnemonic
   - Store master seed securely (hardware wallet, secure backup)
   - Never share or expose the master seed

2. **Index Management**
   - Use sequential indices (0, 1, 2, ...) for organization
   - Document which indices are used for what purpose
   - Avoid gaps in index sequences for easier recovery

3. **Deterministic Recovery**
   - Document the application, word count, language, and index for each derived seed
   - Test recovery procedures with your backup system
   - Verify derived seeds match expected values

### Security Features

- **Memory Cleanup:** All intermediate values are securely cleared
- **Error Safety:** No sensitive data is exposed in error messages
- **Input Validation:** Comprehensive validation of all parameters
- **Constant Time:** Operations designed to avoid timing attacks

## Error Handling

The implementation provides detailed error messages for common issues:

```python
from sseed.bip85.exceptions import Bip85ValidationError, Bip85ApplicationError

try:
    mnemonic = apps.derive_bip39_mnemonic(master_seed, 13, 0, "en")  # Invalid word count
except Bip85ValidationError as e:
    print(f"Validation error: {e}")
    print(f"Parameter: {e.parameter}")
    print(f"Valid range: {e.valid_range}")
```

## Performance Optimization

For multiple operations with the same master seed, consider using the optimization features:

```python
# The master key is automatically cached within the same application instance
apps = Bip85Applications()

# These operations will reuse the cached master key
mnemonic_1 = apps.derive_bip39_mnemonic(master_seed, 12, 0, "en")
mnemonic_2 = apps.derive_bip39_mnemonic(master_seed, 12, 1, "en")
mnemonic_3 = apps.derive_bip39_mnemonic(master_seed, 12, 2, "en")
```

## Compatibility

Our BIP85 implementation is compatible with:

- [ethankosakovsky/bip85](https://github.com/ethankosakovsky/bip85) - Reference implementation
- [AndreasGassmann/bip85](https://github.com/AndreasGassmann/bip85) - JavaScript implementation  
- Ian Coleman's BIP39 tool (when using correct BIP85 entropy)
- All other specification-compliant BIP85 implementations

## Advanced Usage

### Custom Entropy Derivation

For advanced use cases, you can access the core entropy derivation functions directly:

```python
from sseed.bip85.core import derive_bip85_entropy, derive_bip85_bip39_entropy

# Standard BIP85 entropy (non-BIP39)
entropy = derive_bip85_entropy(master_seed, application=128, length=32, index=0, output_bytes=32)

# BIP39-specific entropy with language parameter
bip39_entropy = derive_bip85_bip39_entropy(master_seed, language_code=0, word_count=12, index=0, output_bytes=16)
```

### Integration with Existing Systems

The BIP85 implementation integrates seamlessly with existing SSeed infrastructure:

```python
from sseed.bip39 import entropy_to_mnemonic, validate_mnemonic
from sseed.bip85.core import derive_bip85_bip39_entropy

# Generate entropy using BIP85
entropy = derive_bip85_bip39_entropy(master_seed, 0, 12, 0, 16)

# Convert to mnemonic using SSeed's BIP39 infrastructure  
mnemonic = entropy_to_mnemonic(entropy, "en")

# Validate the result
is_valid = validate_mnemonic(mnemonic, "en")
assert is_valid
```

## Testing

Run the comprehensive test suite to verify the implementation:

```bash
# Run all BIP85 tests
python -m pytest tests/bip85/ -v

# Run only official test vector tests
python -m pytest tests/bip85/test_core.py::TestBip85OfficialTestVectors -v

# Run specific application tests
python -m pytest tests/bip85/test_applications.py -v
```

## References

- [BIP85 Specification](https://github.com/bitcoin/bips/blob/master/bip-0085.mediawiki)
- [BIP32 Hierarchical Deterministic Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
- [BIP39 Mnemonic Code for Generating Deterministic Keys](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [Reference Implementation](https://github.com/ethankosakovsky/bip85) 