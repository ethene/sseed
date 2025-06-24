# Command Line Interface

SSeed provides a comprehensive command-line interface designed for ease of use, security, and integration into automated workflows. The CLI follows Unix conventions and supports both interactive and batch operations.

## Interface Design Philosophy

### Principles
- **Security First**: Secure defaults and fail-safe operations
- **Unix Philosophy**: Do one thing well, compose with other tools
- **User Friendly**: Clear help, intuitive commands, helpful error messages
- **Scriptable**: Suitable for automation and batch processing
- **Consistent**: Predictable behavior across all commands

### Command Structure
```
sseed [global-options] <command> [command-options] [arguments]
```

## Global Options

### Help and Information
```bash
# Show main help with quick examples
sseed --help
sseed -h

# Show version information  
sseed --version

# Show comprehensive usage examples and best practices
sseed --examples
```

### Logging Control
```bash
# Enable verbose output
sseed --verbose <command>
sseed -v <command>

# Set specific log level
sseed --log-level DEBUG <command>
sseed --log-level INFO <command>     # Default
sseed --log-level WARNING <command>
sseed --log-level ERROR <command>
sseed --log-level CRITICAL <command>
```

### Usage Examples
```bash
# Show version
sseed --version
# Output: sseed 1.0.1

# Get comprehensive examples
sseed --examples
# Shows 30+ practical examples with real command syntax

# Generate with debug logging
sseed --log-level DEBUG gen

# Shard with verbose output
sseed -v shard -i seed.txt -g 3-of-5
```

### Comprehensive Examples System
The `--examples` flag provides an extensive reference of practical usage patterns:

#### Example Categories
- **Basic Operations**: Standard generation, sharding, and restoration workflows
- **Advanced Workflows**: Complex multi-group configurations and automation
- **File Management**: Timestamp handling, directory organization, pattern matching
- **Security Best Practices**: Verification procedures, secure storage, testing protocols
- **Integration Examples**: Shell scripting, batch processing, enterprise deployment

#### Sample Output from `sseed --examples`
```bash
SSEED USAGE EXAMPLES

Basic Operations:
  # Generate a new mnemonic
  sseed gen
  
  # Generate and save to file
  sseed gen -o my-wallet-backup.txt

  # Split mnemonic into 3-of-5 shards
  sseed shard -i my-wallet-backup.txt -g 3-of-5
  
  # Restore from any 3 shards
  sseed restore shard_01.txt shard_02.txt shard_03.txt

Advanced Workflows:
  # Generate and immediately shard (one-liner)
  sseed gen | sseed shard -g 2-of-3
  
  # Multi-group enterprise setup
  sseed shard -g "2:(2-of-3,3-of-5)" -i seed.txt --separate -o enterprise-shards

Security Best Practices:
  # Always verify generated mnemonics
  sseed gen -o backup.txt && cat backup.txt
  
  # Store shards in separate secure locations
  sseed shard -i seed.txt -g 3-of-5 --separate -o /secure/location1/
```

#### Benefits of Examples System
- **Learning Tool**: Helps users understand advanced features and patterns
- **Reference**: Quick lookup for complex command combinations
- **Best Practices**: Incorporates security and operational recommendations
- **Real-World**: Practical examples for common deployment scenarios

## Version Command (`version`)

### Purpose
Display comprehensive version and system information for debugging, support, and automation.

### Syntax
```bash
sseed version [options]
```

### Options
- `--json` - Output in JSON format for automation
- `-h, --help` - Show command help

### Usage Examples

#### Human-Readable Output
```bash
# Show detailed version information
sseed version

# Example output
🔐 SSeed v1.4.0
========================================

📋 Core Information:
   Version: 1.4.0
   Python:  3.12.2 (CPython)

🖥️  System Information:
   OS:           Darwin 23.6.0
   Architecture: arm64 (64bit)

📦 Dependencies:
   ✅ bip-utils: 2.9.3
   ✅ slip39: 13.1.0

🔗 Links:
   Repository: https://github.com/ethene/sseed
   PyPI:       https://pypi.org/project/sseed/
   Issues:     https://github.com/ethene/sseed/issues
```

#### JSON Output for Automation
```bash
# Machine-readable format
sseed version --json

# Example output
{
  "sseed": "1.4.0",
  "python": "3.12.2",
  "platform": {
    "system": "Darwin",
    "release": "23.6.0",
    "machine": "arm64",
    "architecture": "64bit"
  },
  "dependencies": {
    "bip-utils": "2.9.3",
    "slip39": "13.1.0"
  },
  "build": {
    "python_implementation": "CPython",
    "python_compiler": "Clang 16.0.6"
  }
}
```

#### Integration Examples
```bash
# Extract version for scripts
VERSION=$(sseed version --json | jq -r '.sseed')
echo "Running SSeed version: $VERSION"

# Check dependency availability
sseed version --json | jq '.dependencies["bip-utils"]'

# System compatibility check
ARCH=$(sseed version --json | jq -r '.platform.machine')
if [ "$ARCH" = "arm64" ]; then
    echo "Running on Apple Silicon"
fi

# CI/CD verification
sseed version --json | jq -e '.sseed == "1.4.0"' && echo "Version verified"
```

### Information Provided

#### Core Information
- **SSeed Version**: Current application version (semantic versioning)
- **Python Version**: Runtime Python version and implementation
- **Platform Details**: Operating system, release, architecture

#### Dependencies
- **bip-utils**: BIP-39 mnemonic operations library version
- **slip39**: SLIP-39 secret sharing library version
- **Status Indicators**: ✅ Available / ❌ Missing

#### Build Information
- **Python Implementation**: CPython, PyPy, etc.
- **Compiler**: Build toolchain information
- **Architecture**: Platform-specific build details

#### Helpful Links
- **Repository**: Source code and documentation
- **PyPI**: Package installation and release history
- **Issues**: Bug reports and feature requests

### Use Cases

#### Development and Debugging
- **Environment Verification**: Confirm correct versions and dependencies
- **Bug Reports**: Provide comprehensive system information
- **Compatibility Testing**: Verify platform and dependency compatibility

#### Automation and CI/CD
- **Version Verification**: Ensure correct version deployment
- **Dependency Auditing**: Monitor library versions
- **Environment Documentation**: Record deployment configurations

#### Support and Troubleshooting
- **System Information**: Quick environment assessment
- **Dependency Status**: Identify missing or outdated libraries
- **Platform Details**: Architecture and OS-specific debugging

## Generation Command (`gen`)

### Purpose
Generate cryptographically secure 24-word BIP-39 mnemonics using OS entropy.

### Syntax
```bash
sseed gen [options]
```

### Options
- `-o, --output FILE` - Output file (default: stdout)
- `--show-entropy` - Display the underlying entropy (hex) alongside the mnemonic
- `-h, --help` - Show command help

### Usage Examples

#### Basic Generation
```bash
# Generate to stdout
sseed gen

# Example output
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual

# Generate with entropy display
sseed gen --show-entropy

# Example output with entropy
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
# Entropy: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456 (32 bytes)
```

#### File Output
```bash
# Generate to file
sseed gen -o my_seed.txt

# Generate with timestamp in filename
sseed gen -o "seed_$(date +%Y%m%d_%H%M%S).txt"

# Generate to secure location
sseed gen -o /secure/vault/backup_seed.txt

# Generate to file with entropy display
sseed gen --show-entropy -o my_seed_with_entropy.txt

# File will contain both mnemonic and entropy comment
```

#### Piping and Redirection
```bash
# Pipe to other commands
sseed gen | wc -w  # Count words (should be 24)

# Redirect with shell
sseed gen > secure_seed.txt

# Append to existing file
sseed gen >> multiple_seeds.txt
```

### Security Features
- **Entropy Quality**: Uses `secrets.SystemRandom()` for cryptographic entropy
- **No Caching**: Each generation uses fresh entropy
- **Memory Cleanup**: Secure variable deletion after generation
- **Offline Operation**: No network calls ever made

### Performance
- **Speed**: < 1ms average generation time
- **Memory**: < 1KB additional memory usage
- **CPU**: Minimal single-core usage

## Master Seed Command (`seed`)

### Purpose
Generate 512-bit master seeds from BIP-39 mnemonics using PBKDF2-HMAC-SHA512 for hierarchical deterministic (HD) wallet systems. This command bridges BIP-39 mnemonics to BIP-32 key derivation.

### Syntax
```bash
sseed seed [options]
```

### Options
- `-i, --input FILE` - Input mnemonic file (default: stdin)
- `-p, --passphrase TEXT` - Optional passphrase for additional security (default: "")
- `-o, --output FILE` - Output file for master seed (default: stdout)
- `--hex` - Output seed in hexadecimal format (default: true)
- `--iterations COUNT` - PBKDF2 iteration count (default: 2048)
- `-h, --help` - Show command help

### Technical Details
- **Algorithm**: PBKDF2-HMAC-SHA512 (BIP-39 standard)
- **Output Size**: 512 bits (64 bytes) = 128 hex characters
- **Salt Format**: "mnemonic" + passphrase (UTF-8 encoded)
- **Normalization**: Unicode NFKD for mnemonic and passphrase
- **Compliance**: Full BIP-39 specification adherence

### Usage Examples

#### Basic Master Seed Generation
```bash
# Generate master seed from file
sseed seed -i mnemonic.txt --hex

# Example output (128 hex characters)
a8b4c2d1e3f4567890abcdef1234567890abcdef1234567890abcdef12345678
90abcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678

# Generate from stdin
cat mnemonic.txt | sseed seed --hex

# Generate and pipe to next operation
sseed gen | sseed seed --hex
```

#### Passphrase Protection (25th Word)
```bash
# Generate with passphrase for additional security
sseed seed -i mnemonic.txt -p "my_secure_passphrase" --hex

# Interactive passphrase (not echoed to terminal)
sseed seed -i mnemonic.txt -p "$(read -s -p 'Passphrase: '; echo $REPLY)" --hex

# Environment variable passphrase
sseed seed -i mnemonic.txt -p "$WALLET_PASSPHRASE" --hex
```

#### Security Hardening
```bash
# Higher iteration count for increased security
sseed seed -i mnemonic.txt --iterations 4096 --hex

# Maximum security with passphrase and high iterations
sseed seed -i mnemonic.txt -p "$SECURE_PASSPHRASE" --iterations 8192 --hex

# Enterprise-grade security
sseed seed -i mnemonic.txt -p "$ENTERPRISE_PASSPHRASE" --iterations 16384 --hex
```

#### File Output and Integration
```bash
# Save master seed to file
sseed seed -i mnemonic.txt -o master_seed.txt --hex

# Generate master seed with timestamp
sseed seed -i mnemonic.txt -o "master_seed_$(date +%Y%m%d_%H%M%S).txt" --hex

# Secure file permissions
sseed seed -i mnemonic.txt -o master_seed.txt --hex && chmod 600 master_seed.txt
```

#### HD Wallet Integration Workflows
```bash
# Complete wallet setup workflow
sseed gen -o wallet_mnemonic.txt                                    # Generate mnemonic
sseed seed -i wallet_mnemonic.txt -p "$PASSPHRASE" -o master_seed.txt --hex  # Generate master seed
sseed shard -i wallet_mnemonic.txt -g 3-of-5 --separate -o backup/   # Create backup shards

# Verification workflow
ORIGINAL_SEED=$(sseed seed -i mnemonic.txt --hex)
RESTORED_MNEMONIC=$(sseed restore shard*.txt)
RESTORED_SEED=$(echo "$RESTORED_MNEMONIC" | sseed seed --hex)
[ "$ORIGINAL_SEED" = "$RESTORED_SEED" ] && echo "Backup verified" || echo "Backup failed"

# Multi-account master seed generation
for account in personal business trading; do
    sseed seed -i "${account}_mnemonic.txt" -p "${account}_passphrase" \
        -o "${account}_master_seed.txt" --hex
done
```

### Security Features
- **Standard Compliance**: Follows BIP-39 specification exactly
- **Key Stretching**: PBKDF2 with configurable iterations (default 2048)
- **Unicode Support**: Proper NFKD normalization for international characters
- **Memory Security**: Automatic cleanup of sensitive variables
- **Deterministic**: Same mnemonic + passphrase always produces identical seed
- **Offline Operation**: No network calls, suitable for air-gapped systems

### HD Wallet Compatibility
The generated master seed serves as the foundation for BIP-32 hierarchical deterministic wallet systems:

- **Master Private Key**: Derived from the 512-bit master seed
- **Extended Keys**: Used to generate extended public/private key pairs
- **Derivation Paths**: Supports standard paths like m/44'/0'/0'/0/0
- **Multi-Account**: Enables multiple wallet accounts from single seed
- **Cross-Platform**: Compatible with all BIP-32 wallet implementations

### Performance
- **Speed**: < 5ms average (2048 iterations), scales linearly with iteration count
- **Memory**: < 1KB additional memory usage during generation
- **CPU**: Single-threaded, computationally intensive (by design for security)

### Integration Examples
```bash
# Integration with hardware security modules
sseed seed -i mnemonic.txt --hex | hsm_import_master_seed

# Integration with wallet software
MASTER_SEED=$(sseed seed -i wallet_mnemonic.txt -p "$PASSPHRASE" --hex)
wallet_software --import-master-seed "$MASTER_SEED"

# Backup verification script
verify_backup() {
    local mnemonic_file="$1"
    local shard_pattern="$2"
    
    original=$(sseed seed -i "$mnemonic_file" --hex)
    restored=$(sseed restore $shard_pattern | sseed seed --hex)
    
    if [ "$original" = "$restored" ]; then
        echo "✅ Backup verification successful"
        return 0
    else
        echo "❌ Backup verification failed"
        return 1
    fi
}
```

## Sharding Command (`shard`)

### Purpose
Split BIP-39 mnemonics into SLIP-39 shards using configurable threshold schemes.

### SLIP-39 Implementation Details
- **Standard**: SLIP-0039 (SatoshiLabs Improvement Proposal 39)
- **Library**: `shamir-mnemonic` v0.3.0 (Official Trezor reference implementation)
- **Word List**: 1024-word SLIP-39 wordlist (differs from BIP-39's 2048 words)
- **Encoding**: 10 bits per word with unique 4-letter prefixes
- **Algorithm**: Shamir's Secret Sharing in GF(256) finite field
- **Security**: Information-theoretic security with perfect secrecy
- **Specification**: https://github.com/satoshilabs/slips/blob/master/slip-0039.md

#### Compatibility with Official Trezor CLI

SSeed is fully interoperable with the official Trezor `shamir` CLI tool from [python-shamir-mnemonic](https://github.com/trezor/python-shamir-mnemonic). Both tools share the same cryptographic foundation:

- **Shared Library**: `shamir-mnemonic==0.3.0`
- **Perfect Interoperability**: SLIP-39 shards are interchangeable between tools
- **Cross-Tool Recovery**: Create with one tool, recover with the other
- **Standard Compliance**: Both follow SLIP-0039 specification exactly

**Installation:**
```bash
pip install shamir-mnemonic[cli]  # Install official Trezor CLI
```

**Cross-Tool Examples:**
```bash
# Create with sseed, recover with official Trezor CLI
sseed shard -i mnemonic.txt -g 2-of-3 --separate -o shards
shamir recover  # Enter sseed-generated shards

# Create with Trezor CLI, recover with sseed
shamir create 2of3  # Save shards to files
sseed restore shard1.txt shard2.txt
```

### Syntax
```bash
sseed shard [options]
```

### Options
- `-i, --input FILE` - Input mnemonic file (default: stdin)
- `-g, --group CONFIG` - Group configuration (default: 3-of-5)
- `-o, --output FILE` - Output file for shards (default: stdout)
- `--separate` - Write each shard to separate files
- `-h, --help` - Show command help

### Group Configuration Formats

#### Simple Threshold Schemes
```bash
# Format: threshold-of-total
sseed shard -g 2-of-3    # Need 2 out of 3 shards
sseed shard -g 3-of-5    # Need 3 out of 5 shards
sseed shard -g 5-of-7    # Need 5 out of 7 shards
sseed shard -g 10-of-15  # Need 10 out of 15 shards
```

#### Multi-Group Schemes
```bash
# Format: groups-needed:(group1-config,group2-config,...)
sseed shard -g "2:(2-of-3,3-of-5)"        # Need 2 groups
sseed shard -g "3:(2-of-3,3-of-5,4-of-7)" # Need 3 groups
sseed shard -g "1:(5-of-7,3-of-5)"        # Need 1 group (either)
```

### Usage Examples

#### Basic Sharding
```bash
# Shard from file with default 3-of-5
sseed shard -i seed.txt

# Shard from stdin
cat seed.txt | sseed shard

# Custom threshold
sseed shard -i seed.txt -g 2-of-3
```

#### Output Options
```bash
# Output to file
sseed shard -i seed.txt -g 3-of-5 -o shards.txt

# Separate files for each shard
sseed shard -i seed.txt -g 3-of-5 --separate -o shards
# Creates: shards_01.txt, shards_02.txt, shards_03.txt, shards_04.txt, shards_05.txt
```

#### Complex Workflows
```bash
# Generate and immediately shard
sseed gen | sseed shard -g 3-of-5 -o backup_shards.txt

# Shard with timestamp
sseed shard -i seed.txt -g 3-of-5 -o "shards_$(date +%Y%m%d).txt"

# Multi-group enterprise backup
sseed shard -i seed.txt -g "2:(3-of-5,2-of-3)" --separate -o enterprise_backup
```

### Security Features
- **Perfect Secrecy**: Insufficient shards reveal no information
- **Integrity Protection**: Built-in SLIP-39 checksums
- **Threshold Enforcement**: Exact threshold requirements
- **Memory Cleanup**: Secure variable deletion

### Performance
- **Speed**: < 5ms for typical 5-shard generation
- **Memory**: < 100KB additional during operation
- **Scalability**: Linear with number of shards

## Restoration Command (`restore`)

### Purpose
Reconstruct original BIP-39 mnemonics from sufficient SLIP-39 shards.

### Syntax
```bash
sseed restore [options] <shard-files...>
```

### Arguments
- `shard-files` - One or more shard files to restore from

### Options
- `-o, --output FILE` - Output file for reconstructed mnemonic (default: stdout)
- `--show-entropy` - Display the underlying entropy (hex) alongside the mnemonic
- `-h, --help` - Show command help

### Usage Examples

#### Basic Restoration
```bash
# Restore from multiple files
sseed restore shard1.txt shard2.txt shard3.txt

# Restore from all shards in directory
sseed restore shards_*.txt

# Restore from stdin (no file arguments)
cat shards.txt | sseed restore

# Restore with entropy display
sseed restore --show-entropy shard1.txt shard2.txt shard3.txt

# Example output with entropy
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
# Entropy: a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456 (32 bytes)
```

#### Output Options
```bash
# Restore to file
sseed restore shard1.txt shard2.txt shard3.txt -o recovered.txt

# Restore and verify
sseed restore shard*.txt | sseed shard -g 3-of-5  # Round-trip test

# Restore to file with entropy display
sseed restore --show-entropy shard1.txt shard2.txt shard3.txt -o recovered_with_entropy.txt

# Entropy verification workflow
ORIGINAL_ENTROPY=$(sseed gen --show-entropy | grep "# Entropy:" | cut -d' ' -f3)
RESTORED_ENTROPY=$(sseed restore --show-entropy shard*.txt | grep "# Entropy:" | cut -d' ' -f3)
[ "$ORIGINAL_ENTROPY" = "$RESTORED_ENTROPY" ] && echo "Entropy verified" || echo "Entropy mismatch"
```

#### Advanced Workflows
```bash
# Restore from separate shard files
sseed restore enterprise_backup_*.txt -o master_seed.txt

# Restore and immediately generate new shards
sseed restore old_shard*.txt | sseed shard -g 5-of-7 -o new_shards.txt

# Conditional restoration based on available shards
if [ $(ls shard*.txt | wc -l) -ge 3 ]; then
    sseed restore shard*.txt -o recovered_seed.txt
fi
```

### Security Features
- **Threshold Validation**: Ensures sufficient shards available
- **Integrity Checking**: Validates all shard checksums
- **Duplicate Detection**: Prevents shard reuse attacks
- **Memory Cleanup**: Secure variable deletion

### Performance
- **Speed**: < 4ms for typical 3-5 shard reconstruction
- **Memory**: < 200KB additional during operation
- **Error Detection**: < 1ms additional validation overhead

## File I/O Capabilities

### Input Sources
```bash
# File input
sseed shard -i mnemonic.txt

# Standard input
cat mnemonic.txt | sseed shard
echo "word1 word2 ... word24" | sseed shard

# Here document
sseed shard << EOF
abandon ability able about above absent absorb abstract
absurd abuse access accident account accuse achieve acid
acoustic acquire across act action actor actress actual
EOF
```

### Output Destinations
```bash
# Standard output (default)
sseed gen

# File output
sseed gen -o seed.txt

# Append to file
sseed gen >> backup_seeds.txt

# Pipe to other commands
sseed gen | gpg --encrypt > encrypted_seed.gpg
```

### File Format Support
- **UTF-8 Encoding**: Full Unicode support
- **Comment Lines**: Lines starting with `#` are ignored
- **Whitespace Handling**: Flexible whitespace and line breaks
- **Cross-Platform**: Works on Windows, macOS, Linux

## Error Handling and Exit Codes

### Comprehensive Exit Code System
SSeed provides granular exit codes for precise error handling in automation and scripting:

- `0` - **Success** - Operation completed successfully
- `1` - **Usage/Argument Error** - Invalid command syntax or missing arguments
- `2` - **Cryptographic Error** - Entropy, validation, or reconstruction failures
- `3` - **File I/O Error** - File system access, permission, or storage issues
- `4` - **Validation Error** - Checksum failures, format errors, or data integrity issues
- `130` - **Interrupted by User** - Operation cancelled with Ctrl+C (SIGINT)

### Error Categories and Examples

#### Usage Errors (Exit Code 1)
```bash
# Invalid command
sseed invalid_command
# Output: error: argument command: invalid choice: 'invalid_command'
# Exit code: 1

# Missing required arguments
sseed restore
# Output: error: the following arguments are required: shards
# Exit code: 1

# Invalid group configuration
sseed shard -g "5-of-3"
# Output: Invalid group configuration: threshold cannot exceed total
# Exit code: 1
```

#### Cryptographic Errors (Exit Code 2)
```bash
# Entropy generation failure
sseed gen  # When system entropy is exhausted
# Output: Cryptographic error: Failed to generate secure entropy
# Exit code: 2

# Invalid mnemonic checksum
echo "invalid mnemonic words here that dont have valid checksum" | sseed shard
# Output: Cryptographic error: Mnemonic checksum validation failed
# Exit code: 2

# Insufficient shards for reconstruction
sseed restore shard1.txt shard2.txt  # When 3 required
# Output: Cryptographic error: Insufficient shards for reconstruction
# Exit code: 2
```

#### File I/O Errors (Exit Code 3)
```bash
# File not found
sseed shard -i nonexistent.txt
# Output: File error: Failed to read mnemonic from file 'nonexistent.txt'
# Exit code: 3

# Permission denied
sseed gen -o /root/restricted.txt
# Output: File error: Permission denied: '/root/restricted.txt'
# Exit code: 3

# Disk full
sseed gen -o /full-disk/file.txt
# Output: File error: No space left on device
# Exit code: 3
```

#### Validation Errors (Exit Code 4)
```bash
# Invalid mnemonic format
echo "not enough words" | sseed shard
# Output: Validation error: Invalid mnemonic length: 3. Must be 24 words
# Exit code: 4

# Duplicate shards
sseed restore shard1.txt shard1.txt shard2.txt
# Output: Validation error: Duplicate shard detected
# Exit code: 4

# Invalid file format
echo "corrupted data" > bad.txt && sseed shard -i bad.txt
# Output: Validation error: Invalid mnemonic format
# Exit code: 4
```

#### User Interruption (Exit Code 130)
```bash
# User presses Ctrl+C during operation
sseed gen -o large_file.txt
^C
# Output: Operation cancelled by user
# Exit code: 130
```

### Advanced Error Handling and Recovery
```bash
# Check if operation succeeded
if sseed gen -o seed.txt; then
    echo "Seed generated successfully"
else
    echo "Failed to generate seed (exit code: $?)"
fi

# Handle specific error types
sseed shard -i input.txt -g 3-of-5 -o output.txt
case $? in
    0) echo "Sharding successful" ;;
    1) echo "Usage error - check command syntax" ;;
    2) echo "Cryptographic error - check input validity" ;;
    3) echo "File I/O error - check permissions and disk space" ;;
    4) echo "Validation error - check data integrity" ;;
    130) echo "Operation cancelled by user" ;;
    *) echo "Unexpected error" ;;
esac

# Conditional execution with error awareness
sseed restore shard*.txt && echo "Recovery successful" || echo "Recovery failed (exit code: $?)"

# Robust backup script with error handling
backup_seed() {
    local seed_file="$1"
    local backup_dir="$2"
    
    # Generate with error checking
    if ! sseed gen -o "$seed_file"; then
        echo "Failed to generate seed" >&2
        return 1
    fi
    
    # Shard with error checking  
    if ! sseed shard -i "$seed_file" -g 3-of-5 --separate -o "$backup_dir/shard"; then
        echo "Failed to create shards" >&2
        return 1
    fi
    
    # Verify reconstruction
    if ! sseed restore "$backup_dir"/shard_*.txt >/dev/null; then
        echo "Failed to verify shards" >&2
        return 1
    fi
    
    echo "Backup completed successfully"
    return 0
}
```

## Integration Features

### Shell Integration
```bash
# Add to PATH after pip install
which sseed  # /usr/local/bin/sseed

# Shell completion (if available)
complete -W "gen shard restore" sseed
```

### Scripting Support
```bash
#!/bin/bash
# Backup script example

BACKUP_DIR="/secure/backup/$(date +%Y%m%d)"
mkdir -p "$BACKUP_DIR"

# Generate seed
sseed gen -o "$BACKUP_DIR/master_seed.txt"

# Create 3-of-5 shards  
sseed shard -i "$BACKUP_DIR/master_seed.txt" -g 3-of-5 \
    --separate -o "$BACKUP_DIR/shard"

# Verify reconstruction
sseed restore "$BACKUP_DIR"/shard_*.txt -o "$BACKUP_DIR/verify.txt"

# Compare original and reconstructed
if cmp -s "$BACKUP_DIR/master_seed.txt" "$BACKUP_DIR/verify.txt"; then
    echo "Backup verification successful"
    rm "$BACKUP_DIR/verify.txt"  # Clean up verification file
else
    echo "Backup verification failed!"
    exit 1
fi
```

### Module Usage
```bash
# Run as Python module
python -m sseed gen
python -m sseed shard -i seed.txt -g 3-of-5
python -m sseed restore shard*.txt
```

## Advanced Features

### Logging and Debugging
```bash
# Debug mode with full logging
sseed --log-level DEBUG gen 2> debug.log

# Timestamp logging for audit trails
sseed -v shard -i seed.txt 2>&1 | ts >> audit.log

# Performance monitoring
time sseed gen  # Measure execution time
```

### Security Considerations
```bash
# Secure file permissions
umask 077  # Ensure files are created with 600 permissions
sseed gen -o seed.txt

# Memory-mapped files (avoid swap)
# Use encrypted filesystems or disable swap for security

# Secure deletion
sseed gen -o seed.txt
# ... use seed.txt ...
shred -vfz -n 3 seed.txt  # Secure deletion
```

### Cross-Platform Compatibility
- **Windows**: Full support via PowerShell or Command Prompt
- **macOS**: Native support via Terminal
- **Linux**: Full support via bash/zsh/fish shells
- **WSL**: Windows Subsystem for Linux compatible

### Performance Optimization
```bash
# Batch operations
for i in {1..10}; do
    sseed gen -o "seed_$i.txt"
done

# Parallel processing
seq 1 10 | xargs -P 4 -I {} sseed gen -o "seed_{}.txt"
```

## Seed Command (`seed`)

### Purpose
Generate 512-bit master seeds from BIP-39 mnemonics using PBKDF2-HMAC-SHA512 as specified in BIP-39. Master seeds can be used for cryptographic key derivation according to BIP-32 hierarchical deterministic (HD) wallet specification.

### Syntax
```bash
sseed seed [options]
```

### Options
- `-i, --input FILE` - Input file containing mnemonic (default: stdin)
- `-p, --passphrase PASSPHRASE` - Optional passphrase for additional security (default: none)
- `-o, --output FILE` - Output file for master seed (default: stdout)
- `--hex` - Output seed as hexadecimal string (default: binary)
- `--iterations COUNT` - PBKDF2 iteration count (default: 2048)
- `-h, --help` - Show command help

### Usage Examples

#### Basic Master Seed Generation
```bash
# Generate from file to stdout (hex format)
sseed seed -i mnemonic.txt --hex

# Example output (128 hex characters = 512 bits)
a8b4c2d1e3f4567890abcdef1234567890abcdef1234567890abcdef12345678
90abcdef1234567890abcdef1234567890abcdef1234567890abcdef12345678
```

#### With Passphrase
```bash
# Generate with passphrase protection
sseed seed -i mnemonic.txt -p "my_secure_passphrase" --hex

# Interactive passphrase entry
sseed seed -i mnemonic.txt -p "" --hex
# Prompts for passphrase securely
```

#### File Input/Output
```bash
# Read from file, write to file
sseed seed -i wallet_mnemonic.txt -o master_seed.txt

# Read from stdin, write to file
echo "abandon ability able about..." | sseed seed -o seed.txt --hex

# Read from file, output to stdout
sseed seed -i mnemonic.txt --hex > seed_backup.txt
```

#### Custom Iterations
```bash
# Higher security with more iterations
sseed seed -i mnemonic.txt --iterations 4096 --hex

# Enterprise-grade security
sseed seed -i mnemonic.txt --iterations 10000 --hex
```

### Security Features
- **BIP-39 Compliance**: Follows Bitcoin Improvement Proposal 39 specification exactly
- **PBKDF2-HMAC-SHA512**: Industry-standard key derivation function
- **Unicode Normalization**: Proper NFKD normalization for international characters
- **Memory Security**: Automatic cleanup of sensitive variables
- **Input Validation**: Comprehensive mnemonic checksum verification

### Performance
- **Speed**: < 5ms average generation time (2048 iterations)
- **Memory Usage**: < 1KB additional during generation
- **Scalability**: Linear scaling with iteration count

### Integration Examples

#### Wallet Generation Workflow
```bash
#!/bin/bash
# Complete wallet setup workflow

# Generate mnemonic
sseed gen -o wallet_mnemonic.txt

# Generate master seed
sseed seed -i wallet_mnemonic.txt -p "wallet_passphrase" -o master_seed.txt --hex

# Create backup shards
sseed shard -i wallet_mnemonic.txt -g 3-of-5 --separate -o backup_shards

# Verify master seed can be regenerated
sseed seed -i wallet_mnemonic.txt -p "wallet_passphrase" --hex | \
    cmp - master_seed.txt && echo "Master seed verified"
```

#### Automated Key Derivation
```bash
# Generate master seed for key derivation
MASTER_SEED=$(sseed seed -i mnemonic.txt -p "$PASSPHRASE" --hex)

# Use in other cryptographic operations
echo "Master seed: $MASTER_SEED"
# ... derive child keys using BIP-32 ...
```

#### Batch Processing
```bash
# Process multiple mnemonics
for mnemonic_file in mnemonics/*.txt; do
    seed_file="seeds/$(basename "$mnemonic_file" .txt)_seed.txt"
    sseed seed -i "$mnemonic_file" --hex -o "$seed_file"
done
```

### Error Handling
- **Invalid Mnemonic**: Clear error message with validation details
- **File I/O Errors**: Descriptive error messages with file paths
- **Memory Errors**: Graceful handling with cleanup
- **Interruption**: Secure cleanup on Ctrl+C

### Exit Codes
- `0` - Success
- `1` - Usage/argument error
- `2` - Cryptographic error (invalid mnemonic, PBKDF2 failure)
- `3` - File I/O error
- `4` - Validation error (checksum failure)
- `130` - Interrupted by user (Ctrl+C)

### Technical Specifications
- **Output Size**: 512 bits (64 bytes)
- **Algorithm**: PBKDF2-HMAC-SHA512
- **Default Iterations**: 2048 (BIP-39 standard)
- **Salt Format**: "mnemonic" + passphrase (UTF-8 encoded)
- **Normalization**: Unicode NFKD for mnemonic and passphrase

## Error Handling and Exit Codes

### Comprehensive Exit Code System
SSeed provides granular exit codes for precise error handling in automation and scripting:

- `0` - **Success** - Operation completed successfully
- `1` - **Usage/Argument Error** - Invalid command syntax or missing arguments
- `2` - **Cryptographic Error** - Entropy, validation, or reconstruction failures
- `3` - **File I/O Error** - File system access, permission, or storage issues
- `4` - **Validation Error** - Checksum failures, format errors, or data integrity issues
- `130` - **Interrupted by User** - Operation cancelled with Ctrl+C (SIGINT)

### Error Categories and Examples

#### Usage Errors (Exit Code 1)
```bash
# Invalid command
sseed invalid_command
# Output: error: argument command: invalid choice: 'invalid_command'
# Exit code: 1

# Missing required arguments
sseed restore
# Output: error: the following arguments are required: shards
# Exit code: 1

# Invalid group configuration
sseed shard -g "5-of-3"
# Output: Invalid group configuration: threshold cannot exceed total
# Exit code: 1
```

#### Cryptographic Errors (Exit Code 2)
```bash
# Entropy generation failure
sseed gen  # When system entropy is exhausted
# Output: Cryptographic error: Failed to generate secure entropy
# Exit code: 2

# Invalid mnemonic checksum
echo "invalid mnemonic words here that dont have valid checksum" | sseed shard
# Output: Cryptographic error: Mnemonic checksum validation failed
# Exit code: 2

# Insufficient shards for reconstruction
sseed restore shard1.txt shard2.txt  # When 3 required
# Output: Cryptographic error: Insufficient shards for reconstruction
# Exit code: 2
```

#### File I/O Errors (Exit Code 3)
```bash
# File not found
sseed shard -i nonexistent.txt
# Output: File error: Failed to read mnemonic from file 'nonexistent.txt'
# Exit code: 3

# Permission denied
sseed gen -o /root/restricted.txt
# Output: File error: Permission denied: '/root/restricted.txt'
# Exit code: 3

# Disk full
sseed gen -o /full-disk/file.txt
# Output: File error: No space left on device
# Exit code: 3
```

#### Validation Errors (Exit Code 4)
```bash
# Invalid mnemonic format
echo "not enough words" | sseed shard
# Output: Validation error: Invalid mnemonic length: 3. Must be 24 words
# Exit code: 4

# Duplicate shards
sseed restore shard1.txt shard1.txt shard2.txt
# Output: Validation error: Duplicate shard detected
# Exit code: 4

# Invalid file format
echo "corrupted data" > bad.txt && sseed shard -i bad.txt
# Output: Validation error: Invalid mnemonic format
# Exit code: 4
```

#### User Interruption (Exit Code 130)
```bash
# User presses Ctrl+C during operation
sseed gen -o large_file.txt
^C
# Output: Operation cancelled by user
# Exit code: 130
```

### Advanced Error Handling and Recovery
```bash
# Check if operation succeeded
if sseed gen -o seed.txt; then
    echo "Seed generated successfully"
else
    echo "Failed to generate seed (exit code: $?)"
fi

# Handle specific error types
sseed shard -i input.txt -g 3-of-5 -o output.txt
case $? in
    0) echo "Sharding successful" ;;
    1) echo "Usage error - check command syntax" ;;
    2) echo "Cryptographic error - check input validity" ;;
    3) echo "File I/O error - check permissions and disk space" ;;
    4) echo "Validation error - check data integrity" ;;
    130) echo "Operation cancelled by user" ;;
    *) echo "Unexpected error" ;;
esac

# Conditional execution with error awareness
sseed restore shard*.txt && echo "Recovery successful" || echo "Recovery failed (exit code: $?)"

# Robust backup script with error handling
backup_seed() {
    local seed_file="$1"
    local backup_dir="$2"
    
    # Generate with error checking
    if ! sseed gen -o "$seed_file"; then
        echo "Failed to generate seed" >&2
        return 1
    fi
    
    # Shard with error checking  
    if ! sseed shard -i "$seed_file" -g 3-of-5 --separate -o "$backup_dir/shard"; then
        echo "Failed to create shards" >&2
        return 1
    fi
    
    # Verify reconstruction
    if ! sseed restore "$backup_dir"/shard_*.txt >/dev/null; then
        echo "Failed to verify shards" >&2
        return 1
    fi
    
    echo "Backup completed successfully"
    return 0
} 