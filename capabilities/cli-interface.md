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

## Generation Command (`gen`)

### Purpose
Generate cryptographically secure 24-word BIP-39 mnemonics using OS entropy.

### Syntax
```bash
sseed gen [options]
```

### Options
- `-o, --output FILE` - Output file (default: stdout)
- `-h, --help` - Show command help

### Usage Examples

#### Basic Generation
```bash
# Generate to stdout
sseed gen

# Example output
abandon ability able about above absent absorb abstract absurd abuse access accident
account accuse achieve acid acoustic acquire across act action actor actress actual
```

#### File Output
```bash
# Generate to file
sseed gen -o my_seed.txt

# Generate with timestamp in filename
sseed gen -o "seed_$(date +%Y%m%d_%H%M%S).txt"

# Generate to secure location
sseed gen -o /secure/vault/backup_seed.txt
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

## Sharding Command (`shard`)

### Purpose
Split BIP-39 mnemonics into SLIP-39 shards using configurable threshold schemes.

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
```

#### Output Options
```bash
# Restore to file
sseed restore shard1.txt shard2.txt shard3.txt -o recovered.txt

# Restore and verify
sseed restore shard*.txt | sseed shard -g 3-of-5  # Round-trip test
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