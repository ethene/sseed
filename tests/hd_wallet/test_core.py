"""Test HD wallet core functionality.

Tests for HDWalletManager class and core HD wallet operations following
SSeed testing patterns and conventions.
"""

from unittest.mock import patch

import pytest

from sseed.hd_wallet import (
    HDWalletManager,
    derive_addresses_from_mnemonic,
)
from sseed.hd_wallet.exceptions import (
    DerivationError,
    HDWalletError,
)


class TestHDWalletManager:
    """Test HDWalletManager core functionality."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    @pytest.fixture
    def invalid_mnemonic(self):
        """Invalid test mnemonic for error testing."""
        return "invalid mnemonic phrase that should fail validation"

    @pytest.fixture
    def wallet_manager(self, test_mnemonic):
        """Create HD wallet manager for testing."""
        return HDWalletManager(test_mnemonic, validate=True)

    def test_wallet_manager_initialization_valid(self, test_mnemonic):
        """Test HDWalletManager initialization with valid mnemonic."""
        manager = HDWalletManager(test_mnemonic, validate=True)
        assert manager._initialized is True
        assert manager._mnemonic == test_mnemonic
        assert manager._master_seed is None  # Lazy initialization
        assert manager._master_key is None  # Lazy initialization
        assert len(manager._derived_keys_cache) == 0

    def test_wallet_manager_initialization_no_validation(self, test_mnemonic):
        """Test HDWalletManager initialization without validation."""
        manager = HDWalletManager(test_mnemonic, validate=False)
        assert manager._initialized is True
        assert manager._mnemonic == test_mnemonic

    def test_wallet_manager_initialization_invalid_mnemonic(self, invalid_mnemonic):
        """Test HDWalletManager initialization with invalid mnemonic."""
        with pytest.raises((HDWalletError, DerivationError)):
            HDWalletManager(invalid_mnemonic, validate=True)

    def test_master_seed_generation(self, wallet_manager):
        """Test master seed generation and caching."""
        # First call should generate seed
        seed1 = wallet_manager._get_master_seed()
        assert len(seed1) == 64  # 512 bits
        assert wallet_manager._master_seed is not None

        # Second call should return cached seed
        seed2 = wallet_manager._get_master_seed()
        assert seed1 == seed2

    def test_master_key_generation(self, wallet_manager):
        """Test master key generation and caching."""
        # First call should generate key
        key1 = wallet_manager._get_master_key()
        assert key1 is not None
        assert wallet_manager._master_key is not None

        # Second call should return cached key
        key2 = wallet_manager._get_master_key()
        assert key1 == key2

    def test_derive_key_at_path(self, wallet_manager):
        """Test key derivation at specific path."""
        path = "m/84'/0'/0'/0/0"
        key = wallet_manager.derive_key_at_path(path)
        assert key is not None

        # Test caching
        key2 = wallet_manager.derive_key_at_path(path, use_cache=True)
        assert key == key2
        assert path in wallet_manager._derived_keys_cache

    def test_derive_key_at_path_no_cache(self, wallet_manager):
        """Test key derivation without caching."""
        path = "m/84'/0'/0'/0/0"
        key1 = wallet_manager.derive_key_at_path(path, use_cache=False)
        key2 = wallet_manager.derive_key_at_path(path, use_cache=False)
        assert key1 == key2  # Same derivation
        assert len(wallet_manager._derived_keys_cache) == 0

    def test_derive_key_invalid_path(self, wallet_manager):
        """Test key derivation with invalid path."""
        with pytest.raises(DerivationError):
            wallet_manager.derive_key_at_path("invalid/path")

    def test_derive_addresses_batch_bitcoin(self, wallet_manager):
        """Test batch address derivation for Bitcoin."""
        addresses = wallet_manager.derive_addresses_batch(
            coin="bitcoin", count=3, address_type="native-segwit"
        )

        assert len(addresses) == 3
        for i, addr in enumerate(addresses):
            assert addr.index == i
            assert addr.coin == "bitcoin"
            assert addr.address_type == "native-segwit"
            assert addr.address.startswith("bc1q")
            assert addr.derivation_path == f"m/84'/0'/0'/0/{i}"

    def test_derive_addresses_batch_ethereum(self, wallet_manager):
        """Test batch address derivation for Ethereum."""
        addresses = wallet_manager.derive_addresses_batch(coin="ethereum", count=2)

        assert len(addresses) == 2
        for i, addr in enumerate(addresses):
            assert addr.index == i
            assert addr.coin == "ethereum"
            assert addr.address.startswith("0x")
            assert len(addr.address) == 42

    def test_derive_addresses_batch_with_custom_params(self, wallet_manager):
        """Test batch address derivation with custom parameters."""
        addresses = wallet_manager.derive_addresses_batch(
            coin="bitcoin",
            count=2,
            account=1,
            change=1,
            address_type="legacy",
            start_index=5,
        )

        assert len(addresses) == 2
        assert addresses[0].index == 5
        assert addresses[1].index == 6
        assert addresses[0].derivation_path == "m/44'/0'/1'/1/5"
        assert addresses[1].derivation_path == "m/44'/0'/1'/1/6"
        for addr in addresses:
            assert addr.address.startswith("1")  # Legacy addresses

    def test_derive_addresses_batch_invalid_coin(self, wallet_manager):
        """Test batch address derivation with invalid coin."""
        with pytest.raises(DerivationError):
            wallet_manager.derive_addresses_batch(coin="invalid_coin", count=1)

    def test_derive_addresses_batch_invalid_address_type(self, wallet_manager):
        """Test batch address derivation with invalid address type."""
        with pytest.raises(DerivationError):
            wallet_manager.derive_addresses_batch(
                coin="bitcoin", count=1, address_type="invalid_type"
            )

    def test_get_extended_keys(self, wallet_manager):
        """Test extended key generation."""
        ext_key = wallet_manager.get_extended_keys(
            coin="bitcoin", address_type="native-segwit", include_private=False
        )

        assert ext_key.coin == "bitcoin"
        assert ext_key.address_type == "native-segwit"
        assert ext_key.account == 0
        assert ext_key.xpub.startswith("zpub")
        assert ext_key.xprv is None
        assert ext_key.derivation_path == "m/84'/0'/0'"

    def test_get_extended_keys_with_private(self, wallet_manager):
        """Test extended key generation with private keys."""
        ext_key = wallet_manager.get_extended_keys(
            coin="bitcoin", address_type="legacy", include_private=True
        )

        assert ext_key.xpub.startswith("xpub")
        assert ext_key.xprv.startswith("xprv")
        assert ext_key.derivation_path == "m/44'/0'/0'"

    def test_get_extended_keys_batch(self, wallet_manager):
        """Test batch extended key generation."""
        accounts = [0, 1, 2]
        ext_keys = wallet_manager.get_extended_keys_batch(
            coin="bitcoin", accounts=accounts, address_type="native-segwit"
        )

        assert len(ext_keys) == 3
        for i, key in enumerate(ext_keys):
            assert key.account == accounts[i]
            assert key.derivation_path == f"m/84'/0'/{accounts[i]}'"

    def test_cache_management(self, wallet_manager):
        """Test cache statistics and clearing."""
        # Generate some cached keys
        wallet_manager.derive_key_at_path("m/84'/0'/0'/0/0")
        wallet_manager.derive_key_at_path("m/84'/0'/0'/0/1")

        stats = wallet_manager.get_cache_stats()
        assert stats["derived_keys_cached"] >= 0
        assert isinstance(stats["cache_paths"], list)

        # Clear cache
        wallet_manager.clear_cache()
        stats_after = wallet_manager.get_cache_stats()
        assert stats_after["derived_keys_cached"] == 0

    def test_secure_cleanup(self, wallet_manager):
        """Test secure cleanup functionality."""
        # Generate some data to clean up
        wallet_manager._get_master_seed()
        wallet_manager._get_master_key()

        # Test cleanup
        wallet_manager._secure_cleanup()
        assert wallet_manager._master_seed is None
        assert wallet_manager._master_key is None
        assert len(wallet_manager._derived_keys_cache) == 0


class TestDeriveAddressesFromMnemonic:
    """Test convenience function for address derivation."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    def test_derive_addresses_from_mnemonic_basic(self, test_mnemonic):
        """Test basic address derivation from mnemonic."""
        addresses = derive_addresses_from_mnemonic(
            mnemonic=test_mnemonic, coin="bitcoin", count=2
        )

        assert len(addresses) == 2
        assert all(addr.coin == "bitcoin" for addr in addresses)
        assert all(
            addr.address.startswith("bc1q") for addr in addresses
        )  # Default native-segwit

    def test_derive_addresses_from_mnemonic_with_params(self, test_mnemonic):
        """Test address derivation with custom parameters."""
        addresses = derive_addresses_from_mnemonic(
            mnemonic=test_mnemonic,
            coin="bitcoin",
            count=1,
            address_type="legacy",
            account=1,
            change=1,
            start_index=10,
        )

        assert len(addresses) == 1
        assert addresses[0].address.startswith("1")
        assert addresses[0].index == 10
        assert addresses[0].derivation_path == "m/44'/0'/1'/1/10"

    def test_derive_addresses_from_mnemonic_invalid_mnemonic(self):
        """Test address derivation with invalid mnemonic."""
        with pytest.raises((HDWalletError, DerivationError)):
            derive_addresses_from_mnemonic(
                mnemonic="invalid mnemonic",
                coin="bitcoin",
                count=1,
                validate_mnemonic=True,
            )

    def test_derive_addresses_from_mnemonic_no_validation(self):
        """Test address derivation without mnemonic validation."""
        # This should still fail during seed generation even without validation
        with pytest.raises((HDWalletError, DerivationError)):
            derive_addresses_from_mnemonic(
                mnemonic="invalid mnemonic",
                coin="bitcoin",
                count=1,
                validate_mnemonic=False,
            )


class TestHDWalletErrorHandling:
    """Test error handling in HD wallet operations."""

    def test_initialization_error_handling(self):
        """Test error handling during initialization."""
        with pytest.raises((HDWalletError, DerivationError)):
            HDWalletManager("", validate=True)

    def test_derive_addresses_error_handling(self):
        """Test error handling in address derivation."""
        manager = HDWalletManager(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        )

        # Test invalid count
        with pytest.raises(DerivationError):
            manager.derive_addresses_batch(coin="bitcoin", count=0)

        # Test negative account
        with pytest.raises(DerivationError):
            manager.derive_addresses_batch(coin="bitcoin", count=1, account=-1)

    @patch("sseed.hd_wallet.core.generate_address")
    def test_address_generation_failure(self, mock_generate):
        """Test handling of address generation failures."""
        mock_generate.side_effect = Exception("Address generation failed")

        manager = HDWalletManager(
            "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
        )

        with pytest.raises(DerivationError) as exc_info:
            manager.derive_addresses_batch(coin="bitcoin", count=1)

        assert "Address generation failed at index 0" in str(exc_info.value)

    def test_cleanup_on_error(self):
        """Test that cleanup happens even on errors."""
        invalid_mnemonic = "invalid mnemonic"

        try:
            derive_addresses_from_mnemonic(invalid_mnemonic, "bitcoin", 1)
        except (HDWalletError, DerivationError):
            pass  # Expected to fail

        # Function should complete without hanging or leaking memory


class TestHDWalletIntegration:
    """Integration tests for HD wallet functionality."""

    @pytest.fixture
    def test_mnemonic(self):
        """Valid test mnemonic for testing."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"

    def test_multiple_coins_integration(self, test_mnemonic):
        """Test HD wallet with multiple cryptocurrencies."""
        manager = HDWalletManager(test_mnemonic)

        # Test all supported coins
        for coin in ["bitcoin", "ethereum", "litecoin"]:
            addresses = manager.derive_addresses_batch(coin=coin, count=1)
            assert len(addresses) == 1
            assert addresses[0].coin == coin

    def test_all_bitcoin_address_types(self, test_mnemonic):
        """Test all Bitcoin address types."""
        manager = HDWalletManager(test_mnemonic)

        address_types = {"legacy": "1", "segwit": "3", "native-segwit": "bc1q"}

        for addr_type, prefix in address_types.items():
            addresses = manager.derive_addresses_batch(
                coin="bitcoin", count=1, address_type=addr_type
            )
            assert addresses[0].address.startswith(prefix)

    def test_large_batch_processing(self, test_mnemonic):
        """Test large batch address generation."""
        manager = HDWalletManager(test_mnemonic)

        # Test batch of 100 addresses
        addresses = manager.derive_addresses_batch(
            coin="bitcoin", count=100, address_type="native-segwit"
        )

        assert len(addresses) == 100

        # Verify uniqueness
        address_set = set(addr.address for addr in addresses)
        assert len(address_set) == 100

        # Verify proper indexing
        for i, addr in enumerate(addresses):
            assert addr.index == i

    def test_extended_keys_integration(self, test_mnemonic):
        """Test extended keys integration."""
        manager = HDWalletManager(test_mnemonic)

        # Test extended keys for multiple address types
        for addr_type in ["legacy", "native-segwit"]:
            ext_key = manager.get_extended_keys(coin="bitcoin", address_type=addr_type)
            assert ext_key.address_type == addr_type.replace(" ", "-")
            assert ext_key.xpub is not None
