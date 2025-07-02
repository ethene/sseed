"""Test HD wallet address generation functionality.

Tests for address generation, formatting, and validation following
SSeed testing patterns and conventions.
"""

from unittest.mock import patch

import pytest

from sseed.hd_wallet.addresses import (
    AddressInfo,
    _basic_address_format_check,
    _validate_address_format,
    derive_address_batch,
    format_address_summary,
    generate_address,
    get_csv_headers,
    validate_address_info_list,
)
from sseed.hd_wallet.coins import get_coin_config
from sseed.hd_wallet.exceptions import AddressGenerationError


class TestAddressInfo:
    """Test AddressInfo data class functionality."""

    @pytest.fixture
    def sample_address_info(self):
        """Create sample AddressInfo for testing."""
        return AddressInfo(
            index=0,
            derivation_path="m/84'/0'/0'/0/0",
            private_key="L3RrLXWvjsSsP9xzUhyYa9hWdBTTEFSSQFjmCwbVczqJdXBv7Mhm",
            public_key="0330d54fd0dd420a6e5f8d3624f5f3482cae350f79d5f0753bf5beef9c2d91af3c",
            address="bc1qcr8te4kr609gcawutmrza0j4xv80jy8z306fyu",
            address_type="native-segwit",
            coin="bitcoin",
            network="Bitcoin Mainnet",
        )

    def test_address_info_creation(self, sample_address_info):
        """Test AddressInfo object creation."""
        assert sample_address_info.index == 0
        assert sample_address_info.coin == "bitcoin"
        assert sample_address_info.address_type == "native-segwit"
        assert sample_address_info.address.startswith("bc1q")

    def test_to_dict_with_private_key(self, sample_address_info):
        """Test to_dict method including private key."""
        data = sample_address_info.to_dict(include_private_key=True)

        assert isinstance(data, dict)
        assert "private_key" in data
        assert data["private_key"] == sample_address_info.private_key
        assert data["address"] == sample_address_info.address
        assert data["derivation_path"] == sample_address_info.derivation_path

    def test_to_dict_without_private_key(self, sample_address_info):
        """Test to_dict method excluding private key."""
        data = sample_address_info.to_dict(include_private_key=False)

        assert isinstance(data, dict)
        assert "private_key" not in data
        assert data["address"] == sample_address_info.address
        assert data["derivation_path"] == sample_address_info.derivation_path

    def test_to_csv_row_with_private_key(self, sample_address_info):
        """Test to_csv_row method including private key."""
        row = sample_address_info.to_csv_row(include_private_key=True)

        assert isinstance(row, list)
        assert len(row) == 8  # All fields including private key
        assert sample_address_info.private_key in row
        assert sample_address_info.address in row

    def test_to_csv_row_without_private_key(self, sample_address_info):
        """Test to_csv_row method excluding private key."""
        row = sample_address_info.to_csv_row(include_private_key=False)

        assert isinstance(row, list)
        assert len(row) == 7  # All fields except private key
        assert sample_address_info.private_key not in row
        assert sample_address_info.address in row

    def test_str_representation(self, sample_address_info):
        """Test string representation of AddressInfo."""
        str_repr = str(sample_address_info)
        assert "bitcoin" in str_repr
        assert "native-segwit" in str_repr
        assert "0" in str_repr  # index
        assert sample_address_info.address in str_repr


class TestGenerateAddress:
    """Test generate_address function."""

    @pytest.fixture
    def test_master_seed(self):
        """Create test master seed."""
        return bytes.fromhex("a" * 128)  # 64 bytes

    @pytest.fixture
    def bitcoin_config(self):
        """Get Bitcoin configuration."""
        return get_coin_config("bitcoin")

    @pytest.fixture
    def ethereum_config(self):
        """Get Ethereum configuration."""
        return get_coin_config("ethereum")

    def test_generate_bitcoin_native_segwit_address(
        self, test_master_seed, bitcoin_config
    ):
        """Test Bitcoin Native SegWit address generation."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        address_info = generate_address(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            derivation_path="m/84'/0'/0'/0/0",
            index=0,
            account=0,
            change=0,
        )

        assert address_info.index == 0
        assert address_info.coin == "bitcoin"
        assert address_info.address_type == "native-segwit"
        assert address_info.address.startswith("bc1q")
        assert address_info.derivation_path == "m/84'/0'/0'/0/0"

    def test_generate_bitcoin_legacy_address(self, test_master_seed, bitcoin_config):
        """Test Bitcoin Legacy address generation."""
        address_config = bitcoin_config.get_address_type("legacy")

        address_info = generate_address(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            derivation_path="m/44'/0'/0'/0/0",
            index=0,
            account=0,
            change=0,
        )

        assert address_info.address.startswith("1")
        assert address_info.address_type == "legacy"

    def test_generate_bitcoin_segwit_address(self, test_master_seed, bitcoin_config):
        """Test Bitcoin SegWit address generation."""
        address_config = bitcoin_config.get_address_type("segwit")

        address_info = generate_address(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            derivation_path="m/49'/0'/0'/0/0",
            index=0,
            account=0,
            change=0,
        )

        assert address_info.address.startswith("3")
        assert address_info.address_type == "segwit"

    def test_generate_ethereum_address(self, test_master_seed, ethereum_config):
        """Test Ethereum address generation."""
        address_config = ethereum_config.get_address_type()  # Default

        address_info = generate_address(
            master_seed=test_master_seed,
            coin_config=ethereum_config,
            address_config=address_config,
            derivation_path="m/44'/60'/0'/0/0",
            index=0,
            account=0,
            change=0,
        )

        assert address_info.coin == "ethereum"
        assert address_info.address.startswith("0x")
        assert len(address_info.address) == 42

    def test_generate_address_with_custom_index(self, test_master_seed, bitcoin_config):
        """Test address generation with custom index."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        address_info = generate_address(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            derivation_path="m/84'/0'/0'/0/5",
            index=5,
            account=0,
            change=0,
        )

        assert address_info.index == 5
        assert "0/5" in address_info.derivation_path

    def test_generate_address_unsupported_purpose(
        self, test_master_seed, bitcoin_config
    ):
        """Test address generation with unsupported BIP purpose."""
        # Create a fake address config with unsupported purpose
        from dataclasses import replace

        address_config = bitcoin_config.get_address_type("native-segwit")
        address_config = replace(address_config, purpose=999)  # Unsupported purpose

        with pytest.raises(AddressGenerationError) as exc_info:
            generate_address(
                master_seed=test_master_seed,
                coin_config=bitcoin_config,
                address_config=address_config,
                derivation_path="m/999'/0'/0'/0/0",
                index=0,
                account=0,
                change=0,
            )

        assert "Unsupported BIP purpose" in str(exc_info.value)

    @patch("bip_utils.Bip84")
    def test_generate_address_bip_context_error(
        self, mock_bip84, test_master_seed, bitcoin_config
    ):
        """Test address generation with BIP context error."""
        mock_bip84.FromSeed.side_effect = Exception("BIP context error")

        address_config = bitcoin_config.get_address_type("native-segwit")

        with pytest.raises(AddressGenerationError) as exc_info:
            generate_address(
                master_seed=test_master_seed,
                coin_config=bitcoin_config,
                address_config=address_config,
                derivation_path="m/84'/0'/0'/0/0",
                index=0,
                account=0,
                change=0,
            )

        assert "BIP context error" in str(exc_info.value)


class TestDeriveAddressBatch:
    """Test derive_address_batch function."""

    @pytest.fixture
    def test_master_seed(self):
        """Create test master seed."""
        return bytes.fromhex("a" * 128)  # 64 bytes

    @pytest.fixture
    def bitcoin_config(self):
        """Get Bitcoin configuration."""
        return get_coin_config("bitcoin")

    def test_derive_address_batch_basic(self, test_master_seed, bitcoin_config):
        """Test basic batch address derivation."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        addresses = derive_address_batch(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            change=0,
            start_index=0,
            count=3,
        )

        assert len(addresses) == 3
        for i, addr in enumerate(addresses):
            assert addr.index == i
            assert addr.coin == "bitcoin"
            assert addr.address.startswith("bc1q")

    def test_derive_address_batch_with_start_index(
        self, test_master_seed, bitcoin_config
    ):
        """Test batch derivation with custom start index."""
        address_config = bitcoin_config.get_address_type("legacy")

        addresses = derive_address_batch(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            change=0,
            start_index=10,
            count=2,
        )

        assert len(addresses) == 2
        assert addresses[0].index == 10
        assert addresses[1].index == 11
        for addr in addresses:
            assert addr.address.startswith("1")

    def test_derive_address_batch_change_addresses(
        self, test_master_seed, bitcoin_config
    ):
        """Test batch derivation for change addresses."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        addresses = derive_address_batch(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            change=1,  # Change addresses
            start_index=0,
            count=2,
        )

        assert len(addresses) == 2
        for addr in addresses:
            assert "/1/" in addr.derivation_path  # Change = 1

    def test_derive_address_batch_different_account(
        self, test_master_seed, bitcoin_config
    ):
        """Test batch derivation for different account."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        addresses = derive_address_batch(
            master_seed=test_master_seed,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=1,  # Account 1
            change=0,
            start_index=0,
            count=1,
        )

        assert len(addresses) == 1
        assert "'/1'/" in addresses[0].derivation_path  # Account = 1

    @patch("sseed.hd_wallet.addresses.generate_address")
    def test_derive_address_batch_generation_error(
        self, mock_generate, test_master_seed, bitcoin_config
    ):
        """Test batch derivation with address generation error."""
        mock_generate.side_effect = Exception("Generation failed")

        address_config = bitcoin_config.get_address_type("native-segwit")

        with pytest.raises(AddressGenerationError) as exc_info:
            derive_address_batch(
                master_seed=test_master_seed,
                coin_config=bitcoin_config,
                address_config=address_config,
                count=1,
            )

        assert "Batch generation failed at index 0" in str(exc_info.value)


class TestAddressFormatting:
    """Test address formatting and utility functions."""

    @pytest.fixture
    def sample_addresses(self):
        """Create sample addresses for testing."""
        return [
            AddressInfo(
                index=0,
                derivation_path="m/84'/0'/0'/0/0",
                private_key="L1...",
                public_key="03...",
                address="bc1qtest1",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            ),
            AddressInfo(
                index=1,
                derivation_path="m/84'/0'/0'/0/1",
                private_key="L2...",
                public_key="03...",
                address="bc1qtest2",
                address_type="native-segwit",
                coin="bitcoin",
                network="Bitcoin Mainnet",
            ),
        ]

    def test_get_csv_headers_with_private_key(self):
        """Test CSV headers including private key."""
        headers = get_csv_headers(include_private_key=True)

        assert "Index" in headers
        assert "PrivateKey" in headers
        assert "Address" in headers
        assert "DerivationPath" in headers

    def test_get_csv_headers_without_private_key(self):
        """Test CSV headers excluding private key."""
        headers = get_csv_headers(include_private_key=False)

        assert "Index" in headers
        assert "PrivateKey" not in headers
        assert "Address" in headers
        assert "DerivationPath" in headers

    def test_format_address_summary_empty(self):
        """Test formatting summary with empty address list."""
        summary = format_address_summary([])
        assert summary == "No addresses generated"

    def test_format_address_summary_single_type(self, sample_addresses):
        """Test formatting summary with single address type."""
        summary = format_address_summary(sample_addresses)

        assert "2 Bitcoin Native Segwit addresses" in summary
        assert "bc1qtest1" in summary
        assert "bc1qtest2" in summary

    def test_format_address_summary_mixed_types(self):
        """Test formatting summary with mixed address types."""
        addresses = [
            AddressInfo(
                0,
                "m/44'/0'/0'/0/0",
                "L1",
                "03",
                "1test1",
                "legacy",
                "bitcoin",
                "Bitcoin Mainnet",
            ),
            AddressInfo(
                1,
                "m/84'/0'/0'/0/0",
                "L2",
                "03",
                "bc1qtest1",
                "native-segwit",
                "bitcoin",
                "Bitcoin Mainnet",
            ),
            AddressInfo(
                0,
                "m/44'/60'/0'/0/0",
                "L3",
                "03",
                "0xtest1",
                "standard",
                "ethereum",
                "Ethereum Mainnet",
            ),
        ]

        summary = format_address_summary(addresses)

        assert "1 Bitcoin Legacy address" in summary
        assert "1 Bitcoin Native Segwit address" in summary
        assert "1 Ethereum Standard address" in summary

    def test_validate_address_info_list_valid(self, sample_addresses):
        """Test validation of valid address list."""
        result = validate_address_info_list(sample_addresses)

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["stats"]["total_addresses"] == 2
        assert result["stats"]["unique_addresses"] == 2

    def test_validate_address_info_list_empty(self):
        """Test validation of empty address list."""
        result = validate_address_info_list([])

        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert result["stats"] == {}

    def test_validate_address_info_list_duplicates(self):
        """Test validation with duplicate addresses."""
        addresses = [
            AddressInfo(
                0,
                "m/84'/0'/0'/0/0",
                "L1",
                "03",
                "bc1qtest",
                "native-segwit",
                "bitcoin",
                "Bitcoin Mainnet",
            ),
            AddressInfo(
                1,
                "m/84'/0'/0'/0/1",
                "L1",
                "03",
                "bc1qtest",
                "native-segwit",
                "bitcoin",
                "Bitcoin Mainnet",
            ),  # Duplicate address and private key
        ]

        result = validate_address_info_list(addresses)

        assert result["valid"] is False
        assert any("Duplicate address" in error for error in result["errors"])
        assert any("Duplicate private key" in error for error in result["errors"])

    def test_validate_address_info_list_missing_fields(self):
        """Test validation with missing required fields."""
        addresses = [
            AddressInfo(
                0, "", "", "", "", "native-segwit", "bitcoin", "Bitcoin Mainnet"
            ),  # Missing fields
        ]

        result = validate_address_info_list(addresses)

        assert result["valid"] is False
        assert any("Missing address" in error for error in result["errors"])
        assert any("Missing derivation path" in error for error in result["errors"])
        assert any("Missing private key" in error for error in result["errors"])


class TestAddressValidation:
    """Test address format validation functions."""

    def test_validate_address_format_bitcoin_legacy(self):
        """Test Bitcoin Legacy address format validation."""
        from sseed.hd_wallet.coins import get_coin_config

        bitcoin_config = get_coin_config("bitcoin")
        legacy_config = bitcoin_config.get_address_type("legacy")

        # Valid Legacy address
        assert (
            _validate_address_format(
                "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", bitcoin_config, legacy_config
            )
            is True
        )

        # Invalid Legacy address (wrong prefix)
        assert (
            _validate_address_format(
                "3A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", bitcoin_config, legacy_config
            )
            is False
        )

    def test_validate_address_format_bitcoin_native_segwit(self):
        """Test Bitcoin Native SegWit address format validation."""
        from sseed.hd_wallet.coins import get_coin_config

        bitcoin_config = get_coin_config("bitcoin")
        segwit_config = bitcoin_config.get_address_type("native-segwit")

        # Valid Native SegWit address
        assert (
            _validate_address_format(
                "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4",
                bitcoin_config,
                segwit_config,
            )
            is True
        )

        # Invalid Native SegWit address (wrong prefix)
        assert (
            _validate_address_format(
                "1w508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", bitcoin_config, segwit_config
            )
            is False
        )

    def test_validate_address_format_ethereum(self):
        """Test Ethereum address format validation."""
        from sseed.hd_wallet.coins import get_coin_config

        ethereum_config = get_coin_config("ethereum")
        eth_address_config = ethereum_config.get_address_type()

        # Valid Ethereum address
        assert (
            _validate_address_format(
                "0x1234567890123456789012345678901234567890",
                ethereum_config,
                eth_address_config,
            )
            is True
        )

        # Invalid Ethereum address (wrong length)
        assert (
            _validate_address_format(
                "0x123456789012345678901234567890123456789",
                ethereum_config,
                eth_address_config,
            )
            is False
        )

        # Invalid Ethereum address (no 0x prefix)
        assert (
            _validate_address_format(
                "1234567890123456789012345678901234567890",
                ethereum_config,
                eth_address_config,
            )
            is False
        )

    def test_basic_address_format_check_bitcoin(self):
        """Test basic Bitcoin address format checking."""
        # Valid Bitcoin addresses
        assert (
            _basic_address_format_check("1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "bitcoin")
            is True
        )
        assert (
            _basic_address_format_check("3J98t1WpEZ73CNmQviecrnyiWrnqRhWNLy", "bitcoin")
            is True
        )
        assert (
            _basic_address_format_check(
                "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4", "bitcoin"
            )
            is True
        )

        # Invalid Bitcoin addresses
        assert _basic_address_format_check("", "bitcoin") is False
        assert _basic_address_format_check("invalid", "bitcoin") is False
        assert _basic_address_format_check("x" * 100, "bitcoin") is False

    def test_basic_address_format_check_ethereum(self):
        """Test basic Ethereum address format checking."""
        # Valid Ethereum address
        assert (
            _basic_address_format_check(
                "0x1234567890123456789012345678901234567890", "ethereum"
            )
            is True
        )

        # Invalid Ethereum addresses
        assert (
            _basic_address_format_check(
                "1234567890123456789012345678901234567890", "ethereum"
            )
            is False
        )
        assert (
            _basic_address_format_check(
                "0x123456789012345678901234567890123456789", "ethereum"
            )
            is False
        )
        assert _basic_address_format_check("", "ethereum") is False

    def test_basic_address_format_check_unknown_coin(self):
        """Test basic address format checking for unknown coin."""
        # Unknown coin should return True (assume valid)
        assert _basic_address_format_check("any_address", "unknown_coin") is True
