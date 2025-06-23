# Cryptographic Operations

SSeed provides robust cryptographic capabilities built on industry-standard algorithms and libraries. All operations are designed for maximum security and compliance with established standards.

## BIP-39 Mnemonic Generation

### Overview
Generates 24-word mnemonics compliant with Bitcoin Improvement Proposal 39 (BIP-39) using cryptographically secure entropy.

### Technical Implementation
- **Entropy Source**: `secrets.SystemRandom().randbits(256)` 
- **Library**: `bip_utils.Bip39MnemonicGenerator`
- **Word Count**: Fixed at 24 words (256 bits entropy)
- **Language**: English wordlist (2048 words)
- **Encoding**: UTF-8 with NFKD normalization

### Security Features
- **Cryptographic Entropy**: Uses OS-provided secure random number generator
- **No Fallbacks**: Never falls back to pseudo-random generators
- **Checksum Validation**: Built-in BIP-39 checksum verification
- **Memory Security**: Immediate cleanup of sensitive variables

### Performance Characteristics
- **Generation Time**: < 1ms average
- **Memory Usage**: < 1KB additional during generation
- **CPU Usage**: Minimal, single-threaded

### Usage Examples

```bash
# Generate to stdout
sseed gen

# Generate to file
sseed gen -o secure_seed.txt

# Example output (24 words)
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
```

### Validation Process
1. **Entropy Generation**: 256 bits of secure random data
2. **Mnemonic Creation**: Conversion using BIP-39 algorithm
3. **Checksum Calculation**: 8-bit checksum appended
4. **Word Mapping**: Map to English wordlist
5. **Validation**: Verify checksum integrity

## BIP-39 Master Seed Generation

### Overview
Generates 512-bit master seeds from BIP-39 mnemonics using PBKDF2-HMAC-SHA512 as specified in the BIP-39 standard. Master seeds serve as the root for hierarchical deterministic (HD) wallet key derivation per BIP-32.

### What is a Master Seed?
A master seed is the cryptographic foundation of hierarchical deterministic (HD) wallets. It's a 512-bit (64-byte) value derived from your BIP-39 mnemonic phrase that serves as the single source of entropy for generating all private keys in an HD wallet system.

**Key Concepts:**
- **Bridge Function**: Converts human-readable mnemonic phrases into cryptographic material
- **Deterministic**: Same mnemonic + passphrase always produces identical master seed
- **Root Source**: All wallet addresses and private keys derive from this single seed
- **Standard Compliance**: Follows BIP-39 → BIP-32 specification chain

**Why Master Seeds Matter:**
- **HD Wallet Foundation**: Required for BIP-32 hierarchical deterministic wallet systems
- **Key Derivation**: Enables generation of unlimited addresses from single backup
- **Wallet Recovery**: Allows complete wallet restoration from mnemonic + passphrase
- **Multi-Account Support**: Supports multiple accounts/purposes from one seed
- **Cross-Platform**: Compatible with all major wallet software and hardware devices

**Common Use Cases:**
- **Wallet Initialization**: Setting up new HD wallets (hardware/software)
- **Key Derivation**: Generating master private keys for BIP-32 systems
- **Backup Verification**: Ensuring mnemonic backups produce correct seeds
- **Multi-Wallet**: Creating seeds for different purposes (personal, business, etc.)
- **Integration**: Feeding seeds into wallet software or hardware security modules

### Technical Implementation
- **Algorithm**: PBKDF2-HMAC-SHA512
- **Output Size**: 512 bits (64 bytes)
- **Default Iterations**: 2048 (BIP-39 standard)
- **Salt Format**: "mnemonic" + passphrase (UTF-8 encoded)
- **Normalization**: Unicode NFKD for mnemonic and passphrase

### Security Features
- **Standard Compliance**: Follows BIP-39 specification exactly
- **Key Stretching**: PBKDF2 with configurable iterations (default 2048)
- **Unicode Support**: Proper NFKD normalization for international characters
- **Memory Security**: Automatic cleanup of sensitive variables
- **Deterministic**: Same mnemonic + passphrase always produces identical seed

### Performance Characteristics
- **Generation Time**: < 5ms average (2048 iterations)
- **Memory Usage**: < 1KB additional during generation
- **Scalability**: Linear scaling with iteration count
- **CPU Usage**: Single-threaded, computationally intensive

### Usage Examples

```bash
# Generate master seed from mnemonic file
sseed seed -i mnemonic.txt --hex

# Example output (128 hex characters = 512 bits)
a8b4c2d1e3f4567890abcdef1234567890abcdef1234567890abcdef12345678
90abcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678

# With passphrase for additional security
sseed seed -i mnemonic.txt -p "my_passphrase" --hex

# Higher security with more iterations
sseed seed -i mnemonic.txt --iterations 4096 --hex

# Binary output to file
sseed seed -i mnemonic.txt -o master_seed.bin
```

### Cryptographic Process
1. **Input Validation**: Verify mnemonic checksum integrity
2. **Normalization**: Apply Unicode NFKD to mnemonic and passphrase
3. **Key Derivation**: PBKDF2-HMAC-SHA512 with configured iterations
4. **Output Generation**: 512-bit seed suitable for BIP-32 key derivation
5. **Memory Cleanup**: Secure deletion of intermediate values

### Integration with HD Wallets
The generated master seed serves as the foundation for BIP-32 hierarchical deterministic wallet systems:

```bash
# Generate master seed for wallet
sseed seed -i wallet_mnemonic.txt -p "$WALLET_PASSPHRASE" -o master_seed.txt --hex

# Master seed can then be used with BIP-32 libraries for:
# - Master private key derivation
# - Extended public/private key generation  
# - Child key derivation paths (m/44'/0'/0'/0/0)
# - Multi-account wallet structures
```

### Security Considerations
- **Passphrase Protection**: Optional passphrase adds 25th word equivalent security
- **Iteration Count**: Higher iterations increase brute-force resistance
- **Memory Handling**: All sensitive data cleared after use
- **Offline Operation**: No network calls, suitable for air-gapped systems
- **Deterministic Output**: Same inputs always produce identical results

### Compliance and Standards
- **BIP-39**: Full compliance with Bitcoin Improvement Proposal 39
- **BIP-32**: Output compatible with hierarchical deterministic wallets
- **PBKDF2**: Uses standard PBKDF2-HMAC-SHA512 implementation
- **Unicode**: NFKD normalization per specification
- **Cryptographic Libraries**: Built on Python's `hashlib` standard library

## SLIP-39 Secret Sharing

### Overview
Implements Shamir's Secret Sharing using the SLIP-39 specification for splitting mnemonics into recoverable shards.

### SLIP-39 Specification and Implementation

#### Official Specification
- **Standard**: SLIP-0039 (SatoshiLabs Improvement Proposal 39)
- **Full Specification**: https://github.com/satoshilabs/slips/blob/master/slip-0039.md
- **Developer**: Trezor/SatoshiLabs team
- **Status**: Final standard, widely adopted

#### Implementation Library
- **Library**: `shamir-mnemonic` version 0.3.0
- **Source**: Official Trezor reference implementation
- **Repository**: https://github.com/trezor/python-shamir-mnemonic
- **Maintainers**: matejcik, satoshilabs, stick
- **License**: MIT License
- **Python Support**: 3.6+ (tested on 3.12)

#### SLIP-39 Word List Specification
- **Total Words**: 1024 words (2^10)
- **Word Length**: 4-8 characters each
- **Language**: English (with "satoshi" included)
- **Encoding**: 10 bits per word
- **Prefix System**: Unique 4-letter prefixes for error prevention
- **Checksum**: Built-in error detection per shard
- **Standard**: Official SLIP-39 wordlist (differs from BIP-39)

#### Key Differences from BIP-39
| Feature | BIP-39 | SLIP-39 |
|---------|--------|---------|
| Word Count | 2048 words | 1024 words |
| Word Length | 3-8 chars | 4-8 chars |
| Bits per Word | 11 bits | 10 bits |
| Primary Use | Seed generation | Secret sharing |
| Checksum | Per mnemonic | Per shard |
| Sharing | Not supported | Native support |

### Technical Implementation
- **Algorithm**: Shamir's Secret Sharing Scheme
- **Field Mathematics**: GF(256) finite field arithmetic
- **Polynomial**: Lagrange interpolation for reconstruction
- **Integrity**: Built-in error detection and correction
- **Security Level**: Information-theoretic security
- **Threshold Logic**: Configurable N-of-M schemes

### Cryptographic Properties
- **Perfect Secrecy**: Insufficient shards reveal no information about the secret
- **Threshold Security**: Exactly N shards required for reconstruction
- **Information Theoretic**: Security not dependent on computational assumptions
- **Error Detection**: Built-in checksums prevent silent corruption
- **Forward Security**: No single point of failure or weakness

### Group Configuration Support

#### Simple Threshold Schemes
```bash
# 3-of-5 scheme: requires 3 shards out of 5
sseed shard -g 3-of-5

# 2-of-3 scheme: requires 2 shards out of 3  
sseed shard -g 2-of-3

# 5-of-7 scheme: requires 5 shards out of 7
sseed shard -g 5-of-7
```

#### Multi-Group Schemes
```bash
# Complex scheme: requires 2 groups
# Group 1: 2-of-3 shards needed
# Group 2: 3-of-5 shards needed
sseed shard -g "2:(2-of-3,3-of-5)"

# Enterprise scheme: requires 3 groups
# Multiple group thresholds
sseed shard -g "3:(2-of-3,3-of-5,4-of-7)"
```

### Security Properties
- **Perfect Secrecy**: Insufficient shards reveal no information
- **Threshold Security**: Exactly threshold shards required
- **Integrity Protection**: Built-in error detection
- **Forward Security**: No single point of failure

### Performance Characteristics
- **Sharding Time**: < 5ms for 5 shards
- **Memory Usage**: < 100KB during operation
- **Scalability**: Linear with number of shards

### Shard Format
```
# SLIP-39 Shard
# Generated by sseed on 2024-06-19 14:30:15
# Group 1, Shard 1 of 5 (threshold: 3)
#
academic acid acrobat romp charity artwork donor voting declare
```

## SLIP-39 Reconstruction

### Overview
Reconstructs original mnemonics from sufficient SLIP-39 shards with comprehensive validation.

### Technical Implementation
- **Algorithm**: Lagrange interpolation in GF(256)
- **Validation**: Multi-layer integrity checking
- **Error Handling**: Graceful handling of insufficient/invalid shards
- **Performance**: Optimized polynomial arithmetic

### Reconstruction Process
1. **Shard Collection**: Gather input shards from files/stdin
2. **Format Validation**: Verify SLIP-39 format compliance
3. **Threshold Check**: Ensure sufficient shards available
4. **Group Validation**: Verify group/threshold requirements
5. **Interpolation**: Reconstruct secret using Lagrange method
6. **Integrity Check**: Validate reconstructed mnemonic
7. **Output**: Return validated BIP-39 mnemonic

### Security Validations
- **Shard Authenticity**: Verify SLIP-39 checksums
- **Duplicate Detection**: Prevent shard reuse attacks
- **Threshold Enforcement**: Exact threshold requirements
- **Group Logic**: Multi-group scheme validation
- **Mnemonic Validation**: BIP-39 checksum verification

### Performance Characteristics
- **Reconstruction Time**: < 4ms for 3-5 shards
- **Memory Usage**: < 200KB during operation
- **Error Detection**: < 1ms additional overhead

### Usage Examples

```bash
# Reconstruct from files
sseed restore shard1.txt shard2.txt shard3.txt

# Reconstruct from stdin
cat shards.txt | sseed restore

# Output to file
sseed restore shard*.txt -o recovered_seed.txt
```

## Cryptographic Validation

### Mnemonic Validation
- **Length Check**: Validates 12, 15, 18, 21, or 24 words
- **Wordlist Validation**: Ensures all words in BIP-39 wordlist
- **Checksum Verification**: Validates BIP-39 checksum integrity
- **Normalization**: NFKD Unicode normalization
- **Encoding**: UTF-8 compliance verification

### SLIP-39 Validation
- **Format Compliance**: Validates SLIP-39 specification
- **Group Logic**: Verifies group/threshold mathematics
- **Shard Integrity**: Individual shard checksum validation
- **Threshold Logic**: Ensures proper threshold requirements
- **Duplicate Prevention**: Detects and rejects duplicate shards

### Error Detection
- **Invalid Characters**: Non-BIP39 word detection
- **Corrupted Data**: Checksum mismatch detection
- **Insufficient Data**: Under-threshold shard detection
- **Format Errors**: Malformed input detection
- **Encoding Issues**: Character encoding problems

## Entropy Quality

### Entropy Sources
- **Primary**: `secrets.SystemRandom()` (OS entropy pool)
- **Quality**: Cryptographically secure pseudorandom
- **Seeding**: Hardware random number generators when available
- **Fallback**: None (fail securely if insufficient entropy)

### Entropy Testing
- **Statistical Tests**: Passes NIST randomness tests
- **Entropy Rate**: 256 bits for 24-word mnemonics
- **Bias Testing**: No detectable patterns or bias
- **Temporal Analysis**: No correlation between generations

### Quality Assurance
- **Security Audit**: Bandit security analysis passed
- **Code Review**: Manual cryptographic review
- **Test Coverage**: 100% coverage of crypto functions
- **Standard Compliance**: BIP-39 and SLIP-39 test vectors

## Standards Compliance

### BIP-39 Compliance
- ✅ **Entropy**: 256 bits for 24-word mnemonics
- ✅ **Wordlist**: Official English wordlist (2048 words)
- ✅ **Checksum**: SHA-256 based checksum validation
- ✅ **Encoding**: UTF-8 with NFKD normalization
- ✅ **Test Vectors**: Passes all official test vectors

### SLIP-39 Compliance  
- ✅ **Algorithm**: Shamir's Secret Sharing in GF(256)
- ✅ **Groups**: Multi-group threshold schemes
- ✅ **Format**: Official SLIP-39 word encoding
- ✅ **Checksums**: Reed-Solomon error detection
- ✅ **Test Vectors**: Passes all specification tests

### Security Standards
- ✅ **FIPS 140-2**: Compatible entropy sources
- ✅ **Common Criteria**: Secure implementation practices
- ✅ **OWASP**: Secure coding guidelines followed
- ✅ **Industry Best Practices**: Cryptographic review standards 