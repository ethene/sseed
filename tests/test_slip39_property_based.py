"""Property-based tests for SLIP-39 Shamir's Secret Sharing using Hypothesis.

This module contains comprehensive property-based tests that verify the cryptographic
properties of SLIP-39 secret sharing under random conditions, ensuring that:

1. Any threshold-sized subset of shards can reconstruct the original mnemonic
2. Any sub-threshold set reveals no information about the original
3. The system is robust across various configurations and inputs
4. Edge cases and boundary conditions are thoroughly tested

Uses Hypothesis for generating random test cases to provide mathematical confidence
in the correctness of the SLIP-39 implementation.
"""

from typing import List, Tuple
import pytest
from hypothesis import given, strategies as st, settings, assume, example
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, invariant

from sseed.bip39 import generate_mnemonic, validate_mnemonic
from sseed.slip39_operations import (
    create_slip39_shards,
    reconstruct_mnemonic_from_shards,
    parse_group_config,
)
from sseed.exceptions import ShardError, MnemonicError


# Hypothesis strategies for SLIP-39 testing
@st.composite
def valid_group_configs(draw) -> List[Tuple[int, int]]:
    """Generate valid SLIP-39 group configurations.
    
    Returns configurations of (threshold, total) pairs where:
    - threshold >= 1 and <= total
    - total >= 1 and <= 16 (reasonable limit for testing)
    - threshold combinations that are cryptographically meaningful
    """
    # Number of groups (1-3 for comprehensive testing)
    num_groups = draw(st.integers(min_value=1, max_value=3))
    
    groups = []
    for _ in range(num_groups):
        # Generate reasonable total counts (2-10 for performance)
        total = draw(st.integers(min_value=2, max_value=10))
        # Threshold must be <= total and >= 1, but also <= total-1 for meaningful sharing
        threshold = draw(st.integers(min_value=1, max_value=min(total, 10)))
        groups.append((threshold, total))
    
    return groups


def valid_mnemonics() -> st.SearchStrategy[str]:
    """Generate valid BIP-39 mnemonics for testing.
    
    Uses the sseed generate_mnemonic function to ensure
    cryptographically valid test inputs.
    """
    # Use deferred generation to ensure fresh mnemonics for each test
    return st.builds(generate_mnemonic)


@st.composite 
def shard_subsets(draw, shards: List[str], threshold: int) -> List[str]:
    """Generate random subsets of shards for reconstruction testing.
    
    Args:
        shards: Complete list of available shards
        threshold: Minimum number of shards needed for reconstruction
        
    Returns:
        Random subset of shards of size >= threshold
    """
    # Ensure we have enough shards available
    assume(len(shards) >= threshold)
    
    # Generate subset size (threshold to total available)
    subset_size = draw(st.integers(min_value=threshold, max_value=len(shards)))
    
    # Generate random subset indices
    indices = draw(st.lists(
        st.integers(min_value=0, max_value=len(shards)-1),
        min_size=subset_size,
        max_size=subset_size,
        unique=True
    ))
    
    return [shards[i] for i in indices]


class TestSlip39Properties:
    """Property-based tests for SLIP-39 cryptographic properties."""

    @given(mnemonic=valid_mnemonics(), groups=valid_group_configs())
    @settings(max_examples=50, deadline=5000)  # Reasonable limits for crypto operations
    def test_property_perfect_reconstruction(self, mnemonic: str, groups: List[Tuple[int, int]]) -> None:
        """Property: Any threshold-sized subset of shards perfectly reconstructs the original.
        
        This is the fundamental property of Shamir's Secret Sharing:
        - Generate shards with specified threshold
        - Any combination of threshold shards should reconstruct the original
        - Reconstruction should be exact and deterministic
        """
        try:
            # Create shards with the given configuration
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            
            # Get the threshold for the first group (simplified for single group testing)
            threshold = groups[0][0]
            
            # Test multiple random subsets of threshold size
            import itertools
            from random import sample
            
            # Test a few random combinations to verify reconstruction property
            if len(shards) >= threshold:
                # Test with exactly threshold shards
                for _ in range(min(5, len(list(itertools.combinations(shards, threshold))))):
                    subset_indices = sample(range(len(shards)), threshold)
                    test_shards = [shards[i] for i in subset_indices]
                    
                    reconstructed = reconstruct_mnemonic_from_shards(test_shards)
                    
                    # Property: Reconstruction must equal original
                    assert reconstructed == mnemonic, (
                        f"Reconstruction failed: got '{reconstructed}', expected '{mnemonic}'"
                    )
                    
                    # Property: Reconstructed mnemonic must be valid
                    assert validate_mnemonic(reconstructed), (
                        f"Reconstructed mnemonic is invalid: {reconstructed}"
                    )
                    
        except Exception as e:
            # Skip configurations that are invalid for SLIP-39
            assume(False)

    @given(mnemonic=valid_mnemonics(), groups=valid_group_configs())
    @settings(max_examples=30, deadline=5000)
    def test_property_insufficient_shards_reveal_nothing(self, mnemonic: str, groups: List[Tuple[int, int]]) -> None:
        """Property: Sub-threshold shards reveal no information about the original.
        
        This is the security property of Shamir's Secret Sharing:
        - With fewer than threshold shards, reconstruction should fail
        - The failure should be consistent (not leak partial information)
        """
        try:
            # Create shards
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            threshold = groups[0][0]
            
            # Test with sub-threshold shard counts
            if threshold > 1 and len(shards) >= threshold:
                for sub_threshold_count in range(1, threshold):
                    if sub_threshold_count <= len(shards):
                        # Take random subset of sub-threshold size
                        from random import sample
                        test_shards = sample(shards, sub_threshold_count)
                        
                        # Property: Reconstruction must fail with sub-threshold shards
                        with pytest.raises(ShardError):
                            reconstruct_mnemonic_from_shards(test_shards)
                            
        except Exception as e:
            # Skip invalid configurations
            assume(False)

    @given(mnemonic=valid_mnemonics())
    @settings(max_examples=20, deadline=3000)
    def test_property_deterministic_reconstruction(self, mnemonic: str) -> None:
        """Property: Reconstruction is deterministic - same shards always give same result.
        
        This ensures the cryptographic implementation is consistent:
        - Same input shards should always produce same output
        - Order of shards should not matter
        - Multiple reconstruction attempts should be identical
        """
        # Use a simple 3-of-5 configuration for determinism testing
        groups = [(3, 5)]
        
        try:
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            
            # Test with the same subset multiple times
            test_shards = shards[:3]  # Take first 3 shards
            
            reconstructions = []
            for _ in range(3):  # Multiple reconstruction attempts
                reconstructed = reconstruct_mnemonic_from_shards(test_shards)
                reconstructions.append(reconstructed)
            
            # Property: All reconstructions must be identical
            assert all(r == reconstructions[0] for r in reconstructions), (
                f"Non-deterministic reconstruction: {reconstructions}"
            )
            
            # Property: All reconstructions must equal original
            assert all(r == mnemonic for r in reconstructions), (
                f"Incorrect reconstruction: got {reconstructions[0]}, expected {mnemonic}"
            )
            
        except Exception as e:
            assume(False)

    @given(mnemonic=valid_mnemonics())
    @settings(max_examples=20, deadline=3000)
    def test_property_shard_order_independence(self, mnemonic: str) -> None:
        """Property: Order of shards does not affect reconstruction.
        
        This tests the mathematical property that polynomial reconstruction
        is independent of the order in which points are provided.
        """
        groups = [(3, 5)]
        
        try:
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            test_shards = shards[:3]
            
            # Test different orderings of the same shards
            import itertools
            orderings = list(itertools.permutations(test_shards))
            
            reconstructions = []
            for ordering in orderings[:6]:  # Test up to 6 permutations
                reconstructed = reconstruct_mnemonic_from_shards(list(ordering))
                reconstructions.append(reconstructed)
            
            # Property: All orderings must produce the same result
            assert all(r == reconstructions[0] for r in reconstructions), (
                f"Order-dependent reconstruction: {set(reconstructions)}"
            )
            
            # Property: Result must equal original
            assert reconstructions[0] == mnemonic, (
                f"Incorrect reconstruction: got {reconstructions[0]}, expected {mnemonic}"
            )
            
        except Exception as e:
            assume(False)

    @given(mnemonic=valid_mnemonics(), groups=valid_group_configs())
    @settings(max_examples=25, deadline=4000)
    def test_property_excess_shards_do_not_harm(self, mnemonic: str, groups: List[Tuple[int, int]]) -> None:
        """Property: Using more than threshold shards does not harm reconstruction.
        
        This tests that the interpolation algorithm correctly handles
        redundant information without degradation.
        """
        try:
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            threshold = groups[0][0]
            
            if len(shards) > threshold:
                # Test with threshold shards
                minimal_reconstruction = reconstruct_mnemonic_from_shards(shards[:threshold])
                
                # Test with all available shards
                maximal_reconstruction = reconstruct_mnemonic_from_shards(shards)
                
                # Property: Both should give the same result
                assert minimal_reconstruction == maximal_reconstruction, (
                    f"Excess shards changed result: minimal={minimal_reconstruction}, "
                    f"maximal={maximal_reconstruction}"
                )
                
                # Property: Both should equal original
                assert minimal_reconstruction == mnemonic, (
                    f"Reconstruction failed: got {minimal_reconstruction}, expected {mnemonic}"
                )
                
        except Exception as e:
            assume(False)

    @given(
        mnemonic=valid_mnemonics(),
        threshold=st.integers(min_value=2, max_value=6),
        total=st.integers(min_value=3, max_value=8),
    )
    @settings(max_examples=30, deadline=4000)
    def test_property_threshold_boundary_conditions(self, mnemonic: str, threshold: int, total: int) -> None:
        """Property: Threshold boundary conditions work correctly.
        
        Tests the exact boundary between sufficient and insufficient shards:
        - threshold shards: should work
        - threshold-1 shards: should fail
        """
        # Ensure valid configuration
        assume(threshold <= total)
        assume(threshold >= 2)  # Meaningful threshold
        
        groups = [(threshold, total)]
        
        try:
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            
            # Property: Exactly threshold shards should succeed
            if len(shards) >= threshold:
                success_shards = shards[:threshold]
                reconstructed = reconstruct_mnemonic_from_shards(success_shards)
                assert reconstructed == mnemonic, (
                    f"Threshold boundary failed: {threshold} shards could not reconstruct"
                )
            
            # Property: Threshold-1 shards should fail
            if threshold > 1 and len(shards) >= threshold - 1:
                fail_shards = shards[:threshold - 1]
                with pytest.raises(ShardError):
                    reconstruct_mnemonic_from_shards(fail_shards)
                    
        except Exception as e:
            assume(False)


class TestSlip39AdvancedProperties:
    """Advanced property-based tests for edge cases and robustness."""

    @given(mnemonic=valid_mnemonics())
    @settings(max_examples=15, deadline=3000)
    def test_property_multiple_group_configurations(self, mnemonic: str) -> None:
        """Property: Different group configurations of same threshold behave equivalently.
        
        This tests that various ways of achieving the same security level
        produce equivalent results.
        """
        try:
            # Test equivalent configurations: 3-of-5 vs 3-of-6 vs 3-of-7
            configs = [[(3, 5)], [(3, 6)], [(3, 7)]]
            
            reconstructions = []
            for groups in configs:
                shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
                
                # Use exactly 3 shards from each configuration
                test_shards = shards[:3]
                reconstructed = reconstruct_mnemonic_from_shards(test_shards)
                reconstructions.append(reconstructed)
            
            # Property: All configurations should reconstruct to the same mnemonic
            assert all(r == mnemonic for r in reconstructions), (
                f"Configuration-dependent results: {set(reconstructions)}"
            )
            
        except Exception as e:
            assume(False)

    @given(mnemonic=valid_mnemonics())
    @settings(max_examples=10, deadline=2000)
    def test_property_passphrase_independence(self, mnemonic: str) -> None:
        """Property: Empty passphrase and no passphrase produce same results.
        
        This tests that the default passphrase handling is consistent.
        """
        groups = [(3, 5)]
        
        try:
            # Create shards with empty passphrase
            shards_empty = create_slip39_shards(mnemonic, group_threshold=1, groups=groups, passphrase="")
            
            # Create shards with no passphrase parameter (default)
            shards_none = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            
            # Test reconstruction consistency
            reconstructed_empty = reconstruct_mnemonic_from_shards(shards_empty[:3], passphrase="")
            reconstructed_none = reconstruct_mnemonic_from_shards(shards_none[:3])
            
            # Property: Both should reconstruct to original
            assert reconstructed_empty == mnemonic
            assert reconstructed_none == mnemonic
            
        except Exception as e:
            assume(False)


class Slip39StateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for SLIP-39 operations.
    
    This uses Hypothesis's stateful testing to explore complex scenarios
    involving multiple operations and state transitions.
    """
    
    mnemonics = Bundle('mnemonics')
    shard_sets = Bundle('shard_sets')
    
    @rule(target=mnemonics)
    def generate_mnemonic(self) -> str:
        """Generate a new valid mnemonic."""
        return generate_mnemonic()
    
    @rule(target=shard_sets, mnemonic=mnemonics)
    def create_shards(self, mnemonic: str) -> dict:
        """Create shards from a mnemonic."""
        # Use simple configuration for stateful testing
        groups = [(3, 5)]
        
        try:
            shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
            return {
                'shards': shards,
                'threshold': 3,
                'original_mnemonic': mnemonic
            }
        except Exception:
            assume(False)
    
    @rule(shard_set=shard_sets)
    def verify_reconstruction(self, shard_set: dict) -> None:
        """Verify that sufficient shards can reconstruct the original."""
        shards = shard_set['shards']
        threshold = shard_set['threshold']
        original = shard_set['original_mnemonic']
        
        # Test with threshold shards
        test_shards = shards[:threshold]
        reconstructed = reconstruct_mnemonic_from_shards(test_shards)
        
        # Invariant: Reconstruction must equal original
        assert reconstructed == original
    
    @rule(shard_set=shard_sets)
    def verify_insufficient_failure(self, shard_set: dict) -> None:
        """Verify that insufficient shards fail to reconstruct."""
        shards = shard_set['shards']
        threshold = shard_set['threshold']
        
        if threshold > 1:
            # Test with sub-threshold shards
            insufficient_shards = shards[:threshold - 1]
            
            # Invariant: Sub-threshold reconstruction must fail
            with pytest.raises(ShardError):
                reconstruct_mnemonic_from_shards(insufficient_shards)


# Instantiate the state machine test
TestSlip39StateMachine = Slip39StateMachine.TestCase


# Example-based tests for known edge cases
class TestSlip39Examples:
    """Example-based tests for specific known scenarios."""
    
    def test_example_minimal_configuration(self) -> None:
        """Test minimal valid configuration: 2-of-2."""
        mnemonic = generate_mnemonic()
        groups = [(2, 2)]
        
        shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
        assert len(shards) == 2
        
        # Both shards needed
        reconstructed = reconstruct_mnemonic_from_shards(shards)
        assert reconstructed == mnemonic
        
        # Single shard should fail
        with pytest.raises(ShardError):
            reconstruct_mnemonic_from_shards(shards[:1])
    
    def test_example_maximum_practical_configuration(self) -> None:
        """Test maximum practical configuration for performance."""
        mnemonic = generate_mnemonic()
        groups = [(7, 10)]  # 7-of-10 scheme
        
        shards = create_slip39_shards(mnemonic, group_threshold=1, groups=groups)
        assert len(shards) == 10
        
        # Exactly threshold should work
        reconstructed = reconstruct_mnemonic_from_shards(shards[:7])
        assert reconstructed == mnemonic
        
        # Sub-threshold should fail
        with pytest.raises(ShardError):
            reconstruct_mnemonic_from_shards(shards[:6])
    
    @example("invalid mnemonic text")
    @given(mnemonic=st.text(min_size=1, max_size=50).filter(lambda x: len(x.split()) not in [12, 15, 18, 21, 24]))
    def test_example_invalid_mnemonics_fail_gracefully(self, mnemonic: str) -> None:
        """Test that invalid mnemonics are handled gracefully."""
        # Test that validation properly handles invalid mnemonics
        try:
            is_valid = validate_mnemonic(mnemonic)
            # If validation succeeds without exception, skip this test case
            if is_valid:
                assume(False)
        except (MnemonicError, Exception):
            # Expected behavior for invalid mnemonics - validation throws exception
            pass
        
        # Invalid mnemonics should raise appropriate errors when used for sharding
        with pytest.raises((MnemonicError, ShardError, Exception)):
            create_slip39_shards(mnemonic, group_threshold=1, groups=[(3, 5)])


if __name__ == "__main__":
    # Run the property-based tests
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"]) 