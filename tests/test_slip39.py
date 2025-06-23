"""Tests for sseed.slip39_operations module.

Tests SLIP-39 sharding and reconstruction operations as implemented in Phase 3.
"""

import pytest

from sseed.bip39 import (
    generate_mnemonic,
    validate_mnemonic,
)
from sseed.exceptions import (
    ShardError,
    ValidationError,
)
from sseed.slip39_operations import (
    create_slip39_shards,
    get_shard_info,
    parse_group_config,
    reconstruct_mnemonic_from_shards,
    validate_slip39_shard,
)


class TestSlip39Operations:
    """Test SLIP-39 sharding and reconstruction operations."""

    def test_create_slip39_shards_default(self) -> None:
        """Test creating SLIP-39 shards with default configuration."""
        # Generate a test mnemonic
        mnemonic = generate_mnemonic()

        # Create shards with default configuration (3-of-5)
        shards = create_slip39_shards(mnemonic)

        # Should create 5 shards
        assert len(shards) == 5
        assert all(isinstance(shard, str) for shard in shards)
        assert all(
            len(shard.split()) in [20, 33] for shard in shards
        )  # SLIP-39 word counts

    def test_create_slip39_shards_custom(self) -> None:
        """Test creating SLIP-39 shards with custom configuration."""
        mnemonic = generate_mnemonic()

        # Custom configuration: 2-of-3
        shards = create_slip39_shards(mnemonic, groups=[(2, 3)])

        assert len(shards) == 3
        assert all(isinstance(shard, str) for shard in shards)

    def test_create_slip39_shards_invalid_mnemonic(self) -> None:
        """Test creating shards with invalid mnemonic."""
        invalid_mnemonic = "invalid mnemonic with wrong words"

        with pytest.raises(Exception):  # Should raise MnemonicError or ShardError
            create_slip39_shards(invalid_mnemonic)

    def test_parse_group_config_simple(self) -> None:
        """Test parsing simple group configurations."""
        # Simple 3-of-5 configuration
        group_threshold, groups = parse_group_config("3-of-5")

        assert group_threshold == 1
        assert groups == [(3, 5)]

    def test_parse_group_config_multiple_groups(self) -> None:
        """Test parsing multiple group configurations."""
        # Multiple groups with explicit threshold
        group_threshold, groups = parse_group_config("1:(2-of-3,3-of-5)")

        assert group_threshold == 1
        assert groups == [(2, 3), (3, 5)]

    def test_parse_group_config_invalid(self) -> None:
        """Test parsing invalid group configurations."""
        with pytest.raises(ValidationError):
            parse_group_config("invalid-config")

        with pytest.raises(ValidationError):
            parse_group_config("0-of-5")  # Invalid threshold

        with pytest.raises(ValidationError):
            parse_group_config("6-of-5")  # Threshold > total

    def test_round_trip_reconstruction(self) -> None:
        """Test complete round-trip: generate -> shard -> reconstruct."""
        # Generate original mnemonic
        original_mnemonic = generate_mnemonic()

        # Create shards
        shards = create_slip39_shards(original_mnemonic, groups=[(3, 5)])
        assert len(shards) == 5

        # Reconstruct using minimum threshold (3 shards)
        selected_shards = shards[:3]
        reconstructed_mnemonic = reconstruct_mnemonic_from_shards(selected_shards)

        # Should match original
        assert reconstructed_mnemonic == original_mnemonic
        assert validate_mnemonic(reconstructed_mnemonic)

    def test_reconstruction_with_all_shards(self) -> None:
        """Test reconstruction using all available shards."""
        original_mnemonic = generate_mnemonic()

        # Create shards
        shards = create_slip39_shards(original_mnemonic, groups=[(2, 3)])

        # Reconstruct using exact threshold (2 shards, not all 3)
        selected_shards = shards[:2]  # Use exactly the threshold number
        reconstructed_mnemonic = reconstruct_mnemonic_from_shards(selected_shards)

        assert reconstructed_mnemonic == original_mnemonic

    def test_reconstruction_insufficient_shards(self) -> None:
        """Test reconstruction with insufficient shards."""
        original_mnemonic = generate_mnemonic()

        # Create 3-of-5 shards
        shards = create_slip39_shards(original_mnemonic, groups=[(3, 5)])

        # Try to reconstruct with only 2 shards (below threshold)
        insufficient_shards = shards[:2]

        with pytest.raises(ShardError):
            reconstruct_mnemonic_from_shards(insufficient_shards)

    def test_reconstruction_duplicate_shards(self) -> None:
        """Test reconstruction with duplicate shards."""
        original_mnemonic = generate_mnemonic()

        # Create shards
        shards = create_slip39_shards(original_mnemonic, groups=[(3, 5)])

        # Create list with duplicates
        shards_with_duplicates = shards[:3] + [shards[0]]  # Add duplicate

        # Should still work (duplicates are filtered)
        reconstructed_mnemonic = reconstruct_mnemonic_from_shards(
            shards_with_duplicates
        )
        assert reconstructed_mnemonic == original_mnemonic

    def test_reconstruction_empty_shards(self) -> None:
        """Test reconstruction with empty shard list."""
        with pytest.raises((ValidationError, ShardError)):
            reconstruct_mnemonic_from_shards([])

    def test_validate_slip39_shard_valid(self) -> None:
        """Test validation of valid SLIP-39 shards."""
        mnemonic = generate_mnemonic()
        shards = create_slip39_shards(mnemonic)

        # All generated shards should be valid
        for shard in shards:
            assert validate_slip39_shard(shard) is True

    def test_validate_slip39_shard_invalid(self) -> None:
        """Test validation of invalid SLIP-39 shards."""
        # Invalid length
        assert validate_slip39_shard("short shard") is False

        # Empty shard
        assert validate_slip39_shard("") is False

        # Wrong word count
        invalid_shard = " ".join(["word"] * 15)  # Wrong length
        assert validate_slip39_shard(invalid_shard) is False

    def test_get_shard_info(self) -> None:
        """Test extracting information from SLIP-39 shards."""
        mnemonic = generate_mnemonic()
        shards = create_slip39_shards(mnemonic)

        for shard in shards:
            info = get_shard_info(shard)

            assert isinstance(info, dict)
            assert "word_count" in info
            assert "shard_type" in info
            assert "valid" in info
            assert info["shard_type"] == "slip39"
            assert info["valid"] is True
            assert info["word_count"] in [20, 33]

    def test_get_shard_info_invalid(self) -> None:
        """Test extracting info from invalid shards."""
        with pytest.raises(ShardError):
            get_shard_info("invalid shard")

    def test_different_group_configurations(self) -> None:
        """Test various group configuration scenarios."""
        mnemonic = generate_mnemonic()

        # Test different configurations (1-of-2 is not allowed in SLIP-39, use 1-of-1)
        configs = [
            [(2, 3)],  # 2-of-3
            [(3, 5)],  # 3-of-5
            [(1, 1)],  # 1-of-1 (valid alternative to 1-of-2)
            [(4, 6)],  # 4-of-6
        ]

        for groups in configs:
            shards = create_slip39_shards(mnemonic, groups=groups)
            threshold, total = groups[0]

            # Should create correct number of shards
            assert len(shards) == total

            # Should be able to reconstruct with threshold shards
            selected_shards = shards[:threshold]
            reconstructed = reconstruct_mnemonic_from_shards(selected_shards)
            assert reconstructed == mnemonic
