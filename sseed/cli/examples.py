"""Examples display for CLI commands.

Provides comprehensive usage examples for all sseed commands with multi-language support.
"""

import argparse

# Define exit code locally to avoid circular import
EXIT_SUCCESS = 0


def show_examples(_: argparse.Namespace) -> int:
    """Show comprehensive usage examples for all commands.

    Args:
        _: Parsed command line arguments (unused).

    Returns:
        Always returns EXIT_SUCCESS (0).
    """
    print("🔐 SSeed Usage Examples")
    print("=" * 40)
    print()

    print("📝 Basic Generation:")
    print("   sseed gen                              # Generate to stdout (English)")
    print("   sseed gen -o wallet.txt                # Generate to file")
    print("   sseed gen --show-entropy               # Show entropy alongside")
    print()

    print("🌍 Multi-Language Generation:")
    print("   sseed gen -l en                        # English (default)")
    print("   sseed gen -l es -o spanish.txt         # Spanish mnemonic")
    print("   sseed gen -l fr -o french.txt          # French mnemonic")
    print("   sseed gen -l zh-cn -o chinese.txt      # Chinese Simplified")
    print("   sseed gen -l zh-tw -o traditional.txt  # Chinese Traditional")
    print("   sseed gen -l ko -o korean.txt          # Korean mnemonic")
    print("   sseed gen -l it -o italian.txt         # Italian mnemonic")
    print("   sseed gen -l pt -o portuguese.txt      # Portuguese mnemonic")
    print("   sseed gen -l cs -o czech.txt           # Czech mnemonic")
    print()

    print("🌱 Master Seed Generation (BIP-39 → BIP-32):")
    print("   sseed seed -i wallet.txt --hex         # Generate 512-bit master seed")
    print(
        "   sseed seed -i wallet.txt -p 'passphrase' --hex  # With passphrase (25th word)"
    )
    print("   sseed seed -i wallet.txt --iterations 4096 --hex # Higher security")
    print("   sseed gen | sseed seed --hex           # Generate and derive seed")
    print()

    print("🔗 Sharding (SLIP-39) with Language Detection:")
    print("   sseed shard -i wallet.txt -g 3-of-5             # Auto-detects language")
    print("   sseed shard -i spanish.txt -g '2:(2-of-3,3-of-5)' # Multi-group Spanish")
    print(
        "   sseed shard -i chinese.txt --separate            # Separate files with Chinese"
    )
    print("   cat korean.txt | sseed shard -g 2-of-3           # Korean from stdin")
    print()

    print("🔄 Restoration with Auto-Detection:")
    print("   sseed restore shard1.txt shard2.txt shard3.txt  # Auto-detects language")
    print("   sseed restore spanish_shard*.txt --show-entropy  # Spanish with entropy")
    print("   sseed restore chinese_shards/*.txt -o restored.txt # Chinese to file")
    print()

    print("🎯 BIP85 Deterministic Entropy Derivation:")
    print("   # Generate child BIP39 mnemonics")
    print("   sseed bip85 bip39 -i master.txt -w 12 -n 0      # 12-word child mnemonic")
    print("   sseed bip85 bip39 -i master.txt -w 24 -l es -n 1 # Spanish 24-word child")
    print("   sseed bip85 bip39 -i master.txt -w 15 -l zh-cn -n 2 # Chinese child")
    print()
    print("   # Generate hex entropy")
    print("   sseed bip85 hex -i master.txt -b 32 -n 0        # 32 bytes hex entropy")
    print("   sseed bip85 hex -i master.txt -b 24 -u -n 1     # 24 bytes uppercase")
    print("   sseed bip85 hex -i master.txt -b 16 -n 5        # 16 bytes for keys")
    print()
    print("   # Generate passwords")
    print(
        "   sseed bip85 password -i master.txt -l 20 -c base64 -n 0  # Base64 password"
    )
    print(
        "   sseed bip85 password -i master.txt -l 30 -c base85 -n 1  # Base85 password"
    )
    print(
        "   sseed bip85 password -i master.txt -l 16 -c alphanumeric -n 2 # Alphanumeric"
    )
    print(
        "   sseed bip85 password -i master.txt -l 25 -c ascii -n 3    # Full ASCII set"
    )
    print()

    print("🔐 Advanced BIP85 Workflows:")
    print("   # Master seed → Child wallets workflow")
    print(
        "   sseed gen -o master.txt                         # Generate master mnemonic"
    )
    print(
        "   sseed bip85 bip39 -i master.txt -w 12 -n 0 -o wallet1.txt  # Child wallet 1"
    )
    print(
        "   sseed bip85 bip39 -i master.txt -w 12 -n 1 -o wallet2.txt  # Child wallet 2"
    )
    print(
        "   sseed bip85 bip39 -i master.txt -w 12 -n 2 -o wallet3.txt  # Child wallet 3"
    )
    print()
    print("   # Multi-language child wallet generation")
    print("   sseed bip85 bip39 -i master.txt -w 24 -l en -n 0 -o english_wallet.txt")
    print("   sseed bip85 bip39 -i master.txt -w 24 -l es -n 1 -o spanish_wallet.txt")
    print(
        "   sseed bip85 bip39 -i master.txt -w 24 -l zh-cn -n 2 -o chinese_wallet.txt"
    )
    print()
    print("   # BIP85 child + SLIP39 sharding combination")
    print("   sseed bip85 bip39 -i master.txt -w 12 -n 0 | sseed shard -g 3-of-5")
    print("   sseed bip85 bip39 -i master.txt -w 24 -l es -n 1 | sseed shard -g 2-of-3")
    print()
    print("   # Application-specific entropy")
    print(
        "   sseed bip85 hex -i master.txt -b 32 -n 0 -o app1_key.hex  # App 1 key material"
    )
    print(
        "   sseed bip85 hex -i master.txt -b 32 -n 1 -o app2_key.hex  # App 2 key material"
    )
    print(
        "   sseed bip85 password -i master.txt -l 32 -n 0 -o app_password.txt # App password"
    )
    print()

    print("🔍 Mnemonic Validation & Analysis:")
    print("   # Basic validation")
    print("   echo 'clarify off only today...' | sseed validate    # Validate from stdin")
    print("   sseed validate -i wallet.txt                        # Validate from file")
    print("   sseed validate 'clarify off only today...'          # Direct validation")
    print()
    print("   # Advanced validation modes")
    print("   sseed validate -i wallet.txt --mode advanced        # Deep analysis")
    print("   sseed validate -i wallet.txt --mode entropy         # Entropy analysis")
    print("   sseed validate -i wallet.txt --mode compatibility   # Cross-tool testing")
    print("   sseed validate -i wallet.txt --mode backup          # Backup verification")
    print()
    print("   # Backup verification workflows")
    print("   sseed validate -i original.txt --mode backup \\")
    print("     --shard-files 'shard*.txt' --group-config '3-of-5'")
    print("   sseed validate -i wallet.txt --mode backup \\")
    print("     --iterations 10 --stress-test                    # Stress testing")
    print()
    print("   # Batch validation")
    print("   sseed validate --batch 'wallets/*.txt'              # Validate directory")
    print("   sseed validate --batch wallets/ --mode advanced     # Advanced batch")
    print("   sseed validate --batch 'backup*.txt' --json         # JSON batch output")
    print()
    print("   # Automation-friendly usage")
    print("   sseed validate -i wallet.txt --json | jq '.overall_status'")
    print("   sseed validate -i wallet.txt --quiet                # Exit code only")
    print("   sseed validate --batch wallets/ --json \\")
    print("     | jq '.summary.success_rate'                     # Batch success rate")
    print()

    print("📋 Information:")
    print("   sseed version                          # Version info")
    print("   sseed version --json                   # JSON format")
    print("   sseed examples                         # This help")
    print()

    print("🚀 Complete Multi-Language Workflows:")
    print("   # Full workflow: Generate → Shard → Restore (Spanish)")
    print("   sseed gen -l es -o master_es.txt")
    print("   sseed shard -i master_es.txt -g 3-of-5 --separate")
    print("   sseed restore shard_*.txt -o recovered_es.txt")
    print()

    print("   # Mixed language handling (auto-detection)")
    print("   sseed gen -l zh-cn -o chinese.txt")
    print("   sseed shard -i chinese.txt -g 2-of-3 --separate")
    print("   sseed restore chinese_shard_*.txt --show-entropy")
    print()

    print("   # Multi-language entropy verification")
    print("   sseed gen -l ko --show-entropy -o korean.txt")
    print("   sseed restore korean_shards/*.txt --show-entropy")
    print()

    print("   # International secure distribution")
    print("   sseed gen -l fr | sseed shard -g '2:(2-of-3,2-of-3)' --separate")
    print()

    print("   # Seed derivation across languages")
    print("   sseed gen -l it -o italian.txt")
    print("   sseed seed -i italian.txt -p -o seed_italian.hex")
    print()

    print("🔐 Advanced Validation & Security Workflows:")
    print("   # Complete wallet validation pipeline")
    print("   sseed gen -o new_wallet.txt")
    print("   sseed validate -i new_wallet.txt --mode advanced --verbose")
    print("   sseed validate -i new_wallet.txt --mode backup --iterations 5")
    print()
    print("   # Multi-wallet batch security audit")
    print("   sseed validate --batch 'production_wallets/*.txt' \\")
    print("     --mode advanced --json -o audit_report.json")
    print()
    print("   # Backup integrity verification workflow")
    print("   sseed shard -i master.txt -g 3-of-5 --separate")
    print("   sseed validate -i master.txt --mode backup \\")
    print("     --shard-files 'shard_*.txt' --stress-test")
    print()
    print("   # Cross-tool compatibility verification")
    print("   sseed validate -i wallet.txt --mode compatibility --verbose")
    print()

    print("🌍 Language Support Reference:")
    print("   en       English (default)")
    print("   es       Spanish (Español)")
    print("   fr       French (Français)")
    print("   it       Italian (Italiano)")
    print("   pt       Portuguese (Português)")
    print("   cs       Czech (Čeština)")
    print("   zh-cn    Chinese Simplified (简体中文)")
    print("   zh-tw    Chinese Traditional (繁體中文)")
    print("   ko       Korean (한국어)")
    print()

    print("🎯 BIP85 Applications Reference:")
    print("   bip39    Generate BIP39 mnemonic phrases in any language")
    print("            • Word counts: 12, 15, 18, 21, 24")
    print("            • Languages: All 9 BIP-39 languages supported")
    print("            • Index: 0 to 2³¹-1 for different child wallets")
    print()
    print("   hex      Generate raw entropy as hexadecimal")
    print("            • Byte lengths: 16-64 bytes")
    print("            • Case: lowercase (default) or uppercase (-u)")
    print("            • Use: Key material, seeds, random data")
    print()
    print("   password Generate passwords with various character sets")
    print("            • base64: URL-safe base64 (20-86 chars)")
    print("            • base85: ASCII85 encoding (10-80 chars)")
    print("            • alphanumeric: A-Z, a-z, 0-9 (10-128 chars)")
    print("            • ascii: Full ASCII printable set (10-128 chars)")
    print()

    print("🔍 Validation Modes Reference:")
    print("   basic        Standard BIP-39 validation (format, language, checksum)")
    print("                • Fast validation for everyday use")
    print("                • Language auto-detection")
    print("                • Checksum verification")
    print()
    print("   advanced     Deep analysis with entropy and pattern detection")
    print("                • Entropy quality scoring (0-100)")
    print("                • Weak pattern detection")
    print("                • Security recommendations")
    print()
    print("   entropy      Specialized entropy analysis and quality metrics")
    print("                • Detailed entropy breakdown")
    print("                • Randomness quality assessment")
    print("                • Entropy source analysis")
    print()
    print("   compatibility Cross-tool compatibility testing")
    print("                • External tool integration tests")
    print("                • Standard compliance verification")
    print("                • Interoperability validation")
    print()
    print("   backup       Comprehensive backup verification")
    print("                • Round-trip backup testing")
    print("                • Shard combination validation")
    print("                • Stress testing with multiple iterations")
    print("                • Entropy consistency verification")
    print()

    print("📚 Tips & Best Practices:")
    print("   • Use separate files (--separate) for safer shard distribution")
    print("   • Always verify with --show-entropy for critical operations")
    print("   • Store shards in different secure locations")
    print("   • Test recovery before relying on shards")
    print("   • Use passphrases for additional security layer")
    print("   • Language is auto-detected for restore/shard/seed operations")
    print("   • Validate mnemonics before using them in production")
    print("   • Use batch validation for auditing multiple wallets")
    print("   • JSON output enables automation and integration")
    print("   • Backup verification ensures shard integrity")
    print("   • Advanced validation provides security insights")

    return EXIT_SUCCESS
