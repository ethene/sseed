"""Test HD wallet CLI integration.

Tests for derive-addresses command integration following SSeed testing
patterns and conventions.
"""

import json
import subprocess
import tempfile
from pathlib import Path

import pytest

from sseed.cli.commands.derive_addresses import (
    DeriveAddressesCommand,
    handle_derive_addresses_command,
)


class TestDeriveAddressesCommand:
    """Test DeriveAddressesCommand class functionality."""

    @pytest.fixture
    def command(self):
        """Create derive-addresses command instance."""
        return DeriveAddressesCommand()

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    @pytest.fixture
    def invalid_mnemonic(self):
        """Invalid test mnemonic for error testing."""
        return "invalid mnemonic phrase"

    def test_command_initialization(self, command):
        """Test command initialization."""
        assert command.name == "derive-addresses"
        assert "cryptocurrency addresses" in command.help_text
        assert "hierarchical deterministic" in command.description

    def test_add_arguments(self, command):
        """Test argument parser setup."""
        import argparse

        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        # Test that all expected arguments are added
        args = parser.parse_args([])
        assert hasattr(args, "coin")
        assert hasattr(args, "count")
        assert hasattr(args, "address_type")
        assert hasattr(args, "account")
        assert hasattr(args, "change")
        assert hasattr(args, "start_index")
        assert hasattr(args, "format")
        assert hasattr(args, "include_private_keys")

    def test_add_arguments_defaults(self, command):
        """Test argument parser default values."""
        import argparse

        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        args = parser.parse_args([])
        assert args.coin == "bitcoin"
        assert args.count == 1
        assert args.account == 0
        assert args.change == 0
        assert args.start_index == 0
        assert args.format == "plain"
        assert args.include_private_keys is False

    def test_format_json_basic(self, command):
        """Test JSON formatting."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L123",
                public_key="03123",
                address="bc1qtest",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            )
        ]

        result = command._format_json(addresses, include_private=False)
        data = json.loads(result)

        assert "addresses" in data
        assert "summary" in data
        assert len(data["addresses"]) == 1
        assert "private_key" not in data["addresses"][0]
        assert data["summary"]["count"] == 1

    def test_format_json_with_private_keys(self, command):
        """Test JSON formatting with private keys."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L123",
                public_key="03123",
                address="bc1qtest",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            )
        ]

        result = command._format_json(addresses, include_private=True)
        data = json.loads(result)

        assert "private_key" in data["addresses"][0]
        assert data["addresses"][0]["private_key"] == "L123"

    def test_format_csv_basic(self, command):
        """Test CSV formatting."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L123",
                public_key="03123",
                address="bc1qtest",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            )
        ]

        result = command._format_csv(addresses, include_private=False)
        lines = result.split("\n")

        assert len(lines) == 2  # Header + 1 data row
        assert "Index" in lines[0]
        assert "PrivateKey" not in lines[0]
        assert "bc1qtest" in lines[1]

    def test_format_csv_with_private_keys(self, command):
        """Test CSV formatting with private keys."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L123",
                public_key="03123",
                address="bc1qtest",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            )
        ]

        result = command._format_csv(addresses, include_private=True)
        lines = result.split("\n")

        assert "PrivateKey" in lines[0]
        assert "L123" in lines[1]

    def test_format_plain_basic(self, command):
        """Test plain text formatting."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L123",
                public_key="03123",
                address="bc1qtest",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            )
        ]

        result = command._format_plain(addresses, include_private=False)

        assert "Generated 1 bitcoin native-segwit address" in result
        assert "0: bc1qtest" in result
        assert "Derivation Path: m/84'/0'/0'/0/0" in result
        assert "Private Key" not in result

    def test_format_plain_with_private_keys(self, command):
        """Test plain text formatting with private keys."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L123",
                public_key="03123",
                address="bc1qtest",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            )
        ]

        result = command._format_plain(addresses, include_private=True)

        assert "Private Key: L123" in result

    def test_format_plain_empty(self, command):
        """Test plain text formatting with empty address list."""
        result = command._format_plain([], include_private=False)
        assert result == "No addresses generated"

    def test_format_plain_multiple_addresses(self, command):
        """Test plain text formatting with multiple addresses."""
        from sseed.hd_wallet import AddressInfo

        addresses = [
            AddressInfo(
                0,
                "m/84'/0'/0'/0/0",
                "L1",
                "031",
                "bc1qtest1",
                "native-segwit",
                "bitcoin",
                "Bitcoin Mainnet",
            ),
            AddressInfo(
                1,
                "m/84'/0'/0'/0/1",
                "L2",
                "032",
                "bc1qtest2",
                "native-segwit",
                "bitcoin",
                "Bitcoin Mainnet",
            ),
        ]

        result = command._format_plain(addresses, include_private=False)

        assert "Generated 2 bitcoin native-segwit addresses" in result
        assert "0: bc1qtest1" in result
        assert "1: bc1qtest2" in result


class TestCLIIntegration:
    """Test CLI integration with subprocess calls."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    @pytest.fixture
    def invalid_mnemonic(self):
        """Invalid test mnemonic for error testing."""
        return "invalid mnemonic phrase"

    def test_cli_help_command(self):
        """Test derive-addresses help command."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "--help"],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "cryptocurrency addresses" in result.stdout
        assert "--coin" in result.stdout
        assert "--count" in result.stdout
        assert "--format" in result.stdout

    def test_cli_basic_bitcoin_derivation(self, test_mnemonic):
        """Test basic Bitcoin address derivation via CLI."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "bc1q" in result.stdout  # Native SegWit address
        assert "Derivation Path: m/84'/0'/0'/0/0" in result.stdout

    def test_cli_bitcoin_legacy_derivation(self, test_mnemonic):
        """Test Bitcoin Legacy address derivation via CLI."""
        result = subprocess.run(
            [
                "python3",
                "-m",
                "sseed",
                "derive-addresses",
                "-c",
                "bitcoin",
                "-t",
                "legacy",
            ],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert result.stdout.startswith("Generated 1 bitcoin legacy address")
        # Look for address starting with '1' anywhere in the output
        assert any(
            line.strip().endswith("1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA")
            or "1LqBGSKuX5yYUonjxT5qGfpUsXKYYWeabA" in line
            for line in result.stdout.split("\n")
        )

    def test_cli_ethereum_derivation(self, test_mnemonic):
        """Test Ethereum address derivation via CLI."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-c", "ethereum"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "0x" in result.stdout
        assert "ethereum" in result.stdout

    def test_cli_batch_derivation(self, test_mnemonic):
        """Test batch address derivation via CLI."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-c", "bitcoin", "-n", "3"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Generated 3 bitcoin" in result.stdout
        assert "0:" in result.stdout
        assert "1:" in result.stdout
        assert "2:" in result.stdout

    def test_cli_json_output(self, test_mnemonic):
        """Test JSON output format via CLI."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "--format", "json"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0

        # Parse JSON output
        data = json.loads(result.stdout)
        assert "addresses" in data
        assert "summary" in data
        assert len(data["addresses"]) == 1
        assert data["addresses"][0]["coin"] == "bitcoin"

    def test_cli_csv_output(self, test_mnemonic):
        """Test CSV output format via CLI."""
        result = subprocess.run(
            [
                "python3",
                "-m",
                "sseed",
                "derive-addresses",
                "--format",
                "csv",
                "-n",
                "2",
            ],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")

        assert len(lines) == 3  # Header + 2 data rows
        assert "Index" in lines[0]
        assert "Address" in lines[0]
        assert "bc1q" in result.stdout

    def test_cli_custom_derivation_params(self, test_mnemonic):
        """Test CLI with custom derivation parameters."""
        result = subprocess.run(
            [
                "python3",
                "-m",
                "sseed",
                "derive-addresses",
                "-c",
                "bitcoin",
                "-t",
                "native-segwit",
                "-a",
                "1",  # Account 1
                "--change",
                "1",  # Change addresses
                "--start-index",
                "5",
                "-n",
                "1",
            ],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "m/84'/0'/1'/1/5" in result.stdout

    def test_cli_file_input_output(self, test_mnemonic):
        """Test CLI with file input and output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            input_file = Path(temp_dir) / "mnemonic.txt"
            output_file = Path(temp_dir) / "addresses.json"

            # Write mnemonic to input file
            input_file.write_text(test_mnemonic)

            # Run command with file I/O
            result = subprocess.run(
                [
                    "python3",
                    "-m",
                    "sseed",
                    "derive-addresses",
                    "-i",
                    str(input_file),
                    "-o",
                    str(output_file),
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
            )

            assert result.returncode == 0
            assert output_file.exists()

            # Verify output file content
            output_data = json.loads(output_file.read_text())
            assert "addresses" in output_data

    def test_cli_error_invalid_mnemonic(self, invalid_mnemonic):
        """Test CLI error handling with invalid mnemonic."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses"],
            input=invalid_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "Address derivation failed" in result.stderr or "Error:" in result.stderr

    def test_cli_error_invalid_coin(self, test_mnemonic):
        """Test CLI error handling with invalid coin."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-c", "invalid_coin"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0

    def test_cli_error_invalid_count(self, test_mnemonic):
        """Test CLI error handling with invalid count."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-n", "0"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Count must be between 1 and 1000" in result.stdout

    def test_cli_error_invalid_account(self, test_mnemonic):
        """Test CLI error handling with invalid account."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-a", "-1"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Account must be non-negative" in result.stdout

    def test_cli_error_large_count(self, test_mnemonic):
        """Test CLI error handling with too large count."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-n", "1001"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "Count must be between 1 and 1000" in result.stdout

    def test_cli_private_keys_warning(self, test_mnemonic):
        """Test CLI private key inclusion warning."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "--include-private-keys"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Private Key:" in result.stdout

    def test_cli_show_entropy_option(self, test_mnemonic):
        """Test CLI show entropy option."""
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "--show-entropy"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        # Should include entropy information if implemented


class TestHandleDeriveAddressesCommand:
    """Test handle_derive_addresses_command function."""

    def test_handle_derive_addresses_command_basic(self):
        """Test basic command handling."""
        import argparse
        from unittest.mock import (
            MagicMock,
            patch,
        )

        # Create mock args
        args = argparse.Namespace()
        args.coin = "bitcoin"
        args.count = 1
        args.address_type = None
        args.account = 0
        args.change = 0
        args.start_index = 0
        args.format = "plain"
        args.include_private_keys = False
        args.show_entropy = False
        args.input = None
        args.output = None

        # Mock the command instance
        with patch(
            "sseed.cli.commands.derive_addresses.DeriveAddressesCommand"
        ) as mock_command_class:
            mock_command = MagicMock()
            mock_command.handle.return_value = 0
            mock_command_class.return_value = mock_command

            result = handle_derive_addresses_command(args)

            assert result == 0
            mock_command.handle.assert_called_once_with(args)


class TestCLIArgumentValidation:
    """Test CLI argument validation."""

    def test_valid_coin_choices(self):
        """Test that valid coin choices are accepted."""
        import argparse

        from sseed.cli.commands.derive_addresses import DeriveAddressesCommand

        command = DeriveAddressesCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        # Valid coins should parse successfully
        for coin in ["bitcoin", "ethereum", "litecoin"]:
            args = parser.parse_args(["-c", coin])
            assert args.coin == coin

    def test_valid_address_type_choices(self):
        """Test that valid address type choices are accepted."""
        import argparse

        from sseed.cli.commands.derive_addresses import DeriveAddressesCommand

        command = DeriveAddressesCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        # Valid address types should parse successfully
        for addr_type in ["legacy", "segwit", "native-segwit", "taproot"]:
            args = parser.parse_args(["-t", addr_type])
            assert args.address_type == addr_type

    def test_valid_format_choices(self):
        """Test that valid format choices are accepted."""
        import argparse

        from sseed.cli.commands.derive_addresses import DeriveAddressesCommand

        command = DeriveAddressesCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        # Valid formats should parse successfully
        for format_type in ["plain", "json", "csv"]:
            args = parser.parse_args(["--format", format_type])
            assert args.format == format_type

    def test_change_choices_validation(self):
        """Test change parameter validation."""
        import argparse

        from sseed.cli.commands.derive_addresses import DeriveAddressesCommand

        command = DeriveAddressesCommand()
        parser = argparse.ArgumentParser()
        command.add_arguments(parser)

        # Valid change values
        for change in [0, 1]:
            args = parser.parse_args(["--change", str(change)])
            assert args.change == change

        # Invalid change values should raise SystemExit
        with pytest.raises(SystemExit):
            parser.parse_args(["--change", "2"])


class TestCLIPerformance:
    """Test CLI performance characteristics."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    @pytest.mark.slow
    def test_cli_large_batch_performance(self, test_mnemonic):
        """Test CLI performance with large batch generation."""
        import time

        start_time = time.time()
        result = subprocess.run(
            ["python3", "-m", "sseed", "derive-addresses", "-n", "100"],
            input=test_mnemonic,
            capture_output=True,
            text=True,
        )
        end_time = time.time()

        assert result.returncode == 0
        assert "Generated 100 bitcoin" in result.stdout

        # Should complete within reasonable time (adjust as needed)
        assert end_time - start_time < 30  # 30 seconds max

        # Verify all addresses are generated
        address_count = result.stdout.count("bc1q")
        assert address_count == 100

    def test_cli_memory_usage_stability(self, test_mnemonic):
        """Test CLI memory usage stability across multiple calls."""
        # Run multiple times to check for memory leaks
        for _ in range(5):
            result = subprocess.run(
                ["python3", "-m", "sseed", "derive-addresses", "-n", "10"],
                input=test_mnemonic,
                capture_output=True,
                text=True,
            )
            assert result.returncode == 0
