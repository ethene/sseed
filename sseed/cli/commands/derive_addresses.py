"""Derive addresses command implementation.

Derives cryptocurrency addresses from HD wallets using BIP32/44/49/84/86.
Supports multiple cryptocurrencies and address types with flexible output formats.
"""

import argparse
import json
from typing import List

from sseed.entropy import secure_delete_variable
from sseed.logging_config import get_logger

from ..base import BaseCommand
from ..error_handling import handle_common_errors

# Define exit code locally to avoid circular import
EXIT_SUCCESS = 0

logger = get_logger(__name__)


class DeriveAddressesCommand(BaseCommand):
    """Derive cryptocurrency addresses from HD wallet mnemonic."""

    def __init__(self) -> None:
        super().__init__(
            name="derive-addresses",
            help_text="Derive cryptocurrency addresses from HD wallet mnemonic",
            description=(
                "Generate cryptocurrency addresses using hierarchical deterministic "
                "wallet derivation from BIP39 mnemonic. Supports Bitcoin (Legacy, SegWit, "
                "Native SegWit, Taproot), Ethereum, and Litecoin with batch generation "
                "and multiple output formats (plain, JSON, CSV)."
            ),
        )

    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add derive-addresses command arguments."""
        # I/O arguments using BaseCommand pattern
        self.add_common_io_arguments(parser)

        # Core derivation arguments
        parser.add_argument(
            "-c",
            "--coin",
            choices=["bitcoin", "ethereum", "litecoin"],
            default="bitcoin",
            metavar="COIN",
            help="Cryptocurrency to derive addresses for (default: bitcoin)",
        )

        parser.add_argument(
            "-n",
            "--count",
            type=int,
            default=1,
            metavar="N",
            help="Number of addresses to generate (default: 1, max: 1000)",
        )

        parser.add_argument(
            "-t",
            "--address-type",
            choices=["legacy", "segwit", "native-segwit", "taproot"],
            metavar="TYPE",
            help=(
                "Address type for Bitcoin (default: native-segwit). "
                "Ignored for other cryptocurrencies. "
                "Choices: legacy(P2PKH), segwit(P2SH-P2WPKH), "
                "native-segwit(P2WPKH), taproot(P2TR)"
            ),
        )

        # Derivation path arguments
        parser.add_argument(
            "-a",
            "--account",
            type=int,
            default=0,
            metavar="N",
            help="Account number for derivation (default: 0)",
        )

        parser.add_argument(
            "--change",
            type=int,
            choices=[0, 1],
            default=0,
            metavar="N",
            help="Change flag: 0=external addresses, 1=internal/change addresses (default: 0)",
        )

        parser.add_argument(
            "--start-index",
            type=int,
            default=0,
            metavar="N",
            help="Starting address index (default: 0)",
        )

        # Output format arguments
        parser.add_argument(
            "--format",
            choices=["plain", "json", "csv"],
            default="plain",
            metavar="FORMAT",
            help="Output format (default: plain)",
        )

        parser.add_argument(
            "--include-private-keys",
            action="store_true",
            help=(
                "Include private keys in output. "
                "WARNING: Private keys provide full access to funds. "
                "Only use with secure storage and transmission."
            ),
        )

        # Add show-entropy support for compatibility
        self.add_entropy_display_argument(parser)

    @handle_common_errors("address derivation")
    def handle(self, args: argparse.Namespace) -> int:
        """Handle the derive-addresses command."""
        logger.info("Starting HD wallet address derivation")

        # Validate arguments
        if args.count <= 0 or args.count > 1000:
            print("Error: Count must be between 1 and 1000")
            return 1

        if args.account < 0:
            print("Error: Account must be non-negative")
            return 1

        if args.start_index < 0:
            print("Error: Start index must be non-negative")
            return 1

        mnemonic = ""
        try:
            # Get mnemonic from input
            mnemonic = self.handle_input(args).strip()

            # Lazy import HD wallet module for better startup performance
            from sseed.hd_wallet import (  # pylint: disable=import-outside-toplevel
                generate_addresses,
            )

            # Generate addresses using HD wallet module
            logger.debug(
                "Generating %d %s addresses starting at index %d",
                args.count,
                args.coin,
                args.start_index,
            )

            addresses = generate_addresses(
                mnemonic=mnemonic,
                coin=args.coin,
                count=args.count,
                account=args.account,
                change=args.change,
                address_type=args.address_type,
                start_index=args.start_index,
            )

            # Format output based on requested format
            if args.format == "json":
                output = self._format_json(addresses, args.include_private_keys)
            elif args.format == "csv":
                output = self._format_csv(addresses, args.include_private_keys)
            else:  # plain
                output = self._format_plain(addresses, args.include_private_keys)

            # Add entropy display if requested
            entropy_info = self.handle_entropy_display(mnemonic, args)
            if entropy_info:
                output = f"{output}\n\n{entropy_info}"

            # Output results
            self.handle_output(
                output,
                args,
                success_message=f"Generated {len(addresses)} {args.coin} addresses to {{file}}",
            )

            logger.info("Successfully generated %d addresses", len(addresses))
            return EXIT_SUCCESS

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Address derivation failed: %s", e)
            print(f"Error: {e}")
            return 1

        finally:
            # Secure cleanup
            if mnemonic:
                secure_delete_variable(mnemonic)

    def _format_json(self, addresses: List, include_private: bool) -> str:
        """Format addresses as JSON.

        Args:
            addresses: List of AddressInfo objects.
            include_private: Whether to include private keys.

        Returns:
            JSON formatted string.
        """
        data = {
            "addresses": [
                addr.to_dict(include_private_key=include_private) for addr in addresses
            ],
            "summary": {
                "count": len(addresses),
                "coin": addresses[0].coin if addresses else None,
                "address_type": addresses[0].address_type if addresses else None,
                "network": addresses[0].network if addresses else None,
            },
        }
        return json.dumps(data, indent=2)

    def _format_csv(self, addresses: List, include_private: bool) -> str:
        """Format addresses as CSV.

        Args:
            addresses: List of AddressInfo objects.
            include_private: Whether to include private keys.

        Returns:
            CSV formatted string.
        """
        from sseed.hd_wallet import (  # pylint: disable=import-outside-toplevel
            get_csv_headers,
        )

        headers = get_csv_headers(include_private_key=include_private)
        lines = [",".join(headers)]

        for addr in addresses:
            row = addr.to_csv_row(include_private_key=include_private)
            # Escape any commas in the data
            escaped_row = [
                f'"{field}"' if "," in str(field) else str(field) for field in row
            ]
            lines.append(",".join(escaped_row))

        return "\n".join(lines)

    def _format_plain(self, addresses: List, include_private: bool) -> str:
        """Format addresses as plain text.

        Args:
            addresses: List of AddressInfo objects.
            include_private: Whether to include private keys.

        Returns:
            Plain text formatted string.
        """
        if not addresses:
            return "No addresses generated"

        lines = []
        first_addr = addresses[0]

        # Add header
        plural = "es" if len(addresses) > 1 else ""
        lines.append(
            f"Generated {len(addresses)} {first_addr.coin} "
            f"{first_addr.address_type} address{plural}:"
        )
        lines.append("")

        # Add addresses
        for addr in addresses:
            lines.append(f"{addr.index}: {addr.address}")
            if include_private:
                lines.append(f"    Private Key: {addr.private_key}")
            lines.append(f"    Derivation Path: {addr.derivation_path}")
            if len(addresses) > 1:  # Add spacing between multiple addresses
                lines.append("")

        # Remove trailing empty line
        if lines and lines[-1] == "":
            lines.pop()

        return "\n".join(lines)


# Backward compatibility handler function following SSeed pattern
def handle_derive_addresses_command(args: argparse.Namespace) -> int:
    """Backward compatibility wrapper for derive-addresses command handler."""
    return DeriveAddressesCommand().handle(args)
