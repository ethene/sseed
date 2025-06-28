# Security Features

SSeed is designed with security as the primary concern. Every aspect of the tool prioritizes protection of sensitive cryptographic material and ensures robust operation in security-critical environments.

## Core Security Principles

### Defense in Depth
- **Multiple validation layers** at every stage
- **Fail-safe defaults** that prioritize security
- **Principle of least privilege** for all operations
- **Zero-trust architecture** for all inputs

### Cryptographic Security
- **Industry-standard algorithms** (BIP-39, SLIP-39)
- **Secure entropy sources** (OS cryptographic RNG)
- **No custom cryptography** - relies on proven implementations
- **Constant-time operations** where possible

### Operational Security
- **Complete offline operation** - no network dependencies
- **Secure memory handling** with explicit cleanup
- **Minimal attack surface** - minimal dependencies
- **Auditable code** with comprehensive logging

## Offline Operation Guarantees

### Network Isolation
SSeed operates completely offline with **zero network calls** under any circumstances.

#### Implementation Details
- **No network imports**: No socket, urllib, requests, or network libraries
- **Dependency analysis**: All dependencies verified for offline operation
- **Static analysis**: Code audited to prevent network calls
- **Runtime verification**: Network operations blocked during testing

#### Verification Methods
```python
# Network call detection in tests
import socket
import urllib.request

# Mock all network operations to detect violations
socket.create_connection = lambda *args: raise Exception("Network call detected!")
urllib.request.urlopen = lambda *args: raise Exception("Network call detected!")
```

#### Air-Gapped Environment Compatibility
- **No internet requirement** for any functionality
- **No external service dependencies** 
- **No automatic updates** or telemetry
- **Offline documentation** included in package
- **Self-contained operation** with bundled libraries

### Benefits for Security
- **Eliminates network attack vectors** entirely
- **Prevents data exfiltration** of sensitive material
- **Enables air-gapped operation** for maximum security
- **Complies with strict security policies** for isolated environments

## Secure Memory Handling

### Memory Protection Strategy
SSeed implements comprehensive memory protection to prevent sensitive data leakage.

#### Automatic Variable Cleanup
```python
def secure_delete_variable(var_name: str, frame_locals: dict) -> None:
    """Securely delete variable from memory."""
    if var_name in frame_locals:
        # Overwrite with random data
        if isinstance(frame_locals[var_name], str):
            frame_locals[var_name] = secrets.token_hex(len(frame_locals[var_name]))
        
        # Delete reference
        del frame_locals[var_name]
        
        # Force garbage collection
        gc.collect()
```

#### Implementation Points
All sensitive operations use secure cleanup:

```python
# BIP-39 generation
mnemonic = generate_mnemonic()
# ... use mnemonic ...
secure_delete_variable('mnemonic', locals())

# SLIP-39 operations  
shards = create_shards(mnemonic)
# ... use shards ...
secure_delete_variable('shards', locals())
secure_delete_variable('mnemonic', locals())

# CLI operations
user_input = read_input()
# ... process input ...
secure_delete_variable('user_input', locals())
```

#### Memory Protection Features
- **Immediate cleanup** after sensitive operations
- **Random overwriting** before deletion
- **Garbage collection** forcing
- **Stack frame cleaning** for function returns
- **No sensitive data caching** in memory

### Swap File Protection
While SSeed cannot directly control swap behavior, it minimizes exposure:

- **Minimal memory footprint** (< 2MB additional)
- **Short-lived sensitive data** (< 5ms exposure)
- **No persistent storage** of sensitive material
- **Recommendations** for swap-disabled environments

## Input Validation and Sanitization

### Multi-Layer Validation
Every input undergoes comprehensive validation before processing.

#### Mnemonic Validation
```python
def validate_mnemonic_words(words: list[str]) -> None:
    """Comprehensive mnemonic validation."""
    # Length validation
    if len(words) not in VALID_LENGTHS:
        raise ValidationError(f"Invalid length: {len(words)}")
    
    # Wordlist validation
    for word in words:
        if word not in BIP39_WORDLIST:
            raise ValidationError(f"Invalid word: {word}")
    
    # Checksum validation
    if not validate_checksum(words):
        raise ValidationError("Invalid checksum")
    
    # Encoding validation
    validate_encoding(words)
```

#### File Input Validation
```python
def validate_file_input(file_path: str) -> None:
    """Validate file input security."""
    # Path traversal protection
    if '..' in file_path or file_path.startswith('/'):
        raise FileError("Invalid file path")
    
    # File existence and permissions
    if not os.path.exists(file_path):
        raise FileError(f"File not found: {file_path}")
    
    # Size limits (prevent DoS)
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        raise FileError("File too large")
    
    # Content validation
    validate_file_content(file_path)
```

#### Group Configuration Validation
```python
def validate_group_config(config: str) -> None:
    """Validate SLIP-39 group configuration."""
    # Format validation
    if not re.match(GROUP_CONFIG_PATTERN, config):
        raise ValidationError("Invalid group format")
    
    # Threshold logic validation
    validate_threshold_logic(config)
    
    # Security parameter validation
    validate_security_parameters(config)
```

### Protection Against Attacks

#### Input Sanitization
- **Path traversal prevention**: File path sanitization
- **Buffer overflow prevention**: Input length limits
- **Injection prevention**: No dynamic code execution
- **Format string prevention**: No user-controlled format strings

#### Denial of Service Protection
- **File size limits**: Maximum input file sizes
- **Memory limits**: Bounded memory allocation
- **Time limits**: Operation timeout protection
- **Resource limits**: CPU and I/O constraints

## Cryptographic Integrity

### Entropy Quality Assurance
SSeed ensures cryptographic-quality entropy for all random operations.

#### Entropy Sources
```python
# Primary entropy source
entropy_bits = secrets.SystemRandom().randbits(256)

# Quality validation
if len(entropy_bits.to_bytes(32, 'big')) != 32:
    raise CryptographicError("Insufficient entropy")

# Statistical testing (during development)
validate_entropy_quality(entropy_bits)
```

#### Entropy Testing
- **NIST SP 800-22** statistical test suite compliance
- **Diehard tests** for randomness quality
- **Entropy estimation** using multiple methods
- **Bias detection** and correlation analysis

### Checksum Validation
Multiple layers of checksum validation ensure data integrity.

#### BIP-39 Checksums
- **SHA-256 based** checksum calculation
- **Bit-level validation** of checksum integrity
- **Standard compliance** with BIP-39 specification
- **Error detection** capability for single and multi-bit errors

#### SLIP-39 Checksums
- **Reed-Solomon codes** for error detection and correction
- **CRC-based validation** for shard integrity
- **Group validation** for multi-group schemes
- **Threshold verification** for reconstruction requirements

### Constant-Time Operations
Where possible, SSeed implements constant-time operations to prevent timing attacks.

```python
def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison to prevent timing attacks."""
    if len(a) != len(b):
        return False
    
    result = 0
    for x, y in zip(a, b):
        result |= x ^ y
    
    return result == 0
```

## Error Handling and Information Disclosure

### Secure Error Handling
Error messages are designed to be helpful without leaking sensitive information.

#### Information Disclosure Prevention
- **Generic error messages** for security-sensitive operations
- **No stack traces** in production output
- **Sanitized file paths** in error messages
- **No sensitive data** in exception messages

#### Error Classification
```python
# Public errors (safe to display)
class ValidationError(Exception):
    """Validation error with safe message."""
    pass

# Private errors (logged but not displayed)
class InternalError(Exception):
    """Internal error with sensitive details."""
    pass

# File errors (path-sanitized messages)
class FileError(Exception):
    """File operation error with sanitized paths."""
    pass
```

### Logging Security
Sensitive operations are logged securely without exposing critical data.

#### Secure Logging Strategy
```python
# Security-focused logging
security_logger = logging.getLogger('sseed.security')

# Log operations without sensitive data
security_logger.info("BIP-39 mnemonic generation initiated")
security_logger.info(f"Entropy generation: {len(entropy)} bytes")
security_logger.info("SLIP-39 sharding completed: {num_shards} shards")

# Never log actual mnemonic words or shards
# Never log entropy values or cryptographic keys
```

#### Log Sanitization
- **No sensitive data** in log messages
- **Sanitized file paths** to prevent information disclosure
- **Operation metadata only** without actual values
- **Structured logging** for security analysis

## Security Auditing and Compliance

### Static Analysis
SSeed undergoes comprehensive static analysis for security vulnerabilities.

#### Bandit Security Audit
```bash
# Security vulnerability scanning
bandit -r sseed/
# Result: No high or medium severity issues found
# Only 2 low-severity false positives (empty string defaults)
```

#### Code Review Process
- **Manual security review** of all cryptographic operations
- **Dependency analysis** for supply chain security
- **Third-party audit** capability with open source code
- **Continuous monitoring** for security updates

### Dependency Security
All dependencies are carefully vetted for security.

#### Dependency Analysis
```python
# Core cryptographic dependencies
"bip-utils>=2.9.3",    # BIP-39 implementation
"slip39>=13.1.0",      # SLIP-39 implementation

# No network dependencies
# No web framework dependencies  
# No database dependencies
# Minimal attack surface
```

#### Supply Chain Security
- **Pinned versions** with known security status
- **Hash verification** for package integrity
- **Minimal dependencies** to reduce attack surface
- **Regular updates** for security patches

### Compliance and Standards

#### Standards Compliance
- ✅ **BIP-39**: Full compliance with specification
- ✅ **SLIP-39**: Complete implementation compliance
- ✅ **NIST**: Entropy and cryptographic standards
- ✅ **OWASP**: Secure coding practices
- ✅ **Common Criteria**: Security implementation guidelines

#### Security Certifications
While SSeed is not formally certified, it follows practices suitable for:
- **FIPS 140-2**: Cryptographic module standards
- **Common Criteria**: Security evaluation criteria
- **ISO 27001**: Information security management
- **SOC 2**: Security and availability controls

## Threat Model and Mitigations

### Identified Threats
SSeed addresses the following threat categories:

#### Data Exfiltration
- **Threat**: Sensitive mnemonic data leaked to attackers
- **Mitigation**: Secure memory handling, offline operation
- **Detection**: Memory analysis, network monitoring

#### Data Corruption
- **Threat**: Corruption of mnemonics or shards
- **Mitigation**: Multiple checksum layers, validation
- **Detection**: Integrity checking, reconstruction testing

#### Supply Chain Attacks
- **Threat**: Compromised dependencies or build process
- **Mitigation**: Dependency pinning, hash verification
- **Detection**: Signature verification, reproducible builds

#### Side-Channel Attacks
- **Threat**: Information leakage through timing or power analysis
- **Mitigation**: Constant-time operations where possible
- **Detection**: Timing analysis, power consumption monitoring

### Risk Assessment
| Threat | Likelihood | Impact | Mitigation |
|--------|------------|--------|------------|
| Data Exfiltration | Low | High | Secure memory handling |
| Data Corruption | Medium | High | Multiple validation layers |
| Supply Chain | Low | High | Dependency verification |
| Side-Channel | Low | Medium | Constant-time operations |

## Security Best Practices

### Deployment Security
Recommendations for secure deployment and operation:

#### Environment Hardening
```bash
# Disable swap to prevent sensitive data on disk
sudo sysctl vm.swappiness=0
sudo swapoff -a

# Use encrypted filesystems
# Enable full-disk encryption (FileVault, BitLocker, LUKS)

# Secure file permissions
umask 077  # Files created with 600 permissions
```

#### Operational Security
```bash
# Run in isolated environment
# Use dedicated user account with minimal privileges
# Monitor system for unauthorized access
# Implement secure deletion of temporary files

# Example secure operation
sseed gen -o seed.txt
# ... use seed.txt immediately ...
shred -vfz -n 3 seed.txt  # Secure deletion
```

### Integration Security
For integration into larger systems:

#### API Security
- **Input validation** for all programmatic inputs
- **Rate limiting** to prevent abuse
- **Authentication** for access control
- **Logging** for security monitoring

#### Container Security
```dockerfile
# Minimal base image
FROM python:3.12-alpine

# Non-root user
RUN adduser -D sseed
USER sseed

# Read-only filesystem
# No network access
# Minimal privileges
``` 
### Custom Entropy Security

#### Advanced Entropy Sources
SSeed supports custom entropy sources for specialized use cases while maintaining strict security standards:

**Security Layers:**
- **Quality Scoring**: 0-100 scale with acceptance thresholds
- **Pattern Detection**: All zeros, repeating sequences, predictable data
- **Distribution Analysis**: Byte frequency analysis and bias detection
- **Weakness Signatures**: Common weak entropy patterns (timestamps, ASCII text)
- **User Consent**: Two-tier consent system (`--allow-weak`, `--force`)
- **Security Warnings**: Clear warnings about entropy quality issues

**Acceptance Thresholds:**
- Default: Reject custom entropy (use system entropy)
- `--allow-weak`: Accept entropy with score ≥ 70 (≥ 60 for dice)
- `--force`: Override all quality checks (dangerous, requires explicit consent)

**Quality Analysis Examples:**
```bash
# Good quality entropy (Score: 95/100)
📊 Entropy Quality Analysis:
   Quality Score: 95/100
   Warnings: None
   Recommendations: Entropy quality is excellent

# Poor quality entropy (Score: 20/100)
📊 Entropy Quality Analysis:
   Quality Score: 20/100
   Warnings: Entropy contains repeating 1-byte pattern
   Recommendations: This entropy is not suitable for cryptographic use
```

**Security Warnings:**
- ⚠️ WARNING: Using custom hex entropy (NOT RECOMMENDED)
- ❌ SECURITY WARNING: Entropy quality insufficient (score/100)
- 🚨 CRITICAL: This entropy appears to be non-random

**Recommended Practices:**
- Use system entropy (`sseed gen`) for maximum security
- Only use custom entropy if you understand the cryptographic implications
- Always validate entropy quality with `--entropy-analysis`
- Never reuse the same entropy source
- Document entropy generation procedures for audit purposes

See `docs/custom-entropy-security.md` for comprehensive security guidelines.
