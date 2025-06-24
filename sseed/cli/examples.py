"""Examples display for CLI commands.

Provides comprehensive usage examples for all sseed commands.
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
    print("   sseed gen                              # Generate to stdout")
    print("   sseed gen -o wallet.txt                # Generate to file")
    print("   sseed gen --show-entropy               # Show entropy alongside")
    print()

    print("🔗 Sharding (SLIP-39):")
    print("   sseed shard -i wallet.txt -g 3-of-5             # Basic threshold")
    print("   sseed shard -i wallet.txt -g '2:(2-of-3,3-of-5)' # Multi-group")
    print("   sseed shard -i wallet.txt --separate             # Separate files")
    print("   cat wallet.txt | sseed shard -g 2-of-3           # From stdin")
    print()

    print("🔄 Restoration:")
    print("   sseed restore shard1.txt shard2.txt shard3.txt  # From files")
    print("   sseed restore shard*.txt --show-entropy         # With entropy")
    print("   sseed restore shards/*.txt -o restored.txt      # To file")
    print()

    print("🌱 Seed Derivation:")
    print("   sseed seed -i wallet.txt                        # Basic derivation")
    print("   sseed seed -i wallet.txt -p                     # With passphrase")
    print("   sseed seed -i wallet.txt --format binary        # Binary output")
    print("   echo 'word1 word2...' | sseed seed -p           # From stdin")
    print()

    print("📋 Information:")
    print("   sseed version                          # Version info")
    print("   sseed version --json                   # JSON format")
    print("   sseed examples                         # This help")
    print()

    print("🚀 Advanced Workflows:")
    print("   # Full workflow: Generate → Shard → Restore")
    print("   sseed gen -o master.txt")
    print("   sseed shard -i master.txt -g 3-of-5 --separate")
    print("   sseed restore shard_*.txt -o recovered.txt")
    print()

    print("   # Entropy verification workflow")
    print("   sseed gen --show-entropy -o wallet.txt")
    print("   sseed restore shards/*.txt --show-entropy")
    print()

    print("   # Secure distribution")
    print("   sseed gen | sseed shard -g '2:(2-of-3,2-of-3)' --separate")
    print()

    print("   # Seed derivation with verification")
    print("   sseed gen -o mnemonic.txt")
    print("   sseed seed -i mnemonic.txt -p -o seed.hex")
    print()

    print("📚 Tips & Best Practices:")
    print("   • Use separate files (--separate) for safer shard distribution")
    print("   • Always verify with --show-entropy for critical operations")
    print("   • Store shards in different secure locations")
    print("   • Test recovery before relying on shards")
    print("   • Use passphrases for additional security layer")
    print()

    print("📖 For detailed help on any command:")
    print("   sseed <command> --help")
    print()

    return EXIT_SUCCESS
