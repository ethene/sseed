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
# Show main help
sseed --help
sseed -h

# Show version information  
sseed --version
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

### Examples
```bash
# Generate with debug logging
sseed --log-level DEBUG gen

# Shard with verbose output
sseed -v shard -i seed.txt -g 3-of-5
```

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

### Exit Codes
- `0` - Success
- `1` - Invalid usage or file error
- `2` - Cryptographic error (invalid seed or shard)

### Error Message Categories

#### Usage Errors (Exit Code 1)
```bash
# Invalid command
sseed invalid_command
# Output: error: argument command: invalid choice: 'invalid_command'

# Missing required arguments
sseed restore
# Output: error: the following arguments are required: shards

# File not found
sseed shard -i nonexistent.txt
# Output: Error: Mnemonic file not found: nonexistent.txt
```

#### Validation Errors (Exit Code 2)
```bash
# Invalid mnemonic
echo "invalid words here" | sseed shard
# Output: Error: Invalid mnemonic length: 3. Must be one of [12, 15, 18, 21, 24]

# Insufficient shards
sseed restore shard1.txt shard2.txt  # When 3 required
# Output: Error: Insufficient shards for reconstruction
```

### Error Recovery
```bash
# Check if operation succeeded
if sseed gen -o seed.txt; then
    echo "Seed generated successfully"
else
    echo "Failed to generate seed"
fi

# Conditional execution
sseed restore shard*.txt && echo "Recovery successful"
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