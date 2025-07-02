"""Test HD wallet extended keys functionality.

Tests for extended key generation, validation, and formatting following
SSeed testing patterns and conventions.
"""

from unittest.mock import (
    MagicMock,
    patch,
)

import pytest

from sseed.hd_wallet import HDWalletManager
from sseed.hd_wallet.coins import get_coin_config
from sseed.hd_wallet.exceptions import ExtendedKeyError
from sseed.hd_wallet.extended_keys import (
    ExtendedKeyInfo,
    _get_key_prefix_info,
    derive_extended_keys,
    derive_extended_keys_batch,
    format_extended_key_summary,
    get_extended_key_csv_headers,
)


class TestExtendedKeyInfo:
    """Test ExtendedKeyInfo data class functionality."""

    @pytest.fixture
    def sample_extended_key_info(self):
        """Create sample ExtendedKeyInfo for testing."""
        return ExtendedKeyInfo(
            coin="bitcoin",
            address_type="native-segwit",
            account=0,
            network="Bitcoin Mainnet",
            derivation_path="m/84'/0'/0'",
            xpub="zpub6rFR7y4Q2AijBEqTUquhVz398hMatFDoTvJ6FdqSkMC51M...",
            xprv="zprvAdG4iTXWBoARxkkzgkHGGLBjyYgF9rWnGY8xzAEkXy4xfRdh...",
            fingerprint="fd13aac9",
            depth=3,
        )

    def test_extended_key_info_creation(self, sample_extended_key_info):
        """Test ExtendedKeyInfo object creation."""
        assert sample_extended_key_info.coin == "bitcoin"
        assert sample_extended_key_info.address_type == "native-segwit"
        assert sample_extended_key_info.account == 0
        assert sample_extended_key_info.xpub.startswith("zpub")
        assert sample_extended_key_info.xprv.startswith("zprv")
        assert sample_extended_key_info.depth == 3

    def test_to_dict_with_private_key(self, sample_extended_key_info):
        """Test to_dict method including private key."""
        data = sample_extended_key_info.to_dict(include_private=True)

        assert isinstance(data, dict)
        assert "xprv" in data
        assert data["xprv"] == sample_extended_key_info.xprv
        assert data["xpub"] == sample_extended_key_info.xpub
        assert data["derivation_path"] == sample_extended_key_info.derivation_path

    def test_to_dict_without_private_key(self, sample_extended_key_info):
        """Test to_dict method excluding private key."""
        data = sample_extended_key_info.to_dict(include_private=False)

        assert isinstance(data, dict)
        assert "xprv" not in data
        assert data["xpub"] == sample_extended_key_info.xpub
        assert data["derivation_path"] == sample_extended_key_info.derivation_path

    def test_str_representation(self, sample_extended_key_info):
        """Test string representation of ExtendedKeyInfo."""
        str_repr = str(sample_extended_key_info)
        assert "bitcoin" in str_repr
        assert "native-segwit" in str_repr
        assert "account 0" in str_repr
        assert sample_extended_key_info.xpub[:20] in str_repr


class TestDeriveExtendedKeys:
    """Test derive_extended_keys function."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    @pytest.fixture
    def wallet_manager(self, test_mnemonic):
        """Create wallet manager for testing."""
        return HDWalletManager(test_mnemonic, validate=True)

    @pytest.fixture
    def bitcoin_config(self):
        """Get Bitcoin configuration."""
        return get_coin_config("bitcoin")

    def test_derive_extended_keys_bitcoin_native_segwit(
        self, wallet_manager, bitcoin_config
    ):
        """Test Bitcoin Native SegWit extended key derivation."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        ext_key = derive_extended_keys(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            include_private=False,
        )

        assert ext_key.coin == "bitcoin"
        assert ext_key.address_type == "native-segwit"
        assert ext_key.account == 0
        assert ext_key.xpub.startswith("zpub")
        assert ext_key.xprv is None
        assert ext_key.derivation_path == "m/84'/0'/0'"
        assert ext_key.depth == 3

    def test_derive_extended_keys_bitcoin_legacy(self, wallet_manager, bitcoin_config):
        """Test Bitcoin Legacy extended key derivation."""
        address_config = bitcoin_config.get_address_type("legacy")

        ext_key = derive_extended_keys(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            include_private=False,
        )

        assert ext_key.address_type == "legacy"
        assert ext_key.xpub.startswith("xpub")
        assert ext_key.derivation_path == "m/44'/0'/0'"

    def test_derive_extended_keys_bitcoin_segwit(self, wallet_manager, bitcoin_config):
        """Test Bitcoin SegWit extended key derivation."""
        address_config = bitcoin_config.get_address_type("segwit")

        ext_key = derive_extended_keys(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            include_private=False,
        )

        assert ext_key.address_type == "segwit"
        assert ext_key.xpub.startswith("ypub")
        assert ext_key.derivation_path == "m/49'/0'/0'"

    def test_derive_extended_keys_with_private_key(
        self, wallet_manager, bitcoin_config
    ):
        """Test extended key derivation with private key."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        ext_key = derive_extended_keys(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            include_private=True,
        )

        assert ext_key.xpub.startswith("zpub")
        assert ext_key.xprv.startswith("zprv")

    def test_derive_extended_keys_different_account(
        self, wallet_manager, bitcoin_config
    ):
        """Test extended key derivation for different account."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        ext_key = derive_extended_keys(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=1,
            include_private=False,
        )

        assert ext_key.account == 1
        assert ext_key.derivation_path == "m/84'/0'/1'"

    def test_derive_extended_keys_unsupported_purpose(
        self, wallet_manager, bitcoin_config
    ):
        """Test extended key derivation with unsupported purpose."""
        from dataclasses import replace
        address_config = bitcoin_config.get_address_type("native-segwit")
        address_config = replace(address_config, purpose=999)  # Unsupported purpose

        with pytest.raises(ExtendedKeyError) as exc_info:
            derive_extended_keys(
                wallet_manager=wallet_manager,
                coin_config=bitcoin_config,
                address_config=address_config,
                account=0,
                include_private=False,
            )

        assert "Unsupported BIP purpose" in str(exc_info.value)

    def test_derive_extended_keys_with_invalid_config(
        self, wallet_manager, bitcoin_config
    ):
        """Test extended key derivation with invalid configuration."""
        from dataclasses import replace
        address_config = bitcoin_config.get_address_type("native-segwit")
        invalid_config = replace(address_config, purpose=123)  # Invalid purpose

        with pytest.raises(ExtendedKeyError) as exc_info:
            derive_extended_keys(
                wallet_manager=wallet_manager,
                coin_config=bitcoin_config,
                address_config=invalid_config,
                account=0,
                include_private=False,
            )

        assert "Unsupported BIP purpose" in str(exc_info.value)

    def test_derive_extended_keys_fingerprint_extraction(
        self, wallet_manager, bitcoin_config
    ):
        """Test fingerprint extraction in extended keys."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        ext_key = derive_extended_keys(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            account=0,
            include_private=False,
        )

        assert ext_key.fingerprint is not None
        assert len(ext_key.fingerprint) == 8  # 4 bytes in hex
        assert all(c in "0123456789abcdef" for c in ext_key.fingerprint.lower())


class TestDeriveExtendedKeysBatch:
    """Test derive_extended_keys_batch function."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    @pytest.fixture
    def wallet_manager(self, test_mnemonic):
        """Create wallet manager for testing."""
        return HDWalletManager(test_mnemonic, validate=True)

    @pytest.fixture
    def bitcoin_config(self):
        """Get Bitcoin configuration."""
        return get_coin_config("bitcoin")

    def test_derive_extended_keys_batch_basic(self, wallet_manager, bitcoin_config):
        """Test basic batch extended key derivation."""
        address_config = bitcoin_config.get_address_type("native-segwit")
        accounts = [0, 1, 2]

        ext_keys = derive_extended_keys_batch(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            accounts=accounts,
            include_private=False,
        )

        assert len(ext_keys) == 3
        for i, key in enumerate(ext_keys):
            assert key.account == accounts[i]
            assert key.derivation_path == f"m/84'/0'/{accounts[i]}'"
            assert key.xpub.startswith("zpub")

    def test_derive_extended_keys_batch_with_private_keys(
        self, wallet_manager, bitcoin_config
    ):
        """Test batch extended key derivation with private keys."""
        address_config = bitcoin_config.get_address_type("legacy")
        accounts = [0, 1]

        ext_keys = derive_extended_keys_batch(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            accounts=accounts,
            include_private=True,
        )

        assert len(ext_keys) == 2
        for key in ext_keys:
            assert key.xpub.startswith("xpub")
            assert key.xprv.startswith("xprv")

    def test_derive_extended_keys_batch_empty_accounts(
        self, wallet_manager, bitcoin_config
    ):
        """Test batch extended key derivation with empty accounts list."""
        address_config = bitcoin_config.get_address_type("native-segwit")

        ext_keys = derive_extended_keys_batch(
            wallet_manager=wallet_manager,
            coin_config=bitcoin_config,
            address_config=address_config,
            accounts=[],
            include_private=False,
        )

        assert len(ext_keys) == 0

    @patch("sseed.hd_wallet.extended_keys.derive_extended_keys")
    def test_derive_extended_keys_batch_single_failure(
        self, mock_derive, wallet_manager, bitcoin_config
    ):
        """Test batch extended key derivation with single key failure."""
        mock_derive.side_effect = [
            MagicMock(),  # First key succeeds
            Exception("Key derivation failed"),  # Second key fails
        ]

        address_config = bitcoin_config.get_address_type("native-segwit")

        with pytest.raises(ExtendedKeyError) as exc_info:
            derive_extended_keys_batch(
                wallet_manager=wallet_manager,
                coin_config=bitcoin_config,
                address_config=address_config,
                accounts=[0, 1],
                include_private=False,
            )

        assert "Batch extended key derivation failed at account 1" in str(
            exc_info.value
        )


class TestExtendedKeyValidation:
    """Test extended key validation functions."""

    def test_get_key_prefix_info_bitcoin_mainnet(self):
        """Test key prefix information for Bitcoin mainnet."""
        # Test various Bitcoin mainnet prefixes
        test_cases = {
            "xpub": {"network": "Bitcoin Mainnet", "purpose": "Multi-purpose public"},
            "xprv": {"network": "Bitcoin Mainnet", "purpose": "Multi-purpose private"},
            "ypub": {
                "network": "Bitcoin Mainnet",
                "purpose": "P2SH-SegWit public (BIP49)",
            },
            "yprv": {
                "network": "Bitcoin Mainnet",
                "purpose": "P2SH-SegWit private (BIP49)",
            },
            "zpub": {
                "network": "Bitcoin Mainnet",
                "purpose": "Native SegWit public (BIP84)",
            },
            "zprv": {
                "network": "Bitcoin Mainnet",
                "purpose": "Native SegWit private (BIP84)",
            },
        }

        for prefix, expected in test_cases.items():
            result = _get_key_prefix_info(prefix)
            assert result["network"] == expected["network"]
            assert result["purpose"] == expected["purpose"]

    def test_get_key_prefix_info_bitcoin_testnet(self):
        """Test key prefix information for Bitcoin testnet."""
        test_cases = {
            "tpub": {"network": "Bitcoin Testnet", "purpose": "Multi-purpose public"},
            "tprv": {"network": "Bitcoin Testnet", "purpose": "Multi-purpose private"},
            "upub": {
                "network": "Bitcoin Testnet",
                "purpose": "P2SH-SegWit public (BIP49)",
            },
            "uprv": {
                "network": "Bitcoin Testnet",
                "purpose": "P2SH-SegWit private (BIP49)",
            },
            "vpub": {
                "network": "Bitcoin Testnet",
                "purpose": "Native SegWit public (BIP84)",
            },
            "vprv": {
                "network": "Bitcoin Testnet",
                "purpose": "Native SegWit private (BIP84)",
            },
        }

        for prefix, expected in test_cases.items():
            result = _get_key_prefix_info(prefix)
            assert result["network"] == expected["network"]
            assert result["purpose"] == expected["purpose"]

    def test_get_key_prefix_info_unknown(self):
        """Test key prefix information for unknown prefix."""
        result = _get_key_prefix_info("unknown")
        assert result["network"] == "unknown"
        assert result["purpose"] == "unknown"


class TestExtendedKeyFormatting:
    """Test extended key formatting functions."""

    @pytest.fixture
    def sample_extended_keys(self):
        """Create sample extended keys for testing."""
        return [
            ExtendedKeyInfo(
                coin="bitcoin",
                address_type="native-segwit",
                account=0,
                network="Bitcoin Mainnet",
                derivation_path="m/84'/0'/0'",
                xpub="zpub6rFR7y4Q2AijBEqTUquhVz398hMatFDoTvJ6FdqSkMC51M...",
                fingerprint="fd13aac9",
                depth=3,
            ),
            ExtendedKeyInfo(
                coin="bitcoin",
                address_type="legacy",
                account=0,
                network="Bitcoin Mainnet",
                derivation_path="m/44'/0'/0'",
                xpub="xpub6BosfCnifzxcFwrSzQiQVxdRd6q4cC9Ay37UqSiLGAkzHkRSfwcQZp...",
                fingerprint="fd13aac9",
                depth=3,
            ),
        ]

    def test_get_extended_key_csv_headers_without_private_key(self):
        """Test CSV headers for extended keys without private key."""
        headers = get_extended_key_csv_headers(include_private=False)

        assert "Coin" in headers
        assert "AddressType" in headers
        assert "Account" in headers
        assert "Xpub" in headers
        assert "Xprv" not in headers
        assert "Fingerprint" in headers
        assert "Depth" in headers

    def test_get_extended_key_csv_headers_with_private_key(self):
        """Test CSV headers for extended keys with private key."""
        headers = get_extended_key_csv_headers(include_private=True)

        assert "Coin" in headers
        assert "Xpub" in headers
        assert "Xprv" in headers
        assert "Fingerprint" in headers

    def test_format_extended_key_summary_empty(self):
        """Test formatting summary with empty extended key list."""
        summary = format_extended_key_summary([])
        assert summary == "No extended keys generated"

    def test_format_extended_key_summary_single_type(self, sample_extended_keys):
        """Test formatting summary with mixed extended key types."""
        summary = format_extended_key_summary(sample_extended_keys)

        assert "Bitcoin" in summary
        assert "extended key" in summary

    def test_format_extended_key_summary_single_key(self):
        """Test formatting summary with single extended key."""
        ext_keys = [
            ExtendedKeyInfo(
                coin="bitcoin",
                address_type="native-segwit",
                account=0,
                network="Bitcoin Mainnet",
                derivation_path="m/84'/0'/0'",
                xpub="zpub...",
                fingerprint="fd13aac9",
                depth=3,
            )
        ]

        summary = format_extended_key_summary(ext_keys)
        assert "1 Bitcoin Native Segwit extended key" in summary

    def test_format_extended_key_summary_multiple_same_type(self):
        """Test formatting summary with multiple keys of same type."""
        ext_keys = [
            ExtendedKeyInfo(
                "bitcoin",
                "native-segwit",
                0,
                "Bitcoin Mainnet",
                "m/84'/0'/0'",
                "zpub1",
                fingerprint="fd13aac9",
            ),
            ExtendedKeyInfo(
                "bitcoin",
                "native-segwit",
                1,
                "Bitcoin Mainnet",
                "m/84'/0'/1'",
                "zpub2",
                fingerprint="fd13aac9",
            ),
            ExtendedKeyInfo(
                "bitcoin",
                "native-segwit",
                2,
                "Bitcoin Mainnet",
                "m/84'/0'/2'",
                "zpub3",
                fingerprint="fd13aac9",
            ),
        ]

        summary = format_extended_key_summary(ext_keys)
        assert "3 Bitcoin Native Segwit extended keys" in summary


class TestExtendedKeyIntegration:
    """Integration tests for extended key functionality."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    def test_extended_keys_with_wallet_manager_integration(self, test_mnemonic):
        """Test extended keys integration with HDWalletManager."""
        manager = HDWalletManager(test_mnemonic)

        try:
            # Test single extended key
            ext_key = manager.get_extended_keys("bitcoin", address_type="native-segwit")
            assert ext_key.xpub.startswith("zpub")

            # Test batch extended keys
            batch_keys = manager.get_extended_keys_batch(
                "bitcoin", accounts=[0, 1], address_type="legacy"
            )
            assert len(batch_keys) == 2
            assert all(key.xpub.startswith("xpub") for key in batch_keys)

        finally:
            manager._secure_cleanup()

    def test_extended_keys_all_bitcoin_address_types(self, test_mnemonic):
        """Test extended keys for all Bitcoin address types."""
        manager = HDWalletManager(test_mnemonic)

        expected_prefixes = {
            "legacy": "xpub",
            "segwit": "ypub",
            "native-segwit": "zpub",
        }

        try:
            for addr_type, prefix in expected_prefixes.items():
                ext_key = manager.get_extended_keys("bitcoin", address_type=addr_type)
                assert ext_key.xpub.startswith(prefix)
                assert ext_key.address_type == addr_type.replace(" ", "-")

        finally:
            manager._secure_cleanup()

    def test_extended_keys_multiple_accounts_consistency(self, test_mnemonic):
        """Test extended key consistency across multiple accounts."""
        manager = HDWalletManager(test_mnemonic)

        try:
            accounts = [0, 1, 2, 3, 4]
            ext_keys = manager.get_extended_keys_batch(
                "bitcoin", accounts=accounts, address_type="native-segwit"
            )

            # Verify account progression
            for i, key in enumerate(ext_keys):
                assert key.account == accounts[i]
                assert f"/{accounts[i]}'" in key.derivation_path

            # Verify uniqueness
            xpub_set = set(key.xpub for key in ext_keys)
            assert len(xpub_set) == len(ext_keys)  # All unique

        finally:
            manager._secure_cleanup()

    def test_extended_keys_fingerprint_consistency(self, test_mnemonic):
        """Test fingerprint consistency across different derivations from same master."""
        manager = HDWalletManager(test_mnemonic)

        try:
            # Get extended keys for different address types
            legacy_key = manager.get_extended_keys("bitcoin", address_type="legacy")
            segwit_key = manager.get_extended_keys(
                "bitcoin", address_type="native-segwit"
            )

            # Both should have valid fingerprints (8 hex characters)
            assert len(legacy_key.fingerprint) == 8
            assert len(segwit_key.fingerprint) == 8
            assert all(c in "0123456789abcdef" for c in legacy_key.fingerprint)
            assert all(c in "0123456789abcdef" for c in segwit_key.fingerprint)
            # Different derivation paths will have different fingerprints
            assert legacy_key.fingerprint != segwit_key.fingerprint

        finally:
            manager._secure_cleanup()

    def test_extended_keys_with_private_keys_security(self, test_mnemonic):
        """Test extended key generation with private keys and security."""
        manager = HDWalletManager(test_mnemonic)

        try:
            # Test with private keys
            ext_key_priv = manager.get_extended_keys(
                "bitcoin", address_type="native-segwit", include_private=True
            )

            assert ext_key_priv.xpub.startswith("zpub")
            assert ext_key_priv.xprv.startswith("zprv")

            # Test without private keys
            ext_key_pub = manager.get_extended_keys(
                "bitcoin", address_type="native-segwit", include_private=False
            )

            assert ext_key_pub.xpub == ext_key_priv.xpub  # Same public key
            assert ext_key_pub.xprv is None  # No private key

        finally:
            manager._secure_cleanup()
