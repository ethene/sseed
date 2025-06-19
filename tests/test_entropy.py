"""Tests for sseed.entropy module.

Tests secure entropy generation and memory handling as implemented in Phase 2.
"""

import pytest

from sseed.entropy import generate_entropy_bits, generate_entropy_bytes, secure_delete_variable
from sseed.exceptions import EntropyError, SecurityError


class TestEntropyGeneration:
    """Test entropy generation functions."""
    
    def test_generate_entropy_bits_default(self) -> None:
        """Test generating default 256 bits of entropy."""
        entropy = generate_entropy_bits()
        
        # Should be within range for 256 bits
        assert 0 <= entropy < (1 << 256)
    
    def test_generate_entropy_bits_custom(self) -> None:
        """Test generating custom number of entropy bits."""
        entropy = generate_entropy_bits(128)
        
        # Should be within range for 128 bits
        assert 0 <= entropy < (1 << 128)
    
    def test_generate_entropy_bits_invalid(self) -> None:
        """Test generating entropy with invalid bit counts."""
        with pytest.raises(SecurityError):
            generate_entropy_bits(0)
        
        with pytest.raises(SecurityError):
            generate_entropy_bits(-1)
        
        with pytest.raises(SecurityError):
            generate_entropy_bits(5000)  # Too large
    
    def test_generate_entropy_bytes_default(self) -> None:
        """Test generating default 32 bytes of entropy."""
        entropy = generate_entropy_bytes()
        
        assert len(entropy) == 32
        assert isinstance(entropy, bytes)
    
    def test_generate_entropy_bytes_custom(self) -> None:
        """Test generating custom number of entropy bytes."""
        entropy = generate_entropy_bytes(16)
        
        assert len(entropy) == 16
        assert isinstance(entropy, bytes)
    
    def test_generate_entropy_bytes_invalid(self) -> None:
        """Test generating entropy with invalid byte counts."""
        with pytest.raises(SecurityError):
            generate_entropy_bytes(0)
        
        with pytest.raises(SecurityError):
            generate_entropy_bytes(-1)
        
        with pytest.raises(SecurityError):
            generate_entropy_bytes(1000)  # Too large
    
    def test_entropy_uniqueness(self) -> None:
        """Test that generated entropy values are unique."""
        entropies = [generate_entropy_bits(256) for _ in range(100)]
        
        # All values should be unique
        assert len(set(entropies)) == 100
    
    def test_secure_delete_variable(self) -> None:
        """Test secure variable deletion."""
        # Test with various data types
        test_dict = {"key": "value"}
        test_list = [1, 2, 3]
        test_bytearray = bytearray(b"sensitive")
        
        # This should not raise an exception
        secure_delete_variable(test_dict, test_list, test_bytearray)


class TestFuzzTesting:
    """Fuzz testing for entropy generation as specified in Phase 7."""
    
    def test_fuzz_100k_seeds_unique_check(self) -> None:
        """Fuzz test: Generate 100k seeds and verify uniqueness (Phase 7 requirement 31).
        
        This test verifies that our entropy generation produces unique values
        even when generating large quantities, as specified in the PRD section 7.
        """
        import time
        start_time = time.time()
        
        # Generate 100,000 entropy values (256 bits each)
        num_seeds = 100_000
        seeds = set()
        
        for i in range(num_seeds):
            seed = generate_entropy_bits(256)
            seeds.add(seed)
            
            # Progress logging every 10k
            if (i + 1) % 10_000 == 0:
                print(f"Generated {i + 1:,} seeds, {len(seeds):,} unique")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify all seeds are unique
        assert len(seeds) == num_seeds, f"Expected {num_seeds} unique seeds, got {len(seeds)}"
        
        # Verify performance requirement (should be well under 5 seconds for 100k)
        print(f"Fuzz test completed in {duration:.2f} seconds ({num_seeds/duration:.0f} seeds/sec)")
        assert duration < 30.0, f"Fuzz test took too long: {duration:.2f}s (should be < 30s)"
        
        print(f"✅ Fuzz test PASSED: {num_seeds:,} unique seeds generated in {duration:.2f}s")
    
    def test_fuzz_entropy_bytes_unique_check(self) -> None:
        """Fuzz test: Generate 10k entropy byte arrays and verify uniqueness."""
        num_samples = 10_000
        entropy_set = set()
        
        for _ in range(num_samples):
            entropy_bytes = generate_entropy_bytes(32)
            entropy_set.add(entropy_bytes)
        
        # All byte arrays should be unique
        assert len(entropy_set) == num_samples
        print(f"✅ Bytes fuzz test PASSED: {num_samples:,} unique byte arrays generated") 