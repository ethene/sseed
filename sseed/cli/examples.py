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

    print("🌱 Seed Derivation with Language Detection:")
    print("   sseed seed -i wallet.txt                        # Auto-detects English")
    print(
        "   sseed seed -i spanish.txt -p                    # Spanish with passphrase"
    )
    print("   sseed seed -i chinese.txt --format binary       # Chinese binary output")
    print("   echo 'palabra1 palabra2...' | sseed seed -p     # Spanish from stdin")
    print()

    print("📋 Information:")
    print("   sseed version                          # Version info")
    print("   sseed version --json                   # JSON format")
    print("   sseed examples                         # This help")
    print()

    print("🚀 Advanced Multi-Language Workflows:")
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

    print("📚 Tips & Best Practices:")
    print("   • Use separate files (--separate) for safer shard distribution")
    print("   • Always verify with --show-entropy for critical operations")
    print("   • Store shards in different secure locations")
    print("   • Test recovery before relying on shards")
    print("   • Use passphrases for additional security layer")
    print("   • Language is auto-detected for restore/shard/seed operations")
    print("   • Generated files include language information as comments")
    print("   • All 9 BIP-39 languages are fully supported")
    print()

    print("📖 For detailed help on any command:")
    print("   sseed <command> --help")
    print()

    return EXIT_SUCCESS
