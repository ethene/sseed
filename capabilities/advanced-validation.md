# Advanced Validation Capabilities

SSeed's advanced validation system provides comprehensive mnemonic analysis, backup verification, and security auditing capabilities for professional cryptocurrency operations.

## Overview

The `sseed validate` command offers five specialized validation modes designed for different use cases:

- **Basic**: Standard BIP-39 validation (format, language, checksum)
- **Advanced**: Deep analysis with entropy scoring and pattern detection
- **Entropy**: Specialized entropy analysis and quality metrics
- **Compatibility**: Cross-tool compatibility testing
- **Backup**: Comprehensive backup verification and integrity testing

## Quick Start

```bash
# Basic validation
sseed validate -i wallet.txt

# Deep analysis
sseed validate -i wallet.txt --mode advanced

# Backup verification
sseed validate -i original.txt --mode backup --shard-files 'shard*.txt'

# Batch validation
sseed validate --batch 'wallets/*.txt' --json
```

## Validation Modes

### Basic Mode

Standard BIP-39 validation for everyday use.

**Features:**
- Format validation (word count, valid words)
- Language auto-detection (9 BIP-39 languages)
- Checksum verification
- Fast execution (<100ms)

**Usage:**
```bash
sseed validate -i wallet.txt
echo "abandon ability able..." | sseed validate
sseed validate "clarify off only today sing hold easily chase phrase lady magic kind"
```

**Output:**
```
🔍 Mnemonic Validation Report
========================================
✅ Overall Score: 100/100
Status: Pass
Analyzed: 2025-06-28T10:30:15.123456

📋 Validation Checks:
--------------------
✅ Format
✅ Language
✅ Checksum
```

### Advanced Mode

Deep analysis with entropy scoring and security insights.

**Features:**
- All basic validation checks
- Entropy quality scoring (0-100)
- Weak pattern detection
- Dictionary attack resistance analysis
- Security recommendations
- Detailed timing analysis

**Usage:**
```bash
sseed validate -i wallet.txt --mode advanced
sseed validate -i wallet.txt --mode advanced --verbose
```

**Output:**
```
🔍 Advanced Mnemonic Analysis Report
========================================
✅ Overall Score: 88/100
Status: Good
Analyzed: 2025-06-28T10:30:15.123456

📋 Validation Checks:
--------------------
✅ Format
✅ Language
✅ Checksum
✅ Entropy Quality (Score: 85/100)
✅ Pattern Analysis
⚠️  Dictionary Resistance (Score: 78/100)

🔬 Analysis Details:
--------------------
• Entropy Source: High-quality randomness detected
• Pattern Strength: No weak patterns found
• Dictionary Risk: Some common word combinations detected
• Security Level: Suitable for production use

💡 Recommendations:
--------------------
• Consider regenerating if higher security is required
• Ensure secure generation environment
• Use additional passphrase for enhanced security
```

### Entropy Mode

Specialized entropy analysis for security auditing.

**Features:**
- Detailed entropy breakdown
- Randomness quality assessment
- Entropy source analysis
- Statistical distribution analysis
- Bias detection

**Usage:**
```bash
sseed validate -i wallet.txt --mode entropy
sseed validate -i wallet.txt --mode entropy --check-entropy
```

### Compatibility Mode

Cross-tool compatibility testing for interoperability.

**Features:**
- External tool integration tests
- Standard compliance verification
- Interoperability validation
- Cross-platform compatibility checks

**Usage:**
```bash
sseed validate -i wallet.txt --mode compatibility
sseed validate -i wallet.txt --mode compatibility --verbose
```

**Requirements:**
- Optional: Trezor shamir CLI for SLIP-39 testing
- Optional: Additional BIP-39 tools for extended testing

### Backup Mode

Comprehensive backup verification and integrity testing.

**Features:**
- Round-trip backup testing
- Shard combination validation
- Stress testing with multiple iterations
- Entropy consistency verification
- Performance timing analysis

**Usage:**
```bash
# Basic backup verification
sseed validate -i original.txt --mode backup

# With existing shard files
sseed validate -i original.txt --mode backup --shard-files 'shard*.txt'

# Stress testing
sseed validate -i wallet.txt --mode backup --iterations 10 --stress-test

# Custom group configuration
sseed validate -i wallet.txt --mode backup --group-config '3-of-5'
```

**Parameters:**
- `--shard-files`: Existing shard files to verify
- `--group-config`: SLIP-39 group configuration (default: "3-of-5")
- `--iterations`: Number of test iterations (default: 1)
- `--stress-test`: Enable stress testing mode

**Output:**
```
🔍 Backup Verification Report
========================================
✅ Overall Score: 95/100
Status: Excellent
Analyzed: 2025-06-28T10:30:15.123456

📋 Tests Performed:
--------------------
✅ Original Mnemonic Validation
✅ Round-trip Backup Testing
✅ Shard Combination Testing
✅ Entropy Consistency Verification

⏱️  Performance Metrics:
--------------------
• Generation Time: 45ms
• File I/O Time: 12ms
• Reconstruction Time: 38ms
• Total Duration: 95ms

💡 Recommendations:
--------------------
• Backup integrity verified successfully
• All shard combinations work correctly
• Performance within expected ranges
```

## Batch Processing

Process multiple files efficiently with concurrent processing.

**Features:**
- Directory and glob pattern support
- Concurrent file processing
- Success rate calculation
- Detailed per-file results
- Summary statistics

**Usage:**
```bash
# Directory validation
sseed validate --batch wallets/

# Glob pattern validation
sseed validate --batch 'wallets/*.txt'

# Advanced batch validation
sseed validate --batch 'production/*.txt' --mode advanced

# JSON output for automation
sseed validate --batch wallets/ --json
```

**Output:**
```
📊 Batch Validation Report
==================================================
✅ Overall Success Rate: 85.7%
📁 Total Files: 14
✅ Passed: 12
❌ Failed: 2

📋 Failed Files:
--------------------
❌ wallets/corrupted.txt - Invalid checksum
❌ wallets/short.txt - Invalid word count

⏱️  Performance:
--------------------
• Total Duration: 1.2s
• Average per File: 86ms
• Concurrent Workers: 4
```

## Output Formats

### Human-Readable Text (Default)

Formatted reports with emojis, colors, and clear structure.

```bash
sseed validate -i wallet.txt
sseed validate -i wallet.txt --verbose
```

### JSON Format

Machine-readable output for automation and integration.

```bash
sseed validate -i wallet.txt --json
sseed validate --batch wallets/ --json
```

**JSON Structure:**
```json
{
  "input": "clarify off only today...",
  "input_type": "mnemonic",
  "mode": "advanced",
  "timestamp": "2025-06-28T10:30:15.123456",
  "overall_status": "pass",
  "overall_score": 88,
  "checks": {
    "format": {
      "status": "pass",
      "word_count": 12,
      "message": "Valid format with 12 words"
    },
    "language": {
      "status": "pass",
      "detected": "en",
      "message": "Language: English"
    },
    "checksum": {
      "status": "pass",
      "message": "Valid BIP-39 checksum"
    },
    "entropy_analysis": {
      "status": "pass",
      "score": 85,
      "quality": "high",
      "message": "High-quality entropy detected"
    }
  },
  "duration_ms": 145,
  "recommendations": [
    "Mnemonic passes all security checks",
    "Suitable for production use"
  ]
}
```

### Quiet Mode

Minimal output for scripting (exit codes only).

```bash
sseed validate -i wallet.txt --quiet
echo $?  # 0 = success, 1 = failure, 2 = partial success
```

## Automation and Integration

### Exit Codes

- `0`: Success (all validations passed)
- `1`: Failure (validation failed or error occurred)
- `2`: Partial success (batch processing with some failures)

### Scripting Examples

```bash
# Simple validation check
if sseed validate -i wallet.txt --quiet; then
    echo "Wallet is valid"
else
    echo "Wallet validation failed"
fi

# Extract specific metrics
SCORE=$(sseed validate -i wallet.txt --json | jq -r '.overall_score')
if [ "$SCORE" -gt 80 ]; then
    echo "High-quality wallet (score: $SCORE)"
fi

# Batch processing with filtering
sseed validate --batch wallets/ --json | \
  jq '.files[] | select(.overall_score < 70) | .filename'
```

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Validate Wallet Files
  run: |
    sseed validate --batch test-wallets/ --json > validation-report.json
    if [ $? -ne 0 ]; then
      echo "Wallet validation failed"
      exit 1
    fi

- name: Upload Validation Report
  uses: actions/upload-artifact@v3
  with:
    name: validation-report
    path: validation-report.json
```

## Performance Characteristics

### Single Validation

- **Basic Mode**: <100ms typical
- **Advanced Mode**: <500ms typical
- **Entropy Mode**: <300ms typical
- **Compatibility Mode**: <2s typical (depends on external tools)
- **Backup Mode**: <1s typical (depends on iterations)

### Batch Processing

- **Concurrent Workers**: Auto-detected (CPU cores)
- **Memory Usage**: ~10MB base + 1MB per concurrent file
- **Throughput**: 50-200 files/second (mode dependent)

### Optimization Tips

```bash
# Use quiet mode for better performance
sseed validate --batch wallets/ --quiet

# Limit concurrent workers for memory-constrained environments
export SSEED_MAX_WORKERS=2
sseed validate --batch large-directory/

# Use basic mode for simple validation
sseed validate --batch wallets/ --mode basic
```

## Security Considerations

### Input Handling

- Mnemonics are never logged or persisted
- Memory is cleared after processing
- Temporary files are securely deleted
- No network communication required

### Backup Verification

- Temporary shard files are created in secure directories
- All temporary files are automatically cleaned up
- Original files are never modified
- Verification uses read-only operations

### External Tool Integration

- External tools are optional and sandboxed
- No sensitive data is passed to external processes
- Tool availability is checked before execution
- Failures are handled gracefully

## Troubleshooting

### Common Issues

**Language Detection Failed**
```
WARNING: Best language score 0.10 below threshold 0.70, language detection failed
```
**Solution**: Specify language explicitly with `--language en`

**External Tool Not Found**
```
ERROR: Trezor shamir CLI not found for compatibility testing
```
**Solution**: Install optional tools or skip compatibility mode

**Permission Denied on Batch Processing**
```
ERROR: Permission denied reading file: /path/to/file.txt
```
**Solution**: Check file permissions and directory access

**Memory Issues with Large Batches**
```
ERROR: Out of memory processing large batch
```
**Solution**: Reduce concurrent workers or process in smaller batches

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
# Verbose output
sseed validate -i wallet.txt --verbose

# Debug mode (if available)
SSEED_DEBUG=1 sseed validate -i wallet.txt

# Trace mode for development
SSEED_TRACE=1 sseed validate -i wallet.txt
```

### Performance Issues

```bash
# Profile validation performance
time sseed validate -i wallet.txt --mode advanced

# Check system resources
sseed validate --batch large-dir/ --verbose | grep "Duration\|Workers"

# Reduce resource usage
sseed validate --batch large-dir/ --mode basic --quiet
```

## Advanced Usage Patterns

### Multi-Stage Validation Pipeline

```bash
#!/bin/bash
# Complete wallet validation pipeline

WALLET="wallet.txt"

# Stage 1: Basic validation
echo "Stage 1: Basic validation..."
if ! sseed validate -i "$WALLET" --quiet; then
    echo "❌ Basic validation failed"
    exit 1
fi

# Stage 2: Advanced analysis
echo "Stage 2: Advanced analysis..."
SCORE=$(sseed validate -i "$WALLET" --mode advanced --json | jq -r '.overall_score')
if [ "$SCORE" -lt 70 ]; then
    echo "⚠️  Low quality score: $SCORE"
fi

# Stage 3: Backup verification
echo "Stage 3: Backup verification..."
sseed validate -i "$WALLET" --mode backup --iterations 5

echo "✅ Validation pipeline complete"
```

### Security Audit Workflow

```bash
#!/bin/bash
# Security audit for production wallets

AUDIT_DIR="production-wallets"
REPORT_FILE="security-audit-$(date +%Y%m%d).json"

echo "🔍 Starting security audit..."

# Comprehensive batch validation
sseed validate --batch "$AUDIT_DIR/" --mode advanced --json > "$REPORT_FILE"

# Extract critical metrics
HIGH_RISK=$(jq '[.files[] | select(.overall_score < 60)] | length' "$REPORT_FILE")
MEDIUM_RISK=$(jq '[.files[] | select(.overall_score >= 60 and .overall_score < 80)] | length' "$REPORT_FILE")
LOW_RISK=$(jq '[.files[] | select(.overall_score >= 80)] | length' "$REPORT_FILE")

echo "📊 Audit Results:"
echo "   High Risk: $HIGH_RISK wallets"
echo "   Medium Risk: $MEDIUM_RISK wallets"
echo "   Low Risk: $LOW_RISK wallets"

# Generate recommendations
if [ "$HIGH_RISK" -gt 0 ]; then
    echo "⚠️  Action Required: $HIGH_RISK high-risk wallets need attention"
    jq -r '.files[] | select(.overall_score < 60) | "❌ \(.filename): \(.overall_score)/100"' "$REPORT_FILE"
fi

echo "📄 Full report saved to: $REPORT_FILE"
```

### Integration with Monitoring Systems

```bash
#!/bin/bash
# Prometheus metrics export

METRICS_FILE="/var/lib/prometheus/sseed_validation.prom"

# Run validation and extract metrics
RESULT=$(sseed validate --batch wallets/ --json)
SUCCESS_RATE=$(echo "$RESULT" | jq -r '.summary.success_rate')
TOTAL_FILES=$(echo "$RESULT" | jq -r '.summary.total_files')
FAILED_FILES=$(echo "$RESULT" | jq -r '.summary.failed')

# Export Prometheus metrics
cat > "$METRICS_FILE" << EOF
# HELP sseed_validation_success_rate Percentage of wallets passing validation
# TYPE sseed_validation_success_rate gauge
sseed_validation_success_rate $SUCCESS_RATE

# HELP sseed_validation_total_files Total number of wallet files processed
# TYPE sseed_validation_total_files gauge
sseed_validation_total_files $TOTAL_FILES

# HELP sseed_validation_failed_files Number of wallet files that failed validation
# TYPE sseed_validation_failed_files gauge
sseed_validation_failed_files $FAILED_FILES
EOF

echo "📊 Metrics exported to $METRICS_FILE"
```

## API Reference

### Command Line Interface

```bash
sseed validate [OPTIONS] [MNEMONIC]

Options:
  -i, --input-file PATH          Input file containing mnemonic
  --batch PATH                   Batch process directory or glob pattern
  --mode MODE                    Validation mode: basic|advanced|entropy|compatibility|backup
  --json                         Output in JSON format
  --verbose                      Verbose output
  --quiet                        Quiet mode (exit codes only)
  --language LANG                Force specific language
  --strict                       Strict validation mode
  --check-entropy                Enable entropy checking

Backup Mode Options:
  --shard-files PATTERN          Existing shard files to verify
  --group-config CONFIG          SLIP-39 group configuration (default: "3-of-5")
  --iterations N                 Number of test iterations (default: 1)
  --stress-test                  Enable stress testing mode

Examples:
  sseed validate -i wallet.txt
  sseed validate --batch wallets/ --mode advanced
  sseed validate -i original.txt --mode backup --shard-files 'shard*.txt'
```

### Python API

```python
from sseed.validation import validate_mnemonic
from sseed.validation.backup_verification import verify_backup_integrity

# Basic validation
result = validate_mnemonic("clarify off only today...", mode="basic")
print(f"Status: {result['overall_status']}")

# Advanced validation
result = validate_mnemonic("clarify off only today...", mode="advanced")
print(f"Score: {result['overall_score']}/100")

# Backup verification
result = verify_backup_integrity(
    mnemonic="clarify off only today...",
    group_config="3-of-5",
    iterations=5
)
print(f"Backup integrity: {result['overall_status']}")
```

## Changelog

### Version 1.0.0 (2025-06-28)

**New Features:**
- ✅ Complete validation command implementation
- ✅ Five specialized validation modes
- ✅ Batch processing with concurrent execution
- ✅ Backup verification and integrity testing
- ✅ JSON output format for automation
- ✅ Cross-tool compatibility testing
- ✅ Comprehensive entropy analysis
- ✅ Security scoring and recommendations

**Performance:**
- ✅ <100ms single validation (basic mode)
- ✅ Concurrent batch processing
- ✅ Memory-efficient large batch handling
- ✅ Optimized entropy calculations

**Security:**
- ✅ No mnemonic persistence or logging
- ✅ Secure temporary file handling
- ✅ Memory cleanup after processing
- ✅ Sandboxed external tool integration

## Support and Contributing

### Getting Help

- **Documentation**: This file and `sseed validate --help`
- **Examples**: `sseed examples` for usage patterns
- **Issues**: Report bugs and feature requests on the project repository

### Contributing

- **Testing**: Add test cases for new validation scenarios
- **External Tools**: Integrate additional BIP-39/SLIP-39 tools
- **Performance**: Optimize validation algorithms
- **Documentation**: Improve examples and troubleshooting guides

### Development

```bash
# Run tests
python -m pytest tests/test_validate_*.py -v

# Performance testing
python -m pytest tests/test_validate_integration.py::TestValidatePerformance -v

# Coverage report
python -m pytest tests/test_validate_*.py --cov=sseed.validation --cov-report=html
``` 