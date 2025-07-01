"""
Command-line examples and help system for SSeed.

This module provides comprehensive examples and usage patterns for all SSeed commands,
including advanced features like BIP85 deterministic entropy and SLIP-39 secret sharing.
"""

import sys
from typing import Any


def _print_section(title: str, content: str) -> None:
    """Print a formatted section with title and content."""
    print(f"\n{title}")
    print("=" * len(title))
    print(content)


def _get_basic_examples() -> str:
    """Get basic command examples."""
    return """
🔐 GENERATE SECURE MNEMONIC
  sseed gen                           # 24-word English mnemonic
  sseed gen -w 12                     # 12-word mnemonic
  sseed gen -l es                     # Spanish mnemonic
  sseed gen -o backup.txt             # Save to file

🌱 GENERATE MASTER SEED
  sseed seed                          # From stdin
  sseed seed -i mnemonic.txt          # From file
  sseed seed -m "word1 word2..."      # Direct input
  sseed seed --hex                    # Hex output format

🎯 BIP85 DETERMINISTIC ENTROPY
  sseed bip85 bip39 -w 12 -n 0        # Child BIP39 mnemonic
  sseed bip85 hex -b 32 -n 1          # 32-byte hex entropy
  sseed bip85 password -l 20 -n 2     # 20-char password

🧩 SLIP-39 SECRET SHARING
  sseed shard -g 3-of-5               # 3-of-5 sharing
  sseed shard -g 2-of-3,2-of-5        # Multi-group
  sseed restore shard*.txt            # Restore from shards

🔍 MNEMONIC VALIDATION
  sseed validate                      # Basic validation
  sseed validate --mode advanced     # Deep analysis
  sseed validate --batch "*.txt"     # Batch validation
"""


def _get_advanced_examples() -> str:
    """Get advanced usage examples."""
    return """
🔧 CUSTOM ENTROPY SOURCES
  # Dice entropy (6-sided dice)
  sseed gen --dice "1,2,3,4,5,6,1,2,3..."

  # Hex entropy
  sseed gen --hex-entropy "a1b2c3d4e5f6..."

  # Combined with custom word count
  sseed gen -w 18 --dice "1,2,3,4,5,6..."

🔬 ENTROPY ANALYSIS & VERIFICATION
  # Analyze system entropy quality
  sseed gen --entropy-analysis

  # Analyze custom entropy sources
  sseed gen --entropy-hex "a1b2c3..." --entropy-analysis
  sseed gen --entropy-dice "1,2,3,4,5,6..." --entropy-analysis

  # Combined entropy analysis and display
  sseed gen --entropy-analysis --show-entropy

  # Validate existing mnemonic entropy
  sseed validate --mode entropy -i wallet.txt

🌍 MULTI-LANGUAGE SUPPORT
  sseed gen -l zh-cn                  # Chinese Simplified
  sseed gen -l ko                     # Korean
  sseed gen -l cs                     # Czech
  sseed seed -l auto                  # Auto-detect language

🎯 ADVANCED BIP85 PATTERNS
  # Generate multiple child wallets
  for i in {0..9}; do
    sseed bip85 bip39 -w 24 -n $i -o "wallet_$i.txt"
  done

  # Generate passwords for different services
  sseed bip85 password -l 16 -n 0 -c alphanumeric  # Service 1
  sseed bip85 password -l 32 -n 1 -c base64        # Service 2

🔗 ADVANCED SLIP-39 CONFIGURATIONS
  # Corporate backup (multiple groups)
  sseed shard -g "2-of-3,3-of-5,1-of-1" -i master.txt

  # Personal backup with recovery options
  sseed shard -g "2-of-3" --group-names "personal,backup,recovery"
"""


def _get_validation_examples() -> str:
    """Get validation examples."""
    return """
🔍 MNEMONIC VALIDATION & ANALYSIS

Basic Validation:
  sseed validate -m "abandon ability able..."     # Direct input
  sseed validate -i wallet.txt                   # From file
  echo "word1 word2..." | sseed validate         # From stdin

Advanced Validation Modes:
  sseed validate --mode basic                    # Checksum + format
  sseed validate --mode advanced                 # Deep analysis + scoring
  sseed validate --mode entropy                  # Entropy quality analysis
  sseed validate --mode compatibility            # Cross-tool testing
  sseed validate --mode backup                   # Backup verification

Backup Verification Workflows:
  # Test existing SLIP-39 shards
  sseed validate --mode backup --shard-files shard1.txt shard2.txt shard3.txt

  # Stress test backup process
  sseed validate --mode backup --group-config "3-of-5" --iterations 20 --stress-test

  # Comprehensive backup validation
  sseed validate --mode backup -i master.txt --group-config "2-of-3" --iterations 10

Batch Validation Patterns:
  sseed validate --batch "wallets/*.txt"         # Validate all wallet files
  sseed validate --batch "**/*.mnemonic" --recursive  # Recursive search
  sseed validate --batch "*.txt" --workers 8     # Parallel processing

Automation-Friendly Usage:
  # JSON output for scripting
  sseed validate --mode advanced --json -i wallet.txt

  # Exit codes for CI/CD
  sseed validate -i wallet.txt && echo "Valid" || echo "Invalid"

  # Batch validation with JSON summary
  sseed validate --batch "*.txt" --json -o validation_report.json
"""


def _get_automation_examples() -> str:
    """Get automation examples."""
    return """
🤖 AUTOMATION & SCRIPTING

Pipeline Examples:
  # Generate → Validate → Backup
  sseed gen -o master.txt
  sseed validate -i master.txt --mode advanced
  sseed shard -g 3-of-5 -i master.txt -o backup/

  # BIP85 Child Wallet Generation
  for i in {0..4}; do
    sseed bip85 bip39 -w 12 -n $i | sseed validate --mode advanced
  done

JSON Processing:
  # Extract validation score
  SCORE=$(sseed validate --mode advanced --json -i wallet.txt | jq '.overall_score')

  # Check if wallet is valid
  sseed validate --json -i wallet.txt | jq -r '.is_valid'

  # Get entropy quality metrics
  sseed validate --mode entropy --json -i wallet.txt | jq '.entropy_analysis'

CI/CD Integration:
  # Quality gate in CI
  sseed validate --mode advanced -i wallet.txt
  if [ $? -eq 0 ]; then
    echo "✅ Wallet validation passed"
  else
    echo "❌ Wallet validation failed"
    exit 1
  fi

Backup Verification Automation:
  # Automated backup testing
  sseed validate --mode backup --json -i master.txt \\
    --group-config "3-of-5" --iterations 10 \\
    -o backup_verification_report.json
"""


def _get_security_examples() -> str:
    """Get security examples."""
    return """
🛡️ SECURITY BEST PRACTICES

Air-Gapped Usage:
  # Offline generation (no network calls)
  sseed gen -o secure_wallet.txt
  sseed validate -i secure_wallet.txt --mode advanced

  # Verify entropy quality
  sseed validate -i secure_wallet.txt --mode entropy

Secure Backup Workflows:
  # Generate master → Create shares → Verify integrity
  sseed gen -o master.txt
  sseed shard -g 3-of-5 -i master.txt -o shares/
  sseed validate --mode backup --shard-files shares/*.txt

Memory-Safe Operations:
  # Use files instead of command line arguments
  echo "abandon ability able..." > temp_mnemonic.txt
  sseed validate -i temp_mnemonic.txt
  shred -u temp_mnemonic.txt  # Secure deletion

Cross-Tool Validation:
  # Verify compatibility with other tools
  sseed validate --mode compatibility -i wallet.txt

  # Advanced entropy analysis
  sseed validate --mode entropy -i wallet.txt --json | jq '.entropy_analysis'
"""


def _get_reference_info() -> str:
    """Get reference information."""
    return """
🔍 VALIDATION MODES REFERENCE

Mode: basic
- Purpose: Standard mnemonic validation
- Checks: BIP-39 checksum, wordlist compliance, format validation
- Output: Pass/fail with basic metadata
- Use case: Quick verification of mnemonic validity

Mode: advanced
- Purpose: Comprehensive mnemonic analysis
- Checks: All basic checks + entropy scoring + pattern detection
- Output: 0-100 quality score with detailed analysis
- Use case: Security auditing and quality assessment

Mode: entropy
- Purpose: Specialized entropy quality analysis
- Checks: Randomness testing, distribution analysis, weakness detection
- Output: Entropy metrics and quality indicators
- Use case: Verifying randomness quality of generated mnemonics

Mode: compatibility
- Purpose: Cross-tool compatibility verification
- Checks: Compatibility with external BIP-39/SLIP-39 implementations
- Output: Compatibility report with external tool results
- Use case: Integration testing and interoperability verification

Mode: backup
- Purpose: Backup integrity and recovery testing
- Checks: Round-trip testing, shard validation, stress testing
- Output: Comprehensive backup verification report
- Use case: Validating backup processes and recovery procedures

EXIT CODES:
  0  - Success (validation passed)
  1  - Validation failed or errors occurred
  130 - Interrupted by user (Ctrl+C)

PERFORMANCE CHARACTERISTICS:
  Basic mode:        <50ms per validation
  Advanced mode:     <200ms per validation
  Entropy mode:      <100ms per validation
  Compatibility mode: <500ms per validation (external tools)
  Backup mode:       <2s per validation (depends on iterations)
"""


def show_examples(_args: Any) -> int:
    """Show comprehensive examples and usage patterns."""
    try:
        print("🔐 SSeed Usage Examples")
        print("=" * 50)

        _print_section("📚 BASIC COMMANDS", _get_basic_examples())
        _print_section("🚀 ADVANCED USAGE", _get_advanced_examples())
        _print_section("🔍 VALIDATION & ANALYSIS", _get_validation_examples())
        _print_section("🤖 AUTOMATION & SCRIPTING", _get_automation_examples())
        _print_section("🛡️ SECURITY WORKFLOWS", _get_security_examples())
        _print_section("📖 REFERENCE", _get_reference_info())

        print("\n" + "=" * 50)
        print("💡 For detailed help on any command: sseed <command> --help")
        print("📚 Full documentation: https://github.com/your-repo/sseed")
        print("🐛 Report issues: https://github.com/your-repo/sseed/issues")

        return 0

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Error displaying examples: {e}", file=sys.stderr)
        return 1
